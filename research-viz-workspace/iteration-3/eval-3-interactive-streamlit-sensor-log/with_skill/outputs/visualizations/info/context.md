# Context — sensor-log streamlit dashboard

> **For future agents:** before touching anything in `visualizations/`, read every `.md` in `info/`, then `ls scripts/`, `ls streamlit/pages/`, `ls intermediate_data/`, and check `../data/` for new files. Reconcile drift before acting. Write `context.md` last as the closing entry of any session.

## Project at a glance

- **Data:** `../data/sensor_log.csv` (single file, 800 rows, 5 columns).
- **Goal:** streamlit dashboard that filters by `site` + `sensor` and shows `value` over time.
- **Scaffolded:** 2026-05-04 from the `research-viz` skill, then trimmed to single-file streamlit-only shape.
- **Python env:** ambient interpreter — streamlit 1.57, altair 6.1, pandas 2.3 (no `.venv` created).

## Layout (after trim)

- `scripts/parser.py` — reads `data/sensor_log.csv`, parses `ts` to datetime, sorts, writes `intermediate_data/sensor_log__parsed.csv` + `parsed_index.json`. Single-file project: no `--combine`, no missing-data strategies (none needed).
- `streamlit/index.py` — landing page: schema, sample, top-line counts, pointer to the time-series page.
- `streamlit/pages/1_time_series.py` — multi-select filters for `site` + `sensor`, optional `ok=True`-only toggle, altair line chart of `value` over `ts` (one line per site/sensor combo, colour=site, dash=sensor).
- `intermediate_data/sensor_log__parsed.csv` — output of the parser.
- `intermediate_data/parsed_index.json` — manifest pointing at the canonical CSV.
- `parse_input.sh`, `interactive_page.sh` — the only two shell wrappers (no `generate_plot.sh` — static plots weren't requested for this project).

## Dataset notes

- Columns: `ts` (datetime), `site` ∈ {east, north, south, west}, `sensor` ∈ {humidity, pressure, temperature}, `value` (float), `ok` (bool).
- 3-hourly readings, 2025-01-01 through 2025-04-10 (≈3 months).
- No missing values in the source — `apply_project_specific_cleaning` only parses `ts` to datetime and sorts.
- ~25% of rows have `ok=False`; the time-series page leaves these in by default and offers a sidebar toggle to drop them.

## Activity log

- **2026-05-04** — scaffolded from `research-viz` skill, then **parser** subskill ran (trimmed to a single-file project: no `--combine`, no missing-data plumbing). Wrote `intermediate_data/sensor_log__parsed.csv` (800 rows) + `parsed_index.json`.
- **2026-05-04** — **interactive** subskill ran. Added `streamlit/pages/1_time_series.py` (site + sensor multi-selects, optional `ok=True` filter, altair line chart with site→colour, sensor→dash, full tooltips). Trimmed `streamlit/index.py` to a single-dataset landing page. Removed `generate_plot.sh` / `plot_gen.py` / `helpers/` / `significance/` from the scaffold since the user only asked for the streamlit page. Versions baked against: streamlit 1.57, altair 6.1.
