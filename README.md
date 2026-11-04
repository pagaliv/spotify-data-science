# Spotify Data Science

Proyecto final de la asignatura Técnicas de Ciencia de Datos (Máster, Universidad
de la Rioja): recogida de los artistas más escuchados en Spotify, enriquecidos con
géneros y similitud de Last.fm y con popularidad de Deezer, para analizar y comparar
el gusto musical de dos usuarios.

> **Versión actual: v1.0.2** — ver [Changelog](CHANGELOG.md).


## Stack

- **Lenguaje:** Python 3 (Jupyter Notebook), entorno reproducible en `requirements.txt`
- **APIs externas:** Spotify Web API (vía `spotipy`), Last.fm API y Deezer API (vía `requests`)
- **Librerías:** `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `scikit-learn`, `spotipy`, `requests`, `python-dotenv`
- **Informe:** LaTeX (`doc/`), siguiendo la plantilla de prácticas del máster

## Estructura

```
spotify-data-science/
├── TrabajoTecnicasDeCienciaDeDatos.ipynb   # extracción de artistas y géneros
├── AnalisisTecnicasDeCienciaDeDatos.ipynb  # análisis, métricas y figuras
├── spotify_analisis.py                     # cálculo y acceso a fuentes
├── tests/                                  # pruebas sin llamadas reales a APIs
├── top_artistas.csv                        # datos de Pablo (no versionado)
├── top_artistasJorge.csv                   # datos de Jorge (no versionado)
├── .env                                    # credenciales (no versionado)
├── .env.example                            # plantilla de credenciales
├── .gitignore
├── requirements.txt
├── doc/                                    # informe del proyecto (LaTeX)
│   ├── main.tex                            # documento maestro
│   ├── main.pdf                            # informe compilado
│   ├── img/                                # figuras generadas por el cuaderno
│   ├── preliminares/
│   │   └── portada.tex
│   └── capitulos/
│       ├── 01-planteamiento.tex
│       ├── 02-datos.tex
│       ├── 03-tratamiento.tex
│       ├── 04-modelo.tex
│       ├── 05-resultados.tex
│       └── 06-conclusiones.tex
├── resultados/                             # tablas agregadas y metricas.json
├── cache/                                  # caché de enriquecimiento (no versionada)
├── info/
│   └── trabajoFinal.pdf                    # enunciado de la asignatura
├── VERSIONS.md
├── CHANGELOG.md
└── README.md
```

## Requisitos

- Python 3.11 o superior (probado con 3.13)
- Una aplicación registrada en el [panel de desarrolladores de Spotify](https://developer.spotify.com/dashboard) (Client ID y Client Secret) con la Redirect URI `http://127.0.0.1:8888/callback`
- Una API key de [Last.fm](https://www.last.fm/api/account/create)
- Para LaTeX: `pdflatex` (TeX Live)

## Instalación

```bash
git clone <url-del-repo> spotify-data-science
cd spotify-data-science

python3 -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Variables de entorno

Crea un fichero `.env` en la raíz del proyecto (no se versiona) a partir de
`.env.example`:

| Variable                | Para qué sirve                                              |
| ------------------------ | ------------------------------------------------------------ |
| `SPOTIPY_CLIENT_ID`      | Client ID de la aplicación de Spotify.                       |
| `SPOTIPY_CLIENT_SECRET`  | Client Secret de la aplicación de Spotify.                   |
| `SPOTIPY_REDIRECT_URI`   | URI de redirección registrada en el panel de Spotify (`http://127.0.0.1:8888/callback`). |
| `LASTFM_API_KEY`         | API key de Last.fm, usada para géneros, popularidad y similitud. |

## Uso

### 1. Extracción de datos (una vez por autor)

Abre `TrabajoTecnicasDeCienciaDeDatos.ipynb`, ajusta `USUARIO` a `"pablo"` o
`"jorge"` y ejecuta. El cuaderno:

- autentica contra Spotify (OAuth en el navegador, scope `user-top-read`);
- solicita hasta 50 artistas en `short_term`, `medium_term` y `long_term`;
- consulta Last.fm una vez por artista único para obtener hasta 4 géneros;
- exporta `top_artistas.csv` o `top_artistasJorge.csv`.

Es recomendable generar ambos CSV el mismo día para limitar la deriva temporal.
Los archivos recibidos tienen 150 filas de Pablo y 148 de Jorge (48/50/50); no se
inventan las dos posiciones restantes. La unión reúne 140 artistas, 5 compartidos.
Solo está acreditada la fecha original de Pablo (2026-11-03); la de Jorge se
mantiene desconocida en los metadatos.

### 2. Análisis

Abre `AnalisisTecnicasDeCienciaDeDatos.ipynb` con ambos CSV en la raíz y ejecuta
todo (*Restart & Run All*). El cuaderno consolida los datos, enriquece con Last.fm
y Deezer, cuantifica y trata nulos, calcula compatibilidad y afinidad, agrupa
artistas por género y genera:

- las diez figuras de `doc/img/`;
- las tablas agregadas y `metricas.json` en `resultados/`.

La caché de enriquecimiento (`cache/`) evita repetir consultas válidas a las APIs.
Los fallos persistentes detienen la ejecución sin registrarse como ausencias; los
artistas no encontrados y las listas vacías válidas sí se cachean. Deezer requiere
coincidencia exacta de nombre, ignorando mayúsculas y espacios exteriores.
Los candidatos necesitan sus propios vecinos de Last.fm antes de calcular afinidad.

Los artistas sin etiquetas participan en Jaccard, pero no en los perfiles de etiquetas.
Las proporciones de etiquetas no son proporciones de tiempo de escucha. La afinidad
es descriptiva, no una probabilidad ni una evaluación predictiva independiente.
El agrupamiento y la PCA son exploratorios; las correlaciones no usan imputaciones.

Si se guarda una copia ejecutada del cuaderno, debe quedar bajo `cache/`, no en el
cuaderno versionado. Los datos originales y las respuestas externas son necesarios
para reproducir los números: el repositorio no distribuye los perfiles personales.

### 3. Pruebas

```bash
./venv/bin/python -m unittest discover -s tests -v
```

Las pruebas usan datos sintéticos y respuestas HTTP simuladas; no necesitan claves
ni acceso a la red. Comprueban métricas, caché, errores, identificación de artistas,
imputación y exportación JSON estricta (`null` para resultados no calculables).

## Privacidad y datos personales

Los datos de partida identifican los gustos musicales de los autores. Por eso
**no se versionan** los CSV crudos, el `.env`, la caché de tokens ni la caché de
enriquecimiento. Solo se publican agregados sin nombres de artistas y las figuras
del informe. Las credenciales nunca se escriben en los registros ni en el código.

## Informe

El informe completo está en [`doc/main.pdf`](doc/main.pdf) (fuente LaTeX en
[`doc/`](doc/)): planteamiento, datos, tratamiento, modelo, resultados y conclusiones.
Se fundamentan el ciclo de vida, las fuentes y los formatos en las sesiones 1–3 del
material docente aportado, y las decisiones visuales en la sesión 6. Las métricas de
similitud, afinidad y agrupamiento se distinguen como elecciones del proyecto.

### Resultados principales (análisis del 2026-11-04)

- 298 registros, 140 artistas distintos y 5 compartidos: Jaccard global **0,0357**.
- Coseno global de etiquetas **0,4686**; no es una probabilidad de compatibilidad.
- Last.fm aporta popularidad y vecinos para los 140 artistas; faltan 20 MBID.
  Deezer tiene coincidencia exacta para 136 (4 ausencias, 2,86 %).
- Los 20 candidatos son puntuables, pero ninguno tiene afinidad positiva para
  ambos perfiles. Ordenar por su media no produce una recomendación de consenso.
- K-Means conserva 133 artistas y 52 etiquetas, selecciona 2 grupos con silueta
  **0,1508**; la PCA explica **26,42 %** de la varianza. Es exploratorio.

Las cifras completas están en [`resultados/metricas.json`](resultados/metricas.json).
La repetición completa con HTTP bloqueado produjo métricas, tablas y figuras
idénticas, sin modificar los CSV originales. El ajuste temporal a IPv4 utilizado
en esta máquina para evitar conexiones IPv6 bloqueadas no modifica el cuaderno
fuente ni los datos. Ver [VERSIONS.md](VERSIONS.md) y [CHANGELOG.md](CHANGELOG.md).

Para recompilar:

```bash
cd doc
pdflatex main.tex
pdflatex main.tex   # segunda pasada para resolver referencias cruzadas
```
