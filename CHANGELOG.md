# Changelog

## v0.4 - Entorno reproducible, módulo de análisis y datos regenerados
Se consolida el proyecto como un entorno reproducible (venv, `requirements.txt`, `.env.example`, `.gitignore`) y se separa la lógica de análisis en un módulo propio. El cuaderno de extracción se parametriza por autor y se regeneran los datos con las credenciales actuales. Se añade el cuaderno de análisis, que consolida ambos CSV, enriquece con Last.fm (`getInfo`, `getSimilar`) y Deezer, cuantifica y trata nulos, y calcula compatibilidad, popularidad, afinidad y agrupamiento. Se actualizan los capítulos 1-4 del informe con el diseño final.

### Detalle por subversión:
- `v0.4.0.1`: `add(env)`: `.gitignore` (datos personales, `.env`, caché y auxiliares LaTeX), `requirements.txt` con versiones compatibles y `.env.example`.
- `v0.4.0.2`: `mod(notebook)`: parametrización `USUARIO`/`ARCHIVO_SALIDA`, instrucciones por autor, dependencias desde `requirements.txt` y salidas limpias antes de versionar.
- `v0.4.0.3`: `add(analisis)`: módulo `spotify_analisis.py` con carga y validación, géneros, métricas de similitud, enriquecimiento con caché, nulos, afinidad y clustering.
- `v0.4.0.4`: `data`: extracción del autor Pablo (150 filas, 3 rangos × 50, 74 artistas únicos) y metadatos en `resultados/extraccion_meta.json`.
- `v0.4.0.5`: `add(analisis)`: cuaderno `AnalisisTecnicasDeCienciaDeDatos.ipynb` con las diez secciones del análisis y exportación de métricas.
- `v0.4.0.6`: `doc`: capítulos 1-4 reescritos con el alcance final (Last.fm/Deezer, MusicBrainz descartada, modelo de datos, nulos y métodos).
- `v0.4.0.7`: `fix(analisis)`: carga explícita de `.env` en el cuaderno de análisis para que el enriquecimiento disponga de `LASTFM_API_KEY`.

## v0.3 - Primer borrador del informe (LaTeX)
Se añade un primer borrador del informe del proyecto en `doc/`, siguiendo la plantilla LaTeX usada en las prácticas del máster (`main.tex` + `preliminares/portada.tex` + `capitulos/`). El informe cubre en detalle el planteamiento del problema, las fuentes de datos (Spotify Web API + Last.fm) y el proceso de obtención y tratamiento ya implementado en el notebook; el diseño del modelo de datos, los resultados/visualización y las conclusiones quedan como esquema de trabajo pendiente de completar con el análisis definitivo.

### Detalle por subversión:
- `v0.3.0.1`: `add(doc)`: estructura inicial del informe (portada, índice, capítulos 1-6) y compilación a `doc/main.pdf`.
- `v0.3.0.2`: `add(doc)`: se amplía el capítulo de diseño del modelo de datos con el enriquecimiento previsto vía Last.fm/Deezer/MusicBrainz, el tratamiento de valores nulos y tres líneas de trabajo planteadas (compatibilidad entre usuarios, afinidad usuario-artista por similitud de contenido, y clustering); se actualizan en consecuencia el plan de visualizaciones y las limitaciones.

=======
## v0.2 - Enriquecimiento con géneros musicales (Last.fm)
Se añade al script de extracción la consulta a la API de Last.fm (`artist.gettoptags`) para asociar hasta 4 géneros musicales a cada artista del `top_artistas.csv`, filtrando etiquetas no musicales (nacionalidad, tipo de voz, etc.) y aplicando un umbral mínimo de peso. Se usa una caché por artista único para minimizar el número de peticiones a la API externa.

### Detalle por subversión:
- `v0.2.0.1`: `add(notebook)`: función `generos_de()` y lógica de combinación de géneros en `TrabajoTecnicasDeCienciaDeDatos.ipynb`.

=======
## v0.1 - Extracción inicial de artistas más escuchados (Spotify)
Primera versión del script de obtención de datos: autenticación OAuth con la Spotify Web API (`spotipy`, scope `user-top-read`) y descarga del top 50 de artistas más escuchados en los tres rangos temporales disponibles (`short_term`, `medium_term`, `long_term`), exportado a CSV.

### Detalle por subversión:
- `v0.1.0.1`: `add(notebook)`: notebook inicial `TrabajoTecnicasDeCienciaDeDatos.ipynb` con el script de extracción de artistas.
- `v0.1.0.2`: `data`: se genera y añade `top_artistasJorge.csv` (datos de uno de los autores).
- `v0.1.0.3`: `del(data)`: se elimina `top_artistasJorge.csv` del repositorio (dato personal, no destinado a quedar versionado).
