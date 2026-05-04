---
name: research-viz
description: Reproducible Python research-visualization workflow for tabular data (csv/xlsx/tsv/txt). Produces a self-documenting `visualizations/` folder with a pandas+numpy parser (quality checks, missing-data handling), a matplotlib+seaborn plot generator, and a streamlit/altair interactive viewer — each behind a small shell wrapper. Use this skill whenever the user wants to "visualize / explore / plot / chart / dashboard" a dataset, asks for "research visualizations", to "make a streamlit app from this data", to "clean up this CSV and chart it", points at a `data/` folder of tabular files, says "summarize this dataset visually", or hands over an .xlsx/.csv/.tsv and wants to see what's in it. Also use whenever the user opens a folder that already contains `visualizations/info/context.md` — the skill is designed to be resumable across agent sessions via that context file.
---

# research-viz

Build (and resume) a reproducible Python research-visualization workspace against a tabular dataset. The deliverable is always a `visualizations/` folder next to the user's `data/`, with three callable entry points (`parse_input.sh`, `generate_plot.sh`, `interactive_page.sh`) and human + agent-readable context in `visualizations/info/`.

There are three subskills inside this skill, and any single user request usually triggers one of them:

1. **parser** — read raw data, do quality checks, handle missing values, write `intermediate_data/parsed_results.csv`.
2. **plot_gen** — produce static publication-style plots with matplotlib + seaborn into `plots/<prompt-slug>/`.
3. **interactive** — build a streamlit app (with optional altair charts) under `streamlit/`, falling back to pre-rendered images for very large data.

Pick the subskill from the user's request. If the user is starting from raw files, run **parser** first; **plot_gen** and **interactive** both consume `intermediate_data/parsed_results.csv` by default.

---

## The big picture: this skill is *resumable*

A user may share their `visualizations/` folder with another agent (or come back to it themselves a week later). That folder is the source of truth, not this conversation. **Treat `visualizations/info/context.md` as the handoff document** — it is the first thing you read, and the last thing you update.

Be cautious: users edit files outside the agent loop. The context file can drift from reality. The protocol below handles that.

### Step 0 — Resumption protocol (run *before* doing anything else)

1. Look for `./visualizations/info/context.md` in the current working directory.
2. If it exists:
   - Read it in full.
   - Run a quick on-disk reconciliation: `ls visualizations/scripts/`, `ls visualizations/plots/`, `ls visualizations/intermediate_data/`, `ls visualizations/streamlit/pages/` — and check `data/` for new or removed files. Compare to what `context.md` claims.
   - If on-disk state diverges from `context.md` (new files, missing files, modified scripts), surface the drift to the user in one short message before acting: "context.md says X was the latest plot, but I see Y/Z on disk and `parser.py` was modified — should I (a) update context.md to match reality, (b) re-run parsing, (c) ignore?" Then proceed based on the answer.
3. If no `visualizations/` exists yet, this is a fresh start — proceed to Step 1 (Pre-flight).

After every meaningful action (parser ran, plots produced, streamlit app updated), append a concise entry to `context.md`. See `assets/scaffolding/info/context.md` for the format and tone. Concise but informative — a future agent should be able to reconstruct *what was done and where to find it* from this file alone.

---

## Step 1 — Pre-flight: folder structure

The expected layout is:

```
.
├── data/                       (the user's raw files — provided)
└── visualizations/             (this skill produces this)
    ├── README.md
    ├── info/
    │   ├── context.md          (continuation point for future agents)
    │   └── how_to_use.md
    ├── parse_input.sh
    ├── generate_plot.sh
    ├── interactive_page.sh
    ├── scripts/
    │   ├── parser.py
    │   ├── plot_gen.py
    │   └── helpers/utils.py
    ├── intermediate_data/
    │   ├── parsed_index.json   (always; manifest of what got parsed)
    │   ├── parsed_results.csv  (only when input is a single file, or --combine concat)
    │   └── <data/-mirrored subdirs with per-file CSVs when input has multiple files>
    ├── plots/                  (subfolder per plot prompt)
    └── streamlit/
        ├── index.py
        └── pages/
```

Confirm before scaffolding (raise these questions with the user — concise, prefer recommendations over open-ended asks):

- **Where is the data?** Is there a `data/` directory at the cwd? If yes, use it. If no, ask the user where their raw files live (single absolute path or a list). Do not guess.
- **Pilot mode?** If `data/` is large or contains many sessions/patients/clients, suggest the user split out a small `pilot_data/` (a handful of representative files) and point the skill at *that* first. The wrappers honor `DATA_DIR=...`, so a typical workflow is: scaffold against `pilot_data/`, iterate on plots/dashboards until they look right, then re-run with `DATA_DIR=$(pwd)/data`. Surface this option whenever the data dir looks heavy (>~1 GB or hundreds of files) — don't force it on small datasets.
- **Existing `visualizations/`?** If yes, follow Step 0 (resumption); do *not* clobber.
- **If fresh:** create the full tree by running `python <skill-path>/scripts/scaffold.py <target-dir> --data-dir <data-path>`. The scaffold script copies templates from `assets/scaffolding/` and seeds the docs (`README.md`, `info/context.md`, `info/how_to_use.md`) with the data path. Read `scripts/scaffold.py` if you need to vary behavior.

---

## Step 2 — Pre-flight: Python environment

Decide the env *before* writing or running any Python.

1. Detect the active interpreter and version: `which python3 && python3 --version`. If a venv is already active in the current shell (`$VIRTUAL_ENV`) or there's a project-local `.venv/`, prefer that.
2. Check whether the packages the chosen subskill needs are importable. The minimum sets:
   - **parser**: `pandas`, `numpy`, `openpyxl` (for xlsx)
   - **plot_gen**: `pandas`, `numpy`, `matplotlib`, `seaborn`
   - **interactive**: `pandas`, `streamlit`, plus `altair` if altair charts are requested
3. If anything is missing, **ask the user how to install** (do not install silently). Offer four choices:
   - install into the current env (`pip install ...`)
   - create a fresh venv at `visualizations/.venv` and install there (skill will then update the `.sh` wrappers to source it)
   - create a fresh conda env (`conda create -n <name> python=3.x ...`)
   - skip — user will install themselves; pause until they confirm

See `references/env-management.md` for the exact commands and the snippet that needs to go into `parse_input.sh` / `generate_plot.sh` / `interactive_page.sh` when a venv-based install is chosen.

---

## Step 3 — Run the requested subskill

### Subskill A — parser (file reader + quality checks)

Use when the user gives you raw files and either says "parse / clean / load / read this", or any other subskill is requested but `intermediate_data/` is empty.

The bundled `assets/scaffolding/scripts/parser.py` is a working starting point. Adapt — don't rewrite from scratch — for the specific dataset:

- It auto-detects file format by extension (`.csv`, `.tsv`, `.txt` with sniffed delimiter, `.xlsx`/`.xls`).
- It runs three quality checks and writes a short report to stdout: per-column dtype consistency (does any cell deviate from the column's modal type?), missing-value counts, and obvious format anomalies (mixed date formats, stray strings in numeric columns).
- Missing-data handling is **interactive by default**. The script prints the missing-value summary, then asks the user per column (or globally) which strategy to apply: `ignore` (leave NaN), `drop_row`, `drop_col`, `mean`, `median`, `mode`, `ffill`, `bfill`, `constant:<value>`, or `custom` (the user supplies a small Python expression).
- For a non-interactive run (e.g. CI, or rerunning after the user has already chosen), the script accepts `--strategy '{"col_a":"mean","col_b":"drop_row"}'` as JSON.
- **Output layout depends on input shape**, controlled by `--combine`:
   - **Single input file** (or `--combine concat` with multiple files): writes `intermediate_data/parsed_results.csv` plus `parsed_results.meta.json`. This is the "everything in one frame" path that downstream subskills default to.
   - **Multiple input files** with the default `--combine per_file` (recommended for research data where each file is a session / patient / client / run and should *not* be aggregated): the parser **mirrors the `data/` directory structure inside `intermediate_data/`**, writing one cleaned CSV per input file. There is **no** `parsed_results.csv` in this mode — that's deliberate, to avoid pretending sessions are interchangeable.
   - `--combine both` writes per-file mirrors *and* a combined `parsed_results.csv`.
- A `parsed_index.json` is **always** written, listing every per-file output (with row counts, dtypes, strategies applied) plus whether a combined CSV exists. This is the manifest downstream tools should read to discover what's available.

When the user describes their data (e.g. "the temperature column has some text like 'N/A'", or "patients have wildly different schemas"), update `parser.py` to handle that specific case — but preserve the structure so the script remains rerunnable. After running it once successfully, append the strategies used to `info/context.md`.

For the menu of missing-data strategies and the rationale behind each, see `references/missing-data-strategies.md`.

### Subskill B — plot_gen (static plots)

Use when the user describes a plot ("scatter of X vs Y colored by Z", "violin per group", "correlation heatmap", "small multiples of <whatever>"). By default it reads `intermediate_data/parsed_results.csv` and writes one or more PNGs (and optionally PDFs) to `plots/<prompt-slug>/`.

Adapt `assets/scaffolding/scripts/plot_gen.py` for the specific request:

- Use seaborn's themed primitives (`relplot`, `displot`, `catplot`, `heatmap`) for almost everything; drop down to matplotlib for layout-heavy figures.
- Always set explicit axis labels, units (if known from the column meta), a title, and a legend with full names. Save at 300dpi and also save the underlying tidy data as a CSV next to the PNG so the plot is reproducible.
- The slug for the subfolder is a short kebab-case version of the user's request — e.g. "scatter of mass vs luminosity colored by spectral class" → `mass-vs-luminosity-by-class/`.
- Append a one-line entry to `info/context.md`: what plot, which columns, where it landed.

**Per-file mode:** if the parser ran in `per_file` mode (no `parsed_results.csv`), the script raises a helpful error listing the per-file outputs so you can pick. Either pass `--data <intermediate_data/path/to/specific.csv>` for a single file, or loop the user-relevant subset (e.g. one plot per session / patient) by reading `parsed_index.json` and invoking `generate_plot.sh` for each, with `--slug` overridden to keep names sane.

For common research-plot recipes (paired axes, log scales, error bars, small multiples, faceting, colorblind-safe palettes), see `references/plotting-patterns.md`.

### Subskill C — interactive (streamlit + altair)

Use when the user wants exploration rather than a fixed figure: "let me filter by …", "make a dashboard", "I want to brush / zoom / drill in", "show me a streamlit app".

Decision rule for streamlit vs. altair vs. fall-back-to-plot_gen:

- **Default** is streamlit (`streamlit/index.py` + `streamlit/pages/<topic>.py`) with native streamlit widgets for filtering and `st.altair_chart(...)` for charts that benefit from altair's interactivity (selection, brushing, linked views).
- **Add altair** specifically when streamlit's built-in chart helpers are too plain and the interaction (linked brushing, selection-driven filters across charts) is the point of the page. Pure altair pages in `streamlit/pages/` are fine — they are still launched via `streamlit run streamlit/index.py`.
- **If the data is too large for live computation** (rule of thumb: > 1M rows, or > 200MB, or any chart that would take more than ~2s to render every interaction), switch to a "viewer" mode: pre-render variants with `plot_gen.py` into `plots/<topic>/`, and have the streamlit page show those PNGs with simple controls (a dropdown that picks which pre-rendered figure to display). State this fallback explicitly in `info/context.md` so a future agent knows why the page is image-based.

Adapt `assets/scaffolding/streamlit/index.py` as the landing page. Each new "exploration topic" goes in `streamlit/pages/<topic>.py` so streamlit picks it up automatically in the sidebar. Wrap every data load in `@st.cache_data` with a hash key derived from the file path + mtime so reruns are fast. Run via `bash visualizations/interactive_page.sh` (which is just `streamlit run visualizations/streamlit/index.py` with the right env activation).

For more streamlit and altair patterns, see `references/streamlit-patterns.md`.

---

## Step 4 — Always close the loop in `context.md`

After any subskill run, edit `visualizations/info/context.md` to append:

- what was requested (one sentence),
- which subskill ran,
- which files changed (relative paths),
- one or two gotchas a future agent should know (e.g. "luminosity column had 12% missing, used median imputation"; "streamlit page falls back to pre-rendered PNGs because dataset is 4M rows").

Keep it concise. The point is *continuation* — not a changelog. If the file grows past ~200 lines, summarize older entries into a "Summary so far" section at the top and trim.

Also keep `visualizations/info/how_to_use.md` accurate — it should reflect the current shell wrappers and how to run them. The bundled scaffolding already contains a usable starting version; touch it only when behavior changes (e.g. a venv was created, a new subpage was added).

---

## Quick references

When you need depth on a specific topic, read the appropriate file (don't preload them):

- `references/missing-data-strategies.md` — strategies, when each is appropriate, common pitfalls.
- `references/plotting-patterns.md` — research-plot recipes in seaborn + matplotlib.
- `references/streamlit-patterns.md` — caching, multi-page apps, altair selections, large-data fallbacks.
- `references/env-management.md` — venv vs. conda, install commands, how to wire the venv into the `.sh` wrappers.

The scaffolding under `assets/scaffolding/` is the single source of truth for the initial file contents — when in doubt, copy from there and adapt rather than writing from scratch.
