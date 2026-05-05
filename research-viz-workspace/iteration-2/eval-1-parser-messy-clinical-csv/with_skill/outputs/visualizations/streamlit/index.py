"""Landing page for the streamlit explorer.

Subpages auto-discovered by streamlit live in `streamlit/pages/`. This file is
intentionally minimal — it shows what the workspace contains and lets the user
peek at the cleaned dataset. Build domain-specific exploration pages as
new files in `pages/`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve workspace paths from this file's location so the app works from anywhere.
HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent
PARSED_CSV = VIZ_ROOT / "intermediate_data" / "parsed_results.csv"
PARSED_META = VIZ_ROOT / "intermediate_data" / "parsed_results.meta.json"
CONTEXT_MD = VIZ_ROOT / "info" / "context.md"

st.set_page_config(page_title="research-viz explorer", layout="wide")
st.title("research-viz explorer")

if not PARSED_CSV.exists():
    st.warning(
        "No parsed dataset yet. Run `bash visualizations/parse_input.sh` first, then refresh this page."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_parsed(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001  (mtime invalidates the cache)
    return pd.read_csv(path)


df = load_parsed(str(PARSED_CSV), PARSED_CSV.stat().st_mtime)

c1, c2, c3 = st.columns(3)
c1.metric("rows", f"{len(df):,}")
c2.metric("columns", len(df.columns))
if PARSED_META.exists():
    meta = json.loads(PARSED_META.read_text())
    c3.metric("source files", len(meta.get("source_files", [])))

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
    "They will appear in the sidebar automatically. See `info/how_to_use.md` for details."
)
