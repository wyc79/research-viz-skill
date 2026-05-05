"""Sensor time-series explorer.

Filter the parsed sensor log by `site` and `sensor`, then view the time series
of `value`. Reads `intermediate_data/parsed_results.csv` (produced by
`parseinput.sh`).

Run from the project root via:

    bash visualizations/interactivepage.sh

This page is auto-discovered by Streamlit because it lives under
`streamlit/pages/`.
"""
from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# Resolve workspace paths relative to this file so the app works no matter
# where streamlit was launched from.
HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent.parent
PARSED_CSV = VIZ_ROOT / "intermediate_data" / "parsed_results.csv"

st.set_page_config(page_title="Sensor time series", layout="wide")
st.title("Sensor time series")
st.caption(
    "Filter the sensor log by site and sensor to inspect how `value` evolves "
    "over time. Data source: `intermediate_data/parsed_results.csv`."
)

if not PARSED_CSV.exists():
    st.warning(
        "No parsed dataset yet. Run `bash visualizations/parseinput.sh` first, "
        "then refresh this page."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_parsed(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001 (mtime busts cache)
    df = pd.read_csv(path)
    # Coerce ts to datetime (parser keeps it as a string in CSV)
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    return df


df = load_parsed(str(PARSED_CSV), PARSED_CSV.stat().st_mtime)

# Defensive checks — surface schema issues clearly rather than blowing up later.
required_cols = {"ts", "site", "sensor", "value"}
missing = required_cols - set(df.columns)
if missing:
    st.error(
        f"parsed_results.csv is missing required column(s): {sorted(missing)}. "
        f"Found columns: {list(df.columns)}"
    )
    st.stop()

sites_all = sorted(df["site"].dropna().unique().tolist())
sensors_all = sorted(df["sensor"].dropna().unique().tolist())

# --- Sidebar filters -------------------------------------------------------
st.sidebar.header("Filters")
selected_sites = st.sidebar.multiselect(
    "Site",
    options=sites_all,
    default=sites_all,
    help="Pick one or more sites. Leave empty to clear the chart.",
)
selected_sensors = st.sidebar.multiselect(
    "Sensor",
    options=sensors_all,
    default=sensors_all,
    help="Pick one or more sensors.",
)

# Optional date range — handy for a time-series page.
ts_min = pd.Timestamp(df["ts"].min())
ts_max = pd.Timestamp(df["ts"].max())
if pd.notna(ts_min) and pd.notna(ts_max) and ts_min != ts_max:
    date_range = st.sidebar.date_input(
        "Date range",
        value=(ts_min.date(), ts_max.date()),
        min_value=ts_min.date(),
        max_value=ts_max.date(),
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = ts_min.date(), ts_max.date()
else:
    start_date, end_date = ts_min.date(), ts_max.date()

only_ok = st.sidebar.checkbox(
    "Only rows where `ok` is True",
    value=False,
    help="The raw log has an `ok` flag — toggle this to drop rows flagged False.",
)

# --- Filter ---------------------------------------------------------------
mask = (
    df["site"].isin(selected_sites)
    & df["sensor"].isin(selected_sensors)
    & (df["ts"] >= pd.Timestamp(start_date))
    & (df["ts"] <= pd.Timestamp(end_date) + pd.Timedelta(days=1))
)
if only_ok and "ok" in df.columns:
    # `ok` may be bool or string after CSV round-trip; normalize.
    ok_series = df["ok"]
    if ok_series.dtype != bool:
        ok_series = ok_series.astype(str).str.lower().isin({"true", "1", "yes"})
    mask &= ok_series

filtered = df.loc[mask].sort_values("ts")

# --- Top-line metrics -----------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("rows after filter", f"{len(filtered):,}")
m2.metric("sites selected", len(selected_sites))
m3.metric("sensors selected", len(selected_sensors))
if len(filtered):
    m4.metric("mean value", f"{filtered['value'].mean():.2f}")
else:
    m4.metric("mean value", "—")

if filtered.empty:
    st.info("No rows match the current filter. Widen the selection in the sidebar.")
    st.stop()

# --- Time-series chart ----------------------------------------------------
# Build a series-key column so a single line is drawn per (site, sensor) pair.
plot_df = filtered.assign(series=filtered["site"] + " · " + filtered["sensor"])

# Use altair so we get tooltips and a date-aware x axis "for free".
chart = (
    alt.Chart(plot_df)
    .mark_line(point=alt.OverlayMarkDef(size=20, opacity=0.6))
    .encode(
        x=alt.X("ts:T", title="timestamp"),
        y=alt.Y("value:Q", title="value"),
        color=alt.Color("series:N", title="site / sensor"),
        tooltip=[
            alt.Tooltip("ts:T", title="time"),
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

# --- Per-series summary table --------------------------------------------
with st.expander("Per-series summary", expanded=False):
    summary = (
        filtered.groupby(["site", "sensor"], as_index=False)["value"]
        .agg(n="count", mean="mean", std="std", min="min", max="max")
        .round(3)
    )
    st.dataframe(summary, use_container_width=True)

with st.expander("Filtered rows (first 500)"):
    st.dataframe(filtered.head(500), use_container_width=True)

st.download_button(
    "Download filtered rows as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="sensor_log_filtered.csv",
    mime="text/csv",
)
