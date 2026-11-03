# Versioning Methodology

This document describes the versioning and change tracking convention used in this project.

## 1. Version Number Format

Every change must be associated with a version number using the following format:

### vX.Y.Z.B

Where:

| Component | Name             | Description                                                      |
|-----------|------------------|--------------------------------------------------------------------|
| `X`       | Major            | Incremented for incompatible or breaking changes.                  |
| `Y`       | Minor            | Incremented for new functionality that is backward compatible.     |
| `Z`       | Patch            | Incremented for bug fixes and small improvements.                  |
| `B`       | Build / Revision | Incremented on every change, even if no public release is made.    |

**Example:** `v0.3.1.2`

- Major: `0`
- Minor: `3`
- Patch: `1`
- Build: `2`

---

## 2. Change Suffix

After the version number, append a colon and a structured summary of the change:

### vX.Y.Z.B:action(scope): description

Where:

- **action** – The type of change performed (see section 3).
- **scope** – The area or module affected, written inside parentheses `()`.
- **description** – A brief, human-readable explanation of what was done.

---

## 3. Action Types

Use one of the following standard action codes:

| Code    | Meaning        | Description                                                               |
|---------|----------------|-----------------------------------------------------------------------------|
| `add`   | Addition       | New file, feature, or resource added.                                       |
| `mod`   | Modification   | Existing functionality or documentation was changed.                        |
| `fix`   | Bug fix        | A defect or error was corrected.                                            |
| `del`   | Deletion       | File, feature, or code block removed.                                       |
| `ref`   | Refactoring    | Code restructured without changing external behavior.                       |
| `doc`   | Documentation  | Documentation-only change (alternative to `mod` for docs).                  |
| `data`  | Data           | Dataset obtained, updated, or exported.                                     |
| `chore` | Maintenance    | Dependencies, configuration, or other non-functional tasks.                 |

---

## 4. Scope

The scope identifies the module, file, or area affected by the change.
It is written in parentheses immediately after the action, with **no spaces**.

Common scopes in this project:

- `notebook` — `TrabajoTecnicasDeCienciaDeDatos.ipynb`
- `analisis` — `AnalisisTecnicasDeCienciaDeDatos.ipynb` y `spotify_analisis.py`
- `data` — ficheros CSV generados (`top_artistas*.csv`)
- `resultados` — tablas agregadas y `resultados/metricas.json`
- `env` — `.gitignore`, `requirements.txt`, `.env.example` y entorno
- `doc` — informe LaTeX (`doc/`)
- `README`
- `info` — enunciado y material de referencia de la asignatura

## 5. How to Use This Convention

1. **Before making a change**, determine the appropriate version increment:
   - Breaking change (p. ej. cambio del esquema de datos) → increase **Major** (`X`), reset Minor, Patch, Build.
   - New backward-compatible feature (p. ej. nuevo capítulo del informe, nueva fuente de datos) → increase **Minor** (`Y`), reset Patch, Build.
   - Bug fix or small improvement → increase **Patch** (`Z`), reset Build.
   - Any internal change → increase **Build** (`B`).

2. **Update the version number** in the relevant files (`README.md`, `CHANGELOG.md`).

3. **Use the full string** as the first line of the commit message, or as an entry in the changelog.

4. **Tag releases** in Git:

   ```bash
   git tag -a v0.3 -m "v0.3:add(doc): primer borrador del informe"
   ```

## 6. Changelog

Maintain a `CHANGELOG.md` file with entries grouped by version.
Each entry should follow the same suffix format.
In this file you can see more information about the commits.
