# Context — research-viz workspace

> **For future agents:** before touching anything in `visualizations/`, **read every `.md` in `info/`** — `context.md` (this file), `style_guide.md` (if present), `project_specific_knowledge.md` (if present), and `how_to_use.md`. Then quickly `ls scripts/`, `ls plots/`, `ls intermediate_data/`, and check `../data/` for any new files. Reconcile drift before acting. While the work proceeds, update the relevant supporting `info/*.md` files as you go; write `context.md` last as the closing entry.

## Style guide

_(none yet — no reference paper / figure / brand guide has been provided. Plots use seaborn's `colorblind` palette via `set_research_theme()`, with a project-pinned three-species mapping in `PROJECT_PALETTE` at the top of `scripts/plot_gen.py`.)_

## Project at a glance

- **Dataset:** `../data/flowers.csv` — iris-style table, 150 rows, 5 columns: `species` (setosa / versicolor / virginica) plus four numeric measurements `sepal_length`, `sepal_width`, `petal_length`, `petal_width` (all cm). User confirmed the file is already clean (no missing values, no dtype issues).
- **Data location:** `../data/` (sibling of this folder; absolute path: `/sessions/vibrant-eager-hypatia/mnt/Visualization Skill/research-viz-workspace/iteration-3/eval-2-plotgen-multi-panel-flowers/with_skill/outputs/data`)
- **Scaffolded:** 2026-05-05T04:57:27
- **Python env:** ambient `/usr/bin/python3` (3.10.12). Versions: pandas 2.3.3, numpy 2.2.6, matplotlib 3.10.8, seaborn 0.13.2. Note: seaborn 0.13 is strict about `hue` + auto-legend on `violinplot` — this project passes `hue=...` + `legend=False` to silence the redundant legend (see `_violin_sepal_length_per_species` in `scripts/plot_gen.py`).

## What lives where

- `scripts/parser.py` — loads `data/flowers.csv`, asserts the schema/cleanliness the user promised, writes `intermediate_data/flowers__parsed.csv` + `parsed_index.json`. Trimmed of all interactive missing-data plumbing; the file is one self-contained `load_and_check + main` pair.
- `scripts/plot_gen.py` — two recipes wired to dedicated render functions (no prompt grammar, no `build_plot` switch). `PROJECT_PALETTE` pins the three species to colourblind-safe blue/orange/green; `SPECIES_ORDER` keeps legend ordering stable.
- `scripts/helpers/utils.py` — trimmed to a single `set_research_theme()` helper.
- `intermediate_data/flowers__parsed.csv` — canonical cleaned CSV (identical to `data/flowers.csv` since the source is already clean; the parsed copy is the contract that downstream tools read).
- `intermediate_data/parsed_index.json` — manifest pointing at `flowers__parsed.csv` as `canonical_csv`.
- `plots/petal-length-vs-width-by-species/` — scatter plot output (figure.png, figure.pdf, data.csv, spec.json).
- `plots/sepal-length-violin-per-species/` — violin plot output (figure.png, figure.pdf, data.csv, spec.json).
- `streamlit/` — scaffolded but unused this session.

## Dataset notes

- `species` has exactly three values: `setosa`, `versicolor`, `virginica` (50 rows each).
- `petal_width` minimum is slightly negative (-0.02) — likely measurement noise, kept as-is per the user's "already clean" claim. If a future analysis needs strictly non-negative widths, clamp at zero in `apply_project_specific_cleaning` (currently absent from the trimmed parser; would need re-adding).
- The petal_length / petal_width scatter shows the classic iris pattern: setosa is well-separated; versicolor and virginica overlap.

## Activity log

- **2026-05-05T04:57:27** — scaffolded — initial workspace created from research-viz skill.
- **2026-05-05T04:59** — `parser` — single-file run on `data/flowers.csv`. Parser was trimmed to a load-and-assert script (no missing-data plumbing, no `--combine` modes, no project_reorganize). Produced `intermediate_data/flowers__parsed.csv` (150 rows, 5 cols) + `parsed_index.json`. No imputation or row drops.
- **2026-05-05T04:59** — `plot_gen` — produced two figures via `bash generate_plot.sh --all`:
  - `plots/petal-length-vs-width-by-species/figure.png` — scatter of petal_length vs petal_width, hue=species, colourblind-safe palette, white-edged markers.
  - `plots/sepal-length-violin-per-species/figure.png` — violin of sepal_length per species with `inner="quartile"`. Used the seaborn 0.13-friendly `hue=species, legend=False` form to avoid the deprecated palette-without-hue warning. Both recipes registered in `PROJECT_RECIPES` so `bash generate_plot.sh --recipe <slug>` and `--all` reproduce them. Trimmed `plot_gen.py` (and `generate_plot.sh`) of the prompt-grammar / `build_plot` switch since neither is used.
  - Updated `info/how_to_use.md` to reflect the simplified wrapper API (recipe / all / list-recipes only — no `--prompt` mode any more).
