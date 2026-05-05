# visualizations/ (BraTS2020 — paper-style 3-D)

A self-contained workspace for reconstructing one BraTS2020 subject's 3-D NIfTI from the per-slice .h5 files in `../data/` and rendering three 3-D isosurface views (front / top / medial) — brain (grey, semi-transparent) with the tumor (red, opaque) inside.

Style follows Khan et al. 2018 ([doi:10.1007/s11042-018-6027-0](https://doi.org/10.1007/s11042-018-6027-0)) with the colour scheme inverted (paper used red brain + blue tumor).

`../data/` is **read-only**. Reconstructed NIfTIs land in `intermediate_data/` (gitignored — they're large).

- [`info/how_to_use.md`](info/how_to_use.md) — human-only guide to running the wrappers yourself.
- [`info/project_specific_knowledge.md`](info/project_specific_knowledge.md) — BraTS slice format, the z-score gotcha, label codes, why marching-cubes + matplotlib 3-D over nilearn / PySurfer.
- [`info/context.md`](info/context.md) — recent activity log + project at a glance.

Two entry points:

- `parse_input.sh` — stack 155 axial slices for `PROJECT_VOLUME_ID` (default `1`) into `intermediate_data/volume_NNN__{t1,t1ce,t2,flair,seg,brain_mask,tumor_mask}.nii.gz`. Tumor mask is clipped against the brain envelope at parse time.
- `render_views.sh` — extract brain + tumor isosurfaces with marching cubes and render into `plots/3d-{front,top,medial}/figure.png`.

Intermediate files follow the `<dataset>__<stage>.<ext>` naming convention. The original scaffold's `generate_plot.sh` / `interactive_page.sh` / `streamlit/` / `significance/` / `helpers/utils.py` were trimmed away — this project doesn't use them.
