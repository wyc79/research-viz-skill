#!/usr/bin/env bash
# Parse + quality-check raw data under data/ into intermediate_data/parsed_results.csv.
# Forwards all flags to parser.py (e.g. --strategy '{"col":"mean"}', --files <glob>).
set -euo pipefail

# Self-locate so this works no matter where it's invoked from.
VIZ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Default to the sibling data/ folder; override with `--data-dir <path>`.
DATA_DIR="${DATA_DIR:-${VIZ_DIR}/../data}"

# If a project-local venv exists, activate it. Otherwise rely on the ambient interpreter.
if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

exec python3 "${VIZ_DIR}/scripts/parser.py" --data-dir "${DATA_DIR}" --out "${VIZ_DIR}/intermediate_data" "$@"
