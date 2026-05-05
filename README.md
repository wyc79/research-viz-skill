# research-viz

A Claude skill for setting up and running a reproducible Python research-visualization workflow against a tabular dataset (csv, xlsx, tsv, txt). It produces a self-documenting `visualizations/` folder next to your `data/`, with three callable entry points (parsing, static plotting, an interactive streamlit app) and a context file that lets a later agent pick up exactly where the last one left off.

The deliverable is a **project-specific recipe**: every choice the user makes during a session — imputation strategies, intermediate-folder layout, plot recipes, color palette, even per-plot styling tweaks — is baked into the python files. The user can run `bash visualizations/parse_input.sh`, `bash visualizations/generate_plot.sh --all`, and `bash visualizations/interactive_page.sh` long after the agent is gone and reproduce the same outputs without an agent in the loop.

## What's in this folder

```
.
├── README.md                  ← you are here
├── research-viz/              ← the skill itself (install this)
│   ├── SKILL.md               ← top-level rules + dispatch to subskills
│   ├── agents/                ← one folder per subskill, each with AGENT.md
│   │   ├── parser/
│   │   ├── plot_gen/
│   │   ├── interactive/
│   │   └── style_infer/
│   ├── assets/scaffolding/    ← templates copied into the user's project
│   ├── references/            ← deeper-dive reading on missing data, plot patterns, streamlit, env mgmt
│   └── scripts/scaffold.py    ← creates a fresh visualizations/ tree for a new project
├── research-viz.skill         ← packaged installer (drop this into Claude)
├── example/                   ← worked example using the Palmer Penguins dataset
└── research-viz-workspace/    ← evaluation artefacts (test runs, benchmark, viewers)
```

## Hard rules the skill enforces

- **`data/` is read-only.** The skill never writes to, renames, or deletes anything in `data/`. If the source layout is awkward (flat dump, opaque names), the skill designs a cleaner tree under `intermediate_data/` and records the mapping — without touching the source.
- **Bake every project decision into the `.py` files.** Imputation strategies, custom dtype coercions, plot recipes, palette, streamlit filters — all live as defaults in `parser.py` / `plot_gen.py` / `streamlit/pages/*.py`, not as flags the user has to remember.
- **Trim and comment the delivered scripts.** The scaffold is a starting template with branches for every supported case; the *delivered* scripts contain only what this project actually uses, with concise per-step comments. A human reading them sees a tight, project-specific recipe — not a generic library with most code unreachable.
- **Meaningful intermediate names.** Every CSV in `intermediate_data/` follows `<original_dataset_name>__<stage>.csv` — e.g. `penguins__parsed.csv`, `penguins__long.csv`, `penguins__imputated.csv`. No generic `parsed_results.csv`.
- **Style guide drives forward, doesn't audit backward.** When the user provides a reference paper / figure or expresses preferences, the **style_infer** subskill writes `info/style_guide.md` (with project-wide rules and per-plot overrides). New plots and pages follow it; existing scripts are not retrofitted unless asked. The guide gets updated whenever the user requests a new look.

## What the skill does

When you point an agent at a `data/` folder with tabular files in it and ask for a visualization, the skill walks the agent through this workflow:

1. **Resumption check.** If a `visualizations/` folder already exists, read `visualizations/info/context.md` first, also read `info/style_guide.md` if present, reconcile any drift between what context.md claims and what's actually on disk, then proceed. Designed so a fresh agent in a new session can take over without losing the thread.
2. **Folder + pilot prompt.** Confirm where the data lives. For large or per-session research datasets, surface the option of pointing at a small `pilot_data/` first (iterate on plots cheaply, then re-run on the full data with a `DATA_DIR=...` switch — no script edits needed).
3. **Env handling.** Detect missing packages (pandas, numpy, matplotlib, seaborn, streamlit, altair). Always *ask* before installing — offer current env / project-local venv / fresh conda env / skip.
4. **Four subskills, picked by intent** (each documented under `research-viz/agents/<name>/AGENT.md`):
   - **parser** — pandas+numpy quality checks (per-column dtype consistency, missing-value counts, mixed-type detection) and missing-data handling. The agreed-on strategies, custom cleaning, and intermediate-folder layout are baked in via `PROJECT_STRATEGIES`, `apply_project_specific_cleaning()`, and `project_reorganize()` at the top of `parser.py`. Default behavior for multi-file input is to mirror the `data/` tree under `intermediate_data/` — one cleaned `<name>__parsed.csv` per session/patient/run, no aggregation. `--combine concat` or `--combine both` produces a single `combined__parsed.csv` instead.
   - **plot_gen** — matplotlib + seaborn static plots. Free-form `bash generate_plot.sh "<prompt>"` works for ad-hoc charts; accepted plots get registered in `PROJECT_RECIPES` (with `PROJECT_PALETTE` for colors) so `bash generate_plot.sh --recipe <slug>` or `--all` reproduce them verbatim. 300dpi PNG + PDF + the underlying tidy CSV next to each figure for reproducibility.
   - **interactive** — streamlit landing page + auto-discovered subpages under `streamlit/pages/`, with altair as a supplement for linked-brushing or selection-driven views. Falls back to a "viewer" of pre-rendered images for very large data. Filters, default selections, palette, and chart specs are hardcoded into the page files.
   - **style_infer** — given a reference paper (PDF) / figure (image) / brand guide and/or explicit user preferences, produces `info/style_guide.md` (project-wide palette, typography, figure dimensions, plot-type preferences, plus per-plot or per-page overrides). Stores reference uploads verbatim under `info/style_refs/`. Adds a "Style guide active" callout to `context.md` so future sessions always read it before generating new plots.
5. **Always close the loop in `info/context.md`** — short activity-log entries that let the next agent know what ran, which files changed, and any gotchas. New styling preferences get folded into `info/style_guide.md` so they outlive the current session.

## The deliverable layout

```
.
├── data/                       (your raw files — read-only to the skill)
└── visualizations/
    ├── README.md
    ├── info/
    │   ├── context.md          (continuation handoff for future agents)
    │   ├── how_to_use.md       (human-only guide to running the python scripts / shell wrappers)
    │   ├── style_guide.md      (when style_infer has run)
    │   └── style_refs/         (reference papers / figures / brand guides)
    ├── parse_input.sh          (self-locating; honors $DATA_DIR for swapping pilot ↔ full)
    ├── generate_plot.sh        (--recipe <slug> | --all | --list-recipes | "<ad-hoc prompt>")
    ├── interactive_page.sh
    ├── scripts/
    │   ├── parser.py           (PROJECT_STRATEGIES, apply_project_specific_cleaning, project_reorganize)
    │   ├── plot_gen.py         (PROJECT_RECIPES, PROJECT_PALETTE)
    │   └── helpers/utils.py
    ├── intermediate_data/      (writable; data/ is never modified)
    │   ├── parsed_index.json   (manifest + canonical_csv pointer)
    │   ├── <name>__parsed.csv  (one per input file)
    │   ├── <name>__long.csv    (example follow-on transform stage)
    │   ├── combined__parsed.csv  (only with --combine concat / both)
    │   └── combined__parsed.meta.json
    ├── plots/<slug>/{figure.png, figure.pdf, data.csv, spec.json}
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

> Note: these eval numbers are from before the recent updates that introduced `PROJECT_STRATEGIES` / `PROJECT_RECIPES`, the `agents/` split, and the **style_infer** subskill. The eval expectations under `research-viz/evals/evals.json` have been updated to match the new naming and `data/` read-only rule, but a fresh re-run hasn't been recorded here yet.

Browse the actual outputs and assertion-by-assertion grades:

- [Iteration 1 review](research-viz-workspace/iteration-1-review.html) — with skill vs no skill, side-by-side
- [Iteration 2 review](research-viz-workspace/iteration-2-review.html) — after renames + self-locating wrappers

## Try it

The fastest way to see the skill in action is the bundled example:

1. Copy `example/` somewhere writable (so you can edit the generated `visualizations/`).
2. Open the folder in a Claude session that has `research-viz` installed.
3. Ask: *"Set up a research-viz workspace for this penguins data. For missing numeric columns use median imputation; for the sex column drop the rows. Then make me a scatter of bill_length_mm vs bill_depth_mm colored by species, in the style of [paper.pdf]."*

The agent should scaffold, run **style_infer** to extract the palette / typography from the paper into `info/style_guide.md`, run **parser** with median-imputation baked into `PROJECT_STRATEGIES`, register the scatter as a `PROJECT_RECIPES` entry that uses the inferred palette, and append entries to `visualizations/info/context.md`. Then close the session, open it again, and ask for a *new* plot — the next agent will read context.md + style_guide.md and produce a chart that matches the established look without re-asking what's already been decided. The user can run `bash visualizations/generate_plot.sh --all` at any later point to reproduce every plot from scratch.

See [`example/README.md`](example/README.md) for the full walkthrough, including the manual command-line equivalent.

## Installing

Drop `research-viz.skill` into your Claude skills via the Cowork installer (or its equivalent for your client). It's a regular zip-format `.skill` package — Python 3.9+, pandas, numpy, matplotlib, seaborn for the static-plot path; add streamlit (and optionally altair) for the interactive path; PIL / pdf-reading capability for the style_infer path.

## License + credits

The skill itself is released under the MIT license. The Palmer Penguins dataset bundled in `example/` is public-domain (CC0), originally collected by Dr. Kristen Gorman and the Palmer Station LTER and packaged by Allison Horst as the [palmerpenguins](https://allisonhorst.github.io/palmerpenguins/) project.
