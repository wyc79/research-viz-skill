"""Sensor time-series explorer.

Reads `intermediate_data/parsed_results.csv` and lets the user filter the
sensor log by site and sensor and inspect the time series of `value`. Uses
streamlit native widgets for the filter controls and altair for the chart so
that hover tooltips, zoom and pan work out of the box.
"""
from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# Resolve workspace paths from this file's location.
HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent.parent  # streamlit/pages/<this>.py -> streamlit -> visualizations
PARSED_CSV = VIZ_ROOT / "intermediate_data" / "parsed_results.csv"

st.set_page_config(page_title="Sensor time series", layout="wide")
st.title("Sensor time series")
st.caption(
    "Filter the sensor log by site and sensor, then inspect the time series of `value`."
)

if not PARSED_CSV.exists():
    st.warning(
        "No parsed dataset yet. Run `bash visualizations/parse_input.sh` first, "
        "then refresh this page."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_sensors(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001  (mtime invalidates the cache)
    df = pd.read_csv(path)
    # Coerce ts to datetime; keep a copy of the raw string for display if needed.
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    # Be tolerant of either string or bool for the `ok` column.
    if df["ok"].dtype == object:
        df["ok"] = df["ok"].astype(str).str.lower().map({"true": True, "false": False}).fillna(False)
    return df.sort_values("ts").reset_index(drop=True)


df = load_sensors(str(PARSED_CSV), PARSED_CSV.stat().st_mtime)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    sites_all = sorted(df["site"].dropna().unique().tolist())
    sensors_all = sorted(df["sensor"].dropna().unique().tolist())

    sites = st.multiselect(
        "Site",
        options=sites_all,
        default=sites_all,
        help="Pick one or more sites to include.",
    )
    sensors = st.multiselect(
        "Sensor",
        options=sensors_all,
        default=sensors_all,
        help="Pick one or more sensor types to include.",
    )

    ts_min = pd.Timestamp(df["ts"].min()).to_pydatetime()
    ts_max = pd.Timestamp(df["ts"].max()).to_pydatetime()
    date_range = st.slider(
        "Time range",
        min_value=ts_min,
        max_value=ts_max,
        value=(ts_min, ts_max),
        format="YYYY-MM-DD HH:mm",
    )

    only_ok = st.checkbox(
        "Only rows where ok = True",
        value=False,
        help="The raw log includes an `ok` flag; tick to drop rows where the reading was flagged bad.",
    )

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
mask = (
    df["site"].isin(sites)
    & df["sensor"].isin(sensors)
    & df["ts"].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
)
if only_ok:
    mask &= df["ok"].astype(bool)

filtered = df.loc[mask].copy()

# ---------------------------------------------------------------------------
# Headline metrics
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("rows shown", f"{len(filtered):,}", delta=f"{len(filtered) - len(df):+d}")
c2.metric("sites", filtered["site"].nunique())
c3.metric("sensors", filtered["sensor"].nunique())
if len(filtered):
    c4.metric("mean value", f"{filtered['value'].mean():.2f}")
else:
    c4.metric("mean value", "n/a")

if filtered.empty:
    st.info("No rows match the current filters. Loosen the selection in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# Time-series chart (altair, with hover tooltip and pan/zoom)
# ---------------------------------------------------------------------------
st.subheader("Time series of `value`")

# Encode one line per (site, sensor) combination. Color by sensor; dash by site.
chart = (
    alt.Chart(filtered)
    .mark_line(point=alt.OverlayMarkDef(size=20, opacity=0.6))
    .encode(
        x=alt.X("ts:T", title="timestamp"),
        y=alt.Y("value:Q", title="value"),
        color=alt.Color("sensor:N", title="sensor"),
        strokeDash=alt.StrokeDash("site:N", title="site"),
        tooltip=[
            alt.Tooltip("ts:T", title="timestamp"),
            alt.Tooltip("site:N"),
            alt.Tooltip("sensor:N"),
            alt.Tooltip("value:Q", format=".2f"),
            alt.Tooltip("ok:N"),
        ],
    )
    .properties(height=420)
    .interactive()
)
st.altair_chart(chart, use_container_width=True)

st.caption(
    "Each line is one (site, sensor) combination. Drag to pan, scroll to zoom, "
    "hover any point for the exact reading."
)

# ---------------------------------------------------------------------------
# Optional: per-site small multiples, when the user wants a cleaner view.
# ---------------------------------------------------------------------------
with st.expander("Faceted view: one panel per site"):
    facet = (
        alt.Chart(filtered)
        .mark_line(point=alt.OverlayMarkDef(size=15, opacity=0.7))
        .encode(
            x=alt.X("ts:T", title="timestamp"),
            y=alt.Y("value:Q", title="value"),
            color=alt.Color("sensor:N", title="sensor"),
            tooltip=[
                alt.Tooltip("ts:T", title="timestamp"),
                alt.Tooltip("site:N"),
                alt.Tooltip("sensor:N"),
                alt.Tooltip("value:Q", format=".2f"),
            ],
        )
        .properties(height=200, width=320)
        .facet(facet=alt.Facet("site:N", title=None), columns=2)
        .resolve_scale(y="shared")
    )
    st.altair_chart(facet, use_container_width=True)

# ---------------------------------------------------------------------------
# Underlying data table (with download)
# ---------------------------------------------------------------------------
with st.expander("Filtered data"):
    st.dataframe(filtered, use_container_width=True, height=300)
    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="sensor_log_filtered.csv",
        mime="text/csv",
    )
