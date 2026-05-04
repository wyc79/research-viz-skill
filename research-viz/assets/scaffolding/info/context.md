# Context — research-viz workspace

> **For future agents:** read this file first, before touching anything in `visualizations/`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, and check `__DATA_DIR__` for any new files. Reconcile drift before acting. After any meaningful change, append an entry to the **Activity log** below.

## Project at a glance

- **Data location:** `../data/` (sibling of this `visualizations/` folder; absolute path on this machine: __DATA_DIR__)
- **Scaffolded:** __TIMESTAMP__
- **Python env:** _(filled in after env decision — current shell, or a venv at `visualizations/.venv`, or a conda env named `<name>`)_

## What lives where

- `scripts/parser.py` — reads raw files, runs quality checks, applies missing-data strategies, writes `intermediate_data/parsed_results.csv`.
- `scripts/plot_gen.py` — produces static research plots from `parsed_results.csv` into `plots/<slug>/`.
- `scripts/helpers/utils.py` — shared helpers (loaders, slug-ification, theming).
- `streamlit/index.py` — landing page for the streamlit explorer; `streamlit/pages/*.py` are subpages.
- `intermediate_data/parsed_results.csv` — the canonical cleaned dataset everything else reads.
- `intermediate_data/parsed_results.meta.json` — column dtypes, missing-data strategy applied, source files, timestamp.

## Dataset notes

_(Append observations about the data as you learn them — column meanings, units, known quirks, missing patterns. Keep concise.)_

- _e.g. `temperature_C` had 12% missing, used median imputation per group_

## Activity log

_Append one entry per subskill run. Format:_
_- **YYYY-MM-DD HH:MM** — `<subskill>` — `<short ask>`. Files: `<paths>`. Notes: `<one or two gotchas>`._

- **__TIMESTAMP__** — scaffolded — initial workspace created from research-viz skill. No subskill has run yet.
