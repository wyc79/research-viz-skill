#!/usr/bin/env python3
"""
parser.py — read raw tabular files, run quality checks, handle missing data,
write a single cleaned `parsed_results.csv` plus a tiny meta JSON.

Designed to be both:
  - **interactive** — prompts the user per column for a missing-data strategy, and
  - **scriptable** — accepts `--strategy '{"col":"mean", ...}'` and runs unattended.

Adapt this script for the specific dataset (e.g. add custom dtype coercions,
drop garbage columns, parse weird date formats) but keep the high-level shape
so future reruns are predictable.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Place this script's parent on sys.path so we can import fcns.utils
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fcns.utils import detect_delimiter, slugify  # noqa: E402

VALID_STRATEGIES = {"ignore", "drop_row", "drop_col", "mean", "median", "mode", "ffill", "bfill"}
# `constant:<value>` is also valid — checked separately.


def find_input_files(data_dir: Path) -> list[Path]:
    """Recursively find tabular files under data_dir."""
    extensions = {".csv", ".tsv", ".txt", ".xlsx", ".xls"}
    out: list[Path] = []
    for p in sorted(data_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in extensions:
            out.append(p)
    return out


def load_one(path: Path) -> pd.DataFrame:
    """Load a single file into a DataFrame, sniffing delimiter for .txt."""
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t")
    if suffix == ".txt":
        delim = detect_delimiter(path)
        return pd.read_csv(path, sep=delim)
    raise ValueError(f"unsupported file type: {path}")


def quality_report(df: pd.DataFrame) -> dict[str, Any]:
    """Return a dict describing column-level quality: dtype consistency, missing counts, format anomalies."""
    report: dict[str, Any] = {"n_rows": len(df), "n_cols": len(df.columns), "columns": {}}
    for col in df.columns:
        s = df[col]
        col_info: dict[str, Any] = {
            "pandas_dtype": str(s.dtype),
            "n_missing": int(s.isna().sum()),
            "pct_missing": round(float(s.isna().mean() * 100), 2),
            "n_unique": int(s.nunique(dropna=True)),
        }
        # Per-cell type heterogeneity (only meaningful for object dtype)
        if s.dtype == object:
            cell_types = Counter(type(v).__name__ for v in s.dropna())
            col_info["cell_type_counts"] = dict(cell_types)
            if len(cell_types) > 1:
                col_info["heterogeneous"] = True
                # Try to coerce to numeric — if most cells are numeric and a few are strings, flag it
                coerced = pd.to_numeric(s, errors="coerce")
                if coerced.notna().sum() > 0 and coerced.isna().sum() > s.isna().sum():
                    col_info["coercible_to_numeric_count"] = int(coerced.notna().sum())
                    col_info["non_numeric_examples"] = (
                        s[coerced.isna() & s.notna()].astype(str).head(5).tolist()
                    )
        # Date-like check: if column name hints at a date but dtype isn't datetime, flag
        name_lower = col.lower()
        if any(k in name_lower for k in ("date", "time", "timestamp")) and not np.issubdtype(s.dtype, np.datetime64):
            col_info["likely_datetime_column_but_not_parsed"] = True
        report["columns"][col] = col_info
    return report


def print_report(report: dict[str, Any]) -> None:
    print(f"\n=== quality report — {report['n_rows']} rows, {report['n_cols']} columns ===\n")
    for col, info in report["columns"].items():
        bits = [f"{info['pandas_dtype']:<10}", f"missing={info['n_missing']:>6} ({info['pct_missing']:>5}%)"]
        if info.get("heterogeneous"):
            bits.append(f"⚠ mixed types {info['cell_type_counts']}")
        if info.get("non_numeric_examples"):
            bits.append(f"non-numeric e.g. {info['non_numeric_examples'][:3]}")
        if info.get("likely_datetime_column_but_not_parsed"):
            bits.append("⚠ looks like a date column but not parsed")
        print(f"  {col:<30}  " + "  ".join(bits))
    print()


def prompt_for_strategy(col: str, info: dict[str, Any]) -> str:
    """Interactively ask the user for a missing-data strategy for a single column."""
    print(f"\ncolumn `{col}` — {info['n_missing']} missing ({info['pct_missing']}%) — dtype {info['pandas_dtype']}")
    print("  options: ignore | drop_row | drop_col | mean | median | mode | ffill | bfill | constant:<value>")
    while True:
        raw = input(f"  strategy for {col} [ignore]: ").strip() or "ignore"
        if raw in VALID_STRATEGIES or raw.startswith("constant:"):
            return raw
        print(f"  unrecognized: {raw!r} — try again")


def apply_strategy(df: pd.DataFrame, col: str, strategy: str) -> pd.DataFrame:
    """Return a new DataFrame with the strategy applied to `col`."""
    if strategy == "ignore":
        return df
    if strategy == "drop_row":
        return df.dropna(subset=[col])
    if strategy == "drop_col":
        return df.drop(columns=[col])
    if strategy in ("mean", "median"):
        s = pd.to_numeric(df[col], errors="coerce")
        fill = s.mean() if strategy == "mean" else s.median()
        df = df.copy()
        df[col] = s.fillna(fill)
        return df
    if strategy == "mode":
        modes = df[col].mode(dropna=True)
        if modes.empty:
            return df
        df = df.copy()
        df[col] = df[col].fillna(modes.iloc[0])
        return df
    if strategy in ("ffill", "bfill"):
        df = df.copy()
        df[col] = df[col].ffill() if strategy == "ffill" else df[col].bfill()
        return df
    if strategy.startswith("constant:"):
        value = strategy.split(":", 1)[1]
        # Try to keep numeric dtype if possible
        try:
            value_cast: Any = float(value) if "." in value else int(value)
        except ValueError:
            value_cast = value
        df = df.copy()
        df[col] = df[col].fillna(value_cast)
        return df
    raise ValueError(f"unknown strategy: {strategy}")


def parse_strategy_arg(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--strategy is not valid JSON: {e}")
    if not isinstance(d, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in d.items()):
        raise SystemExit("--strategy must be a JSON object of {column: strategy}")
    return d


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", required=True, help="Directory containing raw input files")
    p.add_argument("--out", required=True, help="Directory to write parsed_results.csv into")
    p.add_argument("--files", nargs="*", help="Specific input files (override auto-discovery)")
    p.add_argument(
        "--strategy",
        default=None,
        help='JSON object mapping column to strategy, e.g. \'{"temperature_C":"median"}\'. '
        "Skips interactive prompts for listed columns.",
    )
    p.add_argument("--no-interactive", action="store_true", help="Apply 'ignore' to anything not in --strategy.")
    p.add_argument("--combine", choices=("concat", "first"), default="concat",
                   help="If multiple files are found: concat them (with a `__source__` column) or use the first only.")
    args = p.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.files:
        files = [Path(f).resolve() for f in args.files]
    else:
        files = find_input_files(data_dir)
    if not files:
        print(f"no tabular files found under {data_dir}", file=sys.stderr)
        return 1

    print(f"found {len(files)} input file(s):")
    for f in files:
        print(f"  - {f}")

    frames = []
    for f in files:
        df = load_one(f)
        df["__source__"] = f.name
        frames.append(df)

    if args.combine == "first" or len(frames) == 1:
        df = frames[0]
    else:
        df = pd.concat(frames, ignore_index=True, sort=False)

    report = quality_report(df)
    print_report(report)

    strategy_overrides = parse_strategy_arg(args.strategy)
    strategies_applied: dict[str, str] = {}
    cols_with_missing = [c for c, info in report["columns"].items() if info["n_missing"] > 0]

    for col in cols_with_missing:
        if col in strategy_overrides:
            chosen = strategy_overrides[col]
        elif args.no_interactive:
            chosen = "ignore"
        else:
            chosen = prompt_for_strategy(col, report["columns"][col])
        df = apply_strategy(df, col, chosen)
        strategies_applied[col] = chosen

    out_csv = out_dir / "parsed_results.csv"
    out_meta = out_dir / "parsed_results.meta.json"
    df.to_csv(out_csv, index=False, quoting=csv.QUOTE_MINIMAL)

    meta = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_files": [str(f) for f in files],
        "n_rows_after": int(len(df)),
        "n_cols_after": int(len(df.columns)),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
        "strategies_applied": strategies_applied,
        "quality_report": report,
    }
    out_meta.write_text(json.dumps(meta, indent=2, default=str))

    print(f"\nwrote {out_csv}  ({len(df)} rows, {len(df.columns)} columns)")
    print(f"wrote {out_meta}")
    if strategies_applied:
        print("strategies applied:")
        for c, s in strategies_applied.items():
            print(f"  {c}: {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
