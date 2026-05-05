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

## What to bake in (project-time)

- **`PROJECT_RECIPES`** (top of `plot_gen.py`): every plot the user accepted, keyed by slug. Each entry holds at minimum a `prompt`; optionally `data` (a specific CSV) and `extra` (kwargs forwarded to `build_plot`: `palette`, `figsize`, `log_x`, `log_y`, …). The user reproduces a plot with `bash generate_plot.sh --recipe <slug>` or regenerates everything with `--all`. Free-form `bash generate_plot.sh "<prompt>"` is still available for ad-hoc, but anything the project actually keeps must live in `PROJECT_RECIPES`.
- **`PROJECT_PALETTE`** (top of `plot_gen.py`): the project's color choices, lifted from `info/style_guide.md` if it exists. Reference `PROJECT_PALETTE` from every recipe — never inline hex codes elsewhere.
- **Theme / typography**: customize `set_research_theme()` in `helpers/utils.py` if the project's typography or default rcParams differ from the scaffold defaults.

After producing a plot, append a one-line entry to `info/context.md`: what plot, which columns, where it landed, and the recipe slug.

## Per-file mode

If the parser ran in `per_file` mode with multiple inputs (no combined CSV), the script raises a helpful error listing the per-file `<dataset>__parsed.csv` outputs. Either pass `--data <path>` for a single file, or loop the user-relevant subset by reading `parsed_index.json` and invoking `generate_plot.sh` once per file with `--slug` overridden to keep names sane.

## Trim before delivering

Per the SKILL.md trim rule: delete unused branches in `build_plot()` (drop `violin` / `box` / `hist` / `line` / `heatmap` cases the project doesn't use), drop the prompt-grammar parser if `PROJECT_RECIPES` is the only entry point, drop unused imports. If `PROJECT_RECIPES` ends up with one entry, consider collapsing the `--recipe` / `--all` dispatch entirely to a single direct call. Keep concise comments on the surviving steps.

## References

For common research-plot recipes (paired axes, log scales, error bars, small multiples, faceting, colorblind-safe palettes), see `../../references/plotting-patterns.md`.

For general figure-design guidelines — choosing chart kinds for the audience, picking colormaps, avoiding chartjunk and misleading encodings — see `../../references/figure-design-guidelines.md` (a one-page distillation of Rougier et al. 2014). These are *guidelines, not gates*: lean on them when prompting the user, sanity-check finished plots against them, but follow the user when they want something different. A short cite ("for ordered categories I'd reach for a sequential palette — Rougier et al. Rule 6") is more useful in chat than a generic recommendation.
