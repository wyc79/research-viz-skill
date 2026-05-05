# Context — research-viz workspace

> **For future agents:** before touching anything in `visualizations/`, **read every `.md` in `info/`** — `context.md` (this file), `style_guide.md` (if present), `project_specific_knowledge.md` (if present), and `how_to_use.md`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, `ls intermediate_data/`, `ls significance/` (if present), `ls info/style_refs/` (if present), `ls info/knowledge/` (if present), and check `/sessions/vibrant-eager-hypatia/mnt/Visualization Skill/research-viz-workspace/iteration-3/eval-1-parser-messy-clinical-csv/with_skill/outputs/data` for any new files. Reconcile drift before acting. While the work proceeds, update the relevant supporting `info/*.md` files as you go; write `context.md` last as the closing entry.

## Style guide

_(none yet — populated by the **style_infer** subskill once a reference paper / figure / brand guide is provided, or once the user expresses styling preferences)_

<!-- When style_infer runs, replace the line above with:

**Style guide active.** This project has a visualization style guide at [`info/style_guide.md`](style_guide.md), built from references in `info/style_refs/`. Read it before any plot_gen or interactive work and follow it for every new figure / page. Mirror the palette / typography / plot-type preferences into `PROJECT_PALETTE` (in `scripts/plot_gen.py`) and the `PROJECT_RECIPES` entries. Per-plot overrides live in the same guide. The guide is a *guide*, not a strict standard — drive forward, don't audit old code.
-->

## Project at a glance

- **Data location:** `../data/` (sibling of this `visualizations/` folder; absolute path on this machine: /sessions/vibrant-eager-hypatia/mnt/Visualization Skill/research-viz-workspace/iteration-3/eval-1-parser-messy-clinical-csv/with_skill/outputs/data)
- **Scaffolded:** 2026-05-05T04:56:56
- **Python env:** ambient `python3` (Python 3.10.12, pandas 2.3.3, numpy 2.2.6) — no project venv created.

## What lives where

- `scripts/parser.py` — reads raw files, runs quality checks, applies missing-data strategies, writes cleaned outputs into `intermediate_data/`.
- `scripts/plot_gen.py` — produces static research plots (default reads the canonical CSV listed in `parsed_index.json`).
- `scripts/helpers/utils.py` — shared helpers (loaders, slug-ification, seaborn theming).
- `streamlit/index.py` — landing page for the streamlit explorer; `streamlit/pages/*.py` are subpages.
- `intermediate_data/parsed_index.json` — manifest of every parsed output, with a `canonical_csv` field pointing at the recommended file for "give me everything".
- `intermediate_data/<original_name>__parsed.csv` — one cleaned CSV per input file, mirroring `data/`'s subdirectory layout (or whatever layout `project_reorganize` produces).
- `intermediate_data/combined__parsed.csv` (and `.meta.json`) — only present when the parser ran with `--combine concat` or `--combine both`. Has a `__source__` column tagging each row's origin.
- `info/style_refs/` — verbatim copies of any reference papers / figures / brand guides the user provided.
- `info/style_guide.md` — present once **style_infer** has run; describes project-wide palette / typography / plot-type preferences plus any per-plot or per-page overrides.
- `info/project_specific_knowledge.md` — present once **domain_viz** has run; documents domain-specific packages and patterns the agent learned for this project (with reference links so a new session can relearn).
- `info/knowledge/` — long-form per-topic knowledge files when `project_specific_knowledge.md` would otherwise outgrow itself.
- `significance/` — present once **significance_test** has run; one `.txt` + `.json` per test, plus `README.md` index.

## Dataset notes

- Source: single CSV `data/trial_data_messy.csv` — clinical-trial table, 200 rows × 7 columns: `trial_id, treatment, patient_age, recovery_days, blood_pressure, visit_date, notes`.
- `treatment` has 3 levels: `control`, `drug_A`, `drug_B`.
- `patient_age` came in as **object** dtype because it has stray text values mixed in with numbers (`unknown`, `N/A`, `?`, `missing`). The parser coerces those to NaN in `apply_project_specific_cleaning` before median imputation. After cleaning the column is float64.
- Missing-value pattern (raw): `notes` 41.5% missing (83/200), `blood_pressure` 14.5% (29/200), `patient_age` 12% (24/200) including the 4 sentinel-text rows; `recovery_days` and `visit_date` have no missing values.
- `notes` is a free-text label with 3 observed values: `responded`, `no change`, `mild side effect`. User's instruction was to drop rows where it's missing rather than impute — done here, brings n down to **117**.
- `visit_date` is left as a **string** (object dtype) per user instruction — not parsed to datetime yet. If a future plot needs date math, parse it then (e.g. `pd.to_datetime(df["visit_date"])`).

## Activity log

- **2026-05-05T04:56:56** — scaffolded — initial workspace created from research-viz skill.
- **2026-05-05** — `parser` — "clean trial_data_messy.csv: median for numeric, drop rows with missing notes, keep visit_date as-is, patient_age has text mixed in".
  - Files changed: `scripts/parser.py` (trimmed to single-file project; baked in `PROJECT_STRATEGIES`, `apply_project_specific_cleaning` for the patient_age sentinels, `PROJECT_NONINTERACTIVE_DEFAULT=True`).
  - Files written: `intermediate_data/trial_data_messy__parsed.csv` (117 rows × 7 cols), `intermediate_data/trial_data_messy__parsed.meta.json`, `intermediate_data/parsed_index.json`.
  - Gotchas: parser applies `drop_row` on `notes` BEFORE median imputation, so the medians reflect the kept population (n=117) not the original 200. If a future agent wants population-level medians, swap the order in `clean_frame()`. Sentinel set for `patient_age` is `{"unknown","n/a","na","?","missing",""}` (case-insensitive); add to `AGE_SENTINELS` if new variants appear.
