# Style guide — Palmer Penguins example

This guide documents the visual decisions baked into `scripts/plot_gen.py` and the streamlit pages. Future agents touching this workspace should read this **before** producing or modifying any figure or page.

## Project-wide rules

- **No grids on any figure.** `set_research_theme()` in `scripts/helpers/utils.py` sets `style="ticks"` (not `whitegrid`) and explicitly `axes.grid = False`. Don't reintroduce gridlines per-plot — if a chart genuinely needs reference lines, prefer thin neutral `ax.axvline` / `ax.axhline` calls over a full grid.
- **Open-frame look.** Top and right axis spines are off (`axes.spines.top = False`, `axes.spines.right = False`); legends are frameless (`legend.frameon = False`).
- **Two coordinated palettes.** The project ships exactly two palettes — pick the one that matches the figure's intent.

### Palette A — Colorblind-safe categorical (species comparisons)

Used for any figure that compares the three species (Adelie / Chinstrap / Gentoo). Hex codes are pinned in `PROJECT_SPECIES_PALETTE` at the top of `plot_gen.py` so the same species always plots in the same colour across the static plots, the streamlit native page, the altair page, and the gallery viewer.

| Species | Hex | Note |
|---|---|---|
| Adelie | `#0173B2` | seaborn `colorblind` blue |
| Chinstrap | `#DE8F05` | seaborn `colorblind` orange |
| Gentoo | `#029E73` | seaborn `colorblind` green |

Source: seaborn's `colorblind` palette (Wong, 2011).

### Palette B — Monochrome single-hue (single-distribution / sequential)

Used for figures with no categorical hue (single histograms, the correlation heatmap, the per-island boxplot where the x-axis already encodes the category). Defined as `PROJECT_MONOCHROME` in `plot_gen.py`.

| Role | Value | Used in |
|---|---|---|
| `fill` | `#3B7BB5` | histogram fill, boxplot body |
| `edge` | `#1F4E79` | histogram bar edges, box outlines |
| `cmap` | `Blues` | correlation heatmap (sequential, |r|-encoded) |

The mid-blue `fill` deliberately matches the Adelie species blue's saturation so the two palettes feel related when figures from both sets sit on the same page.

## Plot kinds shipped

The seven recipes in `PROJECT_RECIPES`:

- `bill_length-vs-bill_depth-by-species` — scatter, palette A.
- `body_mass-violin-per-species` — violin, palette A.
- `flipper_length-box-per-island` — box, palette B.
- `body_mass-histogram-monochrome` — histogram, palette B.
- `flipper_length-histogram-monochrome` — histogram, palette B.
- `correlation-heatmap-monochrome` — heatmap, palette B.
- `body_mass-violin-per-species-with-ttest` — violin + statannotations bracket, palette A; reads `significance/body_mass_g-adelie-vs-gentoo-ttest.json`.

## Per-plot / per-page overrides

_(none currently — the seven recipes follow the project-wide rules above.)_

If you add a recipe that needs to deviate (e.g. a density plot whose `kind` calls for a divergent cmap), add an entry under this heading naming the slug or page path and the override.

## Heatmap convention

The correlation heatmap uses the `Blues` sequential cmap on `|r|` while annotating each cell with the **signed** r value. This keeps the figure monochrome (no hue boundary at zero), but the user still sees the sign of every correlation in-cell. If a future heatmap needs a divergent palette (e.g. for a plot where the sign matters more than the magnitude), document the override here.

## Streamlit consistency

The two interactive pages (`1_penguins_overview.py`, `2_bill_morphology_altair.py`) import `PROJECT_SPECIES_PALETTE` directly from `plot_gen.py` — keeping a single source of truth for the species colours. The gallery page (`3_prerendered_gallery.py`) just shows the rendered PNGs, so it inherits the palette automatically.
