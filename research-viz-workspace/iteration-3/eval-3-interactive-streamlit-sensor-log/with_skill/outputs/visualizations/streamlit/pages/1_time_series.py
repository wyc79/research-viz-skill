"""Time-series explorer for the sensor log.

Lets the user filter the parsed sensor log by site (multi-select) and sensor
(multi-select) and shows the value over time as a line chart, one line per
(site, sensor) combination. Ticks at 3-hour intervals, ~3-month range.
"""
from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# Resolve the parsed CSV from this file's location so the page works no matter
# where streamlit is launched from.
HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent.parent
PARSED_CSV = VIZ_ROOT / "intermediate_data" / "sensor_log__parsed.csv"

# Project palette: one color per site. Picked from a colorblind-friendly set
# so all four sites stay distinguishable when overlaid in the same chart.
SITE_COLORS = {
    "east":  "#1f77b4",
    "north": "#ff7f0e",
    "south": "#2ca02c",
    "west":  "#d62728",
}

# Stable sensor order so the multiselect default + chart legend don't reshuffle.
SENSOR_ORDER = ["humidity", "pressure", "temperature"]
SITE_ORDER = ["east", "north", "south", "west"]


st.set_page_config(page_title="Sensor time series", layout="wide")
st.title("Sensor time series")
st.caption(
    "Filter the sensor log by site and sensor; the chart shows `value` over time, "
    "with one line per (site, sensor) combination."
)


@st.cache_data(show_spinner=False)
def load_parsed(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001 (mtime invalidates cache)
    df = pd.read_csv(path, parse_dates=["ts"])
    return df


if not PARSED_CSV.exists():
    st.error(
        f"Missing {PARSED_CSV.name}. Run `bash visualizations/parse_input.sh` first, then refresh."
    )
    st.stop()

df = load_parsed(str(PARSED_CSV), PARSED_CSV.stat().st_mtime)

# ---- Sidebar filters ----
st.sidebar.header("Filters")

sites = st.sidebar.multiselect(
    "Site",
    options=SITE_ORDER,
    default=SITE_ORDER,
    help="Geographic site the reading came from. Pick one or several.",
)

sensors = st.sidebar.multiselect(
    "Sensor",
    options=SENSOR_ORDER,
    default=SENSOR_ORDER,
    help="Which sensor produced the reading: humidity, pressure, or temperature.",
)

# Optional: hide rows the upstream system flagged as not OK. Default keeps
# everything so the chart matches the raw log; toggle to inspect only good
# readings.
only_ok = st.sidebar.checkbox(
    "Only show readings where ok=True",
    value=False,
    help="When checked, drop rows where the `ok` column is False (sensor flagged the reading as bad).",
)

# ---- Apply filters ----
mask = df["site"].isin(sites) & df["sensor"].isin(sensors)
if only_ok:
    mask &= df["ok"]
filtered = df.loc[mask].copy()

# Stamp a combined "site / sensor" series label so altair can colour & legend
# each (site, sensor) line distinctly without faceting.
filtered["series"] = filtered["site"] + " / " + filtered["sensor"]

# ---- Top-line metrics ----
c1, c2, c3 = st.columns(3)
c1.metric("rows shown", f"{len(filtered):,}", help="Rows after applying the sidebar filters.")
c2.metric("series", filtered["series"].nunique(), help="Unique site-sensor combinations.")
c3.metric(
    "value range",
    f"{filtered['value'].min():.1f} – {filtered['value'].max():.1f}" if len(filtered) else "—",
    help="Min and max of the filtered `value` column (units depend on the sensor).",
)

# ---- Chart ----
if filtered.empty:
    st.warning("No rows match the current filters — widen the selection in the sidebar.")
else:
    # One line per (site, sensor); colour encodes the site so reading the chart
    # feels consistent even when the user picks one sensor across all sites.
    color_scale = alt.Scale(
        domain=list(SITE_COLORS.keys()),
        range=list(SITE_COLORS.values()),
    )
    chart = (
        alt.Chart(filtered)
        .mark_line(point=alt.OverlayMarkDef(size=20))
        .encode(
            x=alt.X("ts:T", title="Timestamp"),
            y=alt.Y("value:Q", title="Sensor value"),
            color=alt.Color("site:N", scale=color_scale, title="Site"),
            strokeDash=alt.StrokeDash("sensor:N", title="Sensor"),
            tooltip=[
                alt.Tooltip("ts:T", title="Timestamp"),
                alt.Tooltip("site:N", title="Site"),
                alt.Tooltip("sensor:N", title="Sensor"),
                alt.Tooltip("value:Q", title="Value", format=".2f"),
                alt.Tooltip("ok:N", title="OK"),
            ],
        )
        .properties(height=420)
        .interactive()  # pan + zoom on the time axis
    )
    st.altair_chart(chart, width="stretch")

    with st.expander("Filtered rows (first 200)"):
        st.dataframe(
            filtered[["ts", "site", "sensor", "value", "ok"]].head(200),
            width="stretch",
        )

with st.expander("Notes / data source"):
    st.markdown(
        """
        - **Source:** `data/sensor_log.csv` — 800 rows, 3-hourly readings from
          2025-01-01 to 2025-04-10 across four sites (`east`, `north`, `south`,
          `west`) and three sensors (`humidity`, `pressure`, `temperature`).
        - **Cleaning:** the `ts` column is parsed to a real datetime in
          `parser.py`; nothing else is transformed (no missing values in this
          dataset).
        - **`ok` column:** boolean flag from the upstream sensor; toggle the
          sidebar checkbox to drop the rows where it's False.
        """
    )
