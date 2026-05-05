# How to use this folder

This `visualizations/` workspace is tailored to `data/flowers.csv` — an iris-style
dataset with 150 rows, three species, and four numeric measurements. The python
files have been trimmed to just what this project uses.

All commands assume your working directory is the project root (the folder that
contains `data/` and `visualizations/`).

---

## 1. Parse the raw data

```bash
bash visualizations/parse_input.sh
```

Loads `data/flowers.csv`, asserts the schema (column set, dtypes, the three
known species, no missing values), and writes:

- `intermediate_data/flowers__parsed.csv` — the canonical cleaned CSV.
- `intermediate_data/parsed_index.json` — manifest with `canonical_csv` pointing
  at the file above.

The script is non-interactive — the user verified the data is already clean,
so the parser just sanity-checks and copies. If the assertions ever fail, the
script aborts loudly rather than silently masking the change.

To point at a different folder:

```bash
DATA_DIR=/path/to/other_data bash visualizations/parse_input.sh
```

---

## 2. Generate plots

Two recipes are baked in:

| Slug | What it draws |
|---|---|
| `petal-length-vs-width-by-species` | Scatter of petal_length vs petal_width, one colour per species |
| `sepal-length-violin-per-species`  | Violin of sepal_length per species, with quartile lines |

```bash
bash visualizations/generate_plot.sh --list-recipes      # list the slugs
bash visualizations/generate_plot.sh --all               # render both
bash visualizations/generate_plot.sh --recipe petal-length-vs-width-by-species
bash visualizations/generate_plot.sh --recipe sepal-length-violin-per-species
```

Each recipe writes to `plots/<slug>/`:
- `figure.png` (300 dpi)
- `figure.pdf`
- `data.csv` — the tidy slice that backs the figure
- `spec.json` — the recipe spec for traceability

### Colours

The species palette is pinned at the top of `scripts/plot_gen.py` as
`PROJECT_PALETTE` (colourblind-safe blue / orange / green from seaborn's
`colorblind` palette). The species order is `setosa, versicolor, virginica` so
legends and x-axis ticks match across both figures.

Edit `PROJECT_PALETTE` and rerun `--all` to re-render with new colours.

---

## 3. Adding a new plot

Open `scripts/plot_gen.py`, write a new render function (mirror the two
existing ones), and add an entry to `PROJECT_RECIPES`. Then:

```bash
bash visualizations/generate_plot.sh --recipe <new-slug>
```

---

## File map

```
visualizations/
├── parse_input.sh              one-arg-free wrapper for parser.py
├── generate_plot.sh            wrapper around plot_gen.py (--recipe / --all / --list-recipes)
├── scripts/
│   ├── parser.py               loads data/flowers.csv, sanity-checks, writes flowers__parsed.csv
│   ├── plot_gen.py             PROJECT_PALETTE + PROJECT_RECIPES baked in
│   └── helpers/utils.py        set_research_theme() — seaborn theming helper
├── intermediate_data/
│   ├── parsed_index.json
│   └── flowers__parsed.csv
├── plots/
│   ├── petal-length-vs-width-by-species/{figure.png, figure.pdf, data.csv, spec.json}
│   └── sepal-length-violin-per-species/{figure.png, figure.pdf, data.csv, spec.json}
└── info/
    ├── context.md              session handoff
    └── how_to_use.md           this file
```

The streamlit folder and shell wrapper exist but were not used in this project;
they're stub-level until someone needs an interactive explorer.
