# Example 2: BraTS2020 — paper-style 3-D tumor visualization

A worked example of the **`domain_viz`** subskill in `research-viz`: take one subject from the BraTS2020 brain-tumor MRI dataset, reconstruct its 3-D volume, and render front / top / medial **3-D isosurface** snapshots — brain (grey, semi-transparent) with the tumor (red, opaque) inside it.

This complements `example1_penguin/` (which exercises the standard tabular flow). Where example 1 is small + clean + tabular, this one is multi-GB + binary-format + needs a domain-specific rendering pipeline (`scikit-image` marching cubes + `matplotlib`'s 3-D backend, with `nibabel` / nilearn ecosystem for I/O).

## Visual reference

The three rendered views match the iso-cube look from:

> Khan, M.A., Lali, I.U., Rehman, A. et al. *Multimodal brain tumor classification using deep learning and robust feature selection: A machine learning application for radiologists*. **Multimedia Tools and Applications** 78, 16267–16289 (2019). [doi:10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0).

That paper's Fig. 4 shows three 3-D cubes per case (tumor only, brain only, brain + tumor overlay) with visible axis ticks. We render the **brain + tumor overlay** version of each of the three cardinal views; the colour scheme is **inverted** (paper used red brain + blue tumor; we use grey brain + red tumor) so the tumor pops more under a low-alpha envelope.

## What you'll see

After running the steps below, `visualizations/plots/` contains three snapshots of BraTS subject 1:

| slug | matplotlib `(elev, azim)` | view |
|---|---|---|
| `3d-front` | `(15, -80)` | anterior, looking at the front of the brain |
| `3d-top` | `(70, -85)` | superior, looking down through the top |
| `3d-medial` | `(15, 10)` | medial / sagittal, from the side |

Tumor coverage on subject 1: **211,979 voxels across 83 of 155 axial slices**, all confined inside a 1,343,487-voxel brain envelope. The tumor mask is **clipped to the brain envelope at parse time** so no tumor voxel can ever render outside the cranium.

## Getting the data

The dataset is the Kaggle release [`awsaf49/brats2020-training-data`](https://www.kaggle.com/datasets/awsaf49/brats2020-training-data) — the BraTS2020 training set re-shipped as **per-axial-slice HDF5 files**, ~7 GB total. The repo's `.gitignore` excludes `example2_brain/data/` because of the size; you need to fetch it yourself before running anything:

```bash
# 1. Install the Kaggle CLI and put your API token at ~/.kaggle/kaggle.json
#    (https://github.com/Kaggle/kaggle-api#api-credentials)
pip install --user kaggle

# 2. Download + unzip into example2_brain/data/
cd example2_brain
mkdir -p data
kaggle datasets download -d awsaf49/brats2020-training-data -p data --unzip

# data/ should now contain:
#   meta_data.csv
#   volume_1_slice_0.h5 ... volume_369_slice_154.h5   (~57k files)
```

If you already have the original BraTS2020 NIfTIs from Synapse / IPP, skip Kaggle entirely — adapt `scripts/parser.py` to `nib.load(...)` the four `*_t1.nii.gz` / `*_t1ce.nii.gz` / `*_t2.nii.gz` / `*_flair.nii.gz` / `*_seg.nii.gz` files for one subject and write them out under the same `volume_NNN__<modality>.nii.gz` naming. The renderer doesn't care where the NIfTIs came from, only that `parsed_index.json` points at them.

### Python dependencies

```bash
pip install h5py nibabel nilearn scikit-image scipy matplotlib
```

`scikit-image` for `measure.marching_cubes`, `scipy` for the brain-mask hole-fill / connected-components cleanup, `matplotlib` 3-D for the rendering. No FreeSurfer, no Mayavi, no VTK — see `visualizations/info/project_specific_knowledge.md` for why those weren't a fit.

## The example prompt

The prompt that built the workspace you're looking at. Drop it into a fresh agent session — with `data/` populated as above and the working directory set to `example2_brain/` — to reproduce the build:

> Set up a `research-viz` workspace for the BraTS2020 brain-tumor MRI data in `data/`. The dataset is the Kaggle slice format — every file is `data/volume_<id>_slice_<z>.h5` with two HDF5 datasets: `image` of shape `(240, 240, 4)` (the four modalities T1, T1ce, T2, FLAIR — channel order fixed) and `mask` of shape `(240, 240, 3)` (three tumor sub-regions one-hot: NCR/NET, ED, ET). 155 axial slices per volume, 369 volumes total. The data folder is in `.gitignore` and should be treated as read-only.
>
> **Scope.** I want to visualise **one tumor instance only** — pick volume 1 by default; expose `PROJECT_VOLUME_ID` so it can be retargeted later. No streamlit, no statistical tests, no plot_gen for charts — this is a pure `domain_viz` workflow.
>
> **Visual reference.** Match the look of Khan et al. 2018, *Multimodal brain tumor classification using deep learning and robust feature selection*, Multimedia Tools and Applications ([doi:10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0)) — three 3-D cubes per view, with marching-cubes isosurfaces of the brain envelope and the tumor drawn together in one matplotlib 3-D axes, visible cube ticks on three faces. Invert the colour scheme: **brain = grey, semi-transparent; tumor = red, opaque.**
>
> **Parser.** Stack the chosen volume's 155 axial slices into 3-D NIfTI volumes, one per modality (T1 / T1ce / T2 / FLAIR), plus a multi-class segmentation NIfTI, plus a binary brain-envelope mask, plus a binary tumor mask **clipped against the brain envelope**. Naming: `intermediate_data/volume_NNN__{t1,t1ce,t2,flair,seg,brain_mask,tumor_mask}.nii.gz` (per the SKILL.md `<dataset>__<stage>.<ext>` convention). Use BraTS's standard label codes for the segmentation: `0=background, 1=NCR/NET, 2=ED, 4=ET` (note the 3-skip — that's the BraTS evaluation convention, kept for compatibility).
>
> **Brain-mask gotcha.** The Kaggle release z-scores on the **whole volume**, not just the brain, so the originally-zero background sits at small negative values (~−0.6) — `voxel != 0` matches every voxel and gives a useless "whole cube" mask. Use **any-modality-positive** (`np.any(img > 0, axis=-1)`) instead, then fill internal holes (ventricles in T1 dip below the mean and would otherwise be lost) and keep the single largest connected component to drop corner-noise islands. Document this clearly in `info/project_specific_knowledge.md` so the next agent doesn't fall in the same hole.
>
> **Tumor-stays-inside-brain rule.** Real BraTS segmentations occasionally include a few voxels labelled as tumor that fall outside the skull-strip (annotation noise at the edema rim). Clip the tumor mask against the brain envelope at parse time, so the renderer can never show a tumor poking out of the cranium. Re-assert the rule in the renderer as a guard.
>
> **Affine.** The Kaggle slice format doesn't ship the original SRI24-registered affine, so synthesise a centred 1 mm isotropic affine in the parser; document this honestly in `info/project_specific_knowledge.md`. Write a `parsed_index.json` that names the canonical anat (T1), the canonical brain mask, and the canonical tumor overlay.
>
> **Renderer.** Extract isosurfaces with `skimage.measure.marching_cubes` (brain at `step_size=2` for ~250k triangles and a sensible render time; tumor at `step_size=1` for full detail since it's smaller). Render both meshes in one `mpl_toolkits.mplot3d` axes via `Poly3DCollection`. Apply Lambertian shading via `matplotlib.colors.LightSource` so the surfaces read as 3-D under flat-collection rendering. Brain alpha = 0.18, tumor alpha = 1.0; brain colour neutral mid-grey `(0.62, 0.62, 0.62)`, tumor colour crimson red `(0.85, 0.10, 0.10)`. `set_zsort("max")` on both `Poly3DCollection`s to fight matplotlib's depth-sort artefacts on overlapping alpha facets.
>
> **Three named views (the project recipes), each its own folder under `plots/<slug>/`:**
>
> 1. `3d-front` — anterior view, `elev=15, azim=-80`
> 2. `3d-top` — superior view, `elev=70, azim=-85`
> 3. `3d-medial` — sagittal view, `elev=15, azim=10`
>
> Use **off-cardinal angles** so all three cube faces and tick axes are visible per the paper's iso-cube look — pure cardinal `(elev=0, azim=-90)` etc. collapse one axis into a degenerate edge and stack matplotlib's tick labels on top of each other. Each recipe writes `plots/<slug>/{figure.png, figure.pdf, spec.json}`. Light grey panes, visible ticks, no axis labels (the cube ticks convey scale on their own).
>
> **Why marching cubes + matplotlib 3-D, not nilearn / PySurfer.** Document this in `info/project_specific_knowledge.md`: nilearn's `plot_glass_brain` is a 2-D MIP of a stylised template (gives a silhouette, not the actual subject volume); `plot_anat` is 2-D triplanar slices (no 3-D-ness); PySurfer / Mayavi need FreeSurfer fsaverage and VTK + a display, and BraTS tumors live in deep white matter not the cortical mantle. Marching-cubes isosurfaces in a matplotlib 3-D axes are the right fit and run headless.
>
> **Trim.** This project doesn't use the standard plot_gen / interactive / significance_test / style_infer subskills — delete `generate_plot.sh`, `interactive_page.sh`, `streamlit/`, `significance/`, and `helpers/utils.py` from the scaffold per the SKILL.md trim rule. Replace `generate_plot.sh` with a `render_views.sh` that's a thin shim around `scripts/render_views.py --all / --recipe / --list-recipes`. Rename `plot_gen.py` → `render_views.py` to match the project's actual deliverable.
>
> **Wrap-up.** Update `info/context.md` with dataset notes (slice format, label codes, the z-score gotcha, volume-1 tumor stats), `info/project_specific_knowledge.md` with the marching-cubes design rationale + retargeting + restyling instructions, and `info/how_to_use.md` so the file map matches the trimmed shape. Verify by running `bash parse_input.sh` (no flags) and `bash render_views.sh --all` and confirming all three figures show the tumor cleanly contained inside the brain envelope.

## Driving it manually (after the agent has scaffolded once)

```bash
cd example2_brain/

# 1. Reconstruct volume 1 (or set --volume-id 42 / edit PROJECT_VOLUME_ID)
bash visualizations/parse_input.sh

# 2. Render the three 3-D views (~30 s each — ~90 s total for --all)
bash visualizations/render_views.sh --list-recipes
bash visualizations/render_views.sh --all
# or one at a time:
bash visualizations/render_views.sh --recipe 3d-front
```

Outputs land in `visualizations/plots/3d-{front,top,medial}/figure.png`.

## Resulting layout

```
example2_brain/
├── README.md                                    ← this file (with the prompt)
├── data/                                        (gitignored — multi-GB BraTS slice files)
│   ├── meta_data.csv
│   └── volume_*_slice_*.h5                      (~57k files)
└── visualizations/
    ├── parse_input.sh
    ├── render_views.sh
    ├── scripts/
    │   ├── parser.py                            single-subject BraTS slice → NIfTI
    │   └── render_views.py                      marching cubes + matplotlib 3-D, three views
    ├── intermediate_data/                       (gitignored — large reconstructed NIfTIs)
    │   ├── parsed_index.json
    │   └── volume_001__{t1,t1ce,t2,flair,seg,brain_mask,tumor_mask}.nii.gz
    ├── plots/
    │   ├── 3d-front/{figure.png,figure.pdf,spec.json}
    │   ├── 3d-top/{figure.png,figure.pdf,spec.json}
    │   └── 3d-medial/{figure.png,figure.pdf,spec.json}
    └── info/
        ├── context.md                           continuation handoff
        ├── how_to_use.md                        human-only guide
        └── project_specific_knowledge.md        BraTS + marching-cubes domain notes
```

## Citation

> Khan, M.A., Lali, I.U., Rehman, A. et al. (2019). *Multimodal brain tumor classification using deep learning and robust feature selection: A machine learning application for radiologists*. **Multimedia Tools and Applications** 78: 16267–16289. doi: [10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0). — visual reference for the three-cube 3-D layout.
>
> Bakas, S. et al. (2017). *Advancing the Cancer Genome Atlas glioma MRI collections with expert segmentation labels and radiomic features*. **Scientific Data** 4: 170117. doi: [10.1038/sdata.2017.117](https://doi.org/10.1038/sdata.2017.117).
>
> Menze, B.H. et al. (2015). *The Multimodal Brain Tumor Image Segmentation Benchmark (BRATS)*. **IEEE Transactions on Medical Imaging** 34(10): 1993–2024. doi: [10.1109/TMI.2014.2377694](https://doi.org/10.1109/TMI.2014.2377694).
>
> The Kaggle slice-format release: Saif Awsaf, *BraTS2020 Training Data*, [kaggle.com/datasets/awsaf49/brats2020-training-data](https://www.kaggle.com/datasets/awsaf49/brats2020-training-data).
