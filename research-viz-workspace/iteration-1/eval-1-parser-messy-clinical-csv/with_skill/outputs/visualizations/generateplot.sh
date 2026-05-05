#!/usr/bin/env bash
# Generate a static plot from intermediate_data/parsed_results.csv based on a plain-English prompt.
# Usage: bash generateplot.sh "<prompt>" [--slug myname] [--data <override-csv>]
set -euo pipefail

VIZ_DIR="/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-1/eval-1-parser-messy-clinical-csv/with_skill/outputs/visualizations"

if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

if [ "$#" -lt 1 ]; then
    echo "usage: $0 \"<plot request>\" [--slug myname] [--data <csv>]" >&2
    exit 1
fi

exec python3 "${VIZ_DIR}/scripts/plotgen.py" \
    --prompt "$1" \
    --data "${VIZ_DIR}/intermediate_data/parsed_results.csv" \
    --out "${VIZ_DIR}/plots" \
    "${@:2}"
