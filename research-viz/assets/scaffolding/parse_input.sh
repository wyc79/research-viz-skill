#!/usr/bin/env bash
# Parse + quality-check the raw data in `data/` into
# `intermediate_data/<original_dataset_name>__parsed.csv` (one per input file).
#
# `data/` is treated as read-only — this wrapper never writes there.
#
# Quick examples for humans (full reference: ../info/how_to_use.md):
#   bash parse_input.sh                                       # interactive prompts for missing data
#   bash parse_input.sh --no-interactive                      # use 'ignore' for every missing column
#   bash parse_input.sh --no-interactive --strategy '{"col":"median"}'
#   DATA_DIR=/path/to/other bash parse_input.sh               # read from a different folder
#   bash parse_input.sh --combine concat                      # also write combined__parsed.csv
#
# This wrapper is a thin shim around `scripts/parser.py`. To skip it and call python directly:
#   python scripts/parser.py --help
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
