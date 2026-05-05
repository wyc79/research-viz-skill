#!/usr/bin/env bash
# Launch the streamlit explorer in your browser.
#
# Quick examples for humans (full reference: ../info/how_to_use.md):
#   bash interactive_page.sh                       # opens streamlit/index.py at http://localhost:8501
#   bash interactive_page.sh --server.port=8600    # any extra flag is forwarded to `streamlit run`
#
# Direct python invocation (skip this wrapper):
#   streamlit run streamlit/index.py
#   # or any specific page:
#   streamlit run streamlit/pages/2_species_explorer.py
set -euo pipefail

VIZ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${VIZ_DIR}/.venv/bin/activate"
fi

exec streamlit run "${VIZ_DIR}/streamlit/index.py" "$@"
