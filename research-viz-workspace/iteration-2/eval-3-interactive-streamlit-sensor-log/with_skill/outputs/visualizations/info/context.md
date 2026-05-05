# Context — research-viz workspace

> **For future agents:** read this file first, before touching anything in `visualizations/`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, and check `/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-2/eval-3-interactive-streamlit-sensor-log/with_skill/outputs/data` for any new files. Reconcile drift before acting. After any meaningful change, append an entry to the **Activity log** below.

## Project at a glance

- **Data location:** `/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-2/eval-3-interactive-streamlit-sensor-log/with_skill/outputs/data`
- **Workspace location:** `/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-2/eval-3-interactive-streamlit-sensor-log/with_skill/outputs/visualizations`
- **Scaffolded:** 2026-05-04
- **Python env:** ambient interpreter (no `.venv` created). pandas / numpy / matplotlib / seaborn / openpyxl / streamlit / altair are assumed importable. If they aren't, create one with `python3 -m venv visualizations/.venv && source visualizations/.venv/bin/activate && pip install pandas numpy matplotlib seaborn openpyxl streamlit altair` — the existing `.sh` wrappers will then auto-source it.

## What lives where

- `scripts/parser.py` — reads raw files, runs quality checks, applies missing-data strategies, writes `intermediate_data/parsed_results.csv`.
- `scripts/plot_gen.py` — produces static research plots from `parsed_results.csv` into `plots/<slug>/`.
- `scripts/helpers/utils.py` — shared helpers (loaders, slug-ification, theming).
- `streamlit/index.py` — landing page for the streamlit explorer; `streamlit/pages/*.py` are subpages.
- `streamlit/pages/1_sensor_timeseries.py` — sensor-log dashboard: filter by site / sensor / time range / `ok` flag, see the time series of `value` (altair, interactive).
- `intermediate_data/parsed_results.csv` — the canonical cleaned dataset everything else reads.
- `intermediate_data/parsed_results.meta.json` — column dtypes, missing-data strategy applied, source files, timestamp.

## Dataset notes

- Source: `data/sensor_log.csv` (800 rows, 5 raw columns).
- Columns: `ts` (string timestamp, parsed to datetime in the streamlit page; raw dtype is `object`), `site` (categorical: `west`, `north`, `south`, `east`), `sensor` (categorical: `pressure`, `temperature`, `humidity`), `value` (float64, units unknown — treat as raw sensor reading), `ok` (bool flag — `False` rows look like flagged-bad readings).
- Readings are roughly 3-hourly; one (site, sensor) combination per row (no full grid — there are gaps when a site reports a different sensor in a given slot).
- No missing values in any column. The parser ran with `--no-interactive` and applied no imputation. `__source__` is auto-added by `parser.py` and points back to `sensor_log.csv`.

## Activity log

_Append one entry per subskill run. Format:_
_- **YYYY-MM-DD HH:MM** — `<subskill>` — `<short ask>`. Files: `<paths>`. Notes: `<one or two gotchas>`._

- **2026-05-04** — scaffolded — initial workspace created from research-viz skill via `scripts/scaffold.py`.
- **2026-05-04** — parser — non-interactive parse of `data/sensor_log.csv` (no missing values, nothing to impute). Files: `intermediate_data/parsed_results.csv`, `intermediate_data/parsed_results.meta.json`. Notes: parser leaves `ts` as a string; downstream code is responsible for `pd.to_datetime`. The streamlit page does this in its cached loader.
- **2026-05-04** — interactive — built sensor-log dashboard. Files: `streamlit/pages/1_sensor_timeseries.py`. Notes: page reads `parsed_results.csv`, lets the user multi-select `site` and `sensor`, brackets a time range, and optionally drops rows with `ok = False`. Renders the time series of `value` with altair (interactive zoom + tooltips), plus a faceted small-multiples view (one panel per site) and a download-able filtered CSV. The streamlit app has *not* been launched — run `bash visualizations/interactive_page.sh` to start it.
