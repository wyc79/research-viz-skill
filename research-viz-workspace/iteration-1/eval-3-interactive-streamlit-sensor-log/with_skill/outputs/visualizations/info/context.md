# Context — research-viz workspace

> **For future agents:** read this file first, before touching anything in `visualizations/`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, and check `/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-1/eval-3-interactive-streamlit-sensor-log/with_skill/outputs/data` for any new files. Reconcile drift before acting. After any meaningful change, append an entry to the **Activity log** below.

## Project at a glance

- **Data location:** `/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-1/eval-3-interactive-streamlit-sensor-log/with_skill/outputs/data`
- **Workspace location:** `/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-1/eval-3-interactive-streamlit-sensor-log/with_skill/outputs/visualizations`
- **Scaffolded:** 2026-05-04T23:18:32
- **Python env:** current shell. User confirmed pandas / numpy / matplotlib / seaborn / openpyxl / streamlit / altair are pre-installed; no venv was created. Shell wrappers fall back to ambient `python3` / `streamlit`.

## What lives where

- `scripts/parser.py` — reads raw files, runs quality checks, applies missing-data strategies, writes `intermediate_data/parsed_results.csv`.
- `scripts/plotgen.py` — produces static research plots from `parsed_results.csv` into `plots/<slug>/`.
- `scripts/fcns/utils.py` — shared helpers (loaders, slug-ification, theming).
- `streamlit/index.py` — landing page for the streamlit explorer; `streamlit/pages/*.py` are subpages.
- `intermediate_data/parsed_results.csv` — the canonical cleaned dataset everything else reads.
- `intermediate_data/parsed_results.meta.json` — column dtypes, missing-data strategy applied, source files, timestamp.

## Dataset notes

Single source file: `data/sensor_log.csv` (800 rows, 5 raw columns + `__source__` added by parser).

Columns:
- `ts` — timestamp string at 3-hour cadence, 2025-01-01 00:00 -> 2025-04-10 21:00. Stored as `object` in the parsed CSV; cast to datetime in the streamlit page.
- `site` — categorical, 4 values: `east`, `north`, `south`, `west`.
- `sensor` — categorical, 3 values: `humidity`, `pressure`, `temperature`.
- `value` — float64, the observed reading (units unknown).
- `ok` — bool quality flag. 762 True / 38 False. Streamlit page exposes a checkbox to drop the False rows.
- `__source__` — added by parser; always `sensor_log.csv`.

No missing values anywhere, so the parser was run with `--no-interactive` (no strategy decisions needed).

## Activity log

_Append one entry per subskill run. Format:_
_- **YYYY-MM-DD HH:MM** — `<subskill>` — `<short ask>`. Files: `<paths>`. Notes: `<one or two gotchas>`._

- **2026-05-04T23:18:32** — scaffolded — initial workspace created from research-viz skill.
- **2026-05-04** — `parser` — read `data/sensor_log.csv` non-interactively (no missing values to handle). Files: `intermediate_data/parsed_results.csv`, `intermediate_data/parsed_results.meta.json`. Notes: `ts` remains a string in the CSV; downstream code casts it to datetime on load. Bool `ok` round-trips through CSV as the strings `True`/`False` — streamlit page normalizes either form.
- **2026-05-04** — `interactive` — built `streamlit/pages/1_sensor_time_series.py`: sidebar multi-selects for site + sensor (plus optional date range and an "ok only" toggle), altair line chart of `value` vs `ts` with one line per (site, sensor) pair, summary table, and CSV download. Files: `streamlit/pages/1_sensor_time_series.py`. Launch with `bash visualizations/interactivepage.sh`. Not run by the agent — user runs it themselves.
