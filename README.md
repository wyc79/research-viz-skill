# research-viz

A Claude skill for turning a folder of raw research data into a clean, reproducible visualization workspace — with cleaning code, plotting code, statistical-test outputs, and an interactive dashboard that you can rerun yourself, six months from now, without an agent in the loop.

You point an agent at a `data/` folder. It sets up a `visualizations/` folder next door. From then on, three short commands do everything:

```bash
bash visualizations/parse_input.sh          # clean the raw data
bash visualizations/generate_plot.sh --all  # regenerate every plot
bash visualizations/interactive_page.sh     # launch a streamlit dashboard
```

The python files behind those wrappers are tailored to *your* dataset: they hold the imputation strategy you agreed to, the plot recipes you accepted, the colors you picked, the streamlit pages you wanted. Running the wrappers reproduces what was made, byte-for-byte, without re-prompting.

---

## Installing

Two options:

**A — via the `skills` CLI** (recommended):

```bash
npx skills add wyc79/research-viz-skill
```

Follow the prompt — it pulls this repo's `research-viz/` folder and registers it as a skill in your client.

**B — manual** (works for any client that accepts `.skill` packages):

1. `zip -r research-viz.skill research-viz/` (or use your OS's compress UI on the `research-viz/` folder, then rename `.zip` → `.skill`).
2. Upload the resulting `research-viz.skill` to Claude (or drop it into Cowork's installer / your client's equivalent).

### Python requirements

- **Always:** Python 3.9+, pandas, numpy.
- **For static plots:** matplotlib, seaborn.
- **For dashboards:** streamlit, optionally altair.
- **For tests:** scipy, statsmodels, optionally pingouin.
- **For significance brackets on plots:** statannotations.
- **For domain visualizations:** whichever package the domain needs (mne, nilearn, networkx + pyvis, py3Dmol, scanpy, scikit-image, h5py, nibabel, …) — the skill asks before installing anything.

The skill detects installed package versions before generating code (the cheat sheet of version-sensitive APIs is in [`research-viz/references/env-management.md`](research-viz/references/env-management.md)) — it'll write the legacy form of a kwarg when your installed version is older, rather than crashing on a `TypeError` at runtime.

---

## What you give it / what you get back

```
.
├── data/                                        ← your raw files (csv, xlsx, tsv, txt — and binary
│                                                  formats too: NIfTI, HDF5, .fif, .h5ad, .zarr…)
│                                                  this folder is treated as READ-ONLY
└── visualizations/                              ← everything below is generated for you
    ├── parse_input.sh                           clean the raw data
    ├── generate_plot.sh                         generate static plots
    ├── interactive_page.sh                      launch the streamlit dashboard
    ├── scripts/
    │   ├── parser.py                            your cleaning recipe — strategies + custom logic baked in
    │   ├── plot_gen.py                          your plot recipes — palette, slugs, prompts baked in
    │   └── helpers/utils.py
    ├── intermediate_data/
    │   └── <dataset>__parsed.csv                …or .nii.gz / .fif / .h5ad / .zarr / .pdb for domain data
    ├── plots/<slug>/                            each plot lives in its own folder:
    │   ├── figure.png                           300-dpi PNG
    │   ├── figure.pdf                           vector PDF
    │   ├── data.csv                             the tidy data behind the chart
    │   └── spec.json                            the prompt + options used
    ├── significance/                            statistical-test results (only if you asked for them)
    ├── streamlit/                               the dashboard's pages
    └── info/                                    the handoff layer — read first by every new session
        ├── context.md                           what's been done, where to find it
        ├── how_to_use.md                        a human-only guide to running everything yourself
        ├── style_guide.md                       always present; placeholder until style_infer fills it in
        ├── style_refs/                          always present; ships with a README explaining what
        │                                        belongs here (paper PDFs, brand guides, screenshots)
        └── project_specific_knowledge.md        present once domain_viz has run for a non-standard package
```

The trimmed scaffold is what you actually get — for a parser-only project, `plot_gen.py` / `generate_plot.sh` / `streamlit/` get deleted (the skill's "trim unused subskills" rule); for a streamlit-only project, the plot infrastructure goes. The shell wrappers in your `visualizations/` are the entry points; everything else is project-specific.

---

## Why use this

**Reproducible without the agent.** Most "AI made me a plot" workflows leave you with output but no way to reproduce it. This one always leaves a tight, project-specific python file you can rerun yourself. Every decision the agent and you made together — imputation strategy, plot palette, streamlit filter defaults, statistical test choice — is *baked into the python*, not buried in chat history.

**Resumable across sessions.** The `info/` folder is the handoff layer. A new agent (or you, six months later) can pick up where the last session ended without re-asking what was already decided. `context.md` is the activity log; `style_guide.md` carries the visual decisions; `project_specific_knowledge.md` carries the domain learnings.

**Honest about its limits.** The skill never modifies your `data/` folder. It tells you frankly when it can't see an image. It avoids loading specialized domain packages unless you actually need one. It doesn't auto-generate paper-style captions or run statistical tests unprompted — it offers them as next steps. It checks installed package versions before reaching for kwargs that only exist on newer releases (the `streamlit` / `seaborn` / `altair` / `statannotations` / `scipy` API drift is documented in [`research-viz/references/env-management.md`](research-viz/references/env-management.md) so the agent picks legacy vs. modern call sites correctly).

**Style-aware.** Hand it a paper PDF or a brand guide; it copies the file into `info/style_refs/`, fills in `info/style_guide.md` (palette, typography, plot-type preferences, per-plot overrides), and every subsequent plot and dashboard inherits the look. Express styling preferences in plain text and the same thing happens — no file required.

**Trimmed and commented.** The scaffold is a starting template with branches for every supported case. The code that actually ships in your project contains *only* what your project uses, with concise per-step comments — not a generic library with most code unreachable.

---

## What a session looks like

You: *"Set up a research-viz workspace for the data in `data/`. For missing numeric columns use median imputation; drop rows where the consent column is missing. Make me a scatter of `bill_length_mm` vs `bill_depth_mm` colored by species, in the style of the paper at `paper.pdf`."*

The agent will:

1. Scaffold the folder structure (`info/style_guide.md` and `info/style_refs/README.md` ship with the scaffold; `style_guide.md`'s "Status" line is `🟡 Placeholder` until step 2).
2. Copy `paper.pdf` verbatim into `info/style_refs/`, infer a style (palette, typography, plot kinds), fill in `info/style_guide.md`, and flip Status to `🟢 Active`.
3. Bake the imputation choices into `parser.py`'s `PROJECT_STRATEGIES` and set `PROJECT_NONINTERACTIVE_DEFAULT = True` so `bash parse_input.sh` runs unattended.
4. Run the parser, write `intermediate_data/<dataset>__parsed.csv`.
5. Generate the scatter using the inferred palette, register it as a recipe in `plot_gen.py`'s `PROJECT_RECIPES`.
6. Trim every code path the project doesn't use; append a one-liner to `info/context.md`.

A week later, in a fresh session, you ask for a *different* plot. The new agent reads `info/context.md` + `info/style_guide.md` first, sees what's already decided, and produces a plot that matches the established look without re-asking. You can run `bash visualizations/generate_plot.sh --all` at any time to regenerate everything from scratch.

---

## The six subskills

The skill picks the right subskill from the user's request. Most sessions only touch one or two.

**parser** — clean raw data. Quality checks (per-column dtype consistency, missing-value counts, mixed-type detection), missing-data handling (interactive prompts that get baked in as defaults), per-file outputs that mirror the source layout (or a cleaner one you designed if `data/` is awkward).

**plot_gen** — produce static publication-style plots with matplotlib + seaborn. Free-form prompts work for ad-hoc exploration; accepted plots get registered as named recipes and reproduced with `bash generate_plot.sh --recipe <slug>` or `--all`. Significance brackets via `statannotations` when asked.

**interactive** — a streamlit dashboard with auto-discovered subpages. Filters, default selections, and chart specs are hardcoded into the page files — the same dashboard appears every time. Tooltips and a notes expander ship by default. Three-page demo in `examples/example1_penguin/` (native streamlit charts, altair with linked brushing, pre-rendered PNG gallery).

**style_infer** — extract a project-wide visual style from a reference paper, figure, or brand guide, or from plain-text user preferences. **Fills in** `info/style_guide.md` (which always exists from the scaffold as a placeholder) — palette, typography, figure dimensions, plot-type preferences, plus per-plot overrides. All subsequent plots and dashboards inherit it.

**significance_test** — run statistical tests only when asked: t-tests, Mann-Whitney, ANOVA + Tukey, chi-square, correlations, mixed-effects. Reports effect sizes and assumption-check notes alongside p-values, in `significance/<slug>.txt` (paste-able) and `<slug>.json` (machine-readable).

**domain_viz** — handle visualizations that need a specialized python package or rendering pipeline (EEG/MEG topomaps via `mne`, fMRI brain renders via `nilearn`, networks via `networkx + pyvis`, gene tracks via `pyGenomeTracks`, protein structures via `py3Dmol`, 3-D volume isosurfaces via `skimage.measure.marching_cubes` + `matplotlib`, etc.). Asks you for a package + docs link when needed, learns enough to make the figure, persists what it learned to `info/project_specific_knowledge.md` so the next session doesn't relearn from scratch. Saves intermediate data in the package's native format (`.fif`, `.nii.gz`, `.h5ad`, `.zarr`, …) rather than forcing a CSV round-trip.

Full per-subskill documentation lives under [`research-viz/agents/<name>/AGENT.md`](research-viz/agents/).

---

## Two worked examples

| | `examples/example1_penguin/` | `examples/example2_brain/` |
|---|---|---|
| **Dataset** | Palmer Penguins (CC0, ~10 KB) — bundled in the repo. | BraTS2020 (Kaggle slice format, ~7 GB) — fetched separately. |
| **Subskills exercised** | parser, plot_gen, significance_test, interactive | parser, domain_viz |
| **Sample outputs** | 7 plots (3 colorblind-categorical, 3 monochrome, 1 violin with t-test bracket) + 3-page Streamlit app (native / Altair / PNG-gallery) | 3 paper-style 3-D isosurface views (front, top, medial) — brain grey/transparent, tumor red/opaque |
| **What it teaches** | The standard tabular flow + every chart kind + significance overlays + dashboard patterns. | The `domain_viz` workflow: handle binary multi-modal data, write project-specific knowledge, render in native 3-D. |
| **Cite** | Horst, Hill & Gorman 2020. | Khan et al. 2018 ([doi:10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0)). Image style follows their Fig. 4. |

Each folder has its own README with the exact prompt that built the workspace and a "Driving it manually" section so you can rerun any wrapper.

---

## Try it

1. **Copy `examples/example1_penguin/` somewhere writable.** Or `examples/example2_brain/` if you want to see the `domain_viz` flow — that one needs the BraTS2020 Kaggle dataset; instructions in its README.
2. Open the folder in a Claude session that has `research-viz` installed.
3. Try a prompt like: *"Set up a research-viz workspace for this penguins data. Use median imputation for missing numeric columns; drop rows where sex is missing. Plot bill length vs bill depth colored by species."*

The agent should scaffold, parse, plot, and update `visualizations/info/context.md`. Open `visualizations/info/how_to_use.md` for the human-only guide to rerunning everything yourself.

Full walkthroughs:

- [`examples/example1_penguin/README.md`](examples/example1_penguin/README.md) — tabular flow + significance test + 3-page Streamlit.
- [`examples/example2_brain/README.md`](examples/example2_brain/README.md) — BraTS2020 + domain_viz + paper-style 3-D rendering.

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
├── README.md                       ← you are here
├── research-viz/                   ← the skill itself (install this)
│   ├── SKILL.md                    top-level rules + dispatch
│   ├── agents/                     one folder per subskill, each with AGENT.md
│   │   ├── parser/
│   │   ├── plot_gen/
│   │   ├── interactive/
│   │   ├── style_infer/
│   │   ├── significance_test/
│   │   └── domain_viz/
│   ├── assets/scaffolding/         templates copied into your project
│   │                                (now ships info/style_guide.md placeholder
│   │                                 and info/style_refs/README.md too)
│   ├── references/                 deeper-dive reading: missing-data strategies,
│   │                                plotting patterns, streamlit, env management
│   │                                (with the version-sensitive-APIs cheat sheet),
│   │                                figure-design guidelines
│   ├── evals/                      eval definitions (evals.json + input files)
│   └── scripts/scaffold.py         creates a fresh visualizations/ tree
├── research-viz.skill              packaged installer (drop into Claude)
├── examples/
│   ├── example1_penguin/           Palmer Penguins — tabular + tests + streamlit
│   └── example2_brain/             BraTS2020 — domain_viz + 3-D isosurfaces
└── research-viz-workspace/         evaluation artefacts (iteration-1, iteration-2,
                                     iteration-3 + grading + benchmark.json)
```

---

## License + credits

The skill itself is released under the MIT license.

The figure-design guidance under `research-viz/references/figure-design-guidelines.md` is distilled from Rougier, Droettboom, & Bourne (2014), *[Ten Simple Rules for Better Figures](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833)*, PLOS Computational Biology, 10(9), e1003833 — open access, with companion code at <https://github.com/rougier/ten-rules>.

The Palmer Penguins dataset bundled in `examples/example1_penguin/` is public-domain (CC0), originally collected by Dr. Kristen Gorman and the Palmer Station LTER, and packaged by Allison Horst as [palmerpenguins](https://allisonhorst.github.io/palmerpenguins/).

The 3-D isosurface visualization style in `examples/example2_brain/` follows Khan, M.A. et al. (2019), *Multimodal brain tumor classification using deep learning and robust feature selection*, Multimedia Tools and Applications 78: 16267–16289 ([doi:10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0)) — visual reference for the three-cube layout, with the colour scheme inverted per user preference. The BraTS2020 dataset itself is by Bakas et al. 2017 (Sci. Data 4: 170117) and Menze et al. 2015 (IEEE TMI 34(10)), redistributed in slice format on Kaggle by [Saif Awsaf](https://www.kaggle.com/datasets/awsaf49/brats2020-training-data).
