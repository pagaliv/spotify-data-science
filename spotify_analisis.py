"""Funciones de análisis del proyecto Spotify.

Módulo sin estado: carga los CSV extraídos con Spotify/Last.fm, consolida el
modelo de datos, enriquece artistas y calcula los análisis del informe.
"""

from __future__ import annotations

import json
import math
import os
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from scipy.stats import mannwhitneyu, spearmanr
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

load_dotenv()

SEMILLA = 42
RANGOS = {
    "short_term": "ultimas_4_semanas",
    "medium_term": "ultimos_6_meses",
    "long_term": "varios_anios",
}
ORDEN_RANGOS = {etiqueta: i for i, etiqueta in enumerate(RANGOS.values(), start=1)}
USUARIOS = ("pablo", "jorge")
N_SIMILARES = 20
MIN_SOPORTE_GENERO = 2

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
DEEZER_URL = "https://api.deezer.com/search/artist"


# ---------------------------------------------------------------------------
# Carga y validación
# ---------------------------------------------------------------------------


def cargar_datos(rutas: dict[str, str]) -> pd.DataFrame:
    """Carga un CSV por usuario y devuelve el formato largo combinado."""
    partes = []
    for usuario, ruta in rutas.items():
        df = pd.read_csv(ruta, encoding="utf-8-sig")
        df["usuario"] = usuario
        partes.append(df)
    df = pd.concat(partes, ignore_index=True)
    df["rango"] = df["rango"].astype(str).str.strip()
    df["rango_orden"] = df["rango"].map(ORDEN_RANGOS)
    df["posicion"] = pd.to_numeric(df["posicion"], errors="coerce").astype("Int64")
    df["artista"] = df["artista"].astype(str).str.strip()
    df["generos"] = df["generos"].fillna("").astype(str)
    return df.sort_values(["usuario", "rango_orden", "posicion"]).reset_index(drop=True)


def validar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen de calidad por usuario y rango."""
    filas = []
    for (usuario, rango), grupo in df.groupby(["usuario", "rango"], sort=False):
        filas.append(
            {
                "usuario": usuario,
                "rango": rango,
                "filas": len(grupo),
                "artistas_unicos": grupo["artista"].nunique(),
                "duplicados_rango_posicion": int(
                    grupo.duplicated(["rango", "posicion"]).sum()
                ),
                "posiciones_fuera_de_rango": int(
                    ((grupo["posicion"] < 1) | (grupo["posicion"] > 50)).sum()
                ),
                "sin_genero": int(grupo["generos"].str.strip().eq("").sum()),
            }
        )
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Géneros
# ---------------------------------------------------------------------------


def explosionar_generos(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por usuario, rango, artista y género."""
    filas = []
    for fila in df.itertuples(index=False):
        generos = {
            g.strip().lower()
            for g in str(fila.generos).split(";")
            if g and g.strip()
        }
        for genero in sorted(generos):
            filas.append(
                {
                    "usuario": fila.usuario,
                    "rango": fila.rango,
                    "rango_orden": fila.rango_orden,
                    "posicion": fila.posicion,
                    "artista": fila.artista,
                    "genero": genero,
                }
            )
    return pd.DataFrame(filas)


def resumen_por_usuario_rango(df: pd.DataFrame) -> pd.DataFrame:
    """Cobertura y diversidad básica por usuario y rango."""
    filas = []
    for (usuario, rango), grupo in df.groupby(["usuario", "rango"], sort=False):
        artistas = grupo["artista"].nunique()
        con_genero = grupo.loc[grupo["generos"].str.strip().ne(""), "artista"].nunique()
        generos = {
            g.strip().lower()
            for valor in grupo["generos"]
            for g in valor.split(";")
            if g.strip()
        }
        conteo = Counter(
            g.strip().lower()
            for valor in grupo["generos"]
            for g in valor.split(";")
            if g.strip()
        )
        filas.append(
            {
                "usuario": usuario,
                "rango": rango,
                "n_artistas": artistas,
                "n_con_genero": con_genero,
                "pct_con_genero": round(100 * con_genero / artistas, 2) if artistas else 0,
                "n_generos": len(generos),
                "genero_top": conteo.most_common(1)[0][0] if conteo else "",
            }
        )
    return pd.DataFrame(filas)


def genero_principal(df_generos: pd.DataFrame) -> pd.Series:
    """Género más frecuente por artista (desempate alfabético)."""
    salida = {}
    for artista, grupo in df_generos.groupby("artista"):
        conteo = grupo["genero"].value_counts()
        maximos = conteo[conteo == conteo.max()].index.sort_values()
        salida[artista] = maximos[0] if len(maximos) else np.nan
    return pd.Series(salida, name="genero_principal")


def perfil_generos(
    df_generos: pd.DataFrame,
    usuario: str | None = None,
    rango: str | None = None,
) -> pd.Series:
    """Número de artistas distintos por género."""
    filtrado = df_generos
    if usuario is not None:
        filtrado = filtrado[filtrado["usuario"] == usuario]
    if rango is not None:
        filtrado = filtrado[filtrado["rango"] == rango]
    return (
        filtrado.drop_duplicates(["artista", "genero"])["genero"]
        .value_counts()
        .sort_values(ascending=False)
    )


def matriz_artista_genero(df_generos: pd.DataFrame) -> pd.DataFrame:
    """Matriz binaria artista × género."""
    tabla = (
        df_generos.drop_duplicates(["artista", "genero"])
        .assign(valor=1)
        .pivot(index="artista", columns="genero", values="valor")
        .fillna(0)
    )
    return tabla.astype(int)


def entropia_shannon(conteo: pd.Series) -> float:
    """Entropía (base 2) de una distribución de frecuencias."""
    total = conteo.sum()
    if total == 0:
        return 0.0
    proporciones = conteo / total
    return float(-(proporciones * np.log2(proporciones)).sum())


# ---------------------------------------------------------------------------
# Similitud entre usuarios y estabilidad temporal
# ---------------------------------------------------------------------------


def jaccard(a: set, b: set) -> float:
    """Coeficiente de Jaccard entre dos conjuntos."""
    union = set(a) | set(b)
    return len(set(a) & set(b)) / len(union) if union else 0.0


def similitud_coseno(a: pd.Series, b: pd.Series) -> float:
    """Coseno entre dos vectores de frecuencias alineados."""
    a, b = a.align(b, fill_value=0)
    norma = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / norma) if norma else 0.0


def _vectores_usuario_rango(
    df_generos: pd.DataFrame, usuario: str, rango: str
) -> tuple[set, pd.Series]:
    filtrado = df_generos[
        (df_generos["usuario"] == usuario) & (df_generos["rango"] == rango)
    ]
    artistas = set(filtrado["artista"])
    vector = perfil_generos(filtrado)
    return artistas, vector


def estabilidad_por_rangos(df_generos: pd.DataFrame, usuario: str) -> pd.DataFrame:
    """Jaccard de artistas y coseno de géneros entre cada par de rangos."""
    filas = []
    for rango_a, rango_b in combinations(ORDEN_RANGOS, 2):
        artistas_a, vector_a = _vectores_usuario_rango(df_generos, usuario, rango_a)
        artistas_b, vector_b = _vectores_usuario_rango(df_generos, usuario, rango_b)
        filas.append(
            {
                "usuario": usuario,
                "rango_a": rango_a,
                "rango_b": rango_b,
                "jaccard_artistas": round(jaccard(artistas_a, artistas_b), 4),
                "coseno_generos": round(similitud_coseno(vector_a, vector_b), 4),
                "n_comun_artistas": len(artistas_a & artistas_b),
            }
        )
    return pd.DataFrame(filas)


def tabla_compatibilidad(df_generos: pd.DataFrame) -> pd.DataFrame:
    """Compatibilidad entre los dos usuarios por rango y global."""
    filas = []
    for rango in list(ORDEN_RANGOS) + ["global"]:
        conjuntos, vectores = {}, {}
        for usuario in sorted(df_generos["usuario"].unique()):
            filtrado = df_generos[df_generos["usuario"] == usuario]
            if rango != "global":
                filtrado = filtrado[filtrado["rango"] == rango]
            conjuntos[usuario] = set(filtrado["artista"])
            vectores[usuario] = perfil_generos(filtrado)
        usuarios = sorted(conjuntos)
        if len(usuarios) != 2:
            continue
        a, b = usuarios
        filas.append(
            {
                "rango": rango,
                "jaccard_artistas": round(jaccard(conjuntos[a], conjuntos[b]), 4),
                "coseno_generos": round(
                    similitud_coseno(vectores[a], vectores[b]), 4
                ),
                "n_comun_artistas": len(conjuntos[a] & conjuntos[b]),
                "n_comun_generos": len(
                    set(vectores[a].index) & set(vectores[b].index)
                ),
            }
        )
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Enriquecimiento con Last.fm y Deezer
# ---------------------------------------------------------------------------


def _peticion_json(url: str, params: dict, intentos: int = 3) -> dict:
    espera = 1.0
    for intento in range(intentos):
        try:
            respuesta = requests.get(url, params=params, timeout=15)
            if respuesta.status_code == 429 or respuesta.status_code >= 500:
                raise requests.HTTPError(f"HTTP {respuesta.status_code}")
            respuesta.raise_for_status()
            return respuesta.json()
        except (requests.RequestException, ValueError):
            if intento == intentos - 1:
                return {}
            time.sleep(espera)
            espera *= 2
    return {}


def _lastfm_key() -> str:
    clave = os.getenv("LASTFM_API_KEY")
    if not clave:
        raise RuntimeError("Falta LASTFM_API_KEY en el fichero .env")
    return clave


def info_artista(artista: str) -> dict:
    """Popularidad y metadatos básicos de Last.fm (artist.getInfo)."""
    datos = _peticion_json(
        LASTFM_URL,
        {
            "method": "artist.getinfo",
            "artist": artista,
            "api_key": _lastfm_key(),
            "format": "json",
            "autocorrect": 1,
        },
    )
    info = datos.get("artist", {})
    stats = info.get("stats", {})
    return {
        "listeners": int(stats["listeners"]) if stats.get("listeners") else None,
        "playcount": int(stats["playcount"]) if stats.get("playcount") else None,
        "mbid": info.get("mbid") or None,
        "lastfm_url": info.get("url") or None,
    }


def similares_artista(artista: str, limite: int = N_SIMILARES) -> list[dict]:
    """Artistas similares según artist.getSimilar."""
    datos = _peticion_json(
        LASTFM_URL,
        {
            "method": "artist.getsimilar",
            "artist": artista,
            "api_key": _lastfm_key(),
            "format": "json",
            "autocorrect": 1,
            "limit": limite,
        },
    )
    similares = datos.get("similarartists", {}).get("artist", [])
    return [
        {"similar": s.get("name", "").strip(), "match": float(s.get("match", 0))}
        for s in similares
        if s.get("name")
    ]


def deezer_artista(artista: str) -> dict:
    """Popularidad de Deezer (API pública, sin autenticación)."""
    datos = _peticion_json(DEEZER_URL, {"q": artista, "limit": 5})
    resultados = datos.get("data", [])
    if not resultados:
        return {"deezer_fans": None, "deezer_nb_album": None, "deezer_url": None}
    objetivo = artista.casefold().strip()
    elegido = next(
        (r for r in resultados if str(r.get("name", "")).casefold().strip() == objetivo),
        resultados[0],
    )
    return {
        "deezer_fans": elegido.get("nb_fan"),
        "deezer_nb_album": elegido.get("nb_album"),
        "deezer_url": elegido.get("link"),
    }


def _cargar_cache(ruta: str | Path) -> dict:
    ruta = Path(ruta)
    if not ruta.exists():
        return {"version": 1, "entries": {}}
    with open(ruta, encoding="utf-8") as fichero:
        return json.load(fichero)


def _guardar_cache(cache: dict, ruta: str | Path) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fichero:
        json.dump(cache, fichero, ensure_ascii=False, indent=2)


def enriquecer_artistas(
    artistas: list[str],
    ruta_cache: str | Path = "cache/enriquecimiento.json",
    pausa_lastfm: float = 0.25,
    pausa_deezer: float = 0.1,
    guardar_cada: int = 20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Enriquece artistas con Last.fm y Deezer usando caché persistente."""
    cache = _cargar_cache(ruta_cache)
    entradas = cache["entries"]
    pendientes = 0

    for artista in sorted({a for a in artistas if a}):
        clave_info = f"getinfo::{artista}"
        clave_simil = f"getsimilar::{artista}"
        clave_deezer = f"deezer::{artista}"

        if clave_info not in entradas:
            entradas[clave_info] = info_artista(artista)
            time.sleep(pausa_lastfm)
            pendientes += 1
        if clave_simil not in entradas:
            entradas[clave_simil] = similares_artista(artista)
            time.sleep(pausa_lastfm)
            pendientes += 1
        if clave_deezer not in entradas:
            entradas[clave_deezer] = deezer_artista(artista)
            time.sleep(pausa_deezer)
            pendientes += 1

        if pendientes and pendientes % guardar_cada == 0:
            _guardar_cache(cache, ruta_cache)

    _guardar_cache(cache, ruta_cache)

    filas, similitudes = [], []
    for artista in sorted({a for a in artistas if a}):
        info = entradas.get(f"getinfo::{artista}", {})
        simil = entradas.get(f"getsimilar::{artista}", [])
        deezer = entradas.get(f"deezer::{artista}", {})
        filas.append(
            {
                "artista": artista,
                "listeners": info.get("listeners"),
                "playcount": info.get("playcount"),
                "mbid": info.get("mbid"),
                "lastfm_url": info.get("lastfm_url"),
                "n_similares": len(simil),
                "similar_top": simil[0]["similar"] if simil else None,
                "match_top": simil[0]["match"] if simil else None,
                "deezer_fans": deezer.get("deezer_fans"),
                "deezer_nb_album": deezer.get("deezer_nb_album"),
                "deezer_url": deezer.get("deezer_url"),
            }
        )
        for s in simil:
            similitudes.append(
                {"artista": artista, "similar": s["similar"], "match": s["match"]}
            )
    return pd.DataFrame(filas), pd.DataFrame(similitudes)


def unir_enriquecimiento(df: pd.DataFrame, df_artistas: pd.DataFrame) -> pd.DataFrame:
    """Añade los atributos de artista al historial largo."""
    return df.merge(df_artistas, on="artista", how="left")


# ---------------------------------------------------------------------------
# Nulos, imputación y popularidad
# ---------------------------------------------------------------------------


FUENTES_COLUMNAS = {
    "generos": "Last.fm (getTopTags)",
    "listeners": "Last.fm (getInfo)",
    "playcount": "Last.fm (getInfo)",
    "mbid": "Last.fm (getInfo)",
    "n_similares": "Last.fm (getSimilar)",
    "deezer_fans": "Deezer",
    "deezer_nb_album": "Deezer",
}


def resumen_nulos(df_artistas: pd.DataFrame) -> pd.DataFrame:
    """Porcentaje de nulos por columna enriquecida."""
    filas = []
    total = len(df_artistas)
    for columna, fuente in FUENTES_COLUMNAS.items():
        if columna not in df_artistas:
            continue
        if columna == "generos":
            nulos = int(df_artistas[columna].fillna("").astype(str).str.strip().eq("").sum())
        elif columna == "n_similares":
            nulos = int(df_artistas[columna].isna().sum())
        else:
            nulos = int(df_artistas[columna].isna().sum())
        filas.append(
            {
                "columna": columna,
                "fuente": fuente,
                "n_total": total,
                "n_nulos": nulos,
                "pct_nulos": round(100 * nulos / total, 2) if total else 0,
            }
        )
    return pd.DataFrame(filas)


def imputar_popularidad(
    df_artistas: pd.DataFrame,
    columna: str,
    min_grupo: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Imputa una columna numérica por mediana de género principal."""
    df = df_artistas.copy()
    col_imp = f"{columna}_imp"
    col_flag = f"imputado_{columna}"
    df[col_flag] = df[columna].isna()

    if "genero_principal" in df:
        medianas = (
            df.dropna(subset=[columna])
            .groupby("genero_principal")[columna]
            .agg(["median", "count"])
        )
        mediana_global = df[columna].median()
        valores = []
        for fila in df.itertuples(index=False):
            if pd.notna(getattr(fila, columna)):
                valores.append(getattr(fila, columna))
                continue
            grupo = getattr(fila, "genero_principal", None)
            if grupo in medianas.index and medianas.loc[grupo, "count"] >= min_grupo:
                valores.append(medianas.loc[grupo, "median"])
            else:
                valores.append(mediana_global)
        df[col_imp] = valores
    else:
        df[col_imp] = df[columna].fillna(df[columna].median())

    informe = pd.DataFrame(
        [
            {
                "columna": columna,
                "n_imputados": int(df[col_flag].sum()),
                "pct_imputados": round(100 * df[col_flag].mean(), 2),
                "mediana_global": df[columna].median(),
            }
        ]
    )
    return df, informe


def spearman_por_grupo(
    df: pd.DataFrame, columna_popularidad: str = "listeners"
) -> pd.DataFrame:
    """Spearman entre posición en el ranking y popularidad, por usuario/rango."""
    filas = []
    for (usuario, rango), grupo in df.groupby(["usuario", "rango"], sort=False):
        datos = grupo.dropna(subset=["posicion", columna_popularidad])
        datos = datos[datos[columna_popularidad] > 0]
        if len(datos) < 3:
            continue
        rho, p = spearmanr(
            datos["posicion"].astype(float),
            np.log10(datos[columna_popularidad].astype(float)),
        )
        filas.append(
            {
                "usuario": usuario,
                "rango": rango,
                "rho": round(float(rho), 4),
                "p_valor": round(float(p), 6),
                "n": len(datos),
            }
        )
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Afinidad usuario–artista
# ---------------------------------------------------------------------------


def pesos_usuario(df: pd.DataFrame, usuario: str, excluir: str | None = None) -> dict:
    """Peso de cada artista en el historial: 1.0 en el top-1, ~0.02 en el 50."""
    filtrado = df[df["usuario"] == usuario]
    if excluir is not None:
        filtrado = filtrado[filtrado["artista"] != excluir]
    pesos = {}
    for artista, grupo in filtrado.groupby("artista"):
        mejor = grupo["posicion"].min()
        pesos[artista] = max(0.0, (51 - float(mejor)) / 50)
    return pesos


def puntuacion_afinidad(
    artista: str,
    similitudes: pd.DataFrame,
    pesos: dict,
) -> float:
    """Solapamiento ponderado entre los similares del artista y el historial."""
    vecinos = similitudes[similitudes["artista"] == artista]
    if vecinos.empty:
        return float("nan")
    denominador = vecinos["match"].sum()
    if denominador == 0:
        return float("nan")
    numerador = sum(
        fila.match * pesos.get(fila.similar, 0.0) for fila in vecinos.itertuples(index=False)
    )
    return float(numerador / denominador)


def generar_candidatos(
    df: pd.DataFrame,
    similitudes: pd.DataFrame,
    top_por_usuario: int = 10,
    n: int = 20,
) -> list[str]:
    """Artistas similares a los favoritos que no están en ningún historial."""
    historial = set(df["artista"])
    candidatos: dict[str, list[float]] = {}
    for usuario in sorted(df["usuario"].unique()):
        top = (
            df[df["usuario"] == usuario]
            .sort_values("posicion")
            .drop_duplicates("artista")
            .head(top_por_usuario)["artista"]
        )
        for artista in top:
            for fila in similitudes[similitudes["artista"] == artista].itertuples(
                index=False
            ):
                if fila.similar not in historial:
                    candidatos.setdefault(fila.similar, []).append(float(fila.match))
    ordenados = sorted(
        candidatos.items(), key=lambda item: np.mean(item[1]), reverse=True
    )
    return [artista for artista, _ in ordenados[:n]]


def calcular_afinidad(
    df: pd.DataFrame,
    similitudes: pd.DataFrame,
    candidatos: list[str],
) -> pd.DataFrame:
    """Puntuación de afinidad de cada candidato para cada usuario."""
    usuarios = sorted(df["usuario"].unique())
    filas = []
    for candidato in candidatos:
        fila = {"artista_candidato": candidato}
        for usuario in usuarios:
            pesos = pesos_usuario(df, usuario)
            fila[usuario] = puntuacion_afinidad(candidato, similitudes, pesos)
        filas.append(fila)
    if not filas:
        return pd.DataFrame(columns=["artista_candidato", *usuarios])
    return pd.DataFrame(filas)


def evaluar_afinidad_loo(
    df: pd.DataFrame,
    similitudes: pd.DataFrame,
    candidatos: list[str],
    top_por_usuario: int = 10,
) -> pd.DataFrame:
    """Comprueba si los favoritos ocultos puntúan más que los candidatos-control."""
    filas = []
    for usuario in sorted(df["usuario"].unique()):
        top = (
            df[df["usuario"] == usuario]
            .sort_values("posicion")
            .drop_duplicates("artista")
            .head(top_por_usuario)["artista"]
        )
        ocultos = []
        for artista in top:
            pesos = pesos_usuario(df, usuario, excluir=artista)
            ocultos.append(puntuacion_afinidad(artista, similitudes, pesos))
        controles = [
            puntuacion_afinidad(c, similitudes, pesos_usuario(df, usuario))
            for c in candidatos
        ]
        ocultos = [v for v in ocultos if not math.isnan(v)]
        controles = [v for v in controles if not math.isnan(v)]
        if len(ocultos) >= 3 and len(controles) >= 3:
            estadistico, p = mannwhitneyu(ocultos, controles, alternative="greater")
        else:
            estadistico, p = float("nan"), float("nan")
        filas.append(
            {
                "usuario": usuario,
                "n_ocultos": len(ocultos),
                "n_controles": len(controles),
                "mediana_ocultos": round(float(np.median(ocultos)), 4) if ocultos else np.nan,
                "mediana_controles": round(float(np.median(controles)), 4) if controles else np.nan,
                "u_mannwhitney": estadistico,
                "p_valor": p,
            }
        )
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------


def matriz_dummy_artistas(
    df_generos: pd.DataFrame, min_soporte: int = MIN_SOPORTE_GENERO
) -> tuple[pd.DataFrame, dict]:
    """Matriz binaria artista × género filtrando géneros poco frecuentes."""
    matriz = matriz_artista_genero(df_generos)
    soporte = matriz.sum(axis=0)
    conservados = soporte[soporte >= min_soporte].index
    matriz = matriz[conservados]
    matriz = matriz[matriz.sum(axis=1) > 0]
    info = {
        "n_artistas": int(matriz.shape[0]),
        "n_generos": int(matriz.shape[1]),
        "generos_excluidos": int((soporte < min_soporte).sum()),
        "artistas_excluidos": int(
            matriz_artista_genero(df_generos).shape[0] - matriz.shape[0]
        ),
    }
    return matriz, info


def elegir_k(X: np.ndarray, rango_k: range = range(2, 9)) -> tuple[pd.DataFrame, int]:
    """Codo y silhouette para elegir el número de clusters."""
    filas = []
    for k in rango_k:
        if k >= len(X):
            continue
        modelo = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA)
        etiquetas = modelo.fit_predict(X)
        filas.append(
            {
                "k": k,
                "inercia": float(modelo.inertia_),
                "silhouette": float(silhouette_score(X, etiquetas)),
            }
        )
    tabla = pd.DataFrame(filas)
    mejor = tabla["silhouette"].max()
    empatados = tabla[tabla["silhouette"] >= mejor - 0.02]
    k_elegido = int(empatados.iloc[0]["k"]) if len(empatados) else int(tabla.iloc[0]["k"])
    return tabla, k_elegido


def ajustar_clusters(X: np.ndarray, k: int) -> tuple[np.ndarray, KMeans]:
    """Ajusta K-Means con semilla fija."""
    modelo = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA)
    etiquetas = modelo.fit_predict(X)
    return etiquetas, modelo


def etiquetar_clusters(X: pd.DataFrame, etiquetas: np.ndarray) -> pd.DataFrame:
    """Top-3 géneros con mayor prevalencia relativa por cluster."""
    tabla = X.copy()
    tabla["cluster"] = etiquetas
    prevalencia_global = X.mean(axis=0)
    filas = []
    for cluster, grupo in tabla.groupby("cluster"):
        prevalencia = grupo.drop(columns="cluster").mean(axis=0)
        lift = (prevalencia / prevalencia_global.replace(0, np.nan)).fillna(0)
        top = lift.sort_values(ascending=False).head(3).index.tolist()
        filas.append(
            {
                "cluster": int(cluster),
                "n_artistas": len(grupo),
                "generos_top": ", ".join(top),
            }
        )
    return pd.DataFrame(filas).sort_values("cluster").reset_index(drop=True)


def proyectar_pca(X: np.ndarray) -> tuple[np.ndarray, float]:
    """Proyección 2D para visualización."""
    pca = PCA(n_components=2, random_state=SEMILLA)
    coordenadas = pca.fit_transform(X)
    return coordenadas, float(pca.explained_variance_ratio_.sum())


# ---------------------------------------------------------------------------
# Salida de figuras
# ---------------------------------------------------------------------------


def guardar_figura(fig, nombre: str, carpeta: str | Path = "doc/img") -> Path:
    """Guarda una figura a 300 dpi."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}.png"
    fig.savefig(ruta, dpi=300, bbox_inches="tight")
    return ruta
