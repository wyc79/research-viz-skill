"""Shared helpers for the flowers visualisation scripts.

Just one helper: a seaborn theme tuned for printable, colourblind-aware
research figures. Imported by plot_gen.py.
"""
from __future__ import annotations


def set_research_theme() -> None:
    """Seaborn `paper` context, white grid, colorblind palette, no top/right spines."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(context="paper", style="whitegrid", palette="colorblind")
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "font.family": "DejaVu Sans",
    })
