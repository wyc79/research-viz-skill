#!/usr/bin/env python3
"""
parser.py — read raw tabular files (csv/tsv/txt/xlsx), run quality checks,
handle missing data, and write a single cleaned `parsed_results.csv` plus a
small meta JSON describing what was done.

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

# Place this script's parent on sys.path so we can import helpers.utils
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers.utils import detect_delimiter, slugify  # noqa: E402

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


def clean_one_frame(
    df: pd.DataFrame,
    report: dict[str, Any],
    strategy_overrides: dict[str, str],
    no_interactive: bool,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Apply missing-data strategies to a single DataFrame. Returns (cleaned, strategies_applied)."""
    strategies_applied: dict[str, str] = {}
    cols_with_missing = [c for c, info in report["columns"].items() if info["n_missing"] > 0]
    for col in cols_with_missing:
        if col in strategy_overrides:
            chosen = strategy_overrides[col]
        elif no_interactive:
            chosen = "ignore"
        else:
            chosen = prompt_for_strategy(col, report["columns"][col])
        df = apply_strategy(df, col, chosen)
        strategies_applied[col] = chosen
    return df, strategies_applied


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", required=True, help="Directory containing raw input files")
    p.add_argument("--out", required=True, help="Directory to write parsed outputs into")
    p.add_argument("--files", nargs="*", help="Specific input files (override auto-discovery)")
    p.add_argument(
        "--strategy",
        default=None,
        help='JSON object mapping column to strategy, e.g. \'{"temperature_C":"median"}\'. '
        "Skips interactive prompts for listed columns. Strategy is applied per-file when --combine=per_file.",
    )
    p.add_argument("--no-interactive", action="store_true", help="Apply 'ignore' to anything not in --strategy.")
    p.add_argument(
        "--combine",
        choices=("per_file", "concat", "first", "both"),
        default="per_file",
        help=(
            "How to handle multiple input files: "
            "'per_file' (default) — clean each file independently and mirror data/ structure under --out, "
            "useful when sessions/patients shouldn't be aggregated; "
            "'concat' — stack everything into a single parsed_results.csv with a __source__ column; "
            "'first' — only use the first discovered file; "
            "'both' — write per-file mirrors AND parsed_results.csv. "
            "Note: with a single input file, parsed_results.csv is always written for downstream-tool compatibility."
        ),
    )
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

    strategy_overrides = parse_strategy_arg(args.strategy)
    index_entries: list[dict[str, Any]] = []  # for parsed_index.json
    timestamp = datetime.now().isoformat(timespec="seconds")

    # Decide effective mode. With a single file, "per_file" is equivalent to "concat" so we
    # always also produce parsed_results.csv for downstream-tool compatibility.
    single_file = len(files) == 1
    write_per_file = args.combine in {"per_file", "both"} or (single_file and args.combine == "per_file")
    write_combined = args.combine in {"concat", "both", "first"} or single_file

    # Sweep stale outputs from a previous run that don't fit the current mode.
    # The parser is the source of truth for `intermediate_data/` — anything it
    # produced before that the current invocation won't reproduce should go.
    prev_index_path = out_dir / "parsed_index.json"
    if prev_index_path.exists():
        try:
            prev = json.loads(prev_index_path.read_text())
        except Exception:
            prev = {}
        def _try_unlink(p: Path, label: str) -> None:
            try:
                p.unlink()
                print(f"removed stale {label}")
            except OSError as e:
                # Filesystem may not allow deletes (e.g. cowork mount, mounted read-only volumes).
                # Don't crash — just warn and let the new outputs land on top.
                print(f"warning: could not remove stale {label}: {e}", file=sys.stderr)
        # Remove the previous combined CSV+meta if this run isn't producing one.
        if not write_combined and prev.get("has_combined_csv"):
            for stale in (out_dir / "parsed_results.csv", out_dir / "parsed_results.meta.json"):
                if stale.exists():
                    _try_unlink(stale, stale.name)
        # Remove previous per-file mirrors if this run isn't producing per-file outputs.
        if not write_per_file:
            for entry in prev.get("per_file_outputs", []):
                stale_path = out_dir / entry.get("parsed_path", "")
                if stale_path.exists() and stale_path.is_file():
                    _try_unlink(stale_path, str(stale_path.relative_to(out_dir)))

    # ---------- per-file mode ----------
    if write_per_file:
        for f in files:
            try:
                rel = f.relative_to(data_dir)
            except ValueError:
                # File came from --files outside data_dir; flatten the name.
                rel = Path(f.name)
            target = (out_dir / rel).with_suffix(".csv")
            target.parent.mkdir(parents=True, exist_ok=True)

            df = load_one(f)
            report = quality_report(df)
            print(f"\n--- {rel} ---")
            print_report(report)
            df, strategies = clean_one_frame(df, report, strategy_overrides, args.no_interactive)
            df.to_csv(target, index=False, quoting=csv.QUOTE_MINIMAL)
            print(f"wrote {target}  ({len(df)} rows, {len(df.columns)} columns)")
            index_entries.append(
                {
                    "source_file": str(f),
                    "source_relative": str(rel),
                    "parsed_path": str(target.relative_to(out_dir)),
                    "n_rows": int(len(df)),
                    "n_cols": int(len(df.columns)),
                    "dtypes": {c: str(df[c].dtype) for c in df.columns},
                    "strategies_applied": strategies,
                }
            )

    # ---------- combined mode ----------
    if write_combined:
        frames = []
        if args.combine == "first":
            chosen_files = files[:1]
        else:
            chosen_files = files
        for f in chosen_files:
            df = load_one(f)
            try:
                src = str(f.relative_to(data_dir))
            except ValueError:
                src = f.name
            df["__source__"] = src
            frames.append(df)

        if len(frames) == 1:
            df_all = frames[0]
        else:
            df_all = pd.concat(frames, ignore_index=True, sort=False)

        report_all = quality_report(df_all)
        if not write_per_file:  # avoid printing twice
            print_report(report_all)
        df_all, strategies_all = clean_one_frame(df_all, report_all, strategy_overrides, args.no_interactive)

        out_csv = out_dir / "parsed_results.csv"
        out_meta = out_dir / "parsed_results.meta.json"
        df_all.to_csv(out_csv, index=False, quoting=csv.QUOTE_MINIMAL)
        meta = {
            "generated_at": timestamp,
            "source_files": [str(f) for f in chosen_files],
            "n_rows_after": int(len(df_all)),
            "n_cols_after": int(len(df_all.columns)),
            "dtypes": {c: str(df_all[c].dtype) for c in df_all.columns},
            "strategies_applied": strategies_all,
            "quality_report": report_all,
        }
        out_meta.write_text(json.dumps(meta, indent=2, default=str))
        print(f"\nwrote {out_csv}  ({len(df_all)} rows, {len(df_all.columns)} columns)")
        print(f"wrote {out_meta}")
        if strategies_all:
            print("strategies applied (combined):")
            for c, s in strategies_all.items():
                print(f"  {c}: {s}")

    # ---------- always: write parsed_index.json so downstream tools can discover what's there ----------
    parsed_index = {
        "generated_at": timestamp,
        "data_dir": str(data_dir),
        "combine_mode": args.combine,
        "single_file_input": single_file,
        "has_combined_csv": bool(write_combined),
        "combined_csv": "parsed_results.csv" if write_combined else None,
        "per_file_outputs": index_entries,
    }
    (out_dir / "parsed_index.json").write_text(json.dumps(parsed_index, indent=2, default=str))
    print(f"wrote {out_dir/'parsed_index.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
