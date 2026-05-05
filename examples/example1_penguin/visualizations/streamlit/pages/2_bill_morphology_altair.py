"""Page 2 — Bill morphology (Altair).

Two altair charts side-by-side with **linked brushing**: drag a rectangle on
the bill-length-vs-bill-depth scatter and the body-mass histogram on the
right re-renders to show only the brushed points. The legend on the right
is also a clickable selector — click a species to filter both charts to it.

Colour encoding uses PROJECT_SPECIES_PALETTE (imported from plot_gen.py) so
species colours stay consistent across the static plots, page 1, and here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent.parent
PARSED = VIZ_ROOT / "intermediate_data" / "penguins__parsed.csv"
CONTEXT_MD = VIZ_ROOT / "info" / "context.md"

sys.path.insert(0, str(VIZ_ROOT / "scripts"))
from plot_gen import PROJECT_SPECIES_PALETTE  # noqa: E402


st.set_page_config(page_title="Bill morphology (Altair)", layout="wide")
st.title("Bill morphology — interactive (Altair)")
st.caption(
    "Drag a rectangle on the scatter to filter the histogram on the right; "
    "click a species in the legend to focus on it (shift-click to add)."
)


@st.cache_data(show_spinner=False)
def load(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001
    return pd.read_csv(path)


df = load(str(PARSED), PARSED.stat().st_mtime)

# ---- Sidebar filter -------------------------------------------------------
all_islands = sorted(df["island"].dropna().unique().tolist())
chosen_islands = st.multiselect(
    "Islands",
    options=all_islands,
    default=all_islands,
    help="Filter rows by collection island before rendering the charts below.",
)
view = df[df["island"].isin(chosen_islands)] if chosen_islands else df.iloc[0:0]
st.caption(f"**{len(view):,}** rows after the island filter.")
if len(view) == 0:
    st.stop()

# Stable order so legends/colours match across pages.
SPECIES_ORDER = [s for s in ["Adelie", "Chinstrap", "Gentoo"] if s in view["species"].unique()]
SPECIES_COLORS = [PROJECT_SPECIES_PALETTE[s] for s in SPECIES_ORDER]
species_scale = alt.Scale(domain=SPECIES_ORDER, range=SPECIES_COLORS)

# ---- Selections -----------------------------------------------------------
brush = alt.selection_interval(name="brush", encodings=["x", "y"])
legend_pick = alt.selection_point(fields=["species"], bind="legend")

# ---- Scatter (left) -------------------------------------------------------
scatter = (
    alt.Chart(view)
    .mark_circle(size=60, opacity=0.85)
    .encode(
        x=alt.X("bill_length_mm:Q", title="Bill length (mm)", scale=alt.Scale(zero=False)),
        y=alt.Y("bill_depth_mm:Q", title="Bill depth (mm)", scale=alt.Scale(zero=False)),
        color=alt.condition(
            legend_pick,
            alt.Color("species:N", scale=species_scale, title="Species"),
            alt.value("#dddddd"),
        ),
        tooltip=[
            alt.Tooltip("species:N"),
            alt.Tooltip("island:N"),
            alt.Tooltip("bill_length_mm:Q", format=".1f"),
            alt.Tooltip("bill_depth_mm:Q", format=".1f"),
            alt.Tooltip("body_mass_g:Q", format=".0f", title="Body mass (g)"),
        ],
    )
    .add_params(brush, legend_pick)
    .properties(title="Bill length vs. depth (drag to brush)", height=380)
)

# ---- Histogram (right) — linked to the scatter via `brush` ----------------
hist = (
    alt.Chart(view)
    .mark_bar(opacity=0.85)
    .encode(
        x=alt.X(
            "body_mass_g:Q",
            bin=alt.Bin(maxbins=24),
            title="Body mass (g)",
            scale=alt.Scale(zero=False),
        ),
        y=alt.Y("count():Q", title="Count of brushed penguins"),
        color=alt.Color("species:N", scale=species_scale, title="Species"),
        tooltip=[alt.Tooltip("species:N"), alt.Tooltip("count():Q")],
    )
    .transform_filter(brush)
    .transform_filter(legend_pick)
    .properties(title="Body mass — only brushed points", height=380)
)

st.altair_chart(scatter | hist, use_container_width=True)


# ---- Notes expander -------------------------------------------------------
with st.expander("Notes / data source"):
    st.markdown(
        f"Reads `{PARSED.relative_to(VIZ_ROOT.parent)}`. "
        "Linked brushing is wired with `alt.selection_interval` on the scatter "
        "and `transform_filter(brush)` on the histogram. Legend filtering uses "
        "`alt.selection_point(bind='legend')`."
    )
    if CONTEXT_MD.exists():
        st.markdown(CONTEXT_MD.read_text())
