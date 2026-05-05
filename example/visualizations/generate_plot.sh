#!/usr/bin/env bash
# Render the Palmer Penguins project's plots from the cleaned CSV under
# `intermediate_data/`. This wrapper just forwards args to `scripts/plot_gen.py`
# — the script knows about the project's seven recipes (see PROJECT_RECIPES at
# the top of that file).
#
# Quick examples for humans (full reference: info/how_to_use.md):
#   bash generate_plot.sh --list-recipes              # show registered recipes
#   bash generate_plot.sh --all                       # regenerate every recipe
#   bash generate_plot.sh --recipe <slug>             # regenerate one recipe
#
# This trimmed example doesn't ship the free-form `"<prompt>"` mode anymore —
# every plot the project keeps is named in PROJECT_RECIPES.
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

exec python3 "${VIZ_DIR}/scripts/plot_gen.py" \
    --intermediate "${VIZ_DIR}/intermediate_data" \
    --out "${VIZ_DIR}/plots" \
    --significance "${VIZ_DIR}/significance" \
    "$@"
