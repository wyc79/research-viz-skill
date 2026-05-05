# How to use this folder

A human's guide to running everything in this `visualizations/` workspace yourself.

## What this folder is

This folder is a **project-specific recipe**. The python files (`scripts/parser.py`, `scripts/plot_gen.py`, the `streamlit/` pages) have been tailored to *your* dataset — they bake in the imputation strategies you agreed to, any custom dtype/column fixes, the intermediate folder layout that was chosen for your data, the plot recipes that were produced, and the colors/theme used. If a [`info/style_guide.md`](style_guide.md) exists, it documents the palette / typography / plot-type preferences that drive every chart in this folder, plus any per-plot overrides.

The python files only contain the code paths that this project actually uses — unused plot kinds, unused missing-data strategies, and unused configuration plumbing have been trimmed out, and the surviving steps carry inline comments explaining what each one does for *this* dataset. Read top-to-bottom, the scripts should be a short, readable recipe.

That means:

- You can run the shell wrappers below at any time — today, tomorrow, six months from now — and reproduce the exact same outputs without an agent in the loop.
- If something needs to change (a different imputation, a new plot, a different color, a new exploration page), edit the corresponding `.py` file directly, or have an agent edit it. The shell wrappers don't change.
- If you want to do something the script doesn't currently support (e.g. a chart kind that was trimmed out), an agent can add it back from the original `research-viz` skill scaffold.
- The sibling `data/` folder is **read-only** to everything in here — nothing under `visualizations/` will ever modify, rename, or delete files in `data/`. All transformed outputs land in `intermediate_data/`.

All commands assume your working directory is the project root (the folder that contains `data/` and `visualizations/`).

---

## 1. Parse / clean raw data

### Shell wrapper

```bash
bash visualizations/parse_input.sh
```

Walks the sibling `data/` directory, applies your project's cleaning rules, and writes cleaned outputs into `intermediate_data/`. The cleaning rules — per-column missing-data strategies, dtype coercions, etc. — are baked into `scripts/parser.py`:

- `PROJECT_STRATEGIES` (top of `parser.py`) holds the per-column missing-data strategy for this project.
- `apply_project_specific_cleaning(df, source_path)` (top of `parser.py`) holds any custom dtype coercions, column renames, sentinel-replacements, datetime parsing, etc.
- `project_reorganize(source_relative)` (top of `parser.py`) maps source paths under `data/` to (possibly cleaner) paths under `intermediate_data/`.
- `PROJECT_NONINTERACTIVE_DEFAULT` (top of `parser.py`) controls whether the wrapper runs unattended by default.

If `PROJECT_STRATEGIES` is filled in and `PROJECT_NONINTERACTIVE_DEFAULT = True`, `bash parse_input.sh` runs end-to-end without prompting and produces the same output as the last agent session.

### Output

- One **per-file** cleaned CSV per input file, named `<original_dataset_name>__parsed.csv`. So `data/patient_001/session_a.csv` becomes `intermediate_data/patient_001/session_a__parsed.csv` (or wherever `project_reorganize` sends it).
- `intermediate_data/parsed_index.json` — manifest of every output, with a `canonical_csv` field pointing at the recommended file for "give me everything".
- For multi-file `--combine concat` runs, additionally a `combined__parsed.csv` (with a `__source__` column tagging each row's origin) and `combined__parsed.meta.json`.

Available missing-data strategies per column: `ignore` · `drop_row` · `drop_col` · `mean` · `median` · `mode` · `ffill` · `bfill` · `constant:<value>`.

### Override the baked-in defaults

If you want to override `PROJECT_STRATEGIES` for a one-off run:

```bash
# Skip the prompts, override one column
bash visualizations/parse_input.sh --no-interactive \
    --strategy '{"temperature_C":"median","comment":"drop_col"}'

# Force the interactive prompts even if PROJECT_NONINTERACTIVE_DEFAULT = True
bash visualizations/parse_input.sh --interactive
```

### Run on a different data folder

```bash
DATA_DIR=/path/to/other_data bash visualizations/parse_input.sh
# or
bash visualizations/parse_input.sh --data-dir /path/to/other_data
```

A common workflow: keep a small `pilot_data/` next to your full `data/`, iterate on it, then re-run with `DATA_DIR=$(pwd)/data` once the visuals look right.

### Force aggregation across files

By default the parser keeps each input file separate (good for per-session/patient data). If you actually want one combined frame:

```bash
bash visualizations/parse_input.sh --combine concat       # only combined__parsed.csv
bash visualizations/parse_input.sh --combine both         # both per-file outputs AND combined__parsed.csv
```

### Direct Python invocation

The wrapper just runs:

```bash
python visualizations/scripts/parser.py \
    --data-dir <data folder> \
    --out visualizations/intermediate_data \
    [--strategy '{...}'] [--no-interactive] [--interactive] \
    [--combine per_file|concat|first|both]
```

Run `python visualizations/scripts/parser.py --help` for the full flag list.

### Naming convention for intermediate files

Anything written into `intermediate_data/` follows `<original_dataset_name>__<stage>.csv`, for example:

- `penguins__parsed.csv` — basic load + missing-data handling
- `penguins__long.csv` — wide → long reshape
- `penguins__imputated.csv` — separate imputation pass
- `penguins__zscored.csv` — standardized columns

The `__parsed.csv` outputs are produced automatically by `parser.py`; later stages are added by follow-up scripts. Each new file is appended to `parsed_index.json`.

---

## 2. Generate static plots

### List the recipes for this project

```bash
bash visualizations/generate_plot.sh --list-recipes
```

Prints every plot recipe baked into `plot_gen.py`'s `PROJECT_RECIPES` dict — these are the project's canonical plots.

### Regenerate every project plot at once

```bash
bash visualizations/generate_plot.sh --all
```

Re-renders every recipe from `PROJECT_RECIPES`, writing each into its own `plots/<slug>/` folder with `figure.png` (300 dpi), `figure.pdf`, the underlying tidy data as `data.csv`, and a `spec.json` recording the prompt and any extra options.

### Regenerate one named recipe

```bash
bash visualizations/generate_plot.sh --recipe petal-length-vs-width-by-species
```

### Ad-hoc free-form plot

```bash
bash visualizations/generate_plot.sh "scatter of mass vs luminosity colored by spectral_class, log y"
bash visualizations/generate_plot.sh "violin per treatment group of recovery_time, faceted by sex"
bash visualizations/generate_plot.sh "correlation heatmap of all numeric columns"
```

The wrapper reads `intermediate_data/parsed_index.json` and plots from whatever it lists as the canonical CSV — the combined frame if it exists, otherwise the lone per-file output. Output goes to `plots/<slug>/`. The slug is derived from the prompt; override with `--slug <name>`.

If you find yourself running the same ad-hoc prompt repeatedly, **register it as a recipe in `PROJECT_RECIPES`** at the top of `plot_gen.py` so it's reproducible.

### Plot from a specific per-file CSV

When the parser produced multiple per-file outputs and there's no canonical aggregate, point `--data` at the file you want:

```bash
bash visualizations/generate_plot.sh "metric over time" \
    --data visualizations/intermediate_data/patient_001/session_a__parsed.csv \
    --slug patient_001-session_a-metric
```

### Direct Python invocation

```bash
python visualizations/scripts/plot_gen.py \
    --intermediate visualizations/intermediate_data \
    --out visualizations/plots \
    [--prompt "<...>" | --recipe <slug> | --all | --list-recipes] \
    [--slug <name>] [--data <path-to-csv>]
```

Run `python visualizations/scripts/plot_gen.py --help` for the full flag list.

The bundled grammar handles scatter / violin / box / hist / line / correlation heatmap. For anything more complex, edit `visualizations/scripts/plot_gen.py` directly — the `build_plot()` function is a small switch you can extend, and `PROJECT_RECIPES` is where you register the polished result.

### Changing colors / theme

The project palette is defined as `PROJECT_PALETTE` near the top of `plot_gen.py` and as `set_research_theme()` in `scripts/helpers/utils.py`. Edit those and rerun `bash generate_plot.sh --all` to re-render every plot with the new look.

---

## 3. Interactive streamlit explorer

### Shell wrapper

```bash
bash visualizations/interactive_page.sh
```

Launches `streamlit run visualizations/streamlit/index.py` and opens it in your browser. The landing page shows the parsed datasets, schema, and a sample. Each exploration page lives at `visualizations/streamlit/pages/<n>_<topic>.py` — its filters, default selections, charts, and colors are hardcoded for this project, so you land on the same dashboard every time.

If the parser produced multiple per-file outputs, the landing page's sidebar gets a selector to switch between them.

### Direct Python invocation

```bash
streamlit run visualizations/streamlit/index.py
```

Or, to run a specific page directly without the multi-page sidebar:

```bash
streamlit run visualizations/streamlit/pages/2_species_explorer.py
```

Forward extra flags through the wrapper if you need them:

```bash
bash visualizations/interactive_page.sh --server.port=8600
```

### Want to change a page?

Edit the corresponding `.py` file under `streamlit/pages/`. To add a new page, drop a new `<n>_<topic>.py` file in that folder — streamlit picks it up automatically.

### When the data is too large for live charts

If a chart takes more than ~2 s to update on each interaction (rule of thumb: > 1 M rows or > 200 MB), pre-render PNG variants with `generate_plot.sh --all` and have a streamlit page show them via a dropdown.

---

## File map

```
visualizations/
├── parse_input.sh              shell wrapper around scripts/parser.py
├── generate_plot.sh            shell wrapper around scripts/plot_gen.py
├── interactive_page.sh         shell wrapper that launches streamlit
├── scripts/
│   ├── parser.py               PROJECT_STRATEGIES, project_reorganize, apply_project_specific_cleaning baked in
│   ├── plot_gen.py             PROJECT_RECIPES + PROJECT_PALETTE baked in; --recipe / --all
│   └── helpers/utils.py        shared helpers (delimiter sniffing, slugify, seaborn theme)
├── streamlit/
│   ├── index.py                landing page
│   └── pages/                  project-specific exploration pages
├── intermediate_data/          writable scratch space; data/ is never modified
│   ├── parsed_index.json       manifest of every output + canonical_csv pointer
│   ├── <name>__parsed.csv      per-file cleaned outputs (one per input)
│   ├── <name>__long.csv        example follow-on transform stage
│   ├── combined__parsed.csv    only when --combine concat or both
│   └── combined__parsed.meta.json
├── plots/<slug>/{figure.png, figure.pdf, data.csv, spec.json}
├── significance/               (if present) per-test .txt + .json + README index
├── info/
│   ├── context.md                          continuation handoff for future sessions
│   ├── how_to_use.md                       this file
│   ├── style_guide.md                      (if present) palette / typography / plot-type preferences + per-plot overrides
│   ├── style_refs/                         reference papers / figures / brand guides used to derive the style
│   ├── project_specific_knowledge.md       (if present) domain-specific package learnings (e.g. mne, nilearn)
│   └── knowledge/                          long-form per-topic notes when the above gets dense
└── README.md                               short pointer to this file
```

---

## Want behavior to change?

Open the relevant `.py` file and edit it (or hand it to an agent and say "for `parser.py`, change the temperature_C strategy to median and rerun" / "add a new recipe in `plot_gen.py` for X"). The shell wrappers stay the same — they just rerun whatever the python files say to do.
