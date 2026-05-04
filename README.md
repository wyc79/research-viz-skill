# research-viz

A Claude skill for setting up and running a reproducible Python research-visualization workflow against a tabular dataset (csv, xlsx, tsv, txt). It produces a self-documenting `visualizations/` folder next to your `data/`, with three callable entry points (parsing, static plotting, an interactive streamlit app) and a context file that lets a later agent pick up exactly where the last one left off.

## What's in this folder

```
.
├── README.md                  ← you are here
├── research-viz/              ← the skill itself (install this)
├── research-viz.skill         ← packaged installer (drop this into Claude)
├── example/                   ← worked example using the Palmer Penguins dataset
└── research-viz-workspace/    ← evaluation artefacts (test runs, benchmark, viewers)
```

## What the skill actually does

When you point an agent at a `data/` folder with tabular files in it and ask for a visualization, the skill walks the agent through this workflow:

1. **Resumption check.** If a `visualizations/` folder already exists, read `visualizations/info/context.md` first, reconcile any drift between what context.md claims and what's actually on disk, then proceed. Designed so a fresh agent in a new session can take over without losing the thread.
2. **Folder + pilot prompt.** Confirm where the data lives. For large or per-session research datasets, surface the option of pointing at a small `pilot_data/` first (iterate on plots cheaply, then re-run on the full data with a `DATA_DIR=...` switch — no script edits needed).
3. **Env handling.** Detect missing packages (pandas, numpy, matplotlib, seaborn, streamlit, altair). Always *ask* before installing — offer current env / project-local venv / fresh conda env / skip.
4. **Three subskills, picked by intent:**
   - **parser** — pandas+numpy quality checks (per-column dtype consistency, missing-value counts, mixed-type detection) and missing-data handling (interactive prompts or `--strategy '{"col":"median",…}'` JSON for non-interactive runs). Default behavior for multi-file input is to **mirror the `data/` tree under `intermediate_data/`** — one cleaned CSV per session/patient/run, no aggregation. `--combine concat` produces a single combined `parsed_results.csv` instead.
   - **plot_gen** — matplotlib + seaborn static plots driven by plain-English prompts ("scatter of X vs Y colored by Z"). 300dpi PNG + PDF + the underlying tidy CSV next to each figure for reproducibility.
   - **interactive** — streamlit landing page + auto-discovered subpages under `streamlit/pages/`, with altair as a supplement for linked-brushing or selection-driven views. Falls back to a "viewer" of pre-rendered images for very large data.
5. **Always close the loop in `info/context.md`** — short activity-log entries that let the next agent know what ran, which files changed, and any gotchas.

## The deliverable layout

```
.
├── data/                       (your raw files)
└── visualizations/
    ├── README.md
    ├── info/
    │   ├── context.md          (continuation handoff for future agents)
    │   └── how_to_use.md
    ├── parse_input.sh          (self-locating; honors $DATA_DIR for swapping pilot ↔ full)
    ├── generate_plot.sh
    ├── interactive_page.sh
    ├── scripts/
    │   ├── parser.py
    │   ├── plot_gen.py
    │   └── helpers/utils.py
    ├── intermediate_data/
    │   ├── parsed_index.json   (always; manifest of what got parsed)
    │   ├── parsed_results.csv  (single-file or --combine concat)
    │   └── <data/-mirrored subdirs of per-file CSVs when input has many files>
    ├── plots/                  (one subfolder per plot prompt)
    └── streamlit/
        ├── index.py
        └── pages/
```

## Eval results

Tested on three realistic prompts: parse a messy clinical CSV, generate two plots from a flowers dataset, and build a sensor-log streamlit dashboard. Each run was executed twice — once with the skill installed, once with no skill (baseline).

| Metric | with skill | baseline (no skill) | Δ |
|---|---|---|---|
| Pass rate (44 assertions across 3 evals) | **100%** | 4.5% | **+95 pp** |
| Avg. wall time | 175 s | 83 s | +92 s |
| Avg. tokens | 51 k | 24 k | +27 k |

The baselines aren't broken — they produce *something* — but they all freelance their own folder structures (one wrote `app.py` straight at the project root, another invented `trial_data_clean.csv` next to `parser.py`). The skill produces a single canonical reproducible workspace every time, including the resumable `info/context.md` handoff. The token / time premium is the cost of doing it properly.

A second iteration (after applying user-requested renames + a self-locating-wrapper fix that surfaced from iteration-1 transcripts) held at 100% with slightly fewer tokens, confirming the changes didn't regress anything.

Browse the actual outputs and assertion-by-assertion grades:

- [Iteration 1 review](research-viz-workspace/iteration-1-review.html) — with skill vs no skill, side-by-side
- [Iteration 2 review](research-viz-workspace/iteration-2-review.html) — after renames + self-locating wrappers

## Try it

The fastest way to see the skill in action is the bundled example:

1. Copy `example/` somewhere writable (so you can edit the generated `visualizations/`).
2. Open the folder in a Claude session that has `research-viz` installed.
3. Ask: *"Set up a research-viz workspace for this penguins data. For missing numeric columns use median imputation; for the sex column drop the rows. Then make me a scatter of bill_length_mm vs bill_depth_mm colored by species."*

The agent should scaffold, run the parser, produce the plot, and append entries to `visualizations/info/context.md`. Then close the session, open it again, and ask for a *new* plot — the next agent will read the context file and continue without re-asking what's already been decided.

See [`example/README.md`](example/README.md) for the full walkthrough, including the manual command-line equivalent.

## Installing

Drop `research-viz.skill` into your Claude skills via the Cowork installer (or its equivalent for your client). It's a regular zip-format `.skill` package — Python 3.9+, pandas, numpy, matplotlib, seaborn for the static-plot path; add streamlit (and optionally altair) for the interactive path.

## License + credits

The skill itself is released under the MIT license. The Palmer Penguins dataset bundled in `example/` is public-domain (CC0), originally collected by Dr. Kristen Gorman and the Palmer Station LTER and packaged by Allison Horst as the [palmerpenguins](https://allisonhorst.github.io/palmerpenguins/) project.
