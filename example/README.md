# Example: Palmer Penguins

A worked example that exercises every major subskill in `research-viz` against a small, real dataset, and lands a fully reproducible `visualizations/` workspace next to the data.

## The dataset

`data/penguins.csv` is the Palmer Penguins dataset (Horst, Hill & Gorman, 2020) — 344 observations of 3 penguin species (Adelie, Chinstrap, Gentoo) collected from 3 islands in Palmer Archipelago, Antarctica. It's a deliberate modern replacement for Fisher's iris dataset and is a popular open-source dataset on Kaggle, R, and Python.

- **Source:** the [palmerpenguins](https://allisonhorst.github.io/palmerpenguins/) package (originally distributed by Dr. Kristen Gorman / Palmer Station LTER).
- **License:** CC0 (public domain).
- **Why we ship it:** it's small (~10 KB), real-world-messy (natural missing values in `bill_length_mm`, `bill_depth_mm`, `flipper_length_mm`, `body_mass_g`, `sex`), and gives you something visually interesting in every chart kind the skill produces.

### Schema

| column | type | notes |
|---|---|---|
| `species` | str | Adelie (152), Gentoo (124), Chinstrap (68) |
| `island` | str | Biscoe / Dream / Torgersen |
| `bill_length_mm` | float | 2 missing |
| `bill_depth_mm` | float | 2 missing |
| `flipper_length_mm` | float | 2 missing |
| `body_mass_g` | float | 2 missing |
| `sex` | str | 11 missing — non-trivial gap, useful for demonstrating different fill strategies |
| `year` | int | 2007 / 2008 / 2009 |

## What this example exercises

The walkthrough below drives **four of the six subskills** in `research-viz`:

1. **parser** — load `penguins.csv`, run quality checks, apply per-column missing-data strategies, and write `intermediate_data/penguins__parsed.csv`.
2. **plot_gen** — produce several static figures in two coordinated styles: a colorblind-safe categorical palette and a single-hue **monochrome** palette, all rendered **without grids**.
3. **significance_test** — run a Welch's t-test on `body_mass_g` between two species and persist the result to `significance/<slug>.{txt,json}`.
4. **interactive** — build a 3-page Streamlit app: one page using **streamlit native plots**, one using **Altair** with linked selection, and one viewer page that **loads the pre-rendered PNGs** produced by `plot_gen`.

`style_infer` and `domain_viz` are not exercised here (Palmer Penguins is plain tabular data with no domain package or external style reference) — but `info/style_guide.md` is still written by hand so future sessions inherit the no-grids + colorblind/monochrome decisions baked in by `plot_gen`.

## The example prompt

Copy-paste this into an agent session that has the `research-viz` skill installed, with the working directory set to this `example/` folder:

> Set up a `research-viz` workspace for this Palmer Penguins data. The `data/penguins.csv` is the only input file, so use single-file mode (no `--combine`).
>
> **Parsing.** For the four numeric columns with missing values (`bill_length_mm`, `bill_depth_mm`, `flipper_length_mm`, `body_mass_g`) use median imputation. For the `sex` column drop the rows that are missing it. Bake these strategies into `parser.py`'s `PROJECT_STRATEGIES` dict and set `PROJECT_NONINTERACTIVE_DEFAULT = True` so `bash parse_input.sh` runs end-to-end unattended. Trim every code path the project doesn't use.
>
> **Styling (write into `info/style_guide.md` and `PROJECT_PALETTE`).** Two coordinated palettes for this project:
> - a **colorblind-safe categorical palette** for plots that compare species (use seaborn's `colorblind` palette; pin one hex per species so it's stable across plots), and
> - a **monochrome single-hue palette** (shades of one color) for plots that show a single distribution or a single-variable trend without a categorical hue.
>
> All plots in this project should be rendered **without grids** — set `axes.grid = False` in `set_research_theme()` (in `helpers/utils.py`) and use a clean `ticks` style instead of `whitegrid`. Top and right spines off, frameless legends.
>
> **Plots (bake all of these into `PROJECT_RECIPES`).** Produce at least the following six figures:
> 1. **Colorblind set:**
>    - scatter of `bill_length_mm` vs `bill_depth_mm` colored by `species`,
>    - violin of `body_mass_g` per `species`,
>    - boxplot of `flipper_length_mm` per `island`.
> 2. **Monochrome set:**
>    - histogram of `body_mass_g` (single hue, no grouping),
>    - histogram of `flipper_length_mm` (single hue, no grouping),
>    - correlation heatmap of all numeric columns using a single-hue sequential cmap (e.g. `Blues`).
>
> **Statistics.** Run a Welch's t-test on `body_mass_g` between **Adelie** and **Gentoo** (those two species look most different on body mass). Save the result to `significance/body_mass_g-adelie-vs-gentoo-ttest.{txt,json}` with group n / mean / sd, t / df / p, 95% CI, Cohen's d, and Shapiro / Levene assumption checks. Then add a **violin plot of `body_mass_g` per `species` with the t-test bracket overlaid** (use `statannotations`, reading the p-value from the saved JSON) as an additional recipe.
>
> **Streamlit (3 pages).** Create the following multi-page app under `streamlit/`:
> - **Page 1 — Streamlit native plots.** Page title "Penguins overview". Use `st.bar_chart`, `st.line_chart`, and `st.scatter_chart` (or `st.dataframe` + native helpers) to show counts per species, mean body mass by species, and a scatter of bill length vs bill depth. No Altair on this page; use only streamlit's native chart helpers and the `PROJECT_PALETTE` colors via the `color=` argument.
> - **Page 2 — Altair explorer.** Page title "Bill morphology (Altair)". Use `alt.Chart` with an interactive species-selection legend and **linked brushing** between two charts (a scatter of bill length vs bill depth on the left, a histogram of `body_mass_g` on the right). Use `PROJECT_PALETTE` for the species color encoding. Show via `st.altair_chart(..., use_container_width=True)`.
> - **Page 3 — Pre-rendered figure viewer.** Page title "Pre-rendered gallery". Use a `st.selectbox` to pick a recipe slug, then display the corresponding `plots/<slug>/figure.png` via `st.image`, with a small `st.caption` showing the prompt that produced it. This is the "fall-back-to-PNG" pattern from the interactive subskill, useful for the heavy plots and as a printable gallery.
>
> Each page should have a one-line subtitle (`st.caption`), tooltips on widgets where they exist, and a collapsed "Notes / data source" expander pulling from `info/context.md`.
>
> **Wrap-up.** Trim `parser.py` and `plot_gen.py` to only the code paths this project actually uses (single-file parser, only `median` and `drop_row` strategies, only the chart kinds we ship). Update `info/style_guide.md` with the no-grid / palette decisions, append one Activity-log entry per subskill run to `info/context.md`, and verify by running `bash parse_input.sh` (no flags), `bash generate_plot.sh --all`, and a quick `streamlit run streamlit/index.py --server.headless true` smoke test.

That's a single self-contained prompt. The agent should do everything in this folder, finishing with a populated `visualizations/` tree (see "What you should see" below).

## How to walk through the skill against this folder

### A. Drive it through the agent (recommended — the example prompt above)

In an agent session that has the `research-viz` skill installed, point it at this folder and paste the prompt above. The agent will:

1. Detect `data/` is present and run `python <skill-path>/scripts/scaffold.py example/ --data-dir example/data` to lay down the `visualizations/` tree.
2. Check the Python env (pandas / numpy / matplotlib / seaborn / scipy / streamlit / altair / statannotations). If anything is missing, it asks how to install before proceeding.
3. **parser** — edit `scripts/parser.py` to bake in `PROJECT_STRATEGIES`, set `PROJECT_NONINTERACTIVE_DEFAULT = True`, trim unused branches, then run `bash parse_input.sh`.
4. **plot_gen** — edit `scripts/helpers/utils.py` to disable grids in `set_research_theme()`, edit `scripts/plot_gen.py` to define `PROJECT_PALETTE` (colorblind species map + monochrome single-hue) and the six recipes, then `bash generate_plot.sh --all`.
5. **significance_test** — write `significance/body_mass_g-adelie-vs-gentoo-ttest.{txt,json}` and a tiny `significance/README.md` index, then add the t-test-annotated violin recipe and re-run `--all`.
6. **interactive** — write the three streamlit pages under `streamlit/pages/`, wired to read from `intermediate_data/penguins__parsed.csv` and the `plots/<slug>/figure.png` files.
7. Update `info/style_guide.md`, `info/context.md`, and `info/how_to_use.md` and run a final smoke test.

### B. Drive it manually (after the agent has scaffolded once)

```bash
cd example/

# 1. Parse — strategies are baked into parser.py, so no flags needed:
bash visualizations/parse_input.sh

# 2. Plots — every recipe in PROJECT_RECIPES, regenerated:
bash visualizations/generate_plot.sh --all
# or one at a time:
bash visualizations/generate_plot.sh --list-recipes
bash visualizations/generate_plot.sh --recipe bill_length-vs-bill_depth-by-species

# 3. Significance — usually generated once by the agent into `significance/`,
#    then optionally re-run as a python invocation:
python visualizations/scripts/significance.py            # if the agent created one
# (or just re-run the recipe; the .txt / .json are version-controlled outputs)

# 4. Streamlit — launches the 3-page app on http://localhost:8501
bash visualizations/interactive_page.sh
```

## What you should see

After running the example prompt against this folder, the layout becomes:

```
example/
├── data/
│   └── penguins.csv
├── README.md                                ← this file
└── visualizations/
    ├── parse_input.sh
    ├── generate_plot.sh
    ├── interactive_page.sh
    ├── scripts/
    │   ├── parser.py                        ← PROJECT_STRATEGIES baked in, trimmed
    │   ├── plot_gen.py                      ← PROJECT_PALETTE + PROJECT_RECIPES baked in
    │   └── helpers/utils.py                 ← set_research_theme() with grids OFF
    ├── intermediate_data/
    │   ├── parsed_index.json
    │   └── penguins__parsed.csv             ← 333 rows after dropping 11 missing-sex
    ├── plots/                               ← one subfolder per recipe slug
    │   ├── bill_length-vs-bill_depth-by-species/{figure.png, figure.pdf, data.csv, spec.json}
    │   ├── body_mass-violin-per-species/...
    │   ├── flipper_length-box-per-island/...
    │   ├── body_mass-histogram-monochrome/...
    │   ├── flipper_length-histogram-monochrome/...
    │   ├── correlation-heatmap-monochrome/...
    │   └── body_mass-violin-per-species-with-ttest/...   ← annotated with the saved p-value
    ├── significance/
    │   ├── body_mass_g-adelie-vs-gentoo-ttest.txt
    │   ├── body_mass_g-adelie-vs-gentoo-ttest.json
    │   └── README.md                        ← auto-generated index
    ├── streamlit/
    │   ├── index.py
    │   └── pages/
    │       ├── 1_penguins_overview.py       ← native st.* charts
    │       ├── 2_bill_morphology_altair.py  ← linked-brushing altair
    │       └── 3_prerendered_gallery.py     ← loads plots/<slug>/figure.png
    └── info/
        ├── context.md                       ← Activity log: parser, plot_gen, significance_test, interactive
        ├── how_to_use.md
        └── style_guide.md                   ← no-grids + colorblind/monochrome decisions
```

The 333-row count in `penguins__parsed.csv` reflects the `drop_row` choice for `sex`; the four numeric columns are still 333-of-333 after median imputation.

## Resumption demo

If you've run the example once and come back later (or hand the folder to a different agent), just open it again and ask for a *new* plot — e.g. "now also give me a small-multiples scatter of all four numeric columns". The new agent reads `info/context.md`, sees the missing-data strategy and palette decisions already baked in, and produces the new plot without re-asking.

## Citation

> Horst AM, Hill AP, Gorman KB (2020). palmerpenguins: Palmer Archipelago (Antarctica) penguin data. R package version 0.1.0. https://allisonhorst.github.io/palmerpenguins/. doi: 10.5281/zenodo.3960218.
