# Context — research-viz workspace

> **For future agents:** read this file first, before touching anything in `visualizations/`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, and check `/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-2/eval-1-parser-messy-clinical-csv/with_skill/outputs/data` for any new files. Reconcile drift before acting. After any meaningful change, append an entry to the **Activity log** below.

## Project at a glance

- **Data location:** `/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-2/eval-1-parser-messy-clinical-csv/with_skill/outputs/data`
- **Workspace location:** `/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-2/eval-1-parser-messy-clinical-csv/with_skill/outputs/visualizations`
- **Scaffolded:** 2026-05-04T23:28:55
- **Python env:** ambient `python3` (pandas, numpy, matplotlib, seaborn, openpyxl pre-installed; streamlit/altair not verified — install before running `interactive_page.sh`).

## What lives where

- `scripts/parser.py` — reads raw files, runs quality checks, applies missing-data strategies, writes `intermediate_data/parsed_results.csv`.
- `scripts/plot_gen.py` — produces static research plots from `parsed_results.csv` into `plots/<slug>/`.
- `scripts/helpers/utils.py` — shared helpers (loaders, slug-ification, theming).
- `streamlit/index.py` — landing page for the streamlit explorer; `streamlit/pages/*.py` are subpages.
- `intermediate_data/parsed_results.csv` — the canonical cleaned dataset everything else reads.
- `intermediate_data/parsed_results.meta.json` — column dtypes, missing-data strategy applied, source files, timestamp.

## Dataset notes

_(Append observations about the data as you learn them — column meanings, units, known quirks, missing patterns. Keep concise.)_

- Source: `data/trial_data_messy.csv` — 200 rows, columns: `trial_id, treatment, patient_age, recovery_days, blood_pressure, visit_date, notes`.
- `patient_age` is read as object dtype because it contains string sentinels (`unknown`, `?`, `missing`, plus `N/A` which pandas already maps to NaN). The `median` strategy coerces via `pd.to_numeric(errors='coerce')` so all those become NaN and are then filled with the median; column ends up float64. Quality report does NOT flag this as `heterogeneous` because all cells are `str` post-CSV read (the cell-type check is type(cell), not value-level) — easy to miss for future agents.
- `blood_pressure` had 29 missing (14.5%) — filled with median.
- `notes` had 83 missing (41.5%) — rows dropped per user request, so cleaned dataset is 117 rows.
- `recovery_days` had 0 missing.
- `visit_date` left as object (string) per user request — not parsed to datetime yet.

## Activity log

_Append one entry per subskill run. Format:_
_- **YYYY-MM-DD HH:MM** — `<subskill>` — `<short ask>`. Files: `<paths>`. Notes: `<one or two gotchas>`._

- **2026-05-04T23:28:55** — scaffolded — initial workspace created from research-viz skill. No subskill has run yet.
- **2026-05-04** — parser — clean `data/trial_data_messy.csv`: median for numeric missing, drop rows with missing `notes`, keep `visit_date` as-is. Files: `intermediate_data/parsed_results.csv` (117 rows, 8 cols incl. `__source__`), `intermediate_data/parsed_results.meta.json`. Strategies applied: `{"patient_age":"median","blood_pressure":"median","notes":"drop_row"}`. Notes: text sentinels in `patient_age` (`unknown`, `?`, `missing`) were silently coerced to NaN by the median strategy — quality_report did not flag the column as heterogeneous (all cells were `str` after CSV read). If a future run uses a non-numeric strategy on `patient_age`, those strings will leak through unchanged.
