#!/usr/bin/env python3
"""
plot_gen.py — generate a static research plot from a cleaned CSV (default: the
canonical CSV listed in `intermediate_data/parsed_index.json`) based on a
plain-English prompt.

This is a *starting point*. Edit the `build_plot` function (or replace it
entirely) for plots beyond the bundled grammar. The bundled implementation
handles a handful of common cases:

  - "scatter of <x> vs <y> [colored by <hue>] [log x|y]"
  - "violin of <y> [per <group>] [faceted by <facet>]"
  - "boxplot of <y> [per <group>]"
  - "histogram of <x> [bins=N]"
  - "correlation heatmap"
  - "line of <y> vs <x> [colored by <hue>]"

For anything else, edit `build_plot` to assemble whatever figure you want,
saving the result to `<out>/<slug>/figure.png` and the underlying data to
`<out>/<slug>/data.csv`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers.utils import slugify, set_research_theme  # noqa: E402


# ============================================================================
# PROJECT-SPECIFIC CONFIG — edit this block for your dataset.
#
# Once you (or an agent) have produced plots the user is happy with, register
# each one here as a named recipe so `bash generate_plot.sh --recipe <slug>`
# reproduces it verbatim, and `bash generate_plot.sh --all` regenerates every
# plot the project keeps. Free-form `bash generate_plot.sh "<prompt>"` is still
# available for ad-hoc exploration.
# ============================================================================

# Project palette / styling — referenced from recipes below. Edit to taste.
# Pass any of these into `build_plot()` via the `extra` field on a recipe.
PROJECT_PALETTE: dict[str, str] = {
    # "species_setosa": "#4C78A8",
    # "species_versicolor": "#F58518",
    # "species_virginica": "#54A24B",
}

# Each recipe is keyed by its slug (the output folder name under plots/<slug>/).
# Required:    "prompt"   — the natural-language description fed to build_plot.
# Optional:    "data"     — path to a specific CSV; default is parsed_index.json's canonical_csv.
#              "extra"    — kwargs forwarded to build_plot (e.g. palette, figsize, log_x).
#
# Example after the agent has produced two plots for an iris-style dataset:
#
#     PROJECT_RECIPES = {
#         "petal-length-vs-width-by-species": {
#             "prompt": "scatter of petal_length vs petal_width colored by species",
#             "extra": {"palette": PROJECT_PALETTE},
#         },
#         "sepal-length-violin-per-species": {
#             "prompt": "violin of sepal_length per species",
#             "extra": {"palette": PROJECT_PALETTE},
#         },
#     }
PROJECT_RECIPES: dict[str, dict] = {}


# ============================================================================
# End of project-specific config.
# ============================================================================


def _parse_simple_grammar(prompt: str, columns: list[str]) -> dict:
    """Best-effort extract chart kind + columns from a prompt. Defaults to scatter when ambiguous."""
    p = prompt.lower()
    info: dict = {"kind": None, "x": None, "y": None, "hue": None, "facet": None, "log_x": False, "log_y": False}
    cols_lower = {c.lower(): c for c in columns}

    def find_col(token: str) -> str | None:
        token = token.strip().strip("`'\" ,.")
        return cols_lower.get(token)

    if "log x" in p or "log-x" in p:
        info["log_x"] = True
    if "log y" in p or "log-y" in p:
        info["log_y"] = True

    if "heatmap" in p or "correlation" in p:
        info["kind"] = "heatmap"
        return info
    if "violin" in p:
        info["kind"] = "violin"
    elif "box" in p:
        info["kind"] = "box"
    elif "hist" in p or "distribution" in p:
        info["kind"] = "hist"
    elif "line" in p or "time series" in p or "vs time" in p:
        info["kind"] = "line"
    else:
        info["kind"] = "scatter"

    m = re.search(r"of\s+([\w_]+)\s+vs\s+([\w_]+)", p)
    if m:
        info["x"] = find_col(m.group(2))
        info["y"] = find_col(m.group(1))
    else:
        m = re.search(r"of\s+([\w_]+)", p)
        if m:
            info["y"] = find_col(m.group(1))
        m = re.search(r"vs\s+([\w_]+)", p)
        if m:
            info["x"] = find_col(m.group(1))

    m = re.search(r"colou?red by\s+([\w_]+)", p) or re.search(r"by\s+([\w_]+)", p)
    if m:
        info["hue"] = find_col(m.group(1))
    m = re.search(r"facet(?:ed)? by\s+([\w_]+)", p)
    if m:
        info["facet"] = find_col(m.group(1))
    m = re.search(r"per\s+([\w_]+)", p)
    if m and info["kind"] in {"violin", "box"} and not info["x"]:
        info["x"] = find_col(m.group(1))

    return info


def build_plot(
    df: pd.DataFrame,
    prompt: str,
    out_dir: Path,
    *,
    palette: dict | str | None = None,
    figsize: tuple[float, float] | None = None,
    log_x: bool | None = None,
    log_y: bool | None = None,
) -> tuple[Path, Path]:
    """Build the plot described by `prompt`. Returns (png_path, csv_path).

    Recipe-friendly kwargs (`palette`, `figsize`, `log_x`, `log_y`) override the
    grammar-inferred defaults so PROJECT_RECIPES entries can pin styling.
    """
    set_research_theme()
    spec = _parse_simple_grammar(prompt, df.columns.tolist())
    if log_x is not None:
        spec["log_x"] = log_x
    if log_y is not None:
        spec["log_y"] = log_y

    if spec["kind"] == "heatmap":
        numeric = df.select_dtypes(include="number")
        corr = numeric.corr()
        fig, ax = plt.subplots(figsize=figsize or (max(6, 0.5 * len(corr.columns)), max(5, 0.5 * len(corr.columns))))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, ax=ax, cbar_kws={"label": "Pearson r"})
        ax.set_title("Correlation heatmap (numeric columns)")
        tidy = corr.reset_index().melt(id_vars="index", var_name="column_b", value_name="r").rename(columns={"index": "column_a"})
    elif spec["kind"] == "scatter":
        if not spec["x"] or not spec["y"]:
            raise SystemExit(f"scatter needs both x and y columns; got {spec}. columns available: {list(df.columns)}")
        fig, ax = plt.subplots(figsize=figsize or (7, 5))
        sns.scatterplot(data=df, x=spec["x"], y=spec["y"], hue=spec["hue"], palette=palette, ax=ax, s=24, alpha=0.85, edgecolor="none")
        ax.set_title(prompt.strip().rstrip("."))
        if spec["log_x"]:
            ax.set_xscale("log")
        if spec["log_y"]:
            ax.set_yscale("log")
        tidy = df[[c for c in [spec["x"], spec["y"], spec["hue"]] if c]].copy()
    elif spec["kind"] == "violin":
        if not spec["y"]:
            raise SystemExit(f"violin needs y column; got {spec}")
        fig, ax = plt.subplots(figsize=figsize or (7, 5))
        sns.violinplot(data=df, x=spec["x"], y=spec["y"], hue=spec["hue"], palette=palette, inner="quartile", ax=ax)
        ax.set_title(prompt.strip().rstrip("."))
        tidy = df[[c for c in [spec["x"], spec["y"], spec["hue"]] if c]].copy()
    elif spec["kind"] == "box":
        if not spec["y"]:
            raise SystemExit(f"box needs y column; got {spec}")
        fig, ax = plt.subplots(figsize=figsize or (7, 5))
        sns.boxplot(data=df, x=spec["x"], y=spec["y"], hue=spec["hue"], palette=palette, ax=ax)
        ax.set_title(prompt.strip().rstrip("."))
        tidy = df[[c for c in [spec["x"], spec["y"], spec["hue"]] if c]].copy()
    elif spec["kind"] == "hist":
        if not spec["y"] and not spec["x"]:
            raise SystemExit(f"histogram needs a column; got {spec}")
        col = spec["y"] or spec["x"]
        fig, ax = plt.subplots(figsize=figsize or (7, 4))
        sns.histplot(data=df, x=col, hue=spec["hue"], palette=palette, kde=True, ax=ax)
        ax.set_title(prompt.strip().rstrip("."))
        tidy = df[[c for c in [col, spec["hue"]] if c]].copy()
    elif spec["kind"] == "line":
        if not spec["x"] or not spec["y"]:
            raise SystemExit(f"line needs x and y; got {spec}")
        fig, ax = plt.subplots(figsize=figsize or (8, 4.5))
        sns.lineplot(data=df, x=spec["x"], y=spec["y"], hue=spec["hue"], palette=palette, ax=ax)
        ax.set_title(prompt.strip().rstrip("."))
        tidy = df[[c for c in [spec["x"], spec["y"], spec["hue"]] if c]].copy()
    else:
        raise SystemExit(f"unknown plot kind in spec {spec}")

    fig.tight_layout()
    png = out_dir / "figure.png"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(out_dir / "figure.pdf", bbox_inches="tight")
    plt.close(fig)
    csv = out_dir / "data.csv"
    tidy.to_csv(csv, index=False)
    return png, csv


def _resolve_data(args_data: str | None, intermediate: Path) -> Path:
    """Pick which CSV to plot from.

    If the user passed --data, use it (after a sanity check). Otherwise consult
    `parsed_index.json` and fall back to its `canonical_csv` field. If there is
    no canonical (multi-file per-file mode), list the available per-file outputs
    so the user can pick one.
    """
    if args_data:
        p = Path(args_data)
        if p.exists():
            return p
        raise SystemExit(f"--data not found: {p}")

    index_path = intermediate / "parsed_index.json"
    if not index_path.exists():
        raise SystemExit(
            f"no --data given and no parsed_index.json at {index_path}. "
            "Run parse_input.sh first, or pass --data <csv>."
        )
    idx = json.loads(index_path.read_text())
    canonical = idx.get("canonical_csv")
    if canonical:
        return intermediate / canonical
    # Multi-file per_file with no canonical — list options and ask for a pick.
    paths = [str(intermediate / e["parsed_path"]) for e in idx.get("per_file_outputs", [])]
    raise SystemExit(
        "the parser ran in per-file mode and produced no combined CSV; pass --data <one of>:\n  "
        + "\n  ".join(paths[:10])
        + ("\n  ..." if len(paths) > 10 else "")
    )


def _run_one(
    prompt: str,
    *,
    slug: str,
    data_path: Path,
    out_root: Path,
    extra: dict | None = None,
) -> None:
    """Render a single plot to <out_root>/<slug>/ and write spec.json."""
    df = pd.read_csv(data_path)
    out_dir = out_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    png, csv = build_plot(df, prompt, out_dir, **(extra or {}))
    spec_path = out_dir / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "prompt": prompt,
                "data_source": str(data_path),
                "slug": slug,
                "extra": extra or {},
            },
            indent=2,
            default=str,
        )
    )
    print(f"wrote {png}")
    print(f"wrote {csv}")
    print(f"wrote {spec_path}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--prompt", default=None, help="Plain-English plot description (ad-hoc).")
    mode.add_argument(
        "--recipe",
        default=None,
        help="Run a single named recipe from PROJECT_RECIPES (key in plot_gen.py).",
    )
    mode.add_argument(
        "--all",
        action="store_true",
        help="Run every recipe in PROJECT_RECIPES (regenerates all of the project's kept plots).",
    )
    mode.add_argument(
        "--list-recipes",
        action="store_true",
        help="Print the PROJECT_RECIPES keys and exit.",
    )
    p.add_argument(
        "--data",
        default=None,
        help="CSV to plot from. If omitted, the script reads parsed_index.json under "
        "--intermediate and uses its `canonical_csv` field. For recipes, the "
        "recipe's own `data` field takes precedence if set.",
    )
    p.add_argument(
        "--intermediate",
        default=None,
        help="Path to the visualizations/intermediate_data folder. Used to resolve --data when "
        "it isn't given.",
    )
    p.add_argument("--out", required=True, help="Root plots/ directory; a slug subfolder is created")
    p.add_argument("--slug", default=None, help="Override slug for the output subfolder (ad-hoc only)")
    args = p.parse_args()

    if args.list_recipes:
        if not PROJECT_RECIPES:
            print("(no recipes registered — see PROJECT_RECIPES at the top of plot_gen.py)")
        else:
            for slug, rec in PROJECT_RECIPES.items():
                print(f"  {slug:<40} {rec.get('prompt', '')}")
        return 0

    intermediate = Path(args.intermediate).resolve() if args.intermediate else Path.cwd()
    out_root = Path(args.out)

    def resolve_for(recipe_data: str | None) -> Path:
        if recipe_data:
            p = Path(recipe_data)
            if not p.is_absolute():
                p = intermediate / recipe_data
            if not p.exists():
                raise SystemExit(f"recipe data not found: {p}")
            return p
        return _resolve_data(args.data, intermediate)

    if args.all or args.recipe:
        if not PROJECT_RECIPES:
            raise SystemExit(
                "PROJECT_RECIPES is empty — register your project's plots in plot_gen.py "
                "before using --recipe / --all, or pass --prompt for an ad-hoc plot."
            )
        slugs = list(PROJECT_RECIPES.keys()) if args.all else [args.recipe]
        for slug in slugs:
            if slug not in PROJECT_RECIPES:
                raise SystemExit(
                    f"recipe '{slug}' not in PROJECT_RECIPES; available: {list(PROJECT_RECIPES)}"
                )
            rec = PROJECT_RECIPES[slug]
            prompt = rec["prompt"]
            data_path = resolve_for(rec.get("data"))
            _run_one(prompt, slug=slug, data_path=data_path, out_root=out_root, extra=rec.get("extra"))
        return 0

    if not args.prompt:
        raise SystemExit(
            "give one of: --prompt '<...>', --recipe <slug>, --all, or --list-recipes"
        )
    slug = args.slug or slugify(args.prompt)
    data_path = _resolve_data(args.data, intermediate)
    _run_one(args.prompt, slug=slug, data_path=data_path, out_root=out_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
