#!/usr/bin/env python3
"""
parser.py — load `data/penguins.csv`, run a quality report, apply this
project's missing-data strategies, and write the result to
`intermediate_data/penguins__parsed.csv` plus a `parsed_index.json`
manifest.

Trimmed to exactly what the Palmer Penguins example needs:
  - single-file CSV input (no --combine plumbing),
  - only the `median` and `drop_row` strategies,
  - non-interactive by default — `bash parse_input.sh` runs unattended.

Anything more exotic (multi-file mode, mean / mode / ffill / bfill /
constant fills, project-specific reorganisation) was removed when this
file was specialised for the example. Restore it from
`research-viz/assets/scaffolding/scripts/parser.py` if a follow-up
project needs it.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================================
# PROJECT-SPECIFIC CONFIG — Palmer Penguins.
#
# The four numeric columns each have 2 missing rows; we fill those with the
# column median (the gap is small enough that median is unbiased and it lets
# us keep the row's other observations).
#
# `sex` has 11 missing — large enough that imputation would be a real claim
# rather than a small fix; we drop those rows instead.
# ============================================================================

PROJECT_STRATEGIES: dict[str, str] = {
    "bill_length_mm": "median",
    "bill_depth_mm": "median",
    "flipper_length_mm": "median",
    "body_mass_g": "median",
    "sex": "drop_row",
}

# True so `bash parse_input.sh` (no flags) reproduces the cleaned CSV the
# project agreed on, without prompting for a strategy per column.
PROJECT_NONINTERACTIVE_DEFAULT: bool = True


# ============================================================================
# Quality report — printed to stdout each run for a sanity check.
# ============================================================================


def quality_report(df: pd.DataFrame) -> dict[str, Any]:
    """Per-column dtype, missing count, and unique count. Cell-type Counter
    on object columns is kept because penguins.csv has a mix of str / NaN
    in `sex` and we want that to surface."""
    report: dict[str, Any] = {"n_rows": len(df), "n_cols": len(df.columns), "columns": {}}
    for col in df.columns:
        s = df[col]
        info: dict[str, Any] = {
            "pandas_dtype": str(s.dtype),
            "n_missing": int(s.isna().sum()),
            "pct_missing": round(float(s.isna().mean() * 100), 2),
            "n_unique": int(s.nunique(dropna=True)),
        }
        if s.dtype == object:
            info["cell_type_counts"] = dict(Counter(type(v).__name__ for v in s.dropna()))
        report["columns"][col] = info
    return report


def print_report(report: dict[str, Any]) -> None:
    print(f"\n=== quality report — {report['n_rows']} rows, {report['n_cols']} columns ===\n")
    for col, info in report["columns"].items():
        bits = [f"{info['pandas_dtype']:<10}", f"missing={info['n_missing']:>3} ({info['pct_missing']:>4}%)"]
        if "cell_type_counts" in info:
            bits.append(f"cells={info['cell_type_counts']}")
        print(f"  {col:<20}  " + "  ".join(bits))
    print()


# ============================================================================
# Cleaning — only the two strategies this project uses.
# ============================================================================


def apply_strategy(df: pd.DataFrame, col: str, strategy: str) -> pd.DataFrame:
    """`median` for the four numeric columns; `drop_row` for `sex`. Anything
    else is a configuration mistake — fail loudly rather than silently no-op."""
    if strategy == "drop_row":
        return df.dropna(subset=[col])
    if strategy == "median":
        # Coerce defensively in case a stray non-numeric snuck in. The penguins
        # CSV is clean, so this is a no-op in practice.
        s = pd.to_numeric(df[col], errors="coerce")
        df = df.copy()
        df[col] = s.fillna(s.median())
        return df
    raise ValueError(
        f"strategy {strategy!r} for column {col!r} isn't supported by this trimmed parser. "
        "Only 'median' and 'drop_row' are implemented for the penguins example."
    )


def clean_frame(
    df: pd.DataFrame,
    report: dict[str, Any],
    strategy_overrides: dict[str, str],
    no_interactive: bool,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Apply the per-column strategy. With PROJECT_STRATEGIES baked in and
    PROJECT_NONINTERACTIVE_DEFAULT=True, every missing-value column is
    handled non-interactively from the dict above; columns without an
    entry are left untouched (`ignore`)."""
    strategies_applied: dict[str, str] = {}
    cols_with_missing = [c for c, info in report["columns"].items() if info["n_missing"] > 0]
    for col in cols_with_missing:
        if col in strategy_overrides:
            chosen = strategy_overrides[col]
        elif no_interactive:
            # Anything we didn't pre-decide: leave the NaNs alone rather than guess.
            chosen = "ignore"
        else:
            # Interactive fallback — kept as a thin escape hatch for one-off reruns.
            chosen = (input(f"  strategy for {col} [median/drop_row/ignore]: ").strip() or "ignore")
        if chosen == "ignore":
            strategies_applied[col] = "ignore"
            continue
        df = apply_strategy(df, col, chosen)
        strategies_applied[col] = chosen
    return df, strategies_applied


def parse_strategy_arg(raw: str | None) -> dict[str, str]:
    """Allow a one-off `--strategy '{"col":"median"}'` to layer on top of
    PROJECT_STRATEGIES without editing the file."""
    if not raw:
        return {}
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--strategy is not valid JSON: {e}")
    if not isinstance(d, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in d.items()):
        raise SystemExit("--strategy must be a JSON object of {column: strategy}")
    return d


# ============================================================================
# Main — single CSV in `data/`, single CSV out under `intermediate_data/`.
# ============================================================================


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", required=True, help="Directory containing penguins.csv")
    p.add_argument("--out", required=True, help="Directory to write parsed outputs into")
    p.add_argument(
        "--strategy",
        default=None,
        help='Override PROJECT_STRATEGIES with JSON like \'{"bill_length_mm":"median"}\'.',
    )
    p.add_argument(
        "--no-interactive",
        action="store_true",
        default=PROJECT_NONINTERACTIVE_DEFAULT,
        help="Skip prompts (default for this project).",
    )
    p.add_argument(
        "--interactive",
        dest="no_interactive",
        action="store_false",
        help="Force interactive prompts even though PROJECT_NONINTERACTIVE_DEFAULT is True.",
    )
    args = p.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Single-file project — the source is always penguins.csv. Keep the path
    # explicit so a future agent can grep for it; no auto-discovery needed.
    source = data_dir / "penguins.csv"
    if not source.exists():
        print(f"expected {source} but it doesn't exist", flush=True)
        return 1

    df = pd.read_csv(source)
    report = quality_report(df)
    print(f"loaded {source} ({len(df)} rows, {len(df.columns)} columns)")
    print_report(report)

    strategy_overrides: dict[str, str] = dict(PROJECT_STRATEGIES)
    strategy_overrides.update(parse_strategy_arg(args.strategy))
    print(f"strategies: {strategy_overrides}")

    df_clean, strategies_applied = clean_frame(df, report, strategy_overrides, args.no_interactive)

    # Naming convention: <dataset>__parsed.csv. The dataset stem is "penguins".
    target = out_dir / "penguins__parsed.csv"
    df_clean.to_csv(target, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"wrote {target}  ({len(df_clean)} rows, {len(df_clean.columns)} columns)")

    # parsed_index.json: a one-entry manifest. plot_gen and the streamlit pages
    # both consult `canonical_csv` to find this file rather than hard-coding it.
    timestamp = datetime.now().isoformat(timespec="seconds")
    parsed_index = {
        "generated_at": timestamp,
        "data_dir": str(data_dir),
        "single_file_input": True,
        "has_combined_csv": False,
        "combined_csv": None,
        "canonical_csv": "penguins__parsed.csv",
        "per_file_outputs": [
            {
                "source_file": str(source),
                "source_relative": "penguins.csv",
                "parsed_path": "penguins__parsed.csv",
                "n_rows": int(len(df_clean)),
                "n_cols": int(len(df_clean.columns)),
                "dtypes": {c: str(df_clean[c].dtype) for c in df_clean.columns},
                "strategies_applied": strategies_applied,
            }
        ],
    }
    (out_dir / "parsed_index.json").write_text(json.dumps(parsed_index, indent=2, default=str))
    print(f"wrote {out_dir/'parsed_index.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
