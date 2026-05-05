# Context — research-viz workspace

> **For future agents:** read this file first, before touching anything in `visualizations/`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, and check `/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-1/eval-2-plotgen-multi-panel-flowers/with_skill/outputs/data` for any new files. Reconcile drift before acting. After any meaningful change, append an entry to the **Activity log** below.

## Project at a glance

- **Data location:** `/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-1/eval-2-plotgen-multi-panel-flowers/with_skill/outputs/data`
- **Workspace location:** `/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-1/eval-2-plotgen-multi-panel-flowers/with_skill/outputs/visualizations`
- **Scaffolded:** 2026-05-04T23:17:30
- **Python env:** ambient `python3` (3.10.12) — pandas / numpy / matplotlib / seaborn already importable; no venv created.

## What lives where

- `scripts/parser.py` — reads raw files, runs quality checks, applies missing-data strategies, writes `intermediate_data/parsed_results.csv`.
- `scripts/plotgen.py` — produces static research plots from `parsed_results.csv` into `plots/<slug>/`.
- `scripts/fcns/utils.py` — shared helpers (loaders, slug-ification, theming).
- `streamlit/index.py` — landing page for the streamlit explorer; `streamlit/pages/*.py` are subpages.
- `intermediate_data/parsed_results.csv` — the canonical cleaned dataset everything else reads.
- `intermediate_data/parsed_results.meta.json` — column dtypes, missing-data strategy applied, source files, timestamp.

## Dataset notes

_(Append observations about the data as you learn them — column meanings, units, known quirks, missing patterns. Keep concise.)_

- `data/flowers.csv` — classic iris-style flowers dataset, 150 rows x 5 columns.
  - Columns: `species` (object, 3 categories), `sepal_length`, `sepal_width`, `petal_length`, `petal_width` (all float64).
  - **Clean** — zero missing values across all columns; no imputation needed.
  - Parser added a bookkeeping `__source__` column (`flowers.csv`) — 6 columns in `parsed_results.csv`.

## Activity log

_Append one entry per subskill run. Format:_
_- **YYYY-MM-DD HH:MM** — `<subskill>` — `<short ask>`. Files: `<paths>`. Notes: `<one or two gotchas>`._

- **2026-05-04T23:17:30** — scaffolded — initial workspace created from research-viz skill. No subskill has run yet.
- **2026-05-04 23:18** — `parser` — parsed `data/flowers.csv` non-interactively (`--no-interactive`, no overrides). Files: `intermediate_data/parsed_results.csv`, `intermediate_data/parsed_results.meta.json`. Notes: dataset is clean (0% missing in every column); no missing-data strategies applied.
- **2026-05-04 23:18** — `plotgen` — "scatter of petal_length vs petal_width colored by species". Files: `plots/scatter-of-petal-length-vs-petal-width-colored-by-species/{figure.png,figure.pdf,data.csv,spec.json}`. Notes: bundled grammar parses "X vs Y" as y=X, x=Y, so `petal_length` is the y-axis and `petal_width` is the x-axis; `species` drives hue.
- **2026-05-04 23:18** — `plotgen` — "violin of sepal_length per species". Files: `plots/violin-of-sepal-length-per-species/{figure.png,figure.pdf,data.csv,spec.json}`. Notes: `per <col>` is parsed as the categorical x-axis grouping; quartile inner lines shown by default.
