"""Streamlit dashboard for sensor_log.csv.

Run with: ./interactivepage.sh
"""
from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "sensor_log.csv"


@st.cache_data(show_spinner=False)
def load_data(path: Path) -> pd.DataFrame:
    """Load and parse the sensor log CSV."""
    df = pd.read_csv(path, parse_dates=["ts"])
    # Normalize types
    df["site"] = df["site"].astype("category")
    df["sensor"] = df["sensor"].astype("category")
    if df["ok"].dtype != bool:
        df["ok"] = df["ok"].astype(str).str.lower().map({"true": True, "false": False}).fillna(False).astype(bool)
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def main() -> None:
    st.set_page_config(
        page_title="Sensor Log Dashboard",
        page_icon=None,
        layout="wide",
    )

    st.title("Sensor Log Dashboard")
    st.caption(f"Data source: `{DATA_PATH.relative_to(DATA_PATH.parent.parent)}`")

    if not DATA_PATH.exists():
        st.error(f"Could not find data file at {DATA_PATH}")
        st.stop()

    df = load_data(DATA_PATH)

    # ---- Sidebar filters ----
    st.sidebar.header("Filters")

    sites = sorted(df["site"].cat.categories.tolist())
    sensors = sorted(df["sensor"].cat.categories.tolist())

    selected_sites = st.sidebar.multiselect(
        "Site",
        options=sites,
        default=sites,
        help="Choose one or more sites to include.",
    )
    selected_sensors = st.sidebar.multiselect(
        "Sensor",
        options=sensors,
        default=sensors,
        help="Choose one or more sensor types to include.",
    )

    min_ts = df["ts"].min().to_pydatetime()
    max_ts = df["ts"].max().to_pydatetime()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_ts.date(), max_ts.date()),
        min_value=min_ts.date(),
        max_value=max_ts.date(),
    )

    only_ok = st.sidebar.checkbox(
        "Only show readings with ok=True",
        value=False,
        help="If checked, drops rows where the ok column is False.",
    )

    # ---- Apply filters ----
    mask = (
        df["site"].isin(selected_sites)
        & df["sensor"].isin(selected_sensors)
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        start_ts = pd.Timestamp(start_d)
        # Include the entire end day
        end_ts = pd.Timestamp(end_d) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        mask &= df["ts"].between(start_ts, end_ts)
    if only_ok:
        mask &= df["ok"]

    filtered = df.loc[mask].copy()

    # ---- Summary metrics ----
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(filtered):,}")
    c2.metric("Sites selected", len(selected_sites))
    c3.metric("Sensors selected", len(selected_sensors))
    if len(filtered):
        c4.metric("Mean value", f"{filtered['value'].mean():.2f}")
    else:
        c4.metric("Mean value", "n/a")

    if filtered.empty:
        st.warning("No rows match the current filters. Adjust the sidebar to see data.")
        return

    # ---- Time series chart ----
    st.subheader("Time series of value")

    # Build a stable series id "site / sensor" so each combination gets its own line.
    chart_df = filtered.assign(series=filtered["site"].astype(str) + " / " + filtered["sensor"].astype(str))

    base = alt.Chart(chart_df).encode(
        x=alt.X("ts:T", title="Timestamp"),
        y=alt.Y("value:Q", title="Value"),
        color=alt.Color("series:N", title="Site / Sensor"),
        tooltip=[
            alt.Tooltip("ts:T", title="Timestamp"),
            alt.Tooltip("site:N"),
            alt.Tooltip("sensor:N"),
            alt.Tooltip("value:Q", format=".2f"),
            alt.Tooltip("ok:N"),
        ],
    )

    line = base.mark_line(point=False)
    points = base.mark_circle(size=35, opacity=0.6)

    chart = (line + points).properties(height=420).interactive()
    st.altair_chart(chart, use_container_width=True)

    # ---- Per-sensor breakdown ----
    with st.expander("Per-sensor facet (one chart per sensor)", expanded=False):
        facet = (
            alt.Chart(chart_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("ts:T", title="Timestamp"),
                y=alt.Y("value:Q", title="Value"),
                color=alt.Color("site:N", title="Site"),
                tooltip=[
                    alt.Tooltip("ts:T", title="Timestamp"),
                    alt.Tooltip("site:N"),
                    alt.Tooltip("sensor:N"),
                    alt.Tooltip("value:Q", format=".2f"),
                ],
            )
            .properties(height=200, width=600)
            .facet(row=alt.Row("sensor:N", title=None))
            .resolve_scale(y="independent")
        )
        st.altair_chart(facet, use_container_width=True)

    # ---- Summary table ----
    st.subheader("Summary by site / sensor")
    summary = (
        filtered.groupby(["site", "sensor"], observed=True)["value"]
        .agg(count="count", mean="mean", min="min", max="max", std="std")
        .round(2)
        .reset_index()
        .sort_values(["site", "sensor"])
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

    # ---- Raw data ----
    with st.expander("Raw filtered data", expanded=False):
        st.dataframe(
            filtered.sort_values("ts").reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            label="Download filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="sensor_log_filtered.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
