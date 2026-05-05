#!/usr/bin/env bash
# Render front / top / medial 3-D isosurface snapshots of the parsed BraTS
# volume — brain (grey, semi-transparent) + tumor (red, opaque) extracted via
# marching cubes, drawn in matplotlib 3-D. Each recipe writes
# plots/<slug>/{figure.png, figure.pdf, spec.json}.
#
# Quick examples:
#   bash render_views.sh --list-recipes              # show registered views
#   bash render_views.sh --all                       # regenerate every view
#   bash render_views.sh --recipe 3d-front           # regenerate one view
#
# Direct python invocation:
#   python scripts/render_views.py --help
set -euo pipefail

VIZ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

if [ "$#" -eq 0 ]; then
    echo "usage: $0 --all | --recipe <slug> | --list-recipes" >&2
    exit 1
fi

exec python3 "${VIZ_DIR}/scripts/render_views.py" \
    --intermediate "${VIZ_DIR}/intermediate_data" \
    --out "${VIZ_DIR}/plots" \
    "$@"
