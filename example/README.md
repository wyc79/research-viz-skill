# Example: Palmer Penguins

A small worked example to walk through every subskill in `research-viz` end-to-end.

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

## How to walk through the skill against this folder

From this `example/` directory (or copy it somewhere writable first), the skill will produce a `visualizations/` folder next to `data/`. Two ways:

### A. Drive it through the agent

In an agent session that has the `research-viz` skill installed, point it at this folder and try prompts like:

> "Set up a research-viz workspace for this penguins data. For missing numeric columns use median imputation; for the sex column drop the rows. Then make me three plots: a scatter of bill_length_mm vs bill_depth_mm colored by species, a violin plot of body_mass_g per species, and a correlation heatmap of all numeric columns."

The agent should:

1. Recognize `data/` is present, scaffold `visualizations/`.
2. Check Python env (pandas/numpy/matplotlib/seaborn). Prompt about installing if anything is missing.
3. Run `bash visualizations/parse_input.sh --strategy '{"bill_length_mm":"median","bill_depth_mm":"median","flipper_length_mm":"median","body_mass_g":"median","sex":"drop_row"}'` (or interactively).
4. Generate each plot via `bash visualizations/generate_plot.sh "..."`.
5. Append entries to `visualizations/info/context.md`.

### B. Drive it manually (after the agent has scaffolded once)

```bash
# Parse & clean — non-interactive run
bash visualizations/parse_input.sh \
    --no-interactive \
    --strategy '{"bill_length_mm":"median","bill_depth_mm":"median","flipper_length_mm":"median","body_mass_g":"median","sex":"drop_row"}'

# A few plots
bash visualizations/generate_plot.sh "scatter of bill_length_mm vs bill_depth_mm colored by species"
bash visualizations/generate_plot.sh "violin of body_mass_g per species"
bash visualizations/generate_plot.sh "correlation heatmap of all numeric columns"

# Interactive view (when ready)
bash visualizations/interactive_page.sh
```

## What you should see

After running the steps above:

- `visualizations/intermediate_data/parsed_results.csv` — 333 rows after dropping the 11 with missing `sex` (the 4 numeric columns are still 344 of 333 rows × imputed).
- `visualizations/plots/` — three subfolders, each with a `figure.png`, `figure.pdf`, `data.csv`, and `spec.json`.
- `visualizations/info/context.md` — three new "Activity log" entries, one per subskill run.

## Resumption demo

If you've run the example once and come back later (or hand the folder to a different agent), just open it again and ask for a *new* plot — e.g. "now also give me a small-multiples scatter of all four numeric columns against each other". The new agent will read `info/context.md`, see the missing-data strategy already chosen, and produce the new plot without re-asking.

## Citation

> Horst AM, Hill AP, Gorman KB (2020). palmerpenguins: Palmer Archipelago (Antarctica) penguin data. R package version 0.1.0. https://allisonhorst.github.io/palmerpenguins/. doi: 10.5281/zenodo.3960218.
