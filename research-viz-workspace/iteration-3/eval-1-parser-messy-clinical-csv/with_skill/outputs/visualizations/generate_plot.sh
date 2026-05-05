#!/usr/bin/env bash
# Generate static plots from cleaned CSVs in `intermediate_data/`.
#
# This wrapper supports three modes:
#   1) named recipes baked into plot_gen.py's PROJECT_RECIPES dict (the project's
#      canonical plots — these reproduce exactly what was built for this project)
#   2) regenerate every named recipe at once
#   3) ad-hoc free-form prompts
#
# Quick examples for humans (full reference: ../info/how_to_use.md):
#   bash generate_plot.sh --list-recipes              # show registered recipes
#   bash generate_plot.sh --all                       # regenerate every recipe
#   bash generate_plot.sh --recipe <slug>             # regenerate one recipe
#   bash generate_plot.sh "<plot prompt>"             # ad-hoc, uses canonical_csv
#   bash generate_plot.sh "<plot prompt>" --slug myname --data <path-to-csv>
#
# Direct python invocation (skip this wrapper):
#   python scripts/plot_gen.py --help
set -euo pipefail

VIZ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

# If the first arg starts with "--" we forward everything as-is (recipe / all /
# list / etc.). Otherwise treat the first arg as a free-form prompt and forward
# the rest with --prompt prepended.
if [ "$#" -eq 0 ]; then
    echo "usage: $0 \"<plot prompt>\" [--slug name] [--data path-to-csv]" >&2
    echo "       $0 --recipe <slug> | --all | --list-recipes" >&2
    exit 1
fi

if [[ "$1" == --* ]]; then
    exec python3 "${VIZ_DIR}/scripts/plot_gen.py" \
        --intermediate "${VIZ_DIR}/intermediate_data" \
        --out "${VIZ_DIR}/plots" \
        "$@"
else
    exec python3 "${VIZ_DIR}/scripts/plot_gen.py" \
        --prompt "$1" \
        --intermediate "${VIZ_DIR}/intermediate_data" \
        --out "${VIZ_DIR}/plots" \
        "${@:2}"
fi
