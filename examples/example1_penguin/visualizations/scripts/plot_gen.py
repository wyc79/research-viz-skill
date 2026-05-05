#!/usr/bin/env python3
"""
plot_gen.py — render the Palmer Penguins project's named plots.

This file is the project's plot recipe. Every figure in `plots/` is one of
the seven entries in `PROJECT_RECIPES` below. The project's palettes and
the no-grids theme (`set_research_theme` in helpers/utils.py) are baked in
once and reused everywhere.

Two coordinated palettes:
  - PROJECT_SPECIES_PALETTE: a colorblind-safe categorical palette mapping
    each species to a stable hex (so the same species always plots in the
    same colour across figures and the streamlit pages).
  - PROJECT_MONOCHROME: a single-hue (blue) palette + matching sequential
    colormap, used by histograms and the correlation heatmap.

Trimmed: the original scaffold's prompt-grammar parser, scatter / line
branches, free-form `--prompt` mode, and the `--data` override are gone.
This file only renders the seven recipes the project ships.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from statannotations.Annotator import Annotator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers.utils import set_research_theme  # noqa: E402


# ============================================================================
# PROJECT PALETTES
# ============================================================================

# Colorblind-safe categorical palette (lifted from seaborn's "colorblind" set —
# Adelie / Chinstrap / Gentoo are the only categories this project plots, so
# pinning hex codes per species means the same colour appears everywhere).
PROJECT_SPECIES_PALETTE: dict[str, str] = {
    "Adelie":    "#0173B2",  # blue
    "Chinstrap": "#DE8F05",  # orange
    "Gentoo":    "#029E73",  # green
}

# Monochrome single-hue palette — used for plots with no categorical hue
# (single-distribution histograms, correlation heatmap). Sequential `Blues`
# colormap pairs with the species blue so the two palettes feel related.
PROJECT_MONOCHROME = {
    "fill":     "#3B7BB5",  # mid-blue, matches Blues_r mid-tone
    "edge":     "#1F4E79",  # darker blue for histogram edges
    "cmap":     "Blues",    # sequential single-hue colormap for the heatmap
}


# ============================================================================
# PROJECT_RECIPES — every figure this project ships.
#
# Each recipe is keyed by its slug (the output folder name under plots/<slug>/).
# `kind` selects the renderer below; `kwargs` are passed through.
# ============================================================================

PROJECT_RECIPES: dict[str, dict] = {
    # ---- Colorblind-safe set: comparisons between species / islands ----
    "bill_length-vs-bill_depth-by-species": {
        "kind": "scatter_species",
        "title": "Bill length vs. bill depth, by species",
        "x": "bill_length_mm",
        "y": "bill_depth_mm",
    },
    "body_mass-violin-per-species": {
        "kind": "violin_species",
        "title": "Body mass distribution, per species",
        "y": "body_mass_g",
    },
    "flipper_length-box-per-island": {
        "kind": "box_island",
        "title": "Flipper length distribution, per island",
        "y": "flipper_length_mm",
    },

    # ---- Monochrome set: single-distribution / single-variable plots ----
    "body_mass-histogram-monochrome": {
        "kind": "hist_mono",
        "title": "Body mass — overall distribution",
        "x": "body_mass_g",
        "xlabel": "Body mass (g)",
    },
    "flipper_length-histogram-monochrome": {
        "kind": "hist_mono",
        "title": "Flipper length — overall distribution",
        "x": "flipper_length_mm",
        "xlabel": "Flipper length (mm)",
    },
    "correlation-heatmap-monochrome": {
        "kind": "corr_heatmap_mono",
        "title": "Correlation of numeric measurements",
    },

    # ---- Statistics-overlay variant of the violin (uses the saved t-test) ----
    "body_mass-violin-per-species-with-ttest": {
        "kind": "violin_species_ttest",
        "title": "Body mass per species (Welch's t-test: Adelie vs Gentoo)",
        "y": "body_mass_g",
        # Slug of the test under significance/ — its .json carries the p-value.
        "ttest_slug": "body_mass_g-adelie-vs-gentoo-ttest",
    },
}


# ============================================================================
# Renderers — one per `kind`. Each returns (png_path, csv_path).
# ============================================================================


def _save(fig: plt.Figure, out_dir: Path) -> Path:
    """Write figure.png + figure.pdf into out_dir, return the PNG path."""
    fig.tight_layout()
    png = out_dir / "figure.png"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(out_dir / "figure.pdf", bbox_inches="tight")
    plt.close(fig)
    return png


def _species_order(df: pd.DataFrame) -> list[str]:
    """Stable Adelie / Chinstrap / Gentoo order whenever a row exists for it.
    Keeps the legend order matching PROJECT_SPECIES_PALETTE."""
    desired = ["Adelie", "Chinstrap", "Gentoo"]
    present = set(df["species"].dropna().unique())
    return [s for s in desired if s in present]


def render_scatter_species(df: pd.DataFrame, out_dir: Path, *, x: str, y: str, title: str) -> tuple[Path, Path]:
    """Scatter of two numeric columns, points coloured by species."""
    order = _species_order(df)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    sns.scatterplot(
        data=df,
        x=x, y=y,
        hue="species", hue_order=order,
        palette=PROJECT_SPECIES_PALETTE,
        s=28, alpha=0.85, edgecolor="none",
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel(x.replace("_", " ").replace(" mm", " (mm)"))
    ax.set_ylabel(y.replace("_", " ").replace(" mm", " (mm)"))
    ax.legend(title="Species", loc="best")
    png = _save(fig, out_dir)
    tidy = df[[x, y, "species"]].copy()
    csv = out_dir / "data.csv"
    tidy.to_csv(csv, index=False)
    return png, csv


def render_violin_species(df: pd.DataFrame, out_dir: Path, *, y: str, title: str) -> tuple[Path, Path]:
    """Per-species violin of one numeric column, quartile lines inside."""
    order = _species_order(df)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    sns.violinplot(
        data=df,
        x="species", y=y, order=order,
        hue="species", hue_order=order,
        palette=PROJECT_SPECIES_PALETTE,
        inner="quartile", legend=False,
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel("Species")
    ax.set_ylabel(y.replace("_", " ").replace(" g", " (g)").replace(" mm", " (mm)"))
    png = _save(fig, out_dir)
    tidy = df[["species", y]].copy()
    csv = out_dir / "data.csv"
    tidy.to_csv(csv, index=False)
    return png, csv


def render_box_island(df: pd.DataFrame, out_dir: Path, *, y: str, title: str) -> tuple[Path, Path]:
    """Per-island boxplot of one numeric column. Islands aren't species, so we
    use the monochrome fill (single hue) — the box geometry alone tells the
    story; colour would only repeat the x-axis."""
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    sns.boxplot(
        data=df,
        x="island", y=y,
        color=PROJECT_MONOCHROME["fill"],
        width=0.55, fliersize=3,
        ax=ax,
    )
    # Slightly darker median line for legibility against the mid-blue body.
    for patch in ax.patches:
        patch.set_edgecolor(PROJECT_MONOCHROME["edge"])
    ax.set_title(title)
    ax.set_xlabel("Island")
    ax.set_ylabel(y.replace("_", " ").replace(" mm", " (mm)"))
    png = _save(fig, out_dir)
    tidy = df[["island", y]].copy()
    csv = out_dir / "data.csv"
    tidy.to_csv(csv, index=False)
    return png, csv


def render_hist_mono(df: pd.DataFrame, out_dir: Path, *, x: str, xlabel: str, title: str) -> tuple[Path, Path]:
    """Single-hue histogram. No KDE overlay — the project style guide prefers
    the bare histogram for these single-variable distributions."""
    fig, ax = plt.subplots(figsize=(6.5, 4))
    sns.histplot(
        data=df,
        x=x, bins=24,
        color=PROJECT_MONOCHROME["fill"],
        edgecolor=PROJECT_MONOCHROME["edge"],
        kde=False,
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    png = _save(fig, out_dir)
    tidy = df[[x]].copy()
    csv = out_dir / "data.csv"
    tidy.to_csv(csv, index=False)
    return png, csv


def render_corr_heatmap_mono(df: pd.DataFrame, out_dir: Path, *, title: str) -> tuple[Path, Path]:
    """Pearson correlation heatmap on the four numeric columns + year. Single-
    hue `Blues` cmap (sequential) so saturation reads as |r| — keeps the
    monochrome theme even though there are negative correlations (the heatmap
    bottoms out at light-blue near zero rather than crossing a hue boundary).
    """
    numeric = df.select_dtypes(include="number")
    corr = numeric.corr()
    n = len(corr.columns)
    fig, ax = plt.subplots(figsize=(max(5, 0.7 * n) + 0.5, max(4, 0.7 * n)))
    sns.heatmap(
        corr.abs(),
        annot=corr,            # show signed r in cells…
        fmt=".2f",
        cmap=PROJECT_MONOCHROME["cmap"],   # …but colour by |r| for monochrome
        vmin=0, vmax=1,
        cbar_kws={"label": "|Pearson r|"},
        ax=ax,
    )
    ax.set_title(title)
    png = _save(fig, out_dir)
    tidy = corr.reset_index().melt(id_vars="index", var_name="column_b", value_name="r").rename(columns={"index": "column_a"})
    csv = out_dir / "data.csv"
    tidy.to_csv(csv, index=False)
    return png, csv


def render_violin_species_ttest(
    df: pd.DataFrame,
    out_dir: Path,
    *,
    y: str,
    title: str,
    ttest_slug: str,
    significance_root: Path,
) -> tuple[Path, Path]:
    """Violin per species with the Welch's t-test bracket between Adelie and
    Gentoo overlaid. Reads the saved p-value from `significance/<slug>.json`
    so the figure and the test can never disagree — the test is the source
    of truth."""
    order = _species_order(df)
    fig, ax = plt.subplots(figsize=(6.5, 5))
    sns.violinplot(
        data=df,
        x="species", y=y, order=order,
        hue="species", hue_order=order,
        palette=PROJECT_SPECIES_PALETTE,
        inner="quartile", legend=False,
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel("Species")
    ax.set_ylabel(y.replace("_", " ").replace(" g", " (g)"))

    # Pull the p-value from significance/<slug>.json (written by significance.py).
    ttest_json = significance_root / f"{ttest_slug}.json"
    if not ttest_json.exists():
        raise SystemExit(
            f"missing {ttest_json}. Run `python visualizations/scripts/significance.py` first "
            "so this recipe can read the saved p-value."
        )
    ttest = json.loads(ttest_json.read_text())
    p = float(ttest["p_value"])

    pairs = [("Adelie", "Gentoo")]
    annot = Annotator(ax, pairs, data=df, x="species", y=y, order=order)
    # `loc="inside"` keeps the bracket inside the axes so it doesn't get
    # clipped by tight_layout. `verbose=0` suppresses statannotations chatter.
    annot.configure(test=None, text_format="star", loc="inside", verbose=0)
    annot.set_pvalues_and_annotate(pvalues=[p])

    png = _save(fig, out_dir)
    tidy = df[["species", y]].copy()
    csv = out_dir / "data.csv"
    tidy.to_csv(csv, index=False)
    return png, csv


# ============================================================================
# Dispatch
# ============================================================================


def _resolve_canonical(intermediate: Path) -> Path:
    idx_path = intermediate / "parsed_index.json"
    if not idx_path.exists():
        raise SystemExit(f"no parsed_index.json at {idx_path}. Run parse_input.sh first.")
    idx = json.loads(idx_path.read_text())
    canonical = idx["canonical_csv"]
    return intermediate / canonical


def _run_one(slug: str, recipe: dict, df: pd.DataFrame, out_root: Path, significance_root: Path) -> None:
    out_dir = out_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    set_research_theme()

    kind = recipe["kind"]
    if kind == "scatter_species":
        png, csv = render_scatter_species(df, out_dir, x=recipe["x"], y=recipe["y"], title=recipe["title"])
    elif kind == "violin_species":
        png, csv = render_violin_species(df, out_dir, y=recipe["y"], title=recipe["title"])
    elif kind == "box_island":
        png, csv = render_box_island(df, out_dir, y=recipe["y"], title=recipe["title"])
    elif kind == "hist_mono":
        png, csv = render_hist_mono(df, out_dir, x=recipe["x"], xlabel=recipe["xlabel"], title=recipe["title"])
    elif kind == "corr_heatmap_mono":
        png, csv = render_corr_heatmap_mono(df, out_dir, title=recipe["title"])
    elif kind == "violin_species_ttest":
        png, csv = render_violin_species_ttest(
            df, out_dir,
            y=recipe["y"], title=recipe["title"],
            ttest_slug=recipe["ttest_slug"],
            significance_root=significance_root,
        )
    else:
        raise SystemExit(f"unknown recipe kind: {kind}")

    spec_path = out_dir / "spec.json"
    spec_path.write_text(json.dumps({"slug": slug, **recipe}, indent=2))
    print(f"  {slug:<46}  {png}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--recipe", default=None, help="Render one recipe by slug.")
    mode.add_argument("--all", action="store_true", help="Render every recipe.")
    mode.add_argument("--list-recipes", action="store_true", help="Print every recipe's slug + title and exit.")
    p.add_argument("--intermediate", required=True, help="visualizations/intermediate_data path")
    p.add_argument("--out", required=True, help="visualizations/plots path")
    p.add_argument("--significance", default=None, help="visualizations/significance path (defaults next to --out)")
    args = p.parse_args()

    if args.list_recipes:
        for slug, rec in PROJECT_RECIPES.items():
            print(f"  {slug:<46}  {rec.get('title', '')}")
        return 0

    intermediate = Path(args.intermediate).resolve()
    out_root = Path(args.out).resolve()
    significance_root = Path(args.significance).resolve() if args.significance else out_root.parent / "significance"

    df = pd.read_csv(_resolve_canonical(intermediate))

    if args.all:
        slugs = list(PROJECT_RECIPES.keys())
    elif args.recipe:
        if args.recipe not in PROJECT_RECIPES:
            raise SystemExit(f"unknown recipe {args.recipe!r}; available: {list(PROJECT_RECIPES)}")
        slugs = [args.recipe]
    else:
        raise SystemExit("give one of: --all, --recipe <slug>, --list-recipes")

    print(f"rendering {len(slugs)} recipe(s) into {out_root}/")
    for slug in slugs:
        _run_one(slug, PROJECT_RECIPES[slug], df, out_root, significance_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
