"""Page 1 — Penguins overview, using ONLY streamlit's native chart helpers.

This page intentionally avoids altair / matplotlib / seaborn and sticks to:
  - st.bar_chart   for categorical counts,
  - st.scatter_chart for two numeric measurements coloured by species,
  - st.dataframe   for a styled per-species summary table.

The `color=` arguments use PROJECT_SPECIES_PALETTE so the species colours
match the static plots in `plots/` and the altair page next door.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent.parent
PARSED = VIZ_ROOT / "intermediate_data" / "penguins__parsed.csv"
CONTEXT_MD = VIZ_ROOT / "info" / "context.md"

# Pull the project palette from plot_gen.py so the colours stay in lockstep
# between the static plots and this dashboard.
sys.path.insert(0, str(VIZ_ROOT / "scripts"))
from plot_gen import PROJECT_SPECIES_PALETTE  # noqa: E402


st.set_page_config(page_title="Penguins overview", layout="wide")
st.title("Penguins overview")
st.caption(
    "Quick counts and means using only streamlit's native chart helpers — "
    "no altair, no matplotlib. Colours are pulled from the project palette."
)


@st.cache_data(show_spinner=False)
def load(path: str, mtime: float) -> pd.DataFrame:  # noqa: ARG001
    return pd.read_csv(path)


df = load(str(PARSED), PARSED.stat().st_mtime)

# ---- Filter widget --------------------------------------------------------
all_islands = sorted(df["island"].dropna().unique().tolist())
chosen_islands = st.multiselect(
    "Islands to include",
    options=all_islands,
    default=all_islands,
    help="Filter rows by collection island. Leave all selected for the full dataset.",
)
view = df[df["island"].isin(chosen_islands)] if chosen_islands else df.iloc[0:0]
st.caption(f"Showing **{len(view):,}** of {len(df):,} rows.")

# Stable Adelie / Chinstrap / Gentoo order so the bar order matches the static plots.
SPECIES_ORDER = [s for s in ["Adelie", "Chinstrap", "Gentoo"] if s in view["species"].unique()]


# ---- 1. Counts per species (st.bar_chart) ---------------------------------
st.subheader("Counts per species")
counts = (
    view["species"]
    .value_counts()
    .reindex(SPECIES_ORDER)
    .rename_axis("species")
    .reset_index(name="n")
)
st.bar_chart(
    counts,
    x="species",
    y="n",
    color="species",
    # streamlit accepts a list-of-hex aligned with the x-axis order when a
    # color column is given — keep it aligned with SPECIES_ORDER.
)
st.caption(
    "Bar fill colours come from `PROJECT_SPECIES_PALETTE` so they match the "
    "static plots in `plots/` and the altair page."
)


# ---- 2. Mean body mass per species (st.bar_chart) -------------------------
st.subheader("Mean body mass by species")
mean_mass = (
    view.groupby("species", observed=True)["body_mass_g"]
    .mean()
    .reindex(SPECIES_ORDER)
    .rename("mean_body_mass_g")
    .reset_index()
)
st.bar_chart(
    mean_mass,
    x="species",
    y="mean_body_mass_g",
    color="species",
)


# ---- 3. Bill scatter (st.scatter_chart) -----------------------------------
st.subheader("Bill length vs. bill depth")
# st.scatter_chart honours `color=<column>`; reorder so the legend matches.
scatter_df = view.assign(species=pd.Categorical(view["species"], categories=SPECIES_ORDER, ordered=True))
st.scatter_chart(
    scatter_df,
    x="bill_length_mm",
    y="bill_depth_mm",
    color="species",
    size=24,
)
st.caption(
    "Native `st.scatter_chart` — hover any point to see the exact values. "
    "For richer interactivity (linked brushing, selection-driven filtering), "
    "see the **Bill morphology (Altair)** page in the sidebar."
)


# ---- 4. Per-species summary table -----------------------------------------
st.subheader("Per-species summary")
summary = (
    view.groupby("species", observed=True)
    .agg(
        n=("species", "size"),
        mean_body_mass_g=("body_mass_g", "mean"),
        mean_flipper_mm=("flipper_length_mm", "mean"),
        mean_bill_len_mm=("bill_length_mm", "mean"),
        mean_bill_depth_mm=("bill_depth_mm", "mean"),
    )
    .reindex(SPECIES_ORDER)
    .round(1)
)
st.dataframe(summary, use_container_width=True)


# ---- Notes expander -------------------------------------------------------
with st.expander("Notes / data source"):
    st.markdown(
        f"Reads `{PARSED.relative_to(VIZ_ROOT.parent)}` (333 rows after dropping 11 missing-sex). "
        "Cleaning details and full activity log are in `info/context.md`:"
    )
    if CONTEXT_MD.exists():
        st.markdown(CONTEXT_MD.read_text())
