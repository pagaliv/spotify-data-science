# Spotify Data Science

Proyecto final de la asignatura Técnicas de Ciencia de Datos (Máster, Universidad
de la Rioja): recogida de los artistas más escuchados en Spotify, enriquecidos con
géneros y similitud de Last.fm y con popularidad de Deezer, para analizar y comparar
el gusto musical de dos usuarios.

> **Versión actual: v0.4** — ver [Changelog](CHANGELOG.md).

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
├── spotify_analisis.py                     # funciones puras reutilizables
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
- descarga el top 50 en `short_term`, `medium_term` y `long_term`;
- consulta Last.fm una vez por artista único para obtener hasta 4 géneros;
- exporta `top_artistas.csv` o `top_artistasJorge.csv`.

Ambos CSV deben generarse el mismo día para limitar la deriva temporal.

### 2. Análisis

Abre `AnalisisTecnicasDeCienciaDeDatos.ipynb` con ambos CSV en la raíz y ejecuta
todo (*Restart & Run All*). El cuaderno consolida los datos, enriquece con Last.fm
y Deezer, cuantifica y trata nulos, calcula compatibilidad y afinidad, agrupa
artistas por género y genera:

- las diez figuras de `doc/img/`;
- las tablas agregadas y `metricas.json` en `resultados/`.

La caché de enriquecimiento (`cache/`) evita repetir llamadas a las APIs entre
ejecuciones.

## Privacidad y datos personales

Los datos de partida identifican los gustos musicales de los autores. Por eso
**no se versionan** los CSV crudos, el `.env`, la caché de tokens ni la caché de
enriquecimiento. Solo se publican agregados sin nombres de artistas y las figuras
del informe. Las credenciales nunca se escriben en los registros ni en el código.

## Informe

El informe está en [`doc/main.pdf`](doc/main.pdf) (fuente LaTeX en [`doc/`](doc/)).
Los capítulos 1-4 (planteamiento, datos, tratamiento y modelo) están revisados con
el diseño final; los capítulos 5-6 (resultados y conclusiones) se completan con la
ejecución del cuaderno de análisis. Ver [VERSIONS.md](VERSIONS.md) y
[CHANGELOG.md](CHANGELOG.md) para el detalle de lo publicado.

Para recompilar:

```bash
cd doc
pdflatex main.tex
pdflatex main.tex   # segunda pasada para resolver referencias cruzadas
```
