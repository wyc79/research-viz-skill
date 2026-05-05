# How to use this folder

A short human's guide to running everything in this BraTS workspace yourself.

## What this folder is

A project-specific recipe for visualising **one BraTS2020 subject** as three 3-D isosurface snapshots — front, top, medial — with the brain rendered grey and semi-transparent, the tumor rendered red and opaque inside it. Style follows Khan et al. 2018 ([doi:10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0)) with the colour scheme inverted (paper used red brain + blue tumor).

The python files have been trimmed to exactly that scope:

- `scripts/parser.py` reconstructs the chosen subject's 3-D NIfTI from the per-slice .h5 files in `data/`, plus a brain envelope and a tumor mask **clipped to the brain envelope** so no tumor voxel can render outside the cranium.
- `scripts/render_views.py` extracts brain + tumor isosurfaces with marching cubes and renders three 3-D views in matplotlib.

Running the wrappers below reproduces the exact same artifacts every time.

`data/` and `intermediate_data/` are both **gitignored** (the slice files are multi-GB; the reconstructed NIfTIs are also large).

## 1. Reconstruct the chosen BraTS volume

```bash
bash visualizations/parse_input.sh
```

Stacks 155 axial slices for `PROJECT_VOLUME_ID` (default `1`, set in `scripts/parser.py`) into NIfTIs:

```
intermediate_data/
├── volume_001__t1.nii.gz
├── volume_001__t1ce.nii.gz
├── volume_001__t2.nii.gz
├── volume_001__flair.nii.gz
├── volume_001__seg.nii.gz           BraTS labels: 0=bg, 1=NCR/NET, 2=ED, 4=ET
├── volume_001__brain_mask.nii.gz    binary envelope (hole-filled, largest CC)
├── volume_001__tumor_mask.nii.gz    binary tumor union, clipped to brain envelope
└── parsed_index.json                manifest with canonical_brain_mask / canonical_overlay
```

### Pick a different subject

```bash
bash visualizations/parse_input.sh --volume-id 42
```

Or edit `PROJECT_VOLUME_ID` at the top of `scripts/parser.py` and rerun with no flags.

## 2. Render the three 3-D views

```bash
bash visualizations/render_views.sh --list-recipes  # show registered views
bash visualizations/render_views.sh --all           # regenerate every view
bash visualizations/render_views.sh --recipe 3d-front
```

Each view writes to `plots/<slug>/`:

- `figure.png` (200 dpi) — the snapshot you'd paste into a paper.
- `figure.pdf` — vector copy.
- `spec.json` — recipe (elev/azim, alphas, mesh triangle counts).

The three slugs:

| slug | matplotlib `(elev, azim)` | view |
|---|---|---|
| `3d-front` | `(15, -80)` | anterior, looking at the front of the brain |
| `3d-top` | `(70, -85)` | superior, looking down through the top |
| `3d-medial` | `(15, 10)` | from the side |

The angles are deliberately off-cardinal so all three cube faces and tick axes are visible — pure cardinal angles (e.g. `(0, -90)`) collapse one axis into a degenerate edge and stack matplotlib's tick labels. See `info/project_specific_knowledge.md` for the full rationale.

**Each render takes ~30 seconds** — the brain mesh has ~250k triangles after marching cubes; matplotlib's 3-D backend isn't optimised for that scale. `--all` therefore takes ~90 s total.

## 3. Want a different rendering?

Read `info/project_specific_knowledge.md` first — it documents:

- the BraTS slice format + the z-score gotcha (the brain mask uses **any-modality-positive**, not "any-modality-nonzero", because the Kaggle release z-scores on the whole volume),
- BraTS label codes (note: ET is label **4**, not 3),
- why this project uses marching cubes + matplotlib 3-D instead of nilearn / PySurfer,
- the tumor-stays-inside-brain clipping rule,
- style choices: brain alpha, tumor colour, off-cardinal view angles, Lambertian shading,
- how to retarget to a different BraTS subject and how to switch to triplanar 2-D / cortical-surface alternatives.

To add a new view: append to `PROJECT_RECIPES` in `scripts/render_views.py` with new `(elev, azim)` values. To change the colours / alphas: edit `BRAIN_COLOR` / `TUMOR_COLOR` / `BRAIN_ALPHA` / `TUMOR_ALPHA` at the top of the same file.

## File map

```
example2_brain/
├── README.md                                    ← top-level guide + the prompt that built this
├── data/                                        ← BraTS slice files (gitignored, multi-GB)
└── visualizations/
    ├── parse_input.sh                           wrapper around scripts/parser.py
    ├── render_views.sh                          wrapper around scripts/render_views.py
    ├── scripts/
    │   ├── parser.py                            single-subject BraTS slice → NIfTI
    │   └── render_views.py                      marching cubes + mpl 3-D, three views
    ├── intermediate_data/                       (gitignored, large reconstructed NIfTIs)
    │   ├── parsed_index.json
    │   ├── volume_<id>__t1.nii.gz
    │   ├── volume_<id>__t1ce.nii.gz
    │   ├── volume_<id>__t2.nii.gz
    │   ├── volume_<id>__flair.nii.gz
    │   ├── volume_<id>__seg.nii.gz
    │   ├── volume_<id>__brain_mask.nii.gz
    │   └── volume_<id>__tumor_mask.nii.gz
    ├── plots/<slug>/{figure.png, figure.pdf, spec.json}
    └── info/
        ├── context.md                           continuation handoff for future sessions
        ├── how_to_use.md                        this file
        └── project_specific_knowledge.md        BraTS + marching-cubes domain notes
```
