#!/usr/bin/env bash
# Parse data/sensor_log.csv into intermediate_data/sensor_log__parsed.csv.
#
# `data/` is treated as read-only — this wrapper never writes there.
#
# Usage:
#   bash parse_input.sh                            # default: read ../data/sensor_log.csv
#   DATA_DIR=/path/to/other bash parse_input.sh    # read from a different folder
#
# This wrapper is a thin shim around `scripts/parser.py`.
set -euo pipefail

# Self-locate so the wrapper works no matter where you invoke it from.
VIZ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Default to the sibling data/ folder; override with DATA_DIR=... or --data-dir <path>.
DATA_DIR="${DATA_DIR:-${VIZ_DIR}/../data}"

# If a project-local venv exists, activate it. Otherwise rely on the ambient interpreter.
if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

exec python3 "${VIZ_DIR}/scripts/parser.py" \
    --data-dir "${DATA_DIR}" \
    --out "${VIZ_DIR}/intermediate_data" \
    "$@"
