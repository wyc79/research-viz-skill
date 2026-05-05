#!/usr/bin/env bash
# Launch the Streamlit sensor-log dashboard.
#
# Usage:
#   ./interactivepage.sh             # default: localhost:8501
#   PORT=8600 ./interactivepage.sh   # override port
set -euo pipefail

# Always run from the directory this script lives in so relative
# paths (data/sensor_log.csv) resolve correctly.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${PORT:-8501}"

exec streamlit run app.py \
    --server.port "$PORT" \
    --server.headless true \
    --browser.gatherUsageStats false
