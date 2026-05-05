# Style guide

> **For agents:** this project's three 3-D views must follow the choices below. Mirror them into `BRAIN_COLOR` / `TUMOR_COLOR` / `BRAIN_ALPHA` / `TUMOR_ALPHA` and `PROJECT_RECIPES` at the top of `scripts/render_views.py`. Re-render via `bash render_views.sh --all` (~90 s) when the guide changes.

## Status

🟢 **Active** — populated from the user's verbal preferences (grey brain, red tumor, three views) and the visual reference of Khan et al. 2018 (see "References used" below).

## References used

- _(user notes)_ — "create 3 separate 3D visualization (top, front, medial) with similar style as the provided image, except that normal brain being grey and tumor being red". Inverts the paper's red brain + blue tumor scheme.
- _(user notes)_ — "tumor should not exceed the range of the actual brain you plot" → tumor mask is clipped to the brain envelope at parse time (see `info/project_specific_knowledge.md` for the implementation).
- _(reference, no file in `style_refs/` because it's behind a paywall)_ Khan, M.A. et al. (2019), *Multimodal brain tumor classification using deep learning and robust feature selection*, MTA 78: 16267–16289 ([doi:10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0)). Took: three-cube layout, marching-cubes isosurfaces, light-grey panes with visible tick axes on three cube faces.

## Color palette

- **Brain:** `(0.62, 0.62, 0.62)` — neutral mid-grey.
- **Tumor:** `(0.85, 0.10, 0.10)` — crimson red (slightly desaturated from pure red so the Lambertian shading reads cleanly).
- **Brain alpha:** `0.18` — low enough that the tumor inside is clearly visible; tested values 0.10 (too ghostly), 0.30 (starts to hide tumor).
- **Tumor alpha:** `1.0` — fully opaque so the tumor reads as a solid mass.
- **Cube panes:** `(0.94, 0.94, 0.94)` light grey; pane edges `(0.7, 0.7, 0.7)` mid-grey. Matches the paper's iso-cube aesthetic.

## Typography

- **Family:** matplotlib default (DejaVu Sans).
- **Title:** 11 pt, `pad=8`.
- **Tick labels:** 8 pt, `pad=1`.
- **No axis labels** — the cube ticks convey scale on their own; in-axes labels would clutter the small figure.

## Figure dimensions

- **Default size:** 6 × 5.5 in.
- **DPI:** 200 (the marching-cubes meshes have ~250 k triangles and matplotlib 3-D renders are slow to read at higher dpi without diminishing returns).
- **Box aspect:** `(1, 1, 0.95)` — roughly anatomical proportions for the 240×240×155 BraTS volume.

## Plot type preferences

- **Use:** marching-cubes isosurfaces in matplotlib 3-D (`mpl_toolkits.mplot3d.Poly3DCollection`).
- **Avoid:** glass-brain MIP (loses 3-D-ness), 2-D triplanar slices (different question), cortical-surface projection (BraTS tumors are deep white matter, not cortical). Rationale in `info/project_specific_knowledge.md`.

## Axis & grid

- **All three cube faces visible** — that's the look. Achieved by tilting the camera off-cardinal (e.g. front = `elev=15, azim=-80` instead of `0, -90`); pure cardinal angles collapse one axis into a degenerate edge and stack the tick labels on top of each other.
- **Tick marks visible** on all three axes.
- **Pane backgrounds** light grey; pane edges mid-grey. No internal gridlines beyond what the panes show.

## Legend & annotation

- **No legend** — the colour-coding (grey = brain, red = tumor) is unambiguous in this two-class scene.
- **Title** above each cube describes the view.

## Marker / line

- **Mesh edges:** none (`edgecolors="none"`, `linewidths=0.0`) so the surfaces read as smooth volumes rather than wireframes.
- **Lambertian shading** via `matplotlib.colors.LightSource(azdeg=315, altdeg=45)` so the surfaces read as 3-D under matplotlib's flat-collection rendering.

## User overrides (project-wide)

- **Tumor must stay inside brain.** Enforced at parse time (`tumor_clipped = tumor_raw & brain_mask`) and re-asserted in the renderer as a guard. On volume 1 zero voxels needed clipping, but the rule is in place for other subjects where edema-rim noise might put a few tumor voxels outside the skull-strip.
- **Color scheme inverted from the paper** — paper used red brain + blue tumor; we use grey brain + red tumor per the user's instruction.

## Per-plot / per-page overrides

- **`3d-front`** — `(elev=15, azim=-80)`. Looking at the anterior face with slight perspective so all three cube faces show.
- **`3d-top`** — `(elev=70, azim=-85)`. Steeper than the others (looking down, but not straight down — `elev=90` would flatten the figure into 2-D).
- **`3d-medial`** — `(elev=15, azim=10)`. Sagittal/lateral view with slight perspective.

## Mesh resolution

- **Brain `step_size=2`** in `skimage.measure.marching_cubes` — ~250 k triangles, ~30 s render per view; step=1 quadruples the triangle count and the render time without perceptual gain at 6×5.5 in / 200 dpi.
- **Tumor `step_size=1`** — full mesh resolution. The tumor is small (~212 k voxels) so the triangle count stays manageable, and we want every bump.

## Revisions

- **2026-05-05** — initial guide built from the user's verbal preferences + Khan et al. 2018 visual reference. Inverted colour scheme, off-cardinal view angles, alphas tuned to keep the tumor visible inside the brain.
