# Spotify Data Science

Proyecto final de la asignatura Técnicas de Ciencia de Datos (Máster, Universidad
de la Rioja): recogida de los artistas más escuchados en Spotify, enriquecidos con
géneros musicales de Last.fm, para analizar y comparar el gusto musical de dos
usuarios.

> **Versión actual: v0.3** — ver [Changelog](CHANGELOG.md).

## Stack

- **Lenguaje:** Python 3 (Jupyter Notebook)
- **APIs externas:** Spotify Web API (vía `spotipy`), Last.fm API (`requests`)
- **Librerías:** `spotipy`, `pandas`, `requests`, `python-dotenv`, `matplotlib`
- **Informe:** LaTeX (`doc/`), siguiendo la plantilla de prácticas del máster

## Estructura

```
spotify-data-science/
├── TrabajoTecnicasDeCienciaDeDatos.ipynb   # notebook de extracción de datos
├── top_artistas.csv                        # salida del notebook (no versionado)
├── .env                                    # credenciales de las APIs (no versionado)
├── doc/                                    # informe del proyecto (LaTeX)
│   ├── main.tex                            # documento maestro
│   ├── main.pdf                            # informe compilado
│   ├── preliminares/
│   │   └── portada.tex
│   └── capitulos/
│       ├── 01-planteamiento.tex            # problema y análisis de negocio
│       ├── 02-datos.tex                    # fuentes y datos recogidos
│       ├── 03-tratamiento.tex              # tratamiento dado a los datos
│       ├── 04-modelo.tex                   # diseño del modelo de datos (borrador)
│       ├── 05-resultados.tex               # resultados y visualización (borrador)
│       └── 06-conclusiones.tex             # conclusiones (borrador)
├── info/
│   └── trabajoFinal.pdf                    # enunciado de la asignatura
├── VERSIONS.md                             # convenio de versionado
├── CHANGELOG.md
└── README.md
```

## Requisitos

- Python 3.10 o superior
- Una aplicación registrada en el [panel de desarrolladores de Spotify](https://developer.spotify.com/dashboard) (Client ID y Client Secret)
- Una API key de [Last.fm](https://www.last.fm/api/account/create)

## Instalación

### Linux / macOS

```bash
git clone <url-del-repo> spotify-data-science
cd spotify-data-science

python3 -m venv venv
source venv/bin/activate

pip install spotipy pandas requests python-dotenv matplotlib
```

### Windows (PowerShell)

```powershell
git clone <url-del-repo> spotify-data-science
cd spotify-data-science

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install spotipy pandas requests python-dotenv matplotlib
```

## Variables de entorno

Crea un fichero `.env` en la raíz del proyecto (no se versiona) con:

| Variable                | Para qué sirve                                              |
| ------------------------ | ------------------------------------------------------------ |
| `SPOTIPY_CLIENT_ID`      | Client ID de la aplicación de Spotify.                       |
| `SPOTIPY_CLIENT_SECRET`  | Client Secret de la aplicación de Spotify.                   |
| `SPOTIPY_REDIRECT_URI`   | URI de redirección registrada en el panel de Spotify (p. ej. `http://127.0.0.1:8888/callback`). |
| `LASTFM_API_KEY`         | API key de Last.fm, usada para obtener los géneros de cada artista. |

```bash
SPOTIPY_CLIENT_ID=tu_client_id
SPOTIPY_CLIENT_SECRET=tu_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
LASTFM_API_KEY=tu_api_key
```

## Uso

Abrir `TrabajoTecnicasDeCienciaDeDatos.ipynb` y ejecutar las celdas en orden:

1. **Instalación de dependencias** (`pip install ...`).
2. **Autenticación con Spotify** (abre el navegador para el flujo OAuth, scope `user-top-read`).
3. **Extracción y enriquecimiento**: descarga el top 50 de artistas en los tres rangos temporales (`short_term`, `medium_term`, `long_term`), consulta Last.fm una vez por artista único para obtener hasta 4 géneros por artista, y exporta el resultado a `top_artistas.csv` con las columnas `rango, posicion, artista, generos, spotify_url`.

Cada autor del proyecto genera su propio CSV ejecutando el notebook con sus
propias credenciales de Spotify.

## Informe

El informe del proyecto está en [`doc/main.pdf`](doc/main.pdf) (fuente LaTeX en
[`doc/`](doc/)). Los capítulos 1-3 (planteamiento, datos recogidos y tratamiento
dado a los datos) reflejan el estado actual del notebook; los capítulos 4-6
(diseño del modelo, resultados y conclusiones) son un esquema de trabajo
pendiente de completar con el análisis definitivo — ver [VERSIONS.md](VERSIONS.md)
y [CHANGELOG.md](CHANGELOG.md) para el detalle de lo publicado hasta ahora.

Para recompilar el informe:

```bash
cd doc
pdflatex main.tex
pdflatex main.tex   # segunda pasada para resolver referencias cruzadas
```
