"""Landing page for the streamlit explorer.

Subpages auto-discovered by streamlit live in `streamlit/pages/`. This file is
intentionally minimal — it shows what the workspace contains and lets the user
peek at the cleaned dataset. Build domain-specific exploration pages as
new files in `pages/`.

Handles two parser layouts:
  - **single combined** dataset (`intermediate_data/parsed_results.csv`),
  - **per-file** mode where each input file gets its own parsed CSV mirroring `data/`
    (no combined CSV; `parsed_index.json` lists what's there).
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
PARSED_CSV = INTER / "parsed_results.csv"
PARSED_META = INTER / "parsed_results.meta.json"
PARSED_INDEX = INTER / "parsed_index.json"
CONTEXT_MD = VIZ_ROOT / "info" / "context.md"

st.set_page_config(page_title="research-viz explorer", layout="wide")
st.title("research-viz explorer")

if not PARSED_CSV.exists() and not PARSED_INDEX.exists():
    st.warning(
        "No parsed dataset yet. Run `bash visualizations/parse_input.sh` first, then refresh this page."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_parsed(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001  (mtime invalidates the cache)
    return pd.read_csv(path)


# Decide which dataset(s) we're showing.
chosen_label: str
chosen_path: Path
if PARSED_INDEX.exists():
    idx = json.loads(PARSED_INDEX.read_text())
    per_file = idx.get("per_file_outputs", [])
    has_combined = idx.get("has_combined_csv") and PARSED_CSV.exists()

    options: list[tuple[str, Path]] = []
    if has_combined:
        options.append(("Combined (parsed_results.csv)", PARSED_CSV))
    for entry in per_file:
        options.append((entry["source_relative"], INTER / entry["parsed_path"]))

    if len(options) > 1:
        labels = [o[0] for o in options]
        st.sidebar.markdown("### Dataset")
        chosen_label = st.sidebar.radio(
            "Pick which parsed file to inspect", labels, index=0, label_visibility="collapsed"
        )
        chosen_path = dict(options)[chosen_label]
        st.caption(f"Showing **{chosen_label}** ({len(per_file)} per-file outputs available; "
                   "switch in the sidebar).")
    else:
        chosen_label, chosen_path = options[0]
else:
    chosen_label, chosen_path = "parsed_results.csv", PARSED_CSV


df = load_parsed(str(chosen_path), chosen_path.stat().st_mtime)

c1, c2, c3 = st.columns(3)
c1.metric("rows", f"{len(df):,}")
c2.metric("columns", len(df.columns))
if PARSED_META.exists() and chosen_path == PARSED_CSV:
    meta = json.loads(PARSED_META.read_text())
    c3.metric("source files", len(meta.get("source_files", [])))
elif PARSED_INDEX.exists():
    idx = json.loads(PARSED_INDEX.read_text())
    c3.metric("per-file outputs", len(idx.get("per_file_outputs", [])))

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
