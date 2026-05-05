#!/usr/bin/env bash
# Parse + quality-check raw data under /sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-1/eval-1-parser-messy-clinical-csv/with_skill/outputs/data into intermediate_data/parsed_results.csv.
# Forwards all flags to parser.py (e.g. --strategy '{"col":"mean"}', --files <glob>).
set -euo pipefail

VIZ_DIR="/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-1/eval-1-parser-messy-clinical-csv/with_skill/outputs/visualizations"
DATA_DIR="/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-1/eval-1-parser-messy-clinical-csv/with_skill/outputs/data"

# If a venv exists alongside this folder, activate it. Otherwise rely on the ambient interpreter.
if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

exec python3 "${VIZ_DIR}/scripts/parser.py" --data-dir "${DATA_DIR}" --out "${VIZ_DIR}/intermediate_data" "$@"
