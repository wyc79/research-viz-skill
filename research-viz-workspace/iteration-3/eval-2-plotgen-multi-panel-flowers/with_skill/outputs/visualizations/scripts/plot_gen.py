#!/usr/bin/env python3
"""
plot_gen.py — generate the project's static research plots from
`intermediate_data/flowers__parsed.csv`.

Two recipes are baked in for the flowers dataset:

  petal-length-vs-width-by-species
      Scatter of petal_length (x) vs petal_width (y), coloured by species.

  sepal-length-violin-per-species
      Violin plot of sepal_length per species, with quartile lines inside.

Reproduce one with `bash generate_plot.sh --recipe <slug>` or regenerate
both with `bash generate_plot.sh --all`. Each recipe writes
`plots/<slug>/figure.png`, `figure.pdf`, `data.csv` (the tidy slice used)
and `spec.json` (the recipe spec for traceability).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers.utils import set_research_theme  # noqa: E402


# ============================================================================
# PROJECT-SPECIFIC CONFIG
# ============================================================================

# Colourblind-safe palette pinned to the three iris species so the same
# colour means the same species across both figures (and any future plot).
# Picked from seaborn's `colorblind` palette: blue / orange / green.
PROJECT_PALETTE: dict[str, str] = {
    "setosa":     "#0173B2",
    "versicolor": "#DE8F05",
    "virginica":  "#029E73",
}

# Stable species order — keeps legend / x-axis ordering consistent across plots.
SPECIES_ORDER = ["setosa", "versicolor", "virginica"]


def _scatter_petal_length_vs_width_by_species(df: pd.DataFrame, out_dir: Path) -> tuple[Path, Path]:
    """Scatter of petal_length vs petal_width, one colour per species."""
    set_research_theme()
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.scatterplot(
        data=df,
        x="petal_length",
        y="petal_width",
        hue="species",
        hue_order=SPECIES_ORDER,
        palette=PROJECT_PALETTE,
        s=42,
        alpha=0.85,
        edgecolor="white",
        linewidth=0.4,
        ax=ax,
    )
    ax.set_xlabel("Petal length (cm)")
    ax.set_ylabel("Petal width (cm)")
    ax.set_title("Petal length vs petal width, by species")
    ax.legend(title="Species")

    fig.tight_layout()
    png = out_dir / "figure.png"
    pdf = out_dir / "figure.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)

    # Persist the exact slice that backs the plot so the figure is reproducible
    # from data.csv alone.
    tidy = df[["species", "petal_length", "petal_width"]].copy()
    csv_path = out_dir / "data.csv"
    tidy.to_csv(csv_path, index=False)
    return png, csv_path


def _violin_sepal_length_per_species(df: pd.DataFrame, out_dir: Path) -> tuple[Path, Path]:
    """Violin of sepal_length grouped by species, with quartile lines."""
    set_research_theme()
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.violinplot(
        data=df,
        x="species",
        y="sepal_length",
        order=SPECIES_ORDER,
        hue="species",                # seaborn 0.13+ wants hue for per-group palette
        hue_order=SPECIES_ORDER,
        palette=PROJECT_PALETTE,
        legend=False,                 # seaborn 0.13: silence the redundant hue legend
        inner="quartile",
        ax=ax,
    )
    ax.set_xlabel("Species")
    ax.set_ylabel("Sepal length (cm)")
    ax.set_title("Sepal length distribution per species")

    fig.tight_layout()
    png = out_dir / "figure.png"
    pdf = out_dir / "figure.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)

    tidy = df[["species", "sepal_length"]].copy()
    csv_path = out_dir / "data.csv"
    tidy.to_csv(csv_path, index=False)
    return png, csv_path


# Map recipe slug -> (prompt, render function). The prompt is recorded into
# spec.json for traceability; the function does the actual drawing.
PROJECT_RECIPES: dict[str, dict] = {
    "petal-length-vs-width-by-species": {
        "prompt": "scatter of petal_length vs petal_width colored by species",
        "render": _scatter_petal_length_vs_width_by_species,
    },
    "sepal-length-violin-per-species": {
        "prompt": "violin plot of sepal_length per species",
        "render": _violin_sepal_length_per_species,
    },
}


# ============================================================================
# End of project-specific config.
# ============================================================================


def _resolve_data(intermediate: Path) -> Path:
    """Pick the canonical CSV listed in parsed_index.json (always present for
    this single-file project)."""
    index_path = intermediate / "parsed_index.json"
    if not index_path.exists():
        raise SystemExit(
            f"no parsed_index.json at {index_path}. Run parse_input.sh first."
        )
    idx = json.loads(index_path.read_text())
    canonical = idx.get("canonical_csv")
    if not canonical:
        raise SystemExit(f"parsed_index.json at {index_path} has no canonical_csv")
    return intermediate / canonical


def _run_one(slug: str, df: pd.DataFrame, out_root: Path) -> None:
    """Render one recipe to plots/<slug>/ and write spec.json."""
    rec = PROJECT_RECIPES[slug]
    out_dir = out_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    png, csv_path = rec["render"](df, out_dir)
    spec = {
        "prompt": rec["prompt"],
        "slug": slug,
        "palette": PROJECT_PALETTE,
        "species_order": SPECIES_ORDER,
    }
    spec_path = out_dir / "spec.json"
    spec_path.write_text(json.dumps(spec, indent=2, default=str))
    print(f"wrote {png}")
    print(f"wrote {csv_path}")
    print(f"wrote {spec_path}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--recipe", default=None, help="Run a single recipe by slug.")
    mode.add_argument("--all", action="store_true", help="Run every recipe in PROJECT_RECIPES.")
    mode.add_argument("--list-recipes", action="store_true", help="Print the recipe slugs and exit.")
    p.add_argument("--intermediate", required=True, help="Path to the intermediate_data folder.")
    p.add_argument("--out", required=True, help="Root plots/ directory.")
    args = p.parse_args()

    if args.list_recipes:
        for slug, rec in PROJECT_RECIPES.items():
            print(f"  {slug:<40} {rec['prompt']}")
        return 0

    intermediate = Path(args.intermediate).resolve()
    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    data_path = _resolve_data(intermediate)
    df = pd.read_csv(data_path)

    if args.recipe:
        if args.recipe not in PROJECT_RECIPES:
            raise SystemExit(
                f"recipe '{args.recipe}' not in PROJECT_RECIPES; available: {list(PROJECT_RECIPES)}"
            )
        _run_one(args.recipe, df, out_root)
        return 0

    if args.all:
        for slug in PROJECT_RECIPES:
            _run_one(slug, df, out_root)
        return 0

    raise SystemExit("give one of: --recipe <slug>, --all, or --list-recipes")


if __name__ == "__main__":
    raise SystemExit(main())
