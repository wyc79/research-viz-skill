#!/usr/bin/env bash
# Launch the streamlit explorer.
set -euo pipefail

VIZ_DIR="/sessions/lucid-vigilant-fermat/mnt/Visualization Skill/research-viz-workspace/iteration-1/eval-1-parser-messy-clinical-csv/with_skill/outputs/visualizations"

if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

exec streamlit run "${VIZ_DIR}/streamlit/index.py" "$@"
