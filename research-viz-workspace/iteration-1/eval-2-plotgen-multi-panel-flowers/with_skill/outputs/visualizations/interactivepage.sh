#!/usr/bin/env bash
# Launch the streamlit explorer.
set -euo pipefail

VIZ_DIR="/Users/yuanchenwang/Documents/Claude/Projects/Visualization Skill/research-viz-workspace/iteration-1/eval-2-plotgen-multi-panel-flowers/with_skill/outputs/visualizations"

if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

exec streamlit run "${VIZ_DIR}/streamlit/index.py" "$@"
