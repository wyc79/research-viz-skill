"""Landing page for the streamlit explorer.

Shows the cleaned datasets listed in `intermediate_data/parsed_index.json`
(named `<original_dataset_name>__parsed.csv` per input). If the parser ran
in per-file mode against many input files, the sidebar gets a selector for
switching between them. Subpages auto-discovered by streamlit live in
`streamlit/pages/`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve workspace paths from this file's location so the app works from anywhere.
HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent
INTER = VIZ_ROOT / "intermediate_data"
PARSED_INDEX = INTER / "parsed_index.json"
CONTEXT_MD = VIZ_ROOT / "info" / "context.md"

st.set_page_config(page_title="research-viz explorer", layout="wide")
st.title("research-viz explorer")

if not PARSED_INDEX.exists():
    st.warning(
        "No parsed dataset yet. Run `bash visualizations/parse_input.sh` "
        "(or `python visualizations/scripts/parser.py --data-dir ../data --out visualizations/intermediate_data`) first, then refresh."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_parsed(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001  (mtime invalidates the cache)
    return pd.read_csv(path)


idx = json.loads(PARSED_INDEX.read_text())
per_file = idx.get("per_file_outputs", [])
canonical = idx.get("canonical_csv")
combined = idx.get("combined_csv")

# Build the list of selectable datasets. The canonical (combined or sole per-file)
# leads, with any other per-file outputs available below it.
options: list[tuple[str, Path]] = []
if combined:
    options.append((f"Combined ({combined})", INTER / combined))
seen = {opt[1] for opt in options}
for entry in per_file:
    p = INTER / entry["parsed_path"]
    if p in seen:
        continue
    options.append((entry["source_relative"], p))
    seen.add(p)

if not options:
    st.warning("parsed_index.json has no entries — re-run the parser.")
    st.stop()

if len(options) > 1:
    st.sidebar.markdown("### Dataset")
    labels = [o[0] for o in options]
    chosen_label = st.sidebar.radio(
        "Pick which parsed file to inspect", labels, index=0, label_visibility="collapsed"
    )
    chosen_path = dict(options)[chosen_label]
    st.caption(
        f"Showing **{chosen_label}** ({len(per_file)} per-file outputs available; switch in the sidebar)."
    )
else:
    chosen_label, chosen_path = options[0]

df = load_parsed(str(chosen_path), chosen_path.stat().st_mtime)

c1, c2, c3 = st.columns(3)
c1.metric("rows", f"{len(df):,}")
c2.metric("columns", len(df.columns))
c3.metric("per-file outputs", len(per_file))

with st.expander("Schema", expanded=True):
    schema = pd.DataFrame(
        {
            "dtype": [str(df[c].dtype) for c in df.columns],
            "n_unique": [int(df[c].nunique(dropna=True)) for c in df.columns],
            "pct_missing": [round(float(df[c].isna().mean() * 100), 2) for c in df.columns],
        },
        index=df.columns,
    )
    st.dataframe(schema, use_container_width=True)

with st.expander("Sample of cleaned data"):
    st.dataframe(df.head(200), use_container_width=True)

with st.expander("Workspace context (info/context.md)"):
    if CONTEXT_MD.exists():
        st.markdown(CONTEXT_MD.read_text())
    else:
        st.info("No context.md yet.")

st.divider()
st.caption(
    "Add new exploration pages as Python files under `streamlit/pages/`. "
    "They appear in the sidebar automatically. See `info/how_to_use.md` for details."
)
