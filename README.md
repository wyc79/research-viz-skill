# research-viz

A Claude skill for turning a folder of raw research data into a clean, reproducible visualization workspace — with cleaning code, plotting code, and an interactive dashboard that you can rerun yourself, six months from now, without an agent in the loop.

You point an agent at a `data/` folder. It sets up a `visualizations/` folder next door. From then on, three short commands do everything:

```bash
bash visualizations/parse_input.sh          # clean the raw data
bash visualizations/generate_plot.sh --all  # regenerate every plot
bash visualizations/interactive_page.sh     # launch a streamlit dashboard
```

The python files behind those wrappers are tailored to *your* dataset: they hold the imputation strategy you agreed to, the plot recipes you accepted, the colors you picked, the streamlit pages you wanted. Running the wrappers reproduces what was made, byte-for-byte, without re-prompting.

---

## What you give it / what you get back

```
.
├── data/                           ← your raw files (csv, xlsx, tsv, txt — any of those)
│                                     this folder is treated as READ-ONLY
└── visualizations/                 ← everything below is generated for you
    ├── parse_input.sh              clean the raw data
    ├── generate_plot.sh            generate static plots
    ├── interactive_page.sh         launch the streamlit dashboard
    ├── scripts/
    │   ├── parser.py               your cleaning recipe — strategies + custom logic baked in
    │   ├── plot_gen.py             your plot recipes — palette, slugs, prompts baked in
    │   └── helpers/utils.py
    ├── intermediate_data/          cleaned outputs (one file per input dataset)
    │   └── <dataset>__parsed.csv   …or `.fif`, `.nii.gz`, `.h5ad`, etc. for domain-specific data
    ├── plots/<slug>/               each plot lives in its own folder:
    │   ├── figure.png              300-dpi PNG
    │   ├── figure.pdf              vector PDF
    │   ├── data.csv                the tidy data behind the chart
    │   └── spec.json               the prompt + options used
    ├── significance/               statistical-test results (only if you asked for them)
    ├── streamlit/                  the dashboard's pages
    └── info/
        ├── context.md              what's been done, where to find it
        ├── how_to_use.md           a human-only guide to running everything yourself
        ├── style_guide.md          (if you provided a style reference)
        ├── style_refs/             (your reference papers / figures / brand guides)
        └── project_specific_knowledge.md   (if a specialized package was used)
```

---

## Why use this

**Reproducible without the agent.** Most "AI made me a plot" workflows leave you with output but no way to reproduce it. This one always leaves a tight, project-specific python file you can rerun yourself.

**Resumable across sessions.** The `info/` folder is the handoff layer. A new agent (or you, six months later) can pick up where the last session ended without re-asking what was already decided.

**Honest about its limits.** The skill never modifies your `data/` folder. It tells you frankly when it can't see an image. It avoids loading specialized domain packages unless you actually need one. It doesn't auto-generate paper-style captions or run statistical tests unprompted — it offers them as next steps.

**Style-aware.** Hand it a paper PDF or a brand guide; it pulls the palette, typography, and plot-type preferences into a project-wide style guide that all subsequent plots and dashboards inherit.

**Trimmed and commented.** The scaffold is a starting template with branches for every supported case. The code that actually ships in your project contains *only* what your project uses, with concise per-step comments — not a generic library with most code unreachable.

---

## What a session looks like

You: *"Set up a research-viz workspace for the data in `data/`. For missing numeric columns use median imputation; drop rows where the consent column is missing. Make me a scatter of `bill_length_mm` vs `bill_depth_mm` colored by species, in the style of the paper at `paper.pdf`."*

The agent will:

1. Scaffold the folder structure.
2. Open the paper, infer a style (palette, typography, plot kinds), save it to `info/style_guide.md` and copy the PDF into `info/style_refs/`.
3. Bake the imputation choices into `parser.py`'s `PROJECT_STRATEGIES`.
4. Run the parser, write `intermediate_data/<dataset>__parsed.csv`.
5. Generate the scatter using the inferred palette, register it as a recipe in `plot_gen.py`'s `PROJECT_RECIPES`.
6. Append a one-liner to `info/context.md`.

A week later, in a fresh session, you ask for a *different* plot. The new agent reads `info/context.md` + `info/style_guide.md` first, sees what's already decided, and produces a plot that matches the established look without re-asking. You can run `bash visualizations/generate_plot.sh --all` at any time to regenerate everything from scratch.

---

## The six subskills

The skill picks the right subskill from the user's request. Most sessions only touch one or two.

**parser** — clean raw data. Quality checks (per-column dtype consistency, missing-value counts, mixed-type detection), missing-data handling (interactive prompts that get baked in as defaults), per-file outputs that mirror the source layout (or a cleaner one you designed if `data/` is awkward).

**plot_gen** — produce static publication-style plots with matplotlib + seaborn. Free-form prompts work for ad-hoc exploration; accepted plots get registered as named recipes and reproduced with `bash generate_plot.sh --recipe <slug>` or `--all`. Significance brackets via `statannotations` when asked.

**interactive** — a streamlit dashboard with auto-discovered subpages. Filters, default selections, and chart specs are hardcoded into the page files — the same dashboard appears every time. Tooltips and a notes expander ship by default.

**style_infer** — extract a project-wide visual style from a reference paper, figure, or brand guide. Writes `info/style_guide.md` (palette, typography, figure dimensions, plot-type preferences, plus per-plot overrides). All subsequent plots and dashboards inherit it.

**significance_test** — run statistical tests only when asked: t-tests, Mann-Whitney, ANOVA + Tukey, chi-square, correlations, mixed-effects. Reports effect sizes and assumption-check notes alongside p-values, in `significance/<slug>.txt` (paste-able) and `<slug>.json` (machine-readable).

**domain_viz** — handle visualizations that need a specialized python package (EEG/MEG topomaps, fMRI brain renders, networks, gene tracks, protein structures, etc.). Asks you for a package + docs link, learns enough to make the figure, persists what it learned to `info/project_specific_knowledge.md` so the next session doesn't relearn from scratch. Saves intermediate data in the package's native format (`.fif`, `.nii.gz`, `.h5ad`, `.zarr`, …) rather than forcing a CSV round-trip.

Full per-subskill documentation lives under [`research-viz/agents/<name>/AGENT.md`](research-viz/agents/).

---

## Installing

Drop `research-viz.skill` into your Claude skills via the Cowork installer (or its equivalent for your client). It's a regular zip-format `.skill` package.

Python requirements:

- **Always:** Python 3.9+, pandas, numpy.
- **For static plots:** matplotlib, seaborn.
- **For dashboards:** streamlit, optionally altair.
- **For tests:** scipy, statsmodels, optionally pingouin.
- **For significance brackets on plots:** statannotations.
- **For domain visualizations:** whichever package the domain needs (mne, nilearn, networkx + pyvis, py3Dmol, scanpy, …) — the skill asks you before installing anything.

---

## Try it

1. Copy `example/` somewhere writable.
2. Open the folder in a Claude session that has `research-viz` installed.
3. Try a prompt like: *"Set up a research-viz workspace for this penguins data. Use median imputation for missing numeric columns; drop rows where sex is missing. Plot bill length vs bill depth colored by species."*

The agent should scaffold, parse, plot, and update `visualizations/info/context.md`. Open `visualizations/info/how_to_use.md` for the human-only guide to rerunning everything yourself.

See [`example/README.md`](example/README.md) for the full walkthrough.

---

## Eval results

Tested on three realistic prompts: parse a messy clinical CSV, generate two plots from a flowers dataset, and build a sensor-log streamlit dashboard. Each run was executed twice — once with the skill installed, once with no skill (baseline).

| Metric | with skill | baseline (no skill) | Δ |
|---|---|---|---|
| Pass rate (36 assertions across 3 evals) | **100%** | 6% | **+94 pp** |
| Avg. wall time | 353 s | 209 s | +144 s |
| Avg. tokens | 85 k | 22 k | +63 k |

The baselines aren't broken — they produce *something* — but they all freelance their own folder structures. In this run: one wrote `app.py` and `interactive_page.sh` at the project root with no `visualizations/` tree at all; another dropped a single `make_plots.py` next to two PNGs named ad-hoc (`scatter_petal_length_vs_width.png`, `violin_sepal_length.png`); the third invented `parse_trial_data.py` and a `trial_data_clean.csv`. The skill produces a single canonical reproducible workspace every time, with the cleaning rules / plot recipes / streamlit pages baked into the python files so the user can rerun the wrappers six months later without an agent in the loop. The token / time premium is the cost of that — reading SKILL.md and the relevant AGENT.md, scaffolding the tree, trimming unused branches, baking decisions into `PROJECT_STRATEGIES` / `PROJECT_RECIPES`, and writing a closing `info/context.md`.

The full assertion-by-assertion grades and timing breakdowns live under `research-viz-workspace/iteration-3/` (`grading.json`, `timing.json`, `benchmark.json` per run). The grading rubric respects the skill's "trim unused subskills" rule — for a parser-only eval the agent is allowed to delete `plot_gen.py` / `generate_plot.sh` rather than ship dead code, which is why the assertion count shrank from earlier iterations (44 → 36).

---

## Project layout

```
.
├── README.md                   ← you are here
├── research-viz/               ← the skill itself (install this)
│   ├── SKILL.md                top-level rules + dispatch
│   ├── agents/                 one folder per subskill, each with AGENT.md
│   │   ├── parser/
│   │   ├── plot_gen/
│   │   ├── interactive/
│   │   ├── style_infer/
│   │   ├── significance_test/
│   │   └── domain_viz/
│   ├── assets/scaffolding/     templates copied into your project
│   ├── references/             deeper-dive reading (missing data, plotting patterns,
│   │                            streamlit, env mgmt, figure-design guidelines)
│   └── scripts/scaffold.py     creates a fresh visualizations/ tree
├── example/                    worked example using Palmer Penguins
└── research-viz-workspace/     evaluation artefacts (test runs, side-by-side viewers)
```

---

## License + credits

The skill itself is released under the MIT license.

The figure-design guidance under `research-viz/references/figure-design-guidelines.md` is distilled from Rougier, Droettboom, & Bourne (2014), *[Ten Simple Rules for Better Figures](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833)*, PLOS Computational Biology, 10(9), e1003833 — open access, with companion code at <https://github.com/rougier/ten-rules>.

The Palmer Penguins dataset bundled in `example/` is public-domain (CC0), originally collected by Dr. Kristen Gorman and the Palmer Station LTER, and packaged by Allison Horst as [palmerpenguins](https://allisonhorst.github.io/palmerpenguins/).
