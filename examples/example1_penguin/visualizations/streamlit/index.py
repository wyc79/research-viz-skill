"""Landing page for the Palmer Penguins streamlit explorer.

Single dataset (`intermediate_data/penguins__parsed.csv`), so we drop the
multi-dataset selector from the original scaffold and show just the schema +
data sample + workspace context. The three exploration pages live under
`streamlit/pages/`:

  1_penguins_overview.py        — streamlit native charts only
  2_bill_morphology_altair.py   — altair with linked brushing
  3_prerendered_gallery.py      — viewer for the pre-rendered PNGs in plots/
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent
PARSED = VIZ_ROOT / "intermediate_data" / "penguins__parsed.csv"
CONTEXT_MD = VIZ_ROOT / "info" / "context.md"

st.set_page_config(page_title="Palmer Penguins explorer", layout="wide")
st.title("Palmer Penguins explorer")
st.caption(
    "Three-page demo of the `research-viz` interactive subskill — "
    "native streamlit charts, an altair view with linked brushing, and a "
    "viewer for the pre-rendered figures in `plots/`."
)

if not PARSED.exists():
    st.warning(
        "No parsed dataset yet. Run `bash visualizations/parse_input.sh` first, then refresh."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_parsed(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001  (mtime invalidates the cache)
    return pd.read_csv(path)


df = load_parsed(str(PARSED), PARSED.stat().st_mtime)

c1, c2, c3 = st.columns(3)
c1.metric("rows", f"{len(df):,}")
c2.metric("columns", len(df.columns))
c3.metric("species", df["species"].nunique())

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

with st.expander("Notes / data source"):
    if CONTEXT_MD.exists():
        st.markdown(CONTEXT_MD.read_text())
    else:
        st.info("No context.md yet.")

st.divider()
st.caption(
    "Pick an exploration page from the sidebar →. "
    "Add new pages as `streamlit/pages/<n>_<topic>.py` and they'll show up automatically."
)
