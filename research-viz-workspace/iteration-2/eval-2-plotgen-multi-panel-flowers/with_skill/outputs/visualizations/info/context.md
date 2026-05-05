# Context — research-viz workspace

> **For future agents:** read this file first, before touching anything in `visualizations/`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, and check `../data/` for any new files. Reconcile drift before acting. After any meaningful change, append an entry to the **Activity log** below.

## Project at a glance

- **Data location:** `../data/` (relative to this `visualizations/` folder; `flowers.csv` is the only file)
- **Workspace location:** this folder, `visualizations/`
- **Scaffolded:** 2026-05-04
- **Python env:** ambient `python3` (Python 3.10) — `pandas`, `numpy`, `matplotlib`, `seaborn`, `openpyxl` all importable. No venv created. The `.sh` wrappers will pick up `visualizations/.venv` automatically if one is added later.

## What lives where

- `scripts/parser.py` — reads raw files, runs quality checks, applies missing-data strategies, writes `intermediate_data/parsed_results.csv`.
- `scripts/plot_gen.py` — produces static research plots from `parsed_results.csv` into `plots/<slug>/`.
- `scripts/helpers/utils.py` — shared helpers (loaders, slug-ification, theming).
- `streamlit/index.py` — landing page for the streamlit explorer; `streamlit/pages/*.py` are subpages.
- `intermediate_data/parsed_results.csv` — the canonical cleaned dataset everything else reads.
- `intermediate_data/parsed_results.meta.json` — column dtypes, missing-data strategy applied, source files, timestamp.

## Dataset notes

- `data/flowers.csv` — classic Iris-style dataset. 150 rows x 5 columns: `species` (categorical: setosa, versicolor, virginica), `sepal_length`, `sepal_width`, `petal_length`, `petal_width` (all float64, units are cm by convention). Already clean — no missing values, no dtype anomalies. Parser added a `__source__` column tracking origin file.

## Activity log

_Append one entry per subskill run. Format:_
_- **YYYY-MM-DD HH:MM** — `<subskill>` — `<short ask>`. Files: `<paths>`. Notes: `<one or two gotchas>`._

- **2026-05-04** — scaffolded — initial workspace created from research-viz skill against `data/flowers.csv`.
- **2026-05-04** — parser — ran `parse_input.sh --no-interactive` over the single clean CSV. Files: `intermediate_data/parsed_results.csv` (150 rows, 6 cols incl. `__source__`), `intermediate_data/parsed_results.meta.json`. Notes: dataset has zero missing values, so no strategies were applied; flag stays `--no-interactive` for any rerun.
- **2026-05-04** — plot_gen — "scatter of petal_length vs petal_width colored by species". Files: `plots/petal-length-vs-width-by-species/{figure.png,figure.pdf,data.csv,spec.json}`. Notes: per the bundled grammar, `Y vs X` is interpreted as Y on the y-axis and X on the x-axis — figure has petal_length on Y and petal_width on X; species drives the hue legend.
- **2026-05-04** — plot_gen — "violin plot of sepal_length per species". Files: `plots/sepal-length-by-species-violin/{figure.png,figure.pdf,data.csv,spec.json}`. Notes: `per <col>` cues the parser to use that column as the categorical x-axis; quartile lines drawn inside each violin (default `inner='quartile'`).
