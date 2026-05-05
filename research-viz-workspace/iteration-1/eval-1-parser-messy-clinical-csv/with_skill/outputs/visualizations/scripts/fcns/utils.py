"""Shared helpers used across parser.py, plotgen.py, and the streamlit pages."""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd


def detect_delimiter(path: Path, sample_size: int = 8192) -> str:
    """Sniff the delimiter for a delimited text file. Falls back to whitespace."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(sample_size)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t; |")
        return dialect.delimiter
    except csv.Error:
        # Last-ditch: if there are tabs in the first line, treat as TSV
        first = sample.splitlines()[0] if sample else ""
        if "\t" in first:
            return "\t"
        return r"\s+"


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(s: str, max_len: int = 60) -> str:
    """Turn an arbitrary string into a kebab-case filename-safe slug."""
    s = s.lower().strip()
    s = _SLUG_RE.sub("-", s).strip("-")
    return (s[:max_len].rstrip("-")) or "untitled"


def set_research_theme() -> None:
    """A reasonable default theme for research plots — readable, colorblind-aware, print-friendly."""
    import matplotlib.pyplot as plt  # local to keep import cost off the streamlit hot path
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


def load_cleaned(parsed_csv: str | Path) -> pd.DataFrame:
    """Load parsed_results.csv. Future-proofed: a single place to do conversions if needed."""
    df = pd.read_csv(parsed_csv)
    return df
