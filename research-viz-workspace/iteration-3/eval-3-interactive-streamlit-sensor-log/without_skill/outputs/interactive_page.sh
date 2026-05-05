#!/usr/bin/env bash
# Launch the Streamlit sensor dashboard.
#
# Creates/uses a local virtualenv in .venv, installs requirements,
# then runs the app on http://localhost:8501

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$HERE/.venv}"

if [ ! -d "$VENV_DIR" ]; then
    echo ">> Creating virtualenv at $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo ">> Installing requirements"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ">> Starting Streamlit (Ctrl-C to stop)"
exec streamlit run app.py "$@"
