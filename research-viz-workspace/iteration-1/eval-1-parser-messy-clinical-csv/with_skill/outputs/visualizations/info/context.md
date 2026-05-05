# Context — research-viz workspace

> **For future agents:** read this file first, before touching anything in `visualizations/`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, and check `/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-1/eval-1-parser-messy-clinical-csv/with_skill/outputs/data` for any new files. Reconcile drift before acting. After any meaningful change, append an entry to the **Activity log** below.

## Project at a glance

- **Data location:** `/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-1/eval-1-parser-messy-clinical-csv/with_skill/outputs/data`
- **Workspace location:** `/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-1/eval-1-parser-messy-clinical-csv/with_skill/outputs/visualizations`
- **Scaffolded:** 2026-05-04T23:17:37
- **Python env:** system `python3` (pandas 2.3.3, numpy 2.2.6, openpyxl available). No venv created. Note: `streamlit` and `seaborn` are NOT installed — install before running the interactive or plotgen subskills.

## What lives where

- `scripts/parser.py` — reads raw files, runs quality checks, applies missing-data strategies, writes `intermediate_data/parsed_results.csv`.
- `scripts/plotgen.py` — produces static research plots from `parsed_results.csv` into `plots/<slug>/`.
- `scripts/fcns/utils.py` — shared helpers (loaders, slug-ification, theming).
- `streamlit/index.py` — landing page for the streamlit explorer; `streamlit/pages/*.py` are subpages.
- `intermediate_data/parsed_results.csv` — the canonical cleaned dataset everything else reads.
- `intermediate_data/parsed_results.meta.json` — column dtypes, missing-data strategy applied, source files, timestamp.

## Dataset notes

_(Append observations about the data as you learn them — column meanings, units, known quirks, missing patterns. Keep concise.)_

- Source: `data/trial_data_messy.csv` — 200 rows, 7 original columns (`trial_id`, `treatment`, `patient_age`, `recovery_days`, `blood_pressure`, `visit_date`, `notes`). Parser also adds `__source__` for provenance.
- `patient_age` came in as `object` dtype because the column mixed numeric ages with literal text sentinels (`"unknown"`, `"N/A"`, `"?"`, `"missing"`). The parser's `median` strategy uses `pd.to_numeric(..., errors="coerce")` which converts those sentinels to NaN and then fills with the column median (48.5). After parsing the column is clean `float64`. If you need a strict-numeric column dtype check at the source, that's the place to look.
- `blood_pressure` had 14.5% missing (genuine NaN) — median-imputed.
- `recovery_days` had 0 missing — no strategy applied. (User said "median for the numeric columns"; this column needed no fill, so we left it untouched rather than recomputing onto already-numeric data.)
- `notes` had 41.5% missing — rows dropped per user request. Net row count: 200 -> 117.
- `visit_date` kept as string (`object`) per user request; `parser.py`'s quality report flags it as "looks like a date column but not parsed" — that's expected, leave it for now.
- `treatment` values: `control`, `drug_A`, `drug_B`. `notes` values: `responded`, `no change`, `mild side effect` (after the drop, no blanks remain).

## Activity log

_Append one entry per subskill run. Format:_
_- **YYYY-MM-DD HH:MM** — `<subskill>` — `<short ask>`. Files: `<paths>`. Notes: `<one or two gotchas>`._

- **2026-05-04T23:17:37** — scaffolded — initial workspace created from research-viz skill. No subskill has run yet.
- **2026-05-04 23:18** — `parser` — clean `data/trial_data_messy.csv`: median-impute numeric columns, drop rows with missing `notes`, keep `visit_date` as-is. Files: `intermediate_data/parsed_results.csv` (117 rows x 8 cols), `intermediate_data/parsed_results.meta.json`. Strategies passed via `--strategy` JSON: `{"patient_age":"median","recovery_days":"median","blood_pressure":"median","notes":"drop_row","visit_date":"ignore"}` plus `--no-interactive`. Notes: `patient_age` median strategy doubles as the cleanup for the text sentinels (`unknown`, `N/A`, `?`, `missing`) — `pd.to_numeric(errors="coerce")` inside `apply_strategy` handles them. `recovery_days` had 0 missing so no fill happened. `visit_date` left as string.
