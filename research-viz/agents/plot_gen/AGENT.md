# plot_gen subskill

Produce static publication-style plots into `plots/<slug>/` — `figure.png` (300 dpi), `figure.pdf`, `data.csv` (the tidy data behind the chart), and `spec.json` (the prompt + extra options used).

Use when the user describes a plot ("scatter of X vs Y colored by Z", "violin per group", "correlation heatmap", "small multiples of <whatever>"). By default the script reads the canonical CSV listed in `intermediate_data/parsed_index.json` (the combined frame if it exists, otherwise the lone per-file output).

Read this together with `../../SKILL.md` for the top-level rules.

---

## Before you draw

If `visualizations/info/style_guide.md` exists, **read it first** and apply it to every plot you produce: the palette, typography, figure dimensions, axis style, and preferred plot types. Mirror those choices into `PROJECT_PALETTE` and the `PROJECT_RECIPES` entries you write. **Also check the "Per-plot / per-page overrides" section** — if the slug you're about to render has an entry there, honor that override on top of the project-wide style.

The style guide is a *guide, not a strict standard*. Don't audit existing recipes for discrepancies; just make sure new figures (and any plot the user explicitly asks you to update) follow the guide. If during this run the user gives a new styling instruction (project-wide or plot-specific), record it in `style_guide.md` (see `agents/style_infer/AGENT.md`) before wrapping up so future sessions inherit it.

If no style_guide.md exists and the user hasn't expressed preferences, use the seaborn `colorblind` palette and the `set_research_theme()` defaults.

## How to draw

Adapt `assets/scaffolding/scripts/plot_gen.py` for the specific request:

- Use seaborn's themed primitives (`relplot`, `displot`, `catplot`, `heatmap`) for almost everything; drop down to matplotlib for layout-heavy figures.
- Always set explicit axis labels, units (if known from the column meta), a title, and a legend with full names.
- The slug for the subfolder is a short kebab-case version of the user's request — e.g. "scatter of mass vs luminosity colored by spectral class" → `mass-vs-luminosity-by-class/`.
- **Don't auto-generate `caption.txt` or burn long captions onto the figure** by default — the in-figure title + axis labels + legend should be enough on their own. Captions are *paragraph-length context*, which most plots don't need to ship with. After the figure is done, **offer it as a next step**: "Want me to draft a paper-style caption you can paste into your manuscript?" If the user says yes, write it to `plots/<slug>/caption.txt`.

## What to bake in (project-time)

- **`PROJECT_RECIPES`** (top of `plot_gen.py`): every plot the user accepted, keyed by slug. Each entry holds at minimum a `prompt`; optionally `data` (a specific CSV) and `extra` (kwargs forwarded to `build_plot`: `palette`, `figsize`, `log_x`, `log_y`, …). The user reproduces a plot with `bash generate_plot.sh --recipe <slug>` or regenerates everything with `--all`. Free-form `bash generate_plot.sh "<prompt>"` is still available for ad-hoc, but anything the project actually keeps must live in `PROJECT_RECIPES`.
- **`PROJECT_PALETTE`** (top of `plot_gen.py`): the project's color choices, lifted from `info/style_guide.md` if it exists. Reference `PROJECT_PALETTE` from every recipe — never inline hex codes elsewhere.
- **Theme / typography**: customize `set_research_theme()` in `helpers/utils.py` if the project's typography or default rcParams differ from the scaffold defaults.

After producing a plot, append a one-line entry to `info/context.md`: what plot, which columns, where it landed, and the recipe slug.

If `context.md` indicates the parser ran against pilot data (or the user mentioned pilot mode in this session), end with a next-step prompt once the plot looks acceptable: "These plots are off the pilot. Want me to re-run with `DATA_DIR=$(pwd)/data bash visualizations/parse_input.sh && bash visualizations/generate_plot.sh --all` so the figures use the full dataset?"

## Iterating on a plot from a screenshot

A common flow: the user runs an existing recipe, takes a screenshot of `figure.png`, marks it up or describes what's wrong ("the legend overlaps the data in the upper right", "y-axis tick labels are too dense", "more padding around the title"), and asks you to fix it.

When this happens:

- **If you can see images:** look at the actual screenshot first, *then* interpret the user's text. The feedback often makes more sense once you see the geometry — e.g. "upper right" only means something with the figure in front of you, and the user might have annotated the screenshot.
- **If you can't see images:** say so plainly ("I can't see images in this session"), ask the user to describe the issue in coordinates / labels you can act on ("which axis label?", "by how many points?"), or offer to exit the iteration and come back when a vision-capable model is running.
- Never guess at the image content. A frank "I can't see this — describe it" is the right response, not a confident "the legend appears to be …".

After fixing, re-run the recipe and ask the user to confirm before baking the change. If the fix is generalizable (a padding rule, a marker shape) it usually belongs in `style_guide.md`; if it's specific to one plot, it goes in that recipe's `extra` field.

## Per-file mode

If the parser ran in `per_file` mode with multiple inputs (no combined CSV), the script raises a helpful error listing the per-file `<dataset>__parsed.csv` outputs. Either pass `--data <path>` for a single file, or loop the user-relevant subset by reading `parsed_index.json` and invoking `generate_plot.sh` once per file with `--slug` overridden to keep names sane.

## Trim before delivering

Per the SKILL.md trim rule: delete unused branches in `build_plot()` (drop `violin` / `box` / `hist` / `line` / `heatmap` cases the project doesn't use), drop the prompt-grammar parser if `PROJECT_RECIPES` is the only entry point, drop unused imports. If `PROJECT_RECIPES` ends up with one entry, consider collapsing the `--recipe` / `--all` dispatch entirely to a single direct call. Keep concise comments on the surviving steps.

## Check the matplotlib / seaborn / statannotations versions first

Before writing any plot code, confirm what's actually installed — several APIs in this stack drift in non-obvious ways:

```bash
python3 -c "import matplotlib, seaborn; print('matplotlib', matplotlib.__version__, '/ seaborn', seaborn.__version__)"
python3 -c "import statannotations; print('statannotations', statannotations.__version__)" 2>/dev/null || true
```

Traps that hit the renderer specifically (full table in `references/env-management.md`):

- **seaborn ≥ 0.12** moved from `ci=95` to `errorbar=("ci", 95)` on relplot/lineplot/barplot — the old `ci` kwarg is gone in 0.14. Use `errorbar=...` unconditionally if seaborn is ≥ 0.12.
- **seaborn ≥ 0.13** is stricter about `hue` + auto-legend interactions on the catplot family. If you set `hue` and don't want a legend, pass `legend=False` explicitly.
- **matplotlib ≥ 3.9** removed `plt.cm.get_cmap('Blues')` — use `mpl.colormaps['Blues']` instead.
- **statannotations 0.6** lets you pass a pre-computed p-value via `Annotator.set_pvalues_and_annotate(pvalues=[…])` after `configure(test=None, ...)`. On 0.5 or older you have to let the Annotator run the test itself, which means re-doing assumption checks the **significance_test** subskill already did.

Pick the legacy or modern form based on what's installed and move on — don't stall. If a recipe genuinely needs a feature only the newer version has, surface that to the user before touching the env.

## Overlaying significance markers (statannotations)

When the user asks to put significance brackets / stars / p-values on a plot ("add a t-test bracket between groups A and B", "show p-values on the violin"), use the [`statannotations`](https://github.com/trevismd/statannotations) package — it composes cleanly with seaborn `boxplot` / `violinplot` / `barplot` and handles bracket layout, multiple-comparison correction, and label formatting.

Pattern for a single comparison:

```python
import seaborn as sns
from statannotations.Annotator import Annotator

ax = sns.violinplot(data=df, x="treatment", y="recovery_time", inner="quartile")
pairs = [("A", "B")]
annot = Annotator(ax, pairs, data=df, x="treatment", y="recovery_time")
annot.configure(test="t-test_welch", text_format="star", loc="outside", verbose=0)
annot.apply_and_annotate()
```

For multiple pairs, list them all in `pairs`; statannotations stacks the brackets sensibly. Test names follow scipy/statsmodels conventions (`t-test_welch`, `Mann-Whitney`, `t-test_paired`, `Wilcoxon`, `Kruskal`).

When the user has already run the **significance_test** subskill for the same comparison, **don't recompute** — load the p-value from `significance/<slug>.json` and pass it via `Annotator.set_pvalues_and_annotate(pvalues=[…])`. Otherwise statannotations runs the test internally.

Bake the annotation into the matching `PROJECT_RECIPES` entry so `bash generate_plot.sh --recipe <slug>` reproduces the annotated plot.

If `statannotations` isn't in the env, prompt the user to install it (`pip install statannotations`) before running — see `references/env-management.md` for the venv-aware install flow.

## References

For common research-plot recipes (paired axes, log scales, error bars, small multiples, faceting, colorblind-safe palettes), see `../../references/plotting-patterns.md`.

For general figure-design guidelines — choosing chart kinds for the audience, picking colormaps, avoiding chartjunk and misleading encodings — see `../../references/figure-design-guidelines.md` (a one-page distillation of Rougier et al. 2014). These are *guidelines, not gates*: lean on them when prompting the user, sanity-check finished plots against them, but follow the user when they want something different. A short cite ("for ordered categories I'd reach for a sequential palette — Rougier et al. Rule 6") is more useful in chat than a generic recommendation.
