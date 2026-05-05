"""Streamlit dashboard for sensor log data.

Run via: ./interactive_page.sh
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "sensor_log.csv"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    """Read the sensor log CSV and parse types."""
    df = pd.read_csv(path)
    df["ts"] = pd.to_datetime(df["ts"])
    # `ok` is read as the strings "True"/"False" — coerce to bool.
    if df["ok"].dtype == object:
        df["ok"] = df["ok"].astype(str).str.strip().str.lower().map(
            {"true": True, "false": False}
        )
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def main() -> None:
    st.set_page_config(page_title="Sensor Log Dashboard", layout="wide")
    st.title("Sensor Log Dashboard")
    st.caption(f"Source: `{DATA_PATH.relative_to(Path(__file__).parent)}`")

    if not DATA_PATH.exists():
        st.error(f"Could not find data file: {DATA_PATH}")
        st.stop()

    df = load_data(DATA_PATH)

    sites = sorted(df["site"].dropna().unique().tolist())
    sensors = sorted(df["sensor"].dropna().unique().tolist())

    st.sidebar.header("Filters")
    selected_sites = st.sidebar.multiselect(
        "Site", options=sites, default=sites,
    )
    selected_sensors = st.sidebar.multiselect(
        "Sensor", options=sensors, default=sensors,
    )

    only_ok = st.sidebar.checkbox("Only show readings with ok=True", value=False)

    min_ts = df["ts"].min().to_pydatetime()
    max_ts = df["ts"].max().to_pydatetime()
    date_range = st.sidebar.slider(
        "Time range",
        min_value=min_ts,
        max_value=max_ts,
        value=(min_ts, max_ts),
        format="YYYY-MM-DD HH:mm",
    )

    mask = (
        df["site"].isin(selected_sites)
        & df["sensor"].isin(selected_sensors)
        & df["ts"].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
    )
    if only_ok:
        mask &= df["ok"] == True  # noqa: E712 — explicit boolean compare

    filtered = df.loc[mask].copy()

    # ----- Summary metrics -----
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(filtered):,}")
    c2.metric(
        "Mean value",
        f"{filtered['value'].mean():.2f}" if len(filtered) else "—",
    )
    c3.metric(
        "Min / Max",
        (
            f"{filtered['value'].min():.1f} / {filtered['value'].max():.1f}"
            if len(filtered)
            else "—"
        ),
    )
    ok_rate = (
        f"{filtered['ok'].mean() * 100:.1f}%" if len(filtered) else "—"
    )
    c4.metric("ok rate", ok_rate)

    if filtered.empty:
        st.warning("No rows match the current filters.")
        st.stop()

    # ----- Time series chart -----
    st.subheader("Value over time")

    # Pivot so each (site, sensor) pair is its own line. Streamlit's line_chart
    # will draw one line per column.
    chart_df = (
        filtered.assign(series=filtered["site"] + " · " + filtered["sensor"])
        .pivot_table(index="ts", columns="series", values="value", aggfunc="mean")
        .sort_index()
    )
    st.line_chart(chart_df, height=420)

    # ----- Per-sensor average chart -----
    st.subheader("Average value by sensor")
    by_sensor = (
        filtered.groupby("sensor")["value"].mean().sort_values(ascending=False)
    )
    st.bar_chart(by_sensor)

    # ----- Raw data -----
    with st.expander("Show filtered rows"):
        st.dataframe(
            filtered.sort_values("ts").reset_index(drop=True),
            use_container_width=True,
            height=360,
        )


if __name__ == "__main__":
    main()
