#!/usr/bin/env bash
# Parse data/flowers.csv and write the cleaned copy to
# intermediate_data/flowers__parsed.csv (plus parsed_index.json).
#
# data/ is treated as read-only.
#
# Usage:
#   bash parse_input.sh                                  # default: reads ../data
#   DATA_DIR=/path/to/other bash parse_input.sh          # override the data dir
set -euo pipefail

VIZ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${DATA_DIR:-${VIZ_DIR}/../data}"

if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

exec python3 "${VIZ_DIR}/scripts/parser.py" \
    --data-dir "${DATA_DIR}" \
    --out "${VIZ_DIR}/intermediate_data" \
    "$@"
