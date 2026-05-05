"""Landing page for the sensor-log streamlit explorer.

Loads the parsed sensor log, shows a quick schema + data sample, and points the
user at the time-series page in the sidebar.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve workspace paths from this file's location so the app works regardless
# of where streamlit is launched from.
HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent
PARSED_CSV = VIZ_ROOT / "intermediate_data" / "sensor_log__parsed.csv"
CONTEXT_MD = VIZ_ROOT / "info" / "context.md"

st.set_page_config(page_title="sensor-log explorer", layout="wide")
st.title("Sensor-log explorer")
st.caption(
    "Quarterly sensor readings across four sites and three sensors. "
    "Use the sidebar to open the time-series page."
)

if not PARSED_CSV.exists():
    st.warning(
        "No parsed dataset yet. Run `bash visualizations/parse_input.sh` first, then refresh."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_parsed(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001 (mtime invalidates cache)
    return pd.read_csv(path, parse_dates=["ts"])


df = load_parsed(str(PARSED_CSV), PARSED_CSV.stat().st_mtime)

# Top-line counts so the user can see the shape of the dataset at a glance.
c1, c2, c3, c4 = st.columns(4)
c1.metric("rows", f"{len(df):,}")
c2.metric("columns", len(df.columns))
c3.metric("sites", df["site"].nunique())
c4.metric("sensors", df["sensor"].nunique())

with st.expander("Schema", expanded=True):
    schema = pd.DataFrame(
        {
            "dtype": [str(df[c].dtype) for c in df.columns],
            "n_unique": [int(df[c].nunique(dropna=True)) for c in df.columns],
            "pct_missing": [round(float(df[c].isna().mean() * 100), 2) for c in df.columns],
        },
        index=df.columns,
    )
    st.dataframe(schema, width="stretch")

with st.expander("Sample of cleaned data"):
    st.dataframe(df.head(200), width="stretch")

with st.expander("Workspace context (info/context.md)"):
    if CONTEXT_MD.exists():
        st.markdown(CONTEXT_MD.read_text())
    else:
        st.info("No context.md yet.")

st.divider()
st.caption(
    "Open **Time series** in the sidebar to filter by site / sensor and see `value` over time."
)
