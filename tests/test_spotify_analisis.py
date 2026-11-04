import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import requests

import spotify_analisis as sa


class AnalisisTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame([
            {"usuario": usuario, "rango": rango, "rango_orden": i,
             "posicion": pos, "artista": artista, "generos": genero}
            for i, rango in enumerate(sa.ORDEN_RANGOS, 1)
            for usuario, pos, artista, genero in [
                ("pablo", 1, "A", "rock"), ("pablo", 2, "B", ""),
                ("jorge", 1, "B", ""), ("jorge", 2, "C", "pop"),
            ]
        ])
        self.generos = sa.explosionar_generos(self.df)

    def test_jaccard_incluye_artista_sin_genero(self):
        tabla = sa.tabla_compatibilidad(self.df, self.generos)
        self.assertTrue(tabla["jaccard_artistas"].eq(0.3333).all())
        self.assertTrue(tabla["n_comun_artistas"].eq(1).all())
        self.assertTrue(tabla["coseno_generos"].eq(0).all())

    def test_estabilidad_usa_tabla_completa(self):
        corto = next(iter(sa.ORDEN_RANGOS))
        df = self.df[~((self.df["rango"] == corto) & self.df["artista"].eq("B"))]
        tabla = sa.estabilidad_por_rangos(df, sa.explosionar_generos(df), "pablo")
        self.assertEqual(tabla.iloc[0]["jaccard_artistas"], 0.5)

    def test_rango_con_48_artistas_es_valido(self):
        df = pd.DataFrame({
            "usuario": ["jorge"] * 48, "rango": ["ultimas_4_semanas"] * 48,
            "posicion": range(1, 49), "artista": [f"A{i}" for i in range(48)], "generos": [""] * 48,
        })
        fila = sa.validar_datos(df).iloc[0]
        self.assertEqual(fila["filas"], 48)
        self.assertEqual(fila["posiciones_fuera_de_rango"], 0)
        self.assertEqual(fila["duplicados_rango_posicion"], 0)

    def test_afinidad_candidato_con_vecinos(self):
        vecinos = pd.DataFrame([
            {"artista": "Nuevo", "similar": "A", "match": 0.8},
            {"artista": "Nuevo", "similar": "Ajeno", "match": 0.2},
        ])
        tabla = sa.calcular_afinidad(self.df, vecinos, ["Nuevo"])
        self.assertAlmostEqual(tabla.iloc[0]["pablo"], 0.8)
        self.assertEqual(tabla.iloc[0]["jorge"], 0)
        self.assertTrue(math.isnan(sa.puntuacion_afinidad("Sin vecinos", vecinos, {"A": 1})))

    def test_candidatos_excluyen_historial(self):
        vecinos = pd.DataFrame([
            {"artista": "A", "similar": "Nuevo", "match": 0.8},
            {"artista": "A", "similar": "B", "match": 1.0},
        ])
        self.assertEqual(sa.generar_candidatos(self.df, vecinos), ["Nuevo"])

    def test_cache_candidatos_incluye_ausencias_validas(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "cache.json"
            with patch.object(sa, "similares_artista", return_value=[]) as api:
                tabla = sa.enriquecer_similitudes(["Nuevo"], ruta, pausa=0)
                sa.enriquecer_similitudes(["Nuevo"], ruta, pausa=0)
            api.assert_called_once_with("Nuevo")
            self.assertEqual(list(tabla.columns), ["artista", "similar", "match"])
            self.assertTrue(tabla.empty)

    def test_error_no_se_cachea_como_ausencia(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "cache.json"
            with patch.object(sa, "similares_artista", side_effect=RuntimeError("fuente caída")):
                with self.assertRaises(RuntimeError):
                    sa.enriquecer_similitudes(["Nuevo"], ruta, pausa=0)
            self.assertFalse(ruta.exists())

    def test_cache_conserva_respuestas_antes_de_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "cache.json"
            with patch.object(sa, "info_artista", return_value={"listeners": 10}), \
                 patch.object(sa, "similares_artista", side_effect=RuntimeError("fuente caída")):
                with self.assertRaises(RuntimeError):
                    sa.enriquecer_artistas(["A"], ruta, pausa_lastfm=0)
            entradas = json.loads(ruta.read_text())["entries"]
            self.assertEqual(entradas, {"getinfo::A": {"listeners": 10}})

    def test_cache_historial_evitar_repetir_consultas(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "cache.json"
            with patch.object(sa, "info_artista", return_value={}) as info, \
                 patch.object(sa, "similares_artista", return_value=[]) as similares, \
                 patch.object(sa, "deezer_artista", return_value={}) as deezer:
                sa.enriquecer_artistas(["A"], ruta, pausa_lastfm=0, pausa_deezer=0)
                sa.enriquecer_artistas(["A"], ruta, pausa_lastfm=0, pausa_deezer=0)
            info.assert_called_once_with("A")
            similares.assert_called_once_with("A")
            deezer.assert_called_once_with("A")

    @patch.object(sa.time, "sleep")
    @patch.object(sa.requests, "get")
    def test_reintenta_errores_temporales(self, get, sleep):
        respuesta = Mock(status_code=200)
        respuesta.json.return_value = {"data": []}
        get.side_effect = [requests.Timeout("clave-secreta"), respuesta]
        self.assertEqual(sa._peticion_json(sa.DEEZER_URL, {}), {"data": []})
        self.assertEqual(get.call_count, 2)

    @patch.object(sa.time, "sleep")
    @patch.object(sa.requests, "get", side_effect=requests.Timeout("clave-secreta"))
    def test_error_final_no_filtra_url_ni_clave(self, get, sleep):
        with self.assertRaises(RuntimeError) as error:
            sa._peticion_json(sa.DEEZER_URL, {})
        self.assertNotIn("clave-secreta", str(error.exception))
        self.assertEqual(get.call_count, 3)

    @patch.object(sa, "_peticion_json", return_value={"data": [{"name": "Otro", "nb_fan": 999}]})
    def test_deezer_no_acepta_otro_artista(self, api):
        self.assertIsNone(sa.deezer_artista("Buscado")["deezer_fans"])

    @patch.object(sa, "_peticion_json", return_value={"data": [{"name": " BUSCADO ", "nb_fan": 10}]})
    def test_deezer_acepta_nombre_equivalente(self, api):
        self.assertEqual(sa.deezer_artista("Buscado")["deezer_fans"], 10)

    def test_cobertura_detecta_artistas_sin_vecinos(self):
        fila = sa.resumen_nulos(pd.DataFrame({"n_similares": [0, 2, 0]})).iloc[0]
        self.assertEqual(fila["n_nulos"], 2)

    def test_imputacion_no_altera_observaciones(self):
        df = pd.DataFrame({"listeners": [10.0, 20.0, np.nan], "genero_principal": ["rock"] * 3})
        datos, informe = sa.imputar_popularidad(df, "listeners")
        self.assertTrue(pd.isna(datos.loc[2, "listeners"]))
        self.assertEqual(datos.loc[2, "listeners_imp"], 15)
        self.assertEqual(informe.iloc[0]["n_imputados"], 1)

    def test_exportacion_json_estricto(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "metricas.json"
            sa.exportar_metricas({"rho": np.nan, "n": np.int64(2), "valores": [np.inf, 0.0]}, ruta)
            datos = json.loads(ruta.read_text(), parse_constant=lambda s: self.fail(s))
        self.assertEqual(datos, {"rho": None, "n": 2, "valores": [None, 0.0]})


if __name__ == "__main__":
    unittest.main()
