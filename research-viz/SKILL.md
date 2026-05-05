---
name: research-viz
description: Reproducible Python research-visualization workflow for tabular data (csv/xlsx/tsv/txt). Produces a self-documenting `visualizations/` folder with a pandas+numpy parser (quality checks, missing-data handling), a matplotlib+seaborn plot generator, and a streamlit/altair interactive viewer — each behind a small shell wrapper. Use this skill whenever the user wants to "visualize / explore / plot / chart / dashboard" a dataset, asks for "research visualizations", to "make a streamlit app from this data", to "clean up this CSV and chart it", points at a `data/` folder of tabular files, says "summarize this dataset visually", or hands over an .xlsx/.csv/.tsv and wants to see what's in it. Also use whenever the user opens a folder that already contains `visualizations/info/context.md` — the skill is designed to be resumable across agent sessions via that context file.
---

# research-viz

Build (and resume) a reproducible Python research-visualization workspace against a tabular dataset. The deliverable is always a `visualizations/` folder next to the user's `data/`, with three callable entry points (`parse_input.sh`, `generate_plot.sh`, `interactive_page.sh`) and human + agent-readable context in `visualizations/info/`.

There are six subskills inside this skill, and any single user request usually triggers one of them. **Each lives in its own folder under `agents/<name>/AGENT.md` — read the matching AGENT.md before running the subskill.**

| Subskill | Trigger | Read |
|---|---|---|
| **parser** | "parse / clean / load / read this", or any other subskill is requested but `intermediate_data/` is empty | `agents/parser/AGENT.md` |
| **plot_gen** | "scatter of …", "violin per …", "correlation heatmap", "small multiples of …", "make me a figure" | `agents/plot_gen/AGENT.md` |
| **interactive** | "let me filter by …", "make a dashboard", "I want to brush / zoom", "show me a streamlit app" | `agents/interactive/AGENT.md` |
| **style_infer** | user uploads a paper / figure / brand guide and says "match this style", or specifies palette/typography/plot-type preferences in plain text | `agents/style_infer/AGENT.md` |
| **significance_test** | user asks for "t-test of X vs Y", "ANOVA across groups", "stat test", "p-values", "is this difference significant" | `agents/significance_test/AGENT.md` |
| **domain_viz** | user asks for visualizations outside the standard chart types and pointing at a specialized python package — EEG/fMRI/brain (`mne`, `nilearn`), molecular (`py3Dmol`), networks (`networkx`+`pyvis`), gene tracks (`pyGenomeTracks`), etc. | `agents/domain_viz/AGENT.md` |

Pick the subskill from the user's request. If the user is starting from raw files, run **parser** first; **plot_gen** and **interactive** both consume the parser's outputs (selected via `intermediate_data/parsed_index.json`'s `canonical_csv` field) by default. If a `visualizations/info/style_guide.md` exists (produced by **style_infer**), every plot_gen and interactive run must read and follow it before generating anything new. **significance_test** and **domain_viz** are typically *next-step* prompts you offer the user, not things you run unprompted.

### Hard rule: bake every project-specific decision into the `.py` files

The python scripts you produce are *the project's recipe*. After your session ends the user must be able to run `bash visualizations/parse_input.sh`, `bash visualizations/generate_plot.sh --all`, and `bash visualizations/interactive_page.sh` and reproduce **byte-for-byte the same artifacts you produced** — without re-prompting any agent, without remembering CLI flags, without copy-pasting `--strategy '{"col":"median"}'` from chat.

This means **every choice you made during the session must be written into the python file as the default**, not passed as a runtime flag. Specifically:

- **Imputation strategies** the user agreed to: edit `parser.py`'s `PROJECT_STRATEGIES` dict so `bash parse_input.sh` runs non-interactively and applies them automatically.
- **Custom dtype coercions, drop rules, datetime parsing, unit conversions, column renames**: write them into `parser.py` (a clearly-named function near the top, e.g. `apply_project_specific_cleaning(df)`).
- **Intermediate folder reorganization** (when `data/` is awkward and you laid out a cleaner tree under `intermediate_data/`): encode the mapping in `parser.py` (e.g. a `PROJECT_REORGANIZE` function that maps each source path → desired parsed path), so the same reorganized layout falls out on every rerun.
- **Plot recipes**: every plot the user accepted goes into `plot_gen.py`'s `PROJECT_RECIPES` dict (slug, prompt, data source, hue/palette/log-scale/figsize, etc.). Wire them up so `bash generate_plot.sh --recipe <slug>` reruns one and `--all` regenerates the lot.
- **Streamlit pages**: each accepted exploration is a `.py` file under `streamlit/pages/` with the project-specific filters / charts / colors hardcoded. No runtime configuration needed.
- **Colors / themes / styling**: define a project palette near the top of `plot_gen.py` (or in `helpers/utils.py`) and reference it everywhere — don't sprinkle hex codes inline.

The scaffolding under `assets/scaffolding/` is a **starting template**, not the final state. Different projects will end up with very different `parser.py` and `plot_gen.py` contents — that's the point. When the user later wants to change something (a different imputation strategy, a new plot, a different palette), an agent edits the python files; the user keeps using the same shell wrappers.

While a session is in progress: feel free to run things on the user's behalf via direct python calls or by passing flags. But before you wrap up, **migrate every choice into the python files** so the wrappers are self-contained going forward.

### Hard rule: trim the python files to *only what this project uses*

The scaffolded `parser.py` and `plot_gen.py` are starting templates that contain branches for every supported case (every plot kind, every missing-data strategy, multi-file modes, the prompt grammar parser, etc.). The version you *deliver* must not.

Once the project's behavior is settled:

- **Delete every code path that doesn't run for this project.** If the user only ever wants scatter plots, remove the `violin` / `box` / `hist` / `line` / `heatmap` branches from `build_plot()` (and the prompt-grammar lookup that picks between them — replace it with a direct call). If only `median` and `drop_row` are ever used, drop the unused branches in `apply_strategy()`. If the data is always a single file, remove the `--combine` plumbing entirely.
- **Delete the unused imports** that fall out of those removals (`re`, `seaborn`-when-only-matplotlib-is-used, etc.). Run the script once to confirm nothing's referenced after the trim.
- **Inline what no longer needs to be configurable.** If `PROJECT_RECIPES` ends up with one recipe, the recipe-dispatch / `--recipe` / `--all` machinery is overkill — collapse to a single function and have the wrapper call it. The user's mental model should be: "this script does the thing I want, and the code inside is exactly the code that produced the thing."
- **Drop the boilerplate "this is a starting point" docstrings** that referenced the original scaffold. Replace them with a short docstring describing what *this* parser/plot_gen actually does for *this* project.

The principle: a human reading `scripts/parser.py` should see a tight, project-specific script — not a generic library with most of the code unreachable for their dataset.

### Hard rule: comment the surviving code

Every function that remains, and every non-trivial step inside it, gets a concise comment explaining what it's doing *for this project specifically*. Aim for one short line per logical step — enough that a non-expert can follow what's happening without reading pandas docs.

Good (concise, project-specific):

```python
# Drop rows where the patient gave no consent (consent column is "Y"/"N").
df = df[df["consent"] == "Y"]

# Convert visit_date from "DD-MM-YYYY" strings to datetime; rows that fail to parse
# are kept as NaT and handled later by the drop_row strategy on visit_date.
df["visit_date"] = pd.to_datetime(df["visit_date"], format="%d-%m-%Y", errors="coerce")
```

Bad (generic, what-not-why):

```python
# convert column to numeric  ← obvious from the call
df["age"] = pd.to_numeric(df["age"])
```

Bad (overlong essay):

```python
# Here we use pd.to_datetime which is pandas' standard datetime parser. It accepts
# a format argument that follows the strftime conventions, see the pandas docs at
# ...
df["visit_date"] = pd.to_datetime(...)
```

Comment the *intent* and *why this dataset needs it*, not the syntax. The combination of "trimmed code" + "explains what's happening per step" is what makes the file readable as a project recipe rather than a generic tool.

### Hard rule: be honest about what you can see

Several subskills (style_infer, the screenshot-feedback loop in plot_gen / interactive) involve looking at images. **If the model running this skill doesn't have multi-modal capabilities, say so plainly and don't hallucinate image content.** Concretely:

- When the user uploads a paper / figure / screenshot for **style_infer**: still copy the file verbatim into `visualizations/info/style_refs/`, but tell the user honestly you can't read it. Ask them to describe the relevant style features (palette, typography, plot kinds), or offer to exit the subskill.
- When the user sends a screenshot of an existing visualization with feedback ("upper right corner is wrong", "more padding in the middle"): if you *can* see images, look at the actual screenshot before interpreting the feedback — don't reason from the user's text alone. If you *can't* see images, say so and ask the user to describe what's wrong, or offer to exit.
- Never guess at what's in an image. A frank "I can't see this — please describe it or exit" is the right response, not a confident hallucination.

### Hard rule: `data/` is read-only

The skill never writes to, renames, or deletes anything inside `data/`. `data/` is the user's source of truth — treat it as read-only at every step. All cleaned, reshaped, imputed, or otherwise transformed outputs go into `intermediate_data/`.

If the layout under `data/` is awkward (e.g. mixed file types in one folder, opaque names like `final_FINAL_v3.csv`, or one giant flat dump that should be grouped by subject/session), **do not reorganize the source**. Instead, design a cleaner layout *inside* `intermediate_data/` and write the transformed outputs there. Note the mapping (source → reorganized path) in `info/context.md` and in `parsed_index.json` (each per-file entry already records `source_file` and `parsed_path`).

### Naming convention for intermediate outputs

Every file the parser (or any later transform) writes into `intermediate_data/` must use a meaningful suffix that names the *kind of transformation* applied, joined to the source dataset name with a double underscore:

```
<original_dataset_name>__<stage>.<ext>
```

Examples (tabular case — the default):

- `penguins__parsed.csv` — basic load + quality check + missing-data strategies applied
- `penguins__long.csv` — pivoted from wide to long
- `penguins__imputated.csv` — imputation pass distinct from `__parsed`
- `penguins__zscored.csv` — standardized columns
- `penguins__filtered_adults.csv` — row filter applied

**The extension follows the format the data actually needs.** CSV is the right choice for the tabular data the standard parser handles, but for **domain_viz** workflows the format is whatever the domain package expects — forcing everything into CSV is silly and lossy when an established binary format exists. Use the native format and keep the same naming pattern:

- `subj01__parsed.fif` — `mne` Raw / Epochs / Evoked written via `.save(...)`
- `subj01__alpha_band.fif` — band-passed and saved as fif
- `bold_run1__resampled.nii.gz` — `nilearn` 4-D NIfTI image after resampling
- `complex_AB__aligned.pdb` — aligned protein structure
- `cells__filtered.h5ad` — `scanpy` AnnData
- `volume__downsampled.zarr` — `napari` / `zarr` chunked array

Pick the format the next step in the pipeline expects to load — never force a round-trip through CSV unless that's genuinely the cleanest representation. Record the format choice (and the reason, if non-obvious) in `info/project_specific_knowledge.md` and ensure each entry in `parsed_index.json` lists the actual `parsed_path` with extension.

Never use generic names like `parsed_results.csv` or `cleaned.csv`. The dataset prefix lets a human (or a future agent) glance at the folder and immediately see where each file came from; the suffix tells them what was done. When several stages stack on the same dataset, chain suffixes only if it materially helps (`penguins__parsed__long.csv`); otherwise keep the latest stage as the suffix and rely on `parsed_index.json` for the lineage.

The two reserved names produced automatically by the bundled tabular parser are:

- `<dataset>__parsed.csv` — per-file output, one per input file (mirrors `data/` layout, or a *better* layout you chose for `intermediate_data/`).
- `combined__parsed.csv` — only when the user explicitly asks to stack files (`--combine concat` or `--combine both`); has a `__source__` column tagging each row's origin.

---

## The big picture: this skill is *resumable*

A user may share their `visualizations/` folder with another agent (or come back to it themselves a week later). That folder is the source of truth, not this conversation. **The `info/` folder is the handoff layer** — `context.md` is the recent-activity log, `style_guide.md` carries visual decisions, `project_specific_knowledge.md` carries domain learnings, `how_to_use.md` is the human-facing guide. Read all of them at the start; update the relevant supporting files *during* the work; write `context.md` last as the closing entry.

Be cautious: users edit files outside the agent loop. The context file can drift from reality. The protocol below handles that.

### Step 0 — Resumption protocol (run *before* doing anything else)

1. Locate `./visualizations/info/`. If the whole `visualizations/` doesn't exist, it's a fresh start — skip to Step 1 (Pre-flight).
2. **Read every `.md` in `info/` before doing anything else.** The set you might find:
   - `context.md` — recent activity log, project-at-a-glance, drift signals.
   - `style_guide.md` (if present) — palette / typography / plot-type preferences + per-plot overrides. Read this before writing or modifying any plot_gen / streamlit code, regardless of whether `context.md` flags it.
   - `project_specific_knowledge.md` (if present) — domain-specific things a previous agent learned (e.g. how to use `mne` for EEG topomaps). May reference `info/knowledge/<topic>.md` for longer notes — read those if the user's request touches that topic.
   - `how_to_use.md` — the human-facing guide. Skim so you don't contradict it; update it when the wrappers' behavior actually changes.
3. Quick on-disk reconciliation: `ls visualizations/scripts/`, `ls visualizations/plots/`, `ls visualizations/intermediate_data/`, `ls visualizations/streamlit/pages/`, `ls visualizations/significance/` (if present), `ls visualizations/info/style_refs/` (if present), `ls visualizations/info/knowledge/` (if present) — and check `data/` for new or removed files. Compare to what `context.md` claims.
4. If on-disk state diverges from `context.md` (new files, missing files, modified scripts), surface the drift to the user in one short message before acting: "context.md says X was the latest plot, but I see Y/Z on disk and `parser.py` was modified — should I (a) update context.md to match reality, (b) re-run parsing, (c) ignore?" Then proceed based on the answer.

**While the work proceeds:** update the relevant `info/*.md` *as you go* — `style_guide.md` when the user expresses a styling preference, `project_specific_knowledge.md` when you learn something domain-specific, `how_to_use.md` when behavior of the wrappers changes. Don't batch these to the end; they're work-product, not just documentation.

**At the close of the session:** write `context.md` last — append one concise entry per meaningful action (parser ran, plots produced, streamlit app updated, style_guide built or revised, significance test added, project_specific_knowledge appended). See `assets/scaffolding/info/context.md` for the format and tone. A future agent should be able to reconstruct *what was done and where to find it* from `context.md` alone, then load the supporting `info/*.md` files for depth.

---

## Step 1 — Pre-flight: folder structure

The expected layout is:

```
.
├── data/                       (the user's raw files — provided)
└── visualizations/             (this skill produces this)
    ├── README.md
    ├── info/
    │   ├── context.md                    (recent activity log — written last)
    │   ├── how_to_use.md                 (human-facing guide)
    │   ├── style_guide.md                (created by style_infer if any reference / preference exists)
    │   ├── style_refs/                   (verbatim copies of reference papers / figures / brand guides)
    │   ├── project_specific_knowledge.md (created by domain_viz when a non-standard package was learned)
    │   └── knowledge/                    (only when project_specific_knowledge.md gets too long)
    ├── parse_input.sh
    ├── generate_plot.sh
    ├── interactive_page.sh
    ├── scripts/
    │   ├── parser.py
    │   ├── plot_gen.py
    │   └── helpers/utils.py
    ├── intermediate_data/      (writable; data/ is never modified)
    │   ├── parsed_index.json   (always; manifest of what got parsed)
    │   ├── <dataset>__parsed.csv         (one per input file; suffix names the stage)
    │   ├── <dataset>__long.csv           (example follow-on transform)
    │   ├── combined__parsed.csv          (only with --combine concat / both)
    │   └── <subdirs mirroring data/, OR a cleaner layout you designed if data/ is awkward>
    ├── plots/                  (subfolder per plot prompt)
    ├── significance/           (created by significance_test — .txt tables of test results)
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
2. Check whether the packages the chosen subskill needs are importable, **and what version is installed**. Don't just check presence — APIs in our stack (streamlit kwargs, seaborn `ci=` vs `errorbar=`, altair `add_selection` vs `add_params`, statannotations test signature, etc.) drift across releases, and an `ImportError` at write-time is much cheaper than a `TypeError` at the user's runtime. The minimum sets:
   - **parser**: `pandas`, `numpy`, `openpyxl` (for xlsx)
   - **plot_gen**: `pandas`, `numpy`, `matplotlib`, `seaborn` (+ `statannotations` if a recipe overlays significance brackets)
   - **interactive**: `pandas`, `streamlit`, plus `altair` if altair charts are requested
   - **significance_test**: `pandas`, `numpy`, `scipy` (+ `pingouin` if used)

   See **`references/env-management.md`** for a one-shot version-detection snippet and a cheat sheet of **known version-sensitive APIs** in this stack — read it before reaching for any "this kwarg should exist" assumption. When the installed version is older than the cutoff for an API you wanted to use, write the legacy form rather than crashing on the user's machine.
3. If anything is missing, **ask the user how to install** (do not install silently). Offer four choices:
   - install into the current env (`pip install ...`)
   - create a fresh venv at `visualizations/.venv` and install there (skill will then update the `.sh` wrappers to source it)
   - create a fresh conda env (`conda create -n <name> python=3.x ...`)
   - skip — user will install themselves; pause until they confirm
4. **Write the versions you saw into `info/context.md`'s "Python env" line** (one short row: `streamlit 1.28, altair 5.1, statannotations 0.6, …`) so a future agent knows the surface they're targeting and can pick legacy vs. modern API calls without re-detecting.

See `references/env-management.md` for the exact commands, the version-sensitive-API table, and the snippet that needs to go into `parse_input.sh` / `generate_plot.sh` / `interactive_page.sh` when a venv-based install is chosen.

---

## Step 3 — Run the requested subskill

Read the matching `agents/<name>/AGENT.md` before running. Each subskill file documents triggers, behavior, what to bake in, what to trim, and which references to consult.

- **parser** → [`agents/parser/AGENT.md`](agents/parser/AGENT.md)
- **plot_gen** → [`agents/plot_gen/AGENT.md`](agents/plot_gen/AGENT.md)
- **interactive** → [`agents/interactive/AGENT.md`](agents/interactive/AGENT.md)
- **style_infer** → [`agents/style_infer/AGENT.md`](agents/style_infer/AGENT.md)

Common ordering:

1. If the user's request implies styling intent (uploaded a paper/figure/brand guide, or stated explicit visual preferences), run **style_infer** first so subsequent plots inherit the look from `info/style_guide.md`.
2. If `intermediate_data/` is empty, run **parser** before any plot/dashboard work.
3. Then **plot_gen** and/or **interactive** for the actual visualization. Both must read `info/style_guide.md` when it exists.

---

## Step 4 — Always close the loop in `info/`

The session closes in this order: **supporting files first, `context.md` last.**

1. **Update the supporting `info/*.md` files** with anything that came out of the session:
   - **`style_guide.md`** — any styling preference the user expressed (project-wide *or* per-plot, even something as small as "for the petal scatter, use square markers instead of dots"). Style preferences belong in the guide, not buried in a single recipe's `extra` field, so future plots stay consistent.
   - **`project_specific_knowledge.md`** — anything you learned about a domain-specific package or visualization technique that wasn't in your priors (the `domain_viz` subskill drives this).
   - **`how_to_use.md`** — only when the shell wrappers' behavior actually changed (e.g. a venv was created, a new subpage was added, a new subfolder is now part of the layout).
2. **Then write `context.md`** — append one concise entry covering the whole session:
   - what was requested (one sentence),
   - which subskill(s) ran,
   - which files changed (relative paths),
   - one or two gotchas a future agent should know (e.g. "luminosity column had 12% missing, used median imputation"; "streamlit page falls back to pre-rendered PNGs because dataset is 4M rows"; "added project_specific_knowledge.md for `mne` topomaps").

Keep `context.md` concise. The point is *continuation* — not a changelog. If the file grows past ~200 lines, summarize older entries into a "Summary so far" section at the top and trim.

---

## Quick references

When you need depth on a specific topic, read the appropriate file (don't preload them):

- `references/missing-data-strategies.md` — strategies, when each is appropriate, common pitfalls.
- `references/plotting-patterns.md` — research-plot recipes in seaborn + matplotlib.
- `references/streamlit-patterns.md` — caching, multi-page apps, altair selections, large-data fallbacks.
- `references/env-management.md` — venv vs. conda, install commands, how to wire the venv into the `.sh` wrappers.
- `references/figure-design-guidelines.md` — the ten-rules-for-better-figures cheat sheet (Rougier et al. 2014). General design *guidelines, not gates*; useful when discussing chart choice with the user, when style_infer is making default choices, and when sanity-checking output.

The scaffolding under `assets/scaffolding/` is the single source of truth for the initial file contents — when in doubt, copy from there and adapt rather than writing from scratch.
