# Style guide

> **For agents:** every plot_gen and interactive run in this project must follow this guide once it's been filled in. Until then, `plot_gen` falls back to its sensible defaults (seaborn `colorblind` palette + `set_research_theme()`'s rcParams) — but if any user preference is expressed *or* a reference appears in `style_refs/`, the **style_infer** subskill should populate this file and you should re-render the affected plots so they pick up the new style.

## Status

🟡 **Placeholder** — no style references or user preferences have been applied yet. `plot_gen` and `interactive` use the seaborn `colorblind` defaults. Replace this status line with one of:

- 🟢 **Active** — when style_infer has filled the sections below from `style_refs/` and/or user notes.
- 🔴 **Conflicting** — only if the user's preferences fight each other (e.g. "match this nature paper" + "but use grayscale only") and you've recorded both with the resolution rule. Resolve before any new render.

## References used

_(filled in by style_infer when a reference is added to `style_refs/`. Format: `style_refs/<filename> — short note on what was taken from it`. Plain-text user preferences without a file go here too, prefixed `(user notes) —`.)_

## Color palette

- **Categorical:** _not specified — falling back to seaborn `colorblind`._
- **Sequential:** _not specified — `viridis`._
- **Diverging:** _not specified — `vlag`, centred at 0._
- **Background:** `#FFFFFF`.
- **Notes:** _e.g. "colorblind-safe per user request — Wong 2011 palette"._

## Typography

- **Family:** DejaVu Sans (the scaffold default; bake matplotlib-available alternatives only).
- **Title:** 12 pt regular.
- **Axis labels:** 11 pt.
- **Tick labels:** 9 pt.
- **Annotations:** 9 pt italic.

## Figure dimensions

- **Default size:** 7 × 5 in (single panel), 10 × 4 in (small multiples).
- **DPI:** 300 (print).
- **Aspect-ratio rule of thumb:** _not specified._

## Plot type preferences

- **Prefer:** _not specified — let the user's request drive the chart kind._
- **Avoid:** _not specified — but if the user is clearly in research-paper mode, default away from 3D plots, dual y-axes, and pie charts (Rougier et al. 2014, Rule 6)._

## Axis & grid

- **Spines:** top + right off, bottom + left on (1 pt) — `set_research_theme()` default.
- **Gridlines:** off — `set_research_theme()` uses `style="ticks"` not `whitegrid`. Override here if the project wants gridlines.
- **Tick direction:** out, length 3.

## Legend & annotation

- **Legend:** top-right inside frame when ≤ 4 entries; below figure otherwise. Frame off (`legend.frameon = False`).
- **Direct annotations** preferred over legends when the chart has ≤ 3 series.

## Marker / line

- **Marker rotation:** o, s, ^, D.
- **Default marker size:** 24 (scatter); **default line width:** 1.5.

## User overrides (project-wide)

_(filled in by style_infer when the user states a project-wide preference like "always use colorblind-safe palette" or "log y by default for any concentration plot". Format: `- <preference> — applied <date>`.)_

## Per-plot / per-page overrides

_Specific styling decisions that apply only to one named recipe (PROJECT_RECIPES key) or one streamlit page. Newly-generated plots/pages should respect these; existing ones should be re-rendered when the corresponding entry is added or changed._

_(empty — added per-plot when the user asks for a tweak that shouldn't propagate everywhere)_

## Revisions

_Append a line whenever the guide changes. Format: `YYYY-MM-DD — what changed — why`._

- _(no revisions yet — placeholder template)_
