"""Page 3 — Pre-rendered gallery.

The "fall-back-to-PNG" pattern from the interactive subskill: instead of
recomputing charts on every interaction, this page picks a recipe slug from
a dropdown and shows the corresponding `plots/<slug>/figure.png` via
`st.image`. Useful as a printable gallery and as the pattern to use when
the underlying data is too heavy for live rendering.

The dropdown options come from `PROJECT_RECIPES` in `plot_gen.py` so the
gallery automatically picks up any new recipe the project adds.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
VIZ_ROOT = HERE.parent.parent
PLOTS_DIR = VIZ_ROOT / "plots"
CONTEXT_MD = VIZ_ROOT / "info" / "context.md"

sys.path.insert(0, str(VIZ_ROOT / "scripts"))
from plot_gen import PROJECT_RECIPES  # noqa: E402


st.set_page_config(page_title="Pre-rendered gallery", layout="wide")
st.title("Pre-rendered gallery")
st.caption(
    "Viewer for the static PNGs produced by `bash generate_plot.sh --all`. "
    "Use this pattern for charts whose underlying data is too large to "
    "re-render on every interaction."
)

# Build the menu from PROJECT_RECIPES, but only show recipes whose figure
# actually exists on disk (so a missing render doesn't crash the page).
available: dict[str, dict] = {}
for slug, recipe in PROJECT_RECIPES.items():
    fig = PLOTS_DIR / slug / "figure.png"
    if fig.exists():
        available[slug] = recipe

if not available:
    st.warning(
        "No rendered figures found under `plots/`. Run "
        "`bash visualizations/generate_plot.sh --all` first, then refresh."
    )
    st.stop()

slugs = list(available.keys())

# Pretty labels = recipe title where available, otherwise the slug itself.
def _label(slug: str) -> str:
    return available[slug].get("title", slug)


chosen = st.selectbox(
    "Pick a figure",
    options=slugs,
    format_func=_label,
    help="Each option is a recipe registered in `plot_gen.py`'s PROJECT_RECIPES.",
)

# ---- Display the figure + its spec ----------------------------------------
fig_path = PLOTS_DIR / chosen / "figure.png"
spec_path = PLOTS_DIR / chosen / "spec.json"

st.image(str(fig_path), use_column_width=True)
st.caption(_label(chosen))

c1, c2 = st.columns([3, 2])
with c1:
    if spec_path.exists():
        spec = json.loads(spec_path.read_text())
        st.markdown("**Recipe spec**")
        st.json(spec)
with c2:
    pdf_path = PLOTS_DIR / chosen / "figure.pdf"
    csv_path = PLOTS_DIR / chosen / "data.csv"
    st.markdown("**Other artifacts**")
    if pdf_path.exists():
        st.markdown(f"- PDF: `{pdf_path.relative_to(VIZ_ROOT.parent)}`")
    if csv_path.exists():
        st.markdown(f"- Tidy CSV: `{csv_path.relative_to(VIZ_ROOT.parent)}`")


# ---- Notes expander -------------------------------------------------------
with st.expander("Notes / data source"):
    st.markdown(
        "Renders are produced by `bash generate_plot.sh --all`. "
        "If you add a recipe to `plot_gen.py`'s `PROJECT_RECIPES`, re-run "
        "`--all` and the new entry shows up in the dropdown automatically."
    )
    if CONTEXT_MD.exists():
        st.markdown(CONTEXT_MD.read_text())
