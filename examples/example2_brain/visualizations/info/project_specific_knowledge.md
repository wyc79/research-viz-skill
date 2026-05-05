# Project-specific knowledge — BraTS2020, paper-style 3-D isosurfaces

> **For future agents:** read this before any parser / render_views work.

## Dataset shape — the Kaggle "BraTS2020-training-data" slice format

The Kaggle release [`awsaf49/brats2020-training-data`](https://www.kaggle.com/datasets/awsaf49/brats2020-training-data)
ships the BraTS2020 training set as **2-D axial slices in HDF5**, not as the
original 4-modality NIfTI volumes the BraTS organisers distribute.

Each `volume_<id>_slice_<z>.h5` file (where `id ∈ 1..369`, `z ∈ 0..154`)
contains exactly two datasets:

| key | shape | dtype | contents |
|---|---|---|---|
| `image` | `(240, 240, 4)` | `float64` (z-scored) | T1, T1ce, T2, FLAIR — channel order is fixed |
| `mask`  | `(240, 240, 3)` | `uint8` | NCR/NET, ED, ET — one-hot |

155 axial slices per volume, 369 volumes total. `meta_data.csv` lists every
slice with a `target` column (1 if any tumor is present in that slice).

## **Gotcha: the z-score is on the *whole volume***, not just the brain

The original BraTS NIfTIs are skull-stripped — background is exactly `0`
in every modality. The Kaggle release re-normalises with **z-score across
the entire 240×240×155 volume** (not brain-only). Result: the originally-
zero background gets shifted to small **negative** values (~`-0.6`), so a
naive `voxel != 0` brain mask matches every voxel in the cube.

The right rule: **`any modality > 0`** (true brain voxels are above the
volume mean and stay positive after z-scoring; background sits below the
mean and goes negative). `parser.py::build_brain_mask` does this, then
fills internal holes (ventricles dip below the mean in T1) and keeps the
single largest connected component to drop corner-noise islands.
On volume 1 this yields ~1.34 M brain voxels — a believable adult brain.

If you skip the hole-fill step you get a swiss-cheese brain with the
ventricles punched out; if you skip the largest-CC step you get a few
isolated noise blobs at the cube corners surviving as separate meshes.

## BraTS label codes (note the gap)

The seg NIfTI uses **the standard BraTS evaluation codes**:

| code | name | meaning |
|---|---|---|
| 0 | background | non-brain or healthy tissue |
| 1 | NCR/NET | necrotic core + non-enhancing tumor |
| 2 | ED | peritumoral edema |
| **4** | ET | enhancing tumor — note: 4, not 3 |

The 3-skip is a BraTS convention since 2017, kept for backward
compatibility with every existing piece of BraTS tooling. Don't "fix" it.
See Bakas et al. 2017, *Advancing the cancer genome atlas glioma MRI
collections with expert segmentation labels and radiomic features*,
Sci. Data 4: 170117.

## Tumor-stays-inside-brain rule

The renderer should never show a tumor surface poking out past the brain
envelope — at best it looks wrong, at worst it implies the tumor extends
outside the cranium. Real BraTS segmentations occasionally include a few
edge voxels labelled as tumor that sit just outside the skull-strip
(annotation noise at the edema rim).

We enforce the rule **once, at parse time**, in `parser.py`:

```python
tumor_clipped = (tumor_raw & brain_mask).astype(np.uint8)
```

The renderer also re-asserts it as a guard before extracting meshes, so
even if a future parser forgets the clip, no out-of-brain tumor voxels
make it onto the figure.

## Reconstructed NIfTI naming

```
intermediate_data/
├── volume_001__t1.nii.gz       240×240×155 float32 (z-scored)
├── volume_001__t1ce.nii.gz     240×240×155 float32
├── volume_001__t2.nii.gz       240×240×155 float32
├── volume_001__flair.nii.gz    240×240×155 float32
├── volume_001__seg.nii.gz      240×240×155 uint8 (labels: 0/1/2/4)
├── volume_001__brain_mask.nii.gz   240×240×155 uint8 (envelope, hole-filled, largest CC)
└── volume_001__tumor_mask.nii.gz   240×240×155 uint8 (binary union, clipped to brain)
```

Affine is **synthesised** centred on the volume; the Kaggle slice files
don't ship the original SRI24-registered affine. Fine for visualisation,
not for atlas lookup.

## Why marching cubes + matplotlib 3-D, not nilearn / PySurfer

The user's reference was Khan et al. 2018, *Multimodal brain tumor
classification using deep learning and robust feature selection*,
Multimedia Tools and Applications 78: 16267–16289
([doi:10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0)).
That paper renders three 3-D cubes per case showing the brain envelope
and the tumor as separate marching-cubes isosurfaces, with visible cube
ticks. That's the look this project ships.

| Tool | Why it doesn't fit here |
|---|---|
| `nilearn.plot_glass_brain` | 2-D MIP of a stylised template — gives the silhouette but not the actual subject volume. Wrong question. |
| `nilearn.plot_anat` | 2-D triplanar slices — also wrong question (no 3-D-ness). |
| PySurfer / Mayavi | Cortical surface, needs FreeSurfer fsaverage and VTK + display. BraTS tumors are deep white matter, not cortical, and the workflow needs to run headless. |

Marching cubes (`skimage.measure.marching_cubes`) gives us the brain
isosurface and the tumor isosurface from the actual subject volume.
matplotlib's `mpl_toolkits.mplot3d.Poly3DCollection` renders both meshes
in one 3-D axes — works headless, no extra display dependencies.

`nibabel` is used for I/O (ecosystem-consistent with nilearn). If you ever
want to try the cortical-projection alternative anyway, the path is:
`nilearn.surface.vol_to_surf(tumor_mask, fsaverage5)` → load with
`pysurfer.Brain.add_overlay`. Document the trade-off.

## Style choices in the renderer

Inverted from the paper (red brain + blue tumor → grey brain + red tumor)
because the user wanted that direction. Other choices:

- **Brain alpha = 0.18** so the tumor inside reads clearly through the
  envelope. Lower (~0.1) makes the brain ghostly; higher (~0.3) starts to
  hide the tumor.
- **Tumor alpha = 1.0**, `step_size=1` on marching cubes (full mesh
  resolution) — the tumor is small and we want every bump.
- **Brain `step_size=2`** — the envelope mesh has ~250 k triangles at
  step=2 vs ~1 M at step=1; matplotlib renders step=2 in ~30 s vs
  several minutes for step=1, with no perceptual difference at the figure
  size we ship.
- **View angles are off-cardinal** (e.g. front = `elev=15, azim=-80`
  instead of `0/-90`) so all three cube faces and all three axes are
  visible, matching the paper's iso-cube look. Pure cardinal angles
  collapse one axis into a degenerate edge and stack matplotlib's tick
  labels on top of each other.
- **Lambertian shading** via `LightSource` so the surfaces read as 3-D
  under matplotlib's flat collection rendering (`set_zsort("max")` to
  fight depth-sort artefacts on overlapping alpha facets).

## How to retarget to a different BraTS subject

```bash
bash visualizations/parse_input.sh --volume-id 42
bash visualizations/render_views.sh --all
```

Or edit `PROJECT_VOLUME_ID` at the top of `scripts/parser.py` (default
`1`). Volume 1 has a 212k-voxel tumor across 83 of 155 slices — large
enough to be visible from all three views without dominating the brain.
For a different subject, scan `data/meta_data.csv` for rows where
`target == 1` and pick one whose tumor extent looks right.

## How to render in a different style

The renderer is one short file (`scripts/render_views.py`) with one
`render_one()` function. Common edits:

- **Different colours**: change `BRAIN_COLOR` / `TUMOR_COLOR` /
  `BRAIN_ALPHA` / `TUMOR_ALPHA` at the top.
- **Different views**: edit `PROJECT_RECIPES` — add or replace `(elev, azim)`
  tuples; matplotlib 3-D camera convention.
- **Triplanar 2-D slices instead of 3-D**: swap to
  `nilearn.plotting.plot_anat(t1_path, display_mode='ortho',
  overlay=tumor_mask)`. Faster and no marching cubes, but you lose the
  3-D feel.
- **Cortical-surface views (PySurfer-style)**: project the tumor mask to
  fsaverage with `nilearn.surface.vol_to_surf`, load with
  `pysurfer.Brain`. Needs FreeSurfer + VTK + display.
