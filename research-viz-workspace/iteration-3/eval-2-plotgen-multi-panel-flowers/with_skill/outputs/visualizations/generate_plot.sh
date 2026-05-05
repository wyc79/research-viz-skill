#!/usr/bin/env bash
# Generate the project's static plots from intermediate_data/flowers__parsed.csv.
#
# Two recipes are registered (see PROJECT_RECIPES in scripts/plot_gen.py):
#   petal-length-vs-width-by-species   — scatter, coloured by species
#   sepal-length-violin-per-species    — violin plot per species
#
# Usage:
#   bash generate_plot.sh --list-recipes
#   bash generate_plot.sh --all
#   bash generate_plot.sh --recipe petal-length-vs-width-by-species
#   bash generate_plot.sh --recipe sepal-length-violin-per-species
set -euo pipefail

VIZ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

if [ "$#" -eq 0 ]; then
    echo "usage: $0 --recipe <slug> | --all | --list-recipes" >&2
    exit 1
fi

exec python3 "${VIZ_DIR}/scripts/plot_gen.py" \
    --intermediate "${VIZ_DIR}/intermediate_data" \
    --out "${VIZ_DIR}/plots" \
    "$@"
