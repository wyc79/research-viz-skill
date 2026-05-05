"""Shared helpers used across parser.py, plot_gen.py, and the streamlit pages.

Trimmed for the Palmer Penguins example — only `slugify` (used by plot_gen
to derive recipe folder names from prompts), `set_research_theme` (the
no-grids/colorblind/monochrome theme this project ships), and `load_cleaned`
survive. The `detect_delimiter` helper from the original scaffold was
removed because the example only ever loads `penguins.csv`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(s: str, max_len: int = 60) -> str:
    """Turn an arbitrary prompt into a kebab-case folder name for `plots/<slug>/`."""
    s = s.lower().strip()
    s = _SLUG_RE.sub("-", s).strip("-")
    return (s[:max_len].rstrip("-")) or "untitled"


def set_research_theme() -> None:
    """The Palmer Penguins project theme.

    Two project-specific decisions are encoded here:
      1. **Grids OFF.** `style="ticks"` (not "whitegrid") and an explicit
         `axes.grid = False` rcParam — the project's style guide calls for
         clean axis ticks with no gridlines on any plot.
      2. **Colorblind-aware base palette** for any chart that uses
         `palette=...` without specifying one explicitly. Per-recipe palette
         choices (the species map and the monochrome single-hue) are
         imported from plot_gen.py's PROJECT_PALETTE — this just sets the
         default the seaborn primitives reach for when nothing's passed in.
    """
    import matplotlib.pyplot as plt  # local to keep import cost off the streamlit hot path
    import seaborn as sns

    sns.set_theme(context="paper", style="ticks", palette="colorblind")
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        # Project rule: no grids on any figure.
        "axes.grid": False,
        # Open-frame look — top/right spines off, frameless legend.
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "font.family": "DejaVu Sans",
    })


def load_cleaned(parsed_csv: str | Path) -> pd.DataFrame:
    """Load `intermediate_data/penguins__parsed.csv` (or any later-stage CSV
    following the same `<dataset>__<stage>.csv` convention)."""
    return pd.read_csv(parsed_csv)
