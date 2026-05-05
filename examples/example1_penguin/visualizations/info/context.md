# Context — research-viz workspace

> **For future agents:** before touching anything in `visualizations/`, **read every `.md` in `info/`** — `context.md` (this file), `style_guide.md` (if present), `project_specific_knowledge.md` (if present), and `how_to_use.md`. Then quickly `ls scripts/`, `ls plots/`, `ls streamlit/pages/`, `ls intermediate_data/`, `ls significance/` (if present), `ls info/style_refs/` (if present), `ls info/knowledge/` (if present), and check `/sessions/vibrant-eager-hypatia/mnt/Visualization Skill/example/data` for any new files. Reconcile drift before acting. While the work proceeds, update the relevant supporting `info/*.md` files as you go; write `context.md` last as the closing entry.

## Style guide

**Style guide active.** This project has a visualization style guide at [`info/style_guide.md`](style_guide.md). Read it before any plot_gen or interactive work and follow it for every new figure / page. Two coordinated palettes (`PROJECT_SPECIES_PALETTE` colorblind-safe categorical, and `PROJECT_MONOCHROME` single-hue blue) are defined at the top of `scripts/plot_gen.py`. **All figures are rendered without grids** — `set_research_theme()` in `scripts/helpers/utils.py` enforces `style="ticks"` and `axes.grid = False`. The streamlit pages import `PROJECT_SPECIES_PALETTE` directly so colours stay consistent across the static and interactive views.

## Project at a glance

- **Data location:** `../data/` (sibling of this `visualizations/` folder; absolute path on this machine: /sessions/vibrant-eager-hypatia/mnt/Visualization Skill/example/data)
- **Scaffolded:** 2026-05-05T04:35:56
- **Python env:** current shell — pandas / numpy / matplotlib / seaborn / scipy / streamlit / altair / statannotations all importable from the ambient interpreter. No `.venv` was created.

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

- Single input file: `data/penguins.csv`, 344 rows × 8 columns (Palmer Penguins).
- Missing values: 4 numeric columns each have 2 missing rows (~0.6%) — filled with column **median**. `sex` has 11 missing (3.2%) — those rows are **dropped**. After cleaning: 333 rows.
- Strategies are baked into `parser.py`'s `PROJECT_STRATEGIES`; `PROJECT_NONINTERACTIVE_DEFAULT = True` so `bash parse_input.sh` runs unattended.
- Species sizes after cleaning: Adelie 146, Chinstrap 68, Gentoo 119.
- Species are nearly island-disjoint in the wild data (Gentoo only on Biscoe, Chinstrap only on Dream, Adelie on all three) — useful to remember when interpreting the per-island boxplot.

## Activity log

_Append one entry per subskill run. Format:_
_- **YYYY-MM-DD HH:MM** — `<subskill>` — `<short ask>`. Files: `<paths>`. Notes: `<one or two gotchas>`._

- **2026-05-05T04:35:56** — scaffolded — initial workspace created from research-viz skill.
- **2026-05-05 04:39** — `parser` — clean `data/penguins.csv` into `intermediate_data/penguins__parsed.csv`. Files: `scripts/parser.py` (trimmed to single-file mode + median/drop_row strategies, `PROJECT_STRATEGIES` baked in, `PROJECT_NONINTERACTIVE_DEFAULT = True`), `intermediate_data/penguins__parsed.csv`, `intermediate_data/parsed_index.json`. Notes: 333 rows after dropping 11 missing-`sex` rows; 4 numeric columns median-imputed (2 rows each).
- **2026-05-05 04:40** — `style_infer` (manual) — wrote `info/style_guide.md` capturing the no-grids rule + two coordinated palettes (colorblind-safe categorical for species, monochrome single-hue blue for non-categorical). Files: `info/style_guide.md`, `scripts/helpers/utils.py` (`set_research_theme` switched to `style="ticks"` and `axes.grid = False`).
- **2026-05-05 04:40** — `significance_test` — Welch's t-test of `body_mass_g` between Adelie and Gentoo. Files: `scripts/significance.py`, `significance/body_mass_g-adelie-vs-gentoo-ttest.{txt,json}`, `significance/README.md`. Notes: t = -23.3, df = 242.1, p ≈ 1.2e-63, Cohen's d = -2.90 (large). Adelie Shapiro p = 0.04 → normality borderline; reported but kept Welch's because the n is large enough to lean on the CLT and the practical effect is huge regardless.
- **2026-05-05 04:41** — `plot_gen` — rendered the seven recipes in `PROJECT_RECIPES` (3 colorblind-species, 3 monochrome single-hue, 1 violin with t-test bracket). Files: `scripts/plot_gen.py` (trimmed; no free-form prompt mode left), `plots/<slug>/{figure.png,figure.pdf,data.csv,spec.json}` × 7. Notes: trimmed `generate_plot.sh` to forward only `--all / --recipe / --list-recipes`; the violin-with-ttest recipe reads its p-value from `significance/.../*.json` so the figure can never disagree with the saved test.
- **2026-05-05 04:42** — `interactive` — wrote 3-page streamlit app. Files: `streamlit/index.py` (single-dataset landing page), `streamlit/pages/1_penguins_overview.py` (native `st.bar_chart` / `st.scatter_chart`), `streamlit/pages/2_bill_morphology_altair.py` (linked-brushing scatter + histogram with clickable legend selector), `streamlit/pages/3_prerendered_gallery.py` (loads `plots/<slug>/figure.png` via `st.image`). Notes: pages 1 and 2 import `PROJECT_SPECIES_PALETTE` from `plot_gen.py` so colours stay in lockstep with the static plots; page 3's dropdown auto-discovers any new recipe in `PROJECT_RECIPES`. Smoke test via `streamlit.testing.v1.AppTest` — all four scripts run clean (deprecation warnings about `use_container_width` only).
