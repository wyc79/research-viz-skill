#!/usr/bin/env bash
# Reconstruct one BraTS2020 subject's 3-D volume from the per-slice .h5 files
# in `data/`, writing per-modality + per-segmentation NIfTI files plus the
# brain envelope and a tumor mask (clipped to the brain) into `intermediate_data/`.
# `data/` is read-only.
#
# Quick examples (full reference: info/how_to_use.md):
#   bash parse_input.sh                          # reconstruct PROJECT_VOLUME_ID from parser.py
#   bash parse_input.sh --volume-id 42           # reconstruct a different BraTS subject
#   DATA_DIR=/path/to/brats bash parse_input.sh  # read from a different folder
#
# Direct python invocation:
#   python scripts/parser.py --help
set -euo pipefail

VIZ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${DATA_DIR:-${VIZ_DIR}/../data}"

if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

exec python3 "${VIZ_DIR}/scripts/parser.py" \
    --data-dir "${DATA_DIR}" \
    --out "${VIZ_DIR}/intermediate_data" \
    "$@"
