#!/usr/bin/env python3
"""
render_views.py — render front, top, and medial 3-D isosurface snapshots of
the parsed BraTS subject's brain (grey, semi-transparent) with the tumor
(red, opaque) inside it.

Style follows Khan et al. 2018, *Multimodal brain tumor classification using
deep learning and robust feature selection: A machine learning application
for radiologists*, Multimedia Tools and Applications 78: 16267–16289
(doi:10.1007/s11042-018-6027-0) — three 3-D cubes per case showing the
brain envelope and the tumor as separate marching-cubes isosurfaces, with
visible axis ticks. We invert the original colour scheme (paper used red
brain + blue tumor; we use grey brain + red tumor) so the tumor pops more
under the semi-transparent envelope.

Why marching-cubes + matplotlib 3-D, not nilearn.plot_glass_brain: the
question we want to answer is "where is the tumor inside the volume", not
"what's the projected silhouette". Glass-brain is a 2-D MIP of a stylised
template; the paper figure is a true 3-D isosurface of the subject's own
volume. nilearn doesn't ship a volumetric isosurface renderer, so we use
`skimage.measure.marching_cubes` to extract the meshes and matplotlib's
`mpl_toolkits.mplot3d.Poly3DCollection` to render them. nilearn is still
used elsewhere in the project (`nibabel`/nilearn ecosystem for I/O) — see
`info/project_specific_knowledge.md` for the full design rationale.

Three named views — each lands at `plots/<slug>/figure.png`:

  - 3d-front   — looking at the anterior face of the brain
  - 3d-top     — looking down through the superior face
  - 3d-medial  — looking at the lateral face from one side

Each recipe also writes `figure.pdf` and a `spec.json` so a future agent
knows exactly what was rendered.

Tumor-stays-inside-brain rule: the parser already clips the tumor binary
mask against the brain envelope (`build_brain_mask`) and writes the clipped
version as `*__tumor_mask.nii.gz`. So the tumor mesh that `marching_cubes`
extracts here can never extend past the brain mesh — clipping happens once,
upstream, at parse time.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage import measure


# ============================================================================
# PROJECT_RECIPES — three views of the BraTS subject in 3-D.
#
# `elev` and `azim` are matplotlib 3-D camera angles (in degrees).
# Coordinate convention for the BraTS slice array (H, W, Z):
#   axis 0 (X): anterior <-> posterior   (varies by stack orientation; see notes)
#   axis 1 (Y): left <-> right
#   axis 2 (Z): inferior <-> superior
# Empirically, against the rendered output of volume 1, these elev/azim
# values give the labelled view; if the dataset orientation flips for a
# different subject, the view labels are still correct because all three
# are cardinal cube faces.
# ============================================================================

PROJECT_RECIPES: dict[str, dict] = {
    # Pure cardinal angles (elev=0/90, azim=0/-90) collapse one cube face
    # into a degenerate edge and stack matplotlib's tick labels on top of
    # each other. Following the paper's iso-cube look, we tilt each view
    # slightly off-cardinal so all three faces of the cube are visible —
    # the brain still reads as "front" / "top" / "medial" but the figure
    # has an actual 3-D box around it.
    "3d-front": {
        "title": "3-D — anterior (front) view",
        "elev": 15,
        "azim": -80,
    },
    "3d-top": {
        "title": "3-D — superior (top) view",
        "elev": 70,
        "azim": -85,
    },
    "3d-medial": {
        "title": "3-D — medial / sagittal view",
        "elev": 15,
        "azim": 10,
    },
}

# Visual style — calibrated to read close to the Khan et al. 2018 figure
# (with the colour swap noted in the docstring). The brain alpha is low so
# the tumor inside is visible; the tumor alpha is 1.0 so it reads as a
# solid mass. Light shading via matplotlib's LightSource gives the smooth
# isosurface a sense of depth without us having to do explicit shading.
BRAIN_COLOR = (0.62, 0.62, 0.62)   # neutral mid-grey
BRAIN_ALPHA = 0.18
TUMOR_COLOR = (0.85, 0.10, 0.10)   # crimson-red, slightly desaturated
TUMOR_ALPHA = 1.0


# ============================================================================
# Mesh extraction
# ============================================================================


def extract_mesh(mask: np.ndarray, *, step_size: int = 2):
    """Run marching cubes on a binary mask and return (verts, faces).

    `step_size > 1` decimates the mesh — a 240×240×155 brain at step=1
    gives ~1.5M triangles which renders slowly in matplotlib; step=2 is
    ~4x fewer triangles and still smooth-looking at the figure resolution.
    """
    # `level=0.5` is the right threshold for a 0/1 binary mask: marching
    # cubes interpolates the 0.5 isosurface between the on/off voxels.
    verts, faces, _, _ = measure.marching_cubes(
        mask.astype(np.float32),
        level=0.5,
        step_size=step_size,
        allow_degenerate=False,
    )
    return verts, faces


def shaded_facecolors(verts: np.ndarray, faces: np.ndarray, base_color, alpha: float):
    """Apply LightSource shading to the mesh facets so the surface reads
    as 3-D under matplotlib's flat collection rendering."""
    # Per-face normal — average vertex coords give the centroid; the cross
    # product of two edges gives the normal direction.
    tri = verts[faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    norm = np.linalg.norm(n, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    n = n / norm
    # LightSource expects a HxW elevation grid; we simulate it by treating
    # each facet's z-component-of-normal as a brightness modulation.
    ls = LightSource(azdeg=315, altdeg=45)
    # 0.5 + 0.5 * dot(normal, light_dir) — simple Lambertian.
    light = ls.direction
    intensity = 0.5 + 0.5 * np.clip(n @ light, 0, 1)
    rgb = np.tile(np.array(base_color, dtype=np.float32), (len(faces), 1))
    rgb = rgb * intensity[:, None]
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.full((len(faces), 1), alpha)], axis=1)
    return rgba


# ============================================================================
# Rendering — one view per call
# ============================================================================


def render_one(
    slug: str,
    recipe: dict,
    brain_mask: np.ndarray,
    tumor_mask: np.ndarray,
    out_root: Path,
) -> Path:
    """Marching-cubes isosurfaces of brain (grey, semi-transparent) and
    tumor (red, opaque), one cardinal view, saved as figure.png + figure.pdf
    + spec.json under plots/<slug>/."""
    out_dir = out_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Extract meshes once per render. We re-extract per slug instead of
    # caching across views so each plots/<slug>/ folder is self-describing
    # — `spec.json` plus the figure tells you everything about that run.
    bv, bf = extract_mesh(brain_mask, step_size=2)
    tv, tf = extract_mesh(tumor_mask, step_size=1)  # tumor is small; keep full res

    fig = plt.figure(figsize=(6, 5.5))
    ax = fig.add_subplot(111, projection="3d")

    # Brain — draw first so the tumor renders on top. Slightly lower zorder
    # too, in case matplotlib's depth sort gets confused on overlapping
    # alpha facets (which it sometimes does with Poly3DCollection).
    brain_poly = Poly3DCollection(
        bv[bf],
        facecolors=shaded_facecolors(bv, bf, BRAIN_COLOR, BRAIN_ALPHA),
        edgecolors="none",
        linewidths=0.0,
    )
    brain_poly.set_zsort("max")
    ax.add_collection3d(brain_poly)

    tumor_poly = Poly3DCollection(
        tv[tf],
        facecolors=shaded_facecolors(tv, tf, TUMOR_COLOR, TUMOR_ALPHA),
        edgecolors="none",
        linewidths=0.0,
    )
    tumor_poly.set_zsort("max")
    ax.add_collection3d(tumor_poly)

    # Set axis bounds tight to the brain so the cube doesn't have a huge
    # empty margin. Add a tiny pad so the surface doesn't kiss the panes.
    nz = np.argwhere(brain_mask > 0)
    if nz.size:
        mn, mx = nz.min(axis=0), nz.max(axis=0)
        pad = 4
        ax.set_xlim(max(0, mn[0] - pad), mx[0] + pad)
        ax.set_ylim(max(0, mn[1] - pad), mx[1] + pad)
        ax.set_zlim(max(0, mn[2] - pad), mx[2] + pad)
    ax.set_box_aspect((1, 1, 0.95))   # roughly anatomical proportions

    ax.view_init(elev=recipe["elev"], azim=recipe["azim"])

    # Match the paper's look: light grey panes, ticks visible, no axis
    # labels (the labels would clutter the small figure; the cube ticks
    # convey the scale on their own).
    for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
        pane.pane.set_facecolor((0.94, 0.94, 0.94, 1.0))
        pane.pane.set_edgecolor((0.7, 0.7, 0.7, 1.0))
    ax.tick_params(labelsize=8, pad=1)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_zlabel("")
    ax.set_title(recipe["title"], fontsize=11, pad=8)

    fig.tight_layout()
    png = out_dir / "figure.png"
    pdf = out_dir / "figure.pdf"
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)

    spec = {
        "slug": slug,
        "brain_mesh_triangles": int(len(bf)),
        "tumor_mesh_triangles": int(len(tf)),
        "brain_alpha": BRAIN_ALPHA,
        "tumor_alpha": TUMOR_ALPHA,
        **recipe,
    }
    (out_dir / "spec.json").write_text(json.dumps(spec, indent=2))
    return png


# ============================================================================
# Dispatch
# ============================================================================


def _resolve_paths(intermediate: Path) -> tuple[Path, Path]:
    """Pull the canonical brain mask + tumor overlay paths from parsed_index.json."""
    idx_path = intermediate / "parsed_index.json"
    if not idx_path.exists():
        raise SystemExit(f"no parsed_index.json at {idx_path}. Run parse_input.sh first.")
    idx = json.loads(idx_path.read_text())
    brain = intermediate / idx["canonical_brain_mask"]
    overlay = intermediate / idx["canonical_overlay"]
    if not brain.exists() or not overlay.exists():
        raise SystemExit(
            f"missing parsed NIfTI(s): brain_mask={brain.exists()}, tumor_mask={overlay.exists()}"
        )
    return brain, overlay


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--recipe", default=None, help="Render one recipe by slug.")
    mode.add_argument("--all", action="store_true", help="Render every recipe.")
    mode.add_argument("--list-recipes", action="store_true", help="Print every recipe + view and exit.")
    p.add_argument("--intermediate", required=True, help="visualizations/intermediate_data path")
    p.add_argument("--out", required=True, help="visualizations/plots path")
    args = p.parse_args()

    if args.list_recipes:
        for slug, rec in PROJECT_RECIPES.items():
            print(f"  {slug:<14}  elev={rec['elev']:>3}  azim={rec['azim']:>4}  {rec.get('title','')}")
        return 0

    intermediate = Path(args.intermediate).resolve()
    out_root = Path(args.out).resolve()
    brain_path, tumor_path = _resolve_paths(intermediate)

    print(f"loading {brain_path.name} + {tumor_path.name}")
    brain_mask = nib.load(str(brain_path)).get_fdata().astype(np.uint8)
    tumor_mask = nib.load(str(tumor_path)).get_fdata().astype(np.uint8)
    if brain_mask.shape != tumor_mask.shape:
        raise SystemExit(f"shape mismatch: brain {brain_mask.shape} vs tumor {tumor_mask.shape}")
    # Guard the no-tumor-outside-brain rule even if a future parser forgets.
    extra = int(((tumor_mask > 0) & (brain_mask == 0)).sum())
    if extra > 0:
        print(f"  re-clipping {extra} tumor voxel(s) outside brain (parser should have done this)")
        tumor_mask = (tumor_mask & brain_mask).astype(np.uint8)

    if args.all:
        slugs = list(PROJECT_RECIPES.keys())
    elif args.recipe:
        if args.recipe not in PROJECT_RECIPES:
            raise SystemExit(f"unknown recipe {args.recipe!r}; available: {list(PROJECT_RECIPES)}")
        slugs = [args.recipe]
    else:
        raise SystemExit("give one of: --all, --recipe <slug>, --list-recipes")

    print(f"rendering {len(slugs)} view(s) into {out_root}/")
    for slug in slugs:
        png = render_one(slug, PROJECT_RECIPES[slug], brain_mask, tumor_mask, out_root)
        print(f"  {slug:<14}  {png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
