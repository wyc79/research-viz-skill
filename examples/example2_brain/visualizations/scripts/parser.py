#!/usr/bin/env python3
"""
parser.py — reconstruct one BraTS2020 subject's 3-D volume from the 155
per-slice .h5 files shipped on Kaggle (`awsaf49/brats2020-training-data`),
and write each modality + the segmentation as separate NIfTI files into
`intermediate_data/`.

The Kaggle dataset is sliced — every file is `volume_<id>_slice_<z>.h5`
with two HDF5 datasets:
  - `image`: shape (240, 240, 4)  — the four modalities  T1, T1ce, T2, FLAIR
  - `mask` : shape (240, 240, 3)  — three tumor sub-regions, one-hot:
                                    NCR/NET (necrotic + non-enhancing),
                                    ED      (edema),
                                    ET      (enhancing tumor).
There are 155 axial slices per volume. The reconstructed NIfTI is
240×240×155, ~1 mm isotropic (BraTS data is co-registered into a uniform
isotropic grid before slicing — see Bakas et al. 2017).

Output naming follows the SKILL.md `<dataset>__<stage>.<ext>` convention:

  intermediate_data/
    volume_001__t1.nii.gz
    volume_001__t1ce.nii.gz
    volume_001__t2.nii.gz
    volume_001__flair.nii.gz
    volume_001__seg.nii.gz                 (labels: 0 bg, 1 NCR/NET, 2 ED, 4 ET)
    volume_001__brain_mask.nii.gz          (binary brain envelope — used by render_views to clip)
    volume_001__tumor_mask.nii.gz          (binary union of all 3 tumor sub-regions, clipped to brain)
    parsed_index.json

Volume 1 has a 211k-voxel tumor across 83 of 155 slices — large enough
to be visible in the 3-D isosurface renders without dominating the brain.
Change `PROJECT_VOLUME_ID` to retarget.
"""
from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime
from pathlib import Path

import h5py
import nibabel as nib
import numpy as np


# ============================================================================
# PROJECT-SPECIFIC CONFIG — BraTS2020, single subject.
# ============================================================================

PROJECT_VOLUME_ID: int = 1

SLICE_HW: tuple[int, int] = (240, 240)
SLICE_COUNT: int = 155

# Modality channel order in `image` — convention from the dataset author's
# Kaggle notebooks; matches the BraTS file naming `*_t1`, `*_t1ce`, `*_t2`, `*_flair`.
MODALITY_NAMES: tuple[str, ...] = ("t1", "t1ce", "t2", "flair")

# Mask channel order — three tumor sub-regions, one-hot. Collapsed into a
# single integer label volume using BraTS's standard codes. NOTE: ET is 4,
# NOT 3 — that's the BraTS convention since 2017, kept for compatibility
# with every existing piece of BraTS tooling. Don't "fix" it.
MASK_CHANNELS: tuple[tuple[str, int], ...] = (
    ("ncr_net", 1),
    ("ed",      2),
    ("et",      4),
)


def make_affine() -> np.ndarray:
    """Synthesise a centred 1 mm isotropic affine.

    BraTS preprocessed data is 1 mm isotropic in a fixed orientation, but
    the Kaggle slice files don't ship the original SRI24-registered affine.
    A centred identity affine is geometrically faithful at the voxel level
    — it just doesn't have the original SRI24 origin offset. Good enough
    for nilearn / matplotlib-3D rendering; not okay if you need atlas lookup.
    """
    cx = SLICE_HW[1] / 2  # 120
    cy = SLICE_HW[0] / 2  # 120
    cz = SLICE_COUNT / 2  # 77.5
    return np.array(
        [
            [1.0, 0.0, 0.0, -cx],
            [0.0, 1.0, 0.0, -cy],
            [0.0, 0.0, 1.0, -cz],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )


# ============================================================================
# Slice gathering + stacking
# ============================================================================


def find_slice_files(data_dir: Path, volume_id: int) -> list[Path]:
    """Return the 155 .h5 files for one BraTS volume, sorted by slice index."""
    paths = sorted(
        glob.glob(str(data_dir / f"volume_{volume_id}_slice_*.h5")),
        key=lambda p: int(Path(p).stem.split("_slice_")[1]),
    )
    if not paths:
        raise SystemExit(
            f"no slices found for volume {volume_id} under {data_dir}. "
            f"Expected files like volume_{volume_id}_slice_0.h5 ... _slice_{SLICE_COUNT - 1}.h5."
        )
    if len(paths) != SLICE_COUNT:
        print(f"warning: expected {SLICE_COUNT} slices, found {len(paths)}")
    return [Path(p) for p in paths]


def stack_volume(slice_files: list[Path]) -> tuple[np.ndarray, np.ndarray]:
    """Stack per-slice (H, W, 4) image and (H, W, 3) mask arrays into 4-D
    volumes (H, W, Z, 4) and (H, W, Z, 3). Z follows slice index order."""
    H, W = SLICE_HW
    Z = len(slice_files)
    img = np.zeros((H, W, Z, 4), dtype=np.float32)
    msk = np.zeros((H, W, Z, 3), dtype=np.uint8)
    for z, path in enumerate(slice_files):
        with h5py.File(path, "r") as f:
            slice_img = np.asarray(f["image"], dtype=np.float32)
            slice_msk = np.asarray(f["mask"], dtype=np.uint8)
        if slice_img.shape != (H, W, 4) or slice_msk.shape != (H, W, 3):
            raise SystemExit(
                f"slice {path.name}: unexpected shapes "
                f"image={slice_img.shape}, mask={slice_msk.shape}"
            )
        img[:, :, z, :] = slice_img
        msk[:, :, z, :] = slice_msk
    return img, msk


def build_label_volume(mask_4d: np.ndarray) -> np.ndarray:
    """Collapse the 3-channel one-hot mask into a single int label volume
    using BraTS codes (1, 2, 4). On overlap we apply ET > NCR/NET > ED
    priority (ET is the most clinically specific class)."""
    H, W, Z, _ = mask_4d.shape
    labels = np.zeros((H, W, Z), dtype=np.uint8)
    for ch_name, code in MASK_CHANNELS:
        ch_idx = [c[0] for c in MASK_CHANNELS].index(ch_name)
        labels[mask_4d[..., ch_idx] > 0] = code
    et_idx = [c[0] for c in MASK_CHANNELS].index("et")
    labels[mask_4d[..., et_idx] > 0] = 4   # re-apply so ET wins on overlap
    return labels


def build_brain_mask(img_4d: np.ndarray) -> np.ndarray:
    """Recover the brain envelope from the 4-modality stack.

    *Gotcha*: the Kaggle slice release applies z-score normalisation across
    the **whole volume** (not just the brain), so the original
    skull-stripped background — which was exactly 0 in the source NIfTIs —
    sits at small negative values (~−0.6) after normalisation. Checking
    `!= 0` therefore matches every voxel in every slice and gives a useless
    "whole cube" mask.

    The right test is "any modality is *positive*" — true brain voxels
    have intensities above the per-volume mean, so they stay > 0 after
    z-scoring; background sits below the mean and goes negative. We then
    fill internal holes (ventricles in T1 dip below the mean and would
    otherwise be lost) and keep the single largest connected component
    so isolated noise islands at the volume corners don't survive.
    """
    from scipy import ndimage as ndi

    # Step 1: voxel is "brain" if at least one modality is > 0 (above mean).
    raw = np.any(img_4d > 0, axis=-1)

    # Step 2: fill internal holes per axial slice, then in 3-D. Two-pass is
    # cheaper and more reliable than one pure 3-D fill on a 240×240×155 vol.
    filled = np.zeros_like(raw)
    for z in range(raw.shape[2]):
        filled[:, :, z] = ndi.binary_fill_holes(raw[:, :, z])
    filled = ndi.binary_fill_holes(filled)

    # Step 3: keep largest connected component (drops corner-noise islands).
    labels, n = ndi.label(filled)
    if n > 1:
        sizes = np.bincount(labels.ravel())
        sizes[0] = 0  # ignore background
        keep = sizes.argmax()
        filled = labels == keep

    return filled.astype(np.uint8)


# ============================================================================
# Main
# ============================================================================


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", required=True, help="Directory containing the BraTS .h5 slice files")
    p.add_argument("--out", required=True, help="visualizations/intermediate_data path")
    p.add_argument("--volume-id", type=int, default=PROJECT_VOLUME_ID,
                   help=f"BraTS volume id (default {PROJECT_VOLUME_ID})")
    args = p.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    vol = args.volume_id
    files = find_slice_files(data_dir, vol)
    print(f"reconstructing volume {vol} from {len(files)} slice files in {data_dir}")

    img4d, msk4d = stack_volume(files)
    print(f"image stack: {img4d.shape} ({img4d.dtype}), modalities={MODALITY_NAMES}")
    print(f"mask  stack: {msk4d.shape} ({msk4d.dtype}), channels={[c[0] for c in MASK_CHANNELS]}")

    affine = make_affine()
    stem = f"volume_{vol:03d}"
    index: list[dict] = []

    # ---- Per-modality NIfTI -------------------------------------------------
    for ch_idx, name in enumerate(MODALITY_NAMES):
        target = out_dir / f"{stem}__{name}.nii.gz"
        nib.save(nib.Nifti1Image(img4d[..., ch_idx], affine), target)
        index.append({"kind": f"modality_{name}", "parsed_path": target.name,
                      "shape": list(img4d.shape[:3]), "dtype": "float32"})
        print(f"wrote {target}")

    # ---- Multi-class segmentation ------------------------------------------
    labels = build_label_volume(msk4d)
    seg_path = out_dir / f"{stem}__seg.nii.gz"
    nib.save(nib.Nifti1Image(labels, affine), seg_path)
    n_tumor = int((labels > 0).sum())
    n_ncr   = int((labels == 1).sum())
    n_ed    = int((labels == 2).sum())
    n_et    = int((labels == 4).sum())
    print(f"wrote {seg_path}  (tumor voxels: {n_tumor} = NCR/NET {n_ncr} + ED {n_ed} + ET {n_et})")
    index.append({"kind": "segmentation", "parsed_path": seg_path.name,
                  "shape": list(labels.shape), "dtype": "uint8",
                  "label_codes": {"background": 0, "ncr_net": 1, "ed": 2, "et": 4},
                  "tumor_voxels": n_tumor})

    # ---- Brain envelope ----------------------------------------------------
    # The renderer uses this both to draw the brain isosurface and to *clip*
    # the tumor mask, so any tumor voxels falling outside the skull-strip
    # don't poke out into the empty cube.
    brain = build_brain_mask(img4d)
    brain_path = out_dir / f"{stem}__brain_mask.nii.gz"
    nib.save(nib.Nifti1Image(brain, affine), brain_path)
    n_brain = int(brain.sum())
    print(f"wrote {brain_path}  (brain voxels: {n_brain})")
    index.append({"kind": "brain_mask", "parsed_path": brain_path.name,
                  "shape": list(brain.shape), "dtype": "uint8",
                  "brain_voxels": n_brain})

    # ---- Binary tumor union, clipped to brain envelope ---------------------
    tumor_raw = (labels > 0)
    tumor_clipped = (tumor_raw & brain.astype(bool)).astype(np.uint8)
    n_clipped_out = int(tumor_raw.sum() - tumor_clipped.sum())
    if n_clipped_out > 0:
        # Real-world segmentations occasionally have a few voxels labelled as
        # tumor that fall just outside the skull-strip — usually annotation
        # noise at the edema rim. Clipping them out ensures the rendered
        # tumor stays inside the brain isosurface.
        print(f"  clipped {n_clipped_out} tumor voxel(s) outside the brain envelope")
    bin_path = out_dir / f"{stem}__tumor_mask.nii.gz"
    nib.save(nib.Nifti1Image(tumor_clipped, affine), bin_path)
    print(f"wrote {bin_path}  ({int(tumor_clipped.sum())} voxels = ~{int(tumor_clipped.sum() / 1000)}k)")
    index.append({"kind": "tumor_binary_clipped", "parsed_path": bin_path.name,
                  "shape": list(tumor_clipped.shape), "dtype": "uint8",
                  "tumor_voxels": int(tumor_clipped.sum()),
                  "tumor_voxels_clipped_out": n_clipped_out})

    # ---- parsed_index.json --------------------------------------------------
    parsed_index = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_dir": str(data_dir),
        "single_subject_input": True,
        "volume_id": vol,
        "n_slices_input": len(files),
        # The renderer pulls these three by name — keeps the layout one place.
        "canonical_anat": f"{stem}__t1.nii.gz",
        "canonical_brain_mask": f"{stem}__brain_mask.nii.gz",
        "canonical_overlay": f"{stem}__tumor_mask.nii.gz",
        "canonical_segmentation": f"{stem}__seg.nii.gz",
        "outputs": index,
    }
    (out_dir / "parsed_index.json").write_text(json.dumps(parsed_index, indent=2))
    print(f"wrote {out_dir / 'parsed_index.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
