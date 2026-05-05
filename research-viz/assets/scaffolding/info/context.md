# Context — research-viz workspace

> **For future agents:** before touching anything in `visualizations/`, **read every `.md` in `info/`** — `context.md` (this file), `style_guide.md` (if present), `project_specific_knowledge.md` (if present), and `how_to_use.md`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, `ls intermediate_data/`, `ls significance/` (if present), `ls info/style_refs/` (if present), `ls info/knowledge/` (if present), and check `__DATA_DIR__` for any new files. Reconcile drift before acting. While the work proceeds, update the relevant supporting `info/*.md` files as you go; write `context.md` last as the closing entry.

## Style guide

🟡 **Placeholder** — `info/style_guide.md` exists with the scaffold defaults but no project-specific style decisions have been recorded yet. `plot_gen` and `interactive` use the seaborn `colorblind` palette + `set_research_theme()` rcParams. Drop reference materials into `info/style_refs/` and run **style_infer** to populate the guide; the Status line in `style_guide.md` flips to 🟢 *Active* once that happens.

<!-- After style_infer fills the guide, replace the paragraph above with:

🟢 **Style guide active.** This project has a visualization style guide at [`info/style_guide.md`](style_guide.md), built from references in `info/style_refs/`. Read it before any plot_gen or interactive work and follow it for every new figure / page. Mirror the palette / typography / plot-type preferences into `PROJECT_PALETTE` (in `scripts/plot_gen.py`) and the `PROJECT_RECIPES` entries. Per-plot overrides live in the same guide. The guide is a *guide*, not a strict standard — drive forward, don't audit old code.
-->

## Project at a glance

- **Data location:** `../data/` (sibling of this `visualizations/` folder; absolute path on this machine: __DATA_DIR__)
- **Scaffolded:** __TIMESTAMP__
- **Python env:** _(filled in after env decision — current shell, or a venv at `visualizations/.venv`, or a conda env named `<name>`)_

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

_(Append observations about the data as you learn them — column meanings, units, known quirks, missing patterns. Keep concise.)_

- _e.g. `temperature_C` had 12% missing, used median imputation per group_

## Activity log

_Append one entry per subskill run. Format:_
_- **YYYY-MM-DD HH:MM** — `<subskill>` — `<short ask>`. Files: `<paths>`. Notes: `<one or two gotchas>`._

- **__TIMESTAMP__** — scaffolded — initial workspace created from research-viz skill. No subskill has run yet.
