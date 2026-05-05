# Context — research-viz workspace (BraTS2020, 3-D isosurfaces)

> **For future agents:** read every `.md` in `info/` first — this file,
> `style_guide.md`, `project_specific_knowledge.md`, and `how_to_use.md`.
> Then `ls scripts/`, `ls plots/`, `ls intermediate_data/` to reconcile
> drift before acting.

## Style guide

🟢 **Style guide active.** This project's three 3-D views follow the choices in [`info/style_guide.md`](style_guide.md): brain `(0.62, 0.62, 0.62)` grey at α=0.18, tumor `(0.85, 0.10, 0.10)` red at α=1.0, off-cardinal view angles (`elev=15/70`, `azim=-80/-85/10`) so all three cube faces stay visible, marching-cubes `step_size=2` for brain / `step_size=1` for tumor. Mirrored into `BRAIN_COLOR` / `TUMOR_COLOR` / `BRAIN_ALPHA` / `TUMOR_ALPHA` and `PROJECT_RECIPES` at the top of `scripts/render_views.py`. The guide is a *guide*, not a strict standard — drive forward, don't audit old code.

## Project at a glance

- **Dataset:** [`awsaf49/brats2020-training-data`](https://www.kaggle.com/datasets/awsaf49/brats2020-training-data) — BraTS2020 training set, sliced into per-axial-slice HDF5 files. The `data/` folder is in `.gitignore` because the full dataset is multi-GB; only the user has it locally.
- **Scope:** one tumor instance only (volume 1 of 369), three 3-D snapshots — front, top, medial.
- **Visual reference:** Khan et al. 2018, *Multimodal brain tumor classification using deep learning and robust feature selection*, Multimedia Tools and Applications 78: 16267–16289 ([doi:10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0)). Paper renders 3-D cubes with red brain + blue tumor; we invert (grey brain + red tumor) per the user's request.
- **Python env:** ambient interpreter — h5py 3.16, nibabel 5.4, scipy (used for the brain-mask hole-fill + connected-components), scikit-image 0.25 (`measure.marching_cubes`), matplotlib 3.10 (`mpl_toolkits.mplot3d`). No venv.
- **Subskills used:** `parser` (slice-stack → 3-D NIfTI + brain envelope + clipped tumor mask) and `domain_viz` (paper-style 3-D isosurface render).

## What lives where

- `scripts/parser.py` — reads BraTS .h5 slices for one volume; writes 4 modality NIfTIs + multi-class seg + brain envelope + binary tumor mask **clipped to brain envelope** into `intermediate_data/`. Trimmed to single-subject mode; `PROJECT_VOLUME_ID` controls which subject.
- `scripts/render_views.py` — extracts brain + tumor isosurfaces with `skimage.measure.marching_cubes` and renders three views (`PROJECT_RECIPES`: `3d-front`, `3d-top`, `3d-medial`) via `mpl_toolkits.mplot3d.Poly3DCollection`. Brain grey/semi-transparent, tumor red/opaque.
- `intermediate_data/parsed_index.json` — manifest. Records `canonical_anat` (T1), `canonical_brain_mask`, `canonical_overlay` (clipped tumor), `canonical_segmentation`.
- `intermediate_data/volume_001__{t1,t1ce,t2,flair}.nii.gz` — per-modality 3-D volumes, 240×240×155 float32, ~1 mm isotropic.
- `intermediate_data/volume_001__seg.nii.gz` — multi-class segmentation, BraTS label codes (0/1/2/4).
- `intermediate_data/volume_001__brain_mask.nii.gz` — binary brain envelope (any modality > 0, holes filled, largest connected component).
- `intermediate_data/volume_001__tumor_mask.nii.gz` — binary tumor union, **clipped to the brain envelope** so no tumor voxel sits outside the cranium in the figures.
- `plots/<slug>/` — one folder per recipe; each has `figure.png` (200 dpi), `figure.pdf`, and `spec.json`.
- `info/project_specific_knowledge.md` — domain-specific knowledge: BraTS data shape & gotchas, label codes, why marching-cubes + matplotlib over nilearn or PySurfer, style choices.

## Dataset notes

- The Kaggle release ships 2-D axial slices in HDF5 (`volume_<id>_slice_<z>.h5`), **not** the original 4-modality NIfTI volumes. Each h5 has `image: (240,240,4)` (T1, T1ce, T2, FLAIR — channel order fixed) and `mask: (240,240,3)` (NCR/NET, ED, ET — one-hot).
- 155 axial slices per volume, 369 volumes total.
- **Z-score normalisation is on the full volume**, not brain-only — background sits at ~−0.6 instead of exactly 0. Brain mask via `any modality > 0` (not `!= 0`); see `project_specific_knowledge.md` for details.
- Volume 1: 1,343,487 brain voxels; 211,979 tumor voxels (15,443 NCR/NET + 168,794 ED + 27,742 ET) all sitting inside the brain envelope (zero clipped). Substantial mass in the left hemisphere — clearly visible in all three 3-D views.

## Activity log

- **2026-05-05** — scaffolded — `python research-viz/scripts/scaffold.py example2_brain --data-dir example2_brain/data`. Trimmed unused scaffolding immediately: removed `streamlit/`, `significance/`, `helpers/`, `interactive_page.sh`. Renamed `generate_plot.sh` → `render_views.sh`, `plot_gen.py` → `render_views.py`.
- **2026-05-05** — `parser` — reconstruct volume 1's 3-D NIfTI from its 155 .h5 slices. Files: `scripts/parser.py` (BraTS-slice mode, `PROJECT_VOLUME_ID = 1`), `intermediate_data/volume_001__{t1,t1ce,t2,flair,seg,brain_mask,tumor_mask}.nii.gz`, `parsed_index.json`. Notes: brain-mask logic is **`any modality > 0`** (not `!= 0`) because the Kaggle release z-scores on the whole volume. Hole-fill + largest-CC cleanup. Tumor mask clipped against brain envelope at parse time so the renderer can never show a tumor poking out.
- **2026-05-05** — `domain_viz` — three paper-style 3-D isosurface views via marching cubes + matplotlib 3-D. Files: `scripts/render_views.py` (`PROJECT_RECIPES`: `3d-front`/`-top`/`-medial`), `plots/<slug>/{figure.png,figure.pdf,spec.json}` × 3. Notes: nilearn doesn't render volumetric isosurfaces — used `skimage.measure.marching_cubes` for mesh extraction (brain `step_size=2`, ~250k triangles, ~30s per view; tumor `step_size=1` for full detail). Off-cardinal view angles (e.g. `elev=15, azim=-80` for front) so all three cube faces are visible per the paper's iso-cube look — pure cardinal angles collapse one axis and stack tick labels. Brain alpha 0.18, tumor alpha 1.0, Lambertian shading via `LightSource`.
- **2026-05-05** — `domain_viz` (knowledge persistence) — wrote `info/project_specific_knowledge.md` with the z-score gotcha, label codes, the marching-cubes-vs-nilearn-vs-PySurfer rationale, the tumor-stays-inside-brain rule, and how to retarget / restyle.

## Trim notes

This project doesn't use plot_gen / interactive / significance_test / style_infer, so the corresponding scaffolding (`generate_plot.sh`, `interactive_page.sh`, `streamlit/`, `significance/`, `helpers/utils.py`) was deleted per the SKILL.md trim rule. The wrapper this project ships is `render_views.sh`, replacing `generate_plot.sh`.
