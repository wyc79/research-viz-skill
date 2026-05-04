#!/usr/bin/env python3
"""
plot_gen.py — generate a static research plot from parsed_results.csv based on a plain-English prompt.

This is a *starting point*. The agent calling the skill is expected to adapt the
`build_plot` function (or replace it entirely) for the specific request before
running. The bundled implementation handles a handful of common cases:

  - "scatter of <x> vs <y> [colored by <hue>] [log x|y]"
  - "violin of <y> [per <group>] [faceted by <facet>]"
  - "boxplot of <y> [per <group>]"
  - "histogram of <x> [bins=N]"
  - "correlation heatmap"
  - "line of <y> vs <x> [colored by <hue>]"

For anything else, edit `build_plot` to assemble whatever figure the user described,
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


def build_plot(df: pd.DataFrame, prompt: str, out_dir: Path) -> tuple[Path, Path]:
    """Build the plot described by `prompt`. Returns (png_path, csv_path)."""
    set_research_theme()
    spec = _parse_simple_grammar(prompt, df.columns.tolist())

    if spec["kind"] == "heatmap":
        numeric = df.select_dtypes(include="number")
        corr = numeric.corr()
        fig, ax = plt.subplots(figsize=(max(6, 0.5 * len(corr.columns)), max(5, 0.5 * len(corr.columns))))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, ax=ax, cbar_kws={"label": "Pearson r"})
        ax.set_title("Correlation heatmap (numeric columns)")
        tidy = corr.reset_index().melt(id_vars="index", var_name="column_b", value_name="r").rename(columns={"index": "column_a"})
    elif spec["kind"] == "scatter":
        if not spec["x"] or not spec["y"]:
            raise SystemExit(f"scatter needs both x and y columns; got {spec}. columns available: {list(df.columns)}")
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.scatterplot(data=df, x=spec["x"], y=spec["y"], hue=spec["hue"], ax=ax, s=24, alpha=0.85, edgecolor="none")
        ax.set_title(prompt.strip().rstrip("."))
        if spec["log_x"]:
            ax.set_xscale("log")
        if spec["log_y"]:
            ax.set_yscale("log")
        tidy = df[[c for c in [spec["x"], spec["y"], spec["hue"]] if c]].copy()
    elif spec["kind"] == "violin":
        if not spec["y"]:
            raise SystemExit(f"violin needs y column; got {spec}")
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.violinplot(data=df, x=spec["x"], y=spec["y"], hue=spec["hue"], inner="quartile", ax=ax)
        ax.set_title(prompt.strip().rstrip("."))
        tidy = df[[c for c in [spec["x"], spec["y"], spec["hue"]] if c]].copy()
    elif spec["kind"] == "box":
        if not spec["y"]:
            raise SystemExit(f"box needs y column; got {spec}")
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.boxplot(data=df, x=spec["x"], y=spec["y"], hue=spec["hue"], ax=ax)
        ax.set_title(prompt.strip().rstrip("."))
        tidy = df[[c for c in [spec["x"], spec["y"], spec["hue"]] if c]].copy()
    elif spec["kind"] == "hist":
        if not spec["y"] and not spec["x"]:
            raise SystemExit(f"histogram needs a column; got {spec}")
        col = spec["y"] or spec["x"]
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.histplot(data=df, x=col, hue=spec["hue"], kde=True, ax=ax)
        ax.set_title(prompt.strip().rstrip("."))
        tidy = df[[c for c in [col, spec["hue"]] if c]].copy()
    elif spec["kind"] == "line":
        if not spec["x"] or not spec["y"]:
            raise SystemExit(f"line needs x and y; got {spec}")
        fig, ax = plt.subplots(figsize=(8, 4.5))
        sns.lineplot(data=df, x=spec["x"], y=spec["y"], hue=spec["hue"], ax=ax)
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


def _resolve_data(args_data: str) -> Path:
    """Resolve --data to an existing CSV. If it points at parsed_results.csv but that doesn't
    exist (per-file mode without --combine concat), fall back to parsed_index.json with a helpful
    error message rather than a cryptic FileNotFoundError."""
    p = Path(args_data)
    if p.exists():
        return p
    # If the user pointed at intermediate_data/parsed_results.csv, look for the index.
    index = p.parent / "parsed_index.json" if p.name == "parsed_results.csv" else None
    if index and index.exists():
        idx = json.loads(index.read_text())
        if idx.get("per_file_outputs"):
            paths = [str(p.parent / e["parsed_path"]) for e in idx["per_file_outputs"]]
            raise SystemExit(
                f"{p} doesn't exist — the parser ran in per-file mode and wrote {len(paths)} per-file CSV(s):\n  "
                + "\n  ".join(paths[:10])
                + ("\n  ..." if len(paths) > 10 else "")
                + "\n\nPick one and pass --data <path>, or rerun the parser with --combine concat (or --combine both)."
            )
    raise SystemExit(f"--data not found: {p}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prompt", required=True, help="Plain-English plot description")
    p.add_argument(
        "--data",
        required=True,
        help="CSV to plot from. Default callers point at parsed_results.csv; in per-file mode "
        "pass the path to a specific per-file CSV under intermediate_data/.",
    )
    p.add_argument("--out", required=True, help="Root plots/ directory; a slug subfolder is created")
    p.add_argument("--slug", default=None, help="Override slug for the output subfolder")
    args = p.parse_args()

    data_path = _resolve_data(args.data)
    df = pd.read_csv(data_path)
    slug = args.slug or slugify(args.prompt)
    out_dir = Path(args.out) / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    png, csv = build_plot(df, args.prompt, out_dir)
    spec_path = out_dir / "spec.json"
    spec_path.write_text(json.dumps({"prompt": args.prompt, "data_source": str(data_path), "slug": slug}, indent=2))

    print(f"wrote {png}")
    print(f"wrote {csv}")
    print(f"wrote {spec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
