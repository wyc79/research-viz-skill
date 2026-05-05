#!/usr/bin/env python3
"""
parser.py — clean the clinical-trial CSV `data/trial_data_messy.csv` into
`intermediate_data/trial_data_messy__parsed.csv`.

Project-specific behavior baked in (no flags needed; `bash parse_input.sh`
reproduces the exact same output):

  - Coerces `patient_age` to numeric: the raw column has stray text values
    ("unknown", "N/A", "?", "missing") mixed in with the real ages — those
    become NaN here so the median imputation below can fill them.
  - Drops rows where `notes` is missing (per user instruction).
  - Imputes `patient_age`, `recovery_days`, `blood_pressure` with the column
    median (numeric columns only).
  - Leaves `visit_date` as a plain string for now (per user instruction).

`data/` is read-only — every output lands under `intermediate_data/`.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================================
# PROJECT-SPECIFIC CONFIG
# ============================================================================

# Per-column missing-data strategies for trial_data_messy.csv.
# - notes: drop_row    (user: "just drop rows where notes is missing")
# - patient_age / recovery_days / blood_pressure: median imputation (numeric)
# - visit_date: not in here because it has no missing values; left as-is.
PROJECT_STRATEGIES: dict[str, str] = {
    "notes": "drop_row",
    "patient_age": "median",
    "recovery_days": "median",
    "blood_pressure": "median",
}

# Run unattended — `bash parse_input.sh` should not prompt.
PROJECT_NONINTERACTIVE_DEFAULT: bool = True

# Sentinel strings that appear in patient_age in place of a real number.
# Anything in this set (case-insensitive, whitespace-stripped) gets coerced to
# NaN before median imputation runs.
AGE_SENTINELS = {"unknown", "n/a", "na", "?", "missing", ""}


def apply_project_specific_cleaning(df: pd.DataFrame, source_path: Path) -> pd.DataFrame:
    """Pre-imputation cleanup for trial_data_messy.csv.

    The `patient_age` column came in as object dtype because a handful of rows
    contain words ("unknown", "missing") or a literal "?". Replace those with
    NaN and coerce the column to float so the median strategy below can
    actually compute a median.
    """
    # patient_age has text values mixed in with numbers — coerce to numeric so
    # NaNs flow into the median imputation step.
    if "patient_age" in df.columns:
        df = df.copy()
        # Normalize whitespace + case, then null out anything in AGE_SENTINELS.
        as_str = df["patient_age"].astype(str).str.strip().str.lower()
        df.loc[as_str.isin(AGE_SENTINELS), "patient_age"] = pd.NA
        # Coerce to float; any other non-numeric stragglers also become NaN.
        df["patient_age"] = pd.to_numeric(df["patient_age"], errors="coerce")
    return df


# ============================================================================
# Generic helpers (trimmed: only the strategies this project uses).
# ============================================================================


def quality_report(df: pd.DataFrame) -> dict[str, Any]:
    """Per-column dtype + missing-count summary, used for the printed report
    and for parsed_index.json's record of what came in."""
    report: dict[str, Any] = {"n_rows": len(df), "n_cols": len(df.columns), "columns": {}}
    for col in df.columns:
        s = df[col]
        report["columns"][col] = {
            "pandas_dtype": str(s.dtype),
            "n_missing": int(s.isna().sum()),
            "pct_missing": round(float(s.isna().mean() * 100), 2),
            "n_unique": int(s.nunique(dropna=True)),
        }
    return report


def print_report(report: dict[str, Any]) -> None:
    print(f"\n=== quality report — {report['n_rows']} rows, {report['n_cols']} columns ===\n")
    for col, info in report["columns"].items():
        print(
            f"  {col:<20}  {info['pandas_dtype']:<10}  "
            f"missing={info['n_missing']:>4} ({info['pct_missing']:>5}%)  "
            f"unique={info['n_unique']}"
        )
    print()


def apply_strategy(df: pd.DataFrame, col: str, strategy: str) -> pd.DataFrame:
    """Apply one of the two strategies this project uses: drop_row or median."""
    if strategy == "drop_row":
        # Used for `notes`: rows with no note are dropped entirely.
        return df.dropna(subset=[col])
    if strategy == "median":
        # Used for the three numeric columns. to_numeric is a safety net in
        # case apply_project_specific_cleaning didn't already coerce.
        s = pd.to_numeric(df[col], errors="coerce")
        df = df.copy()
        df[col] = s.fillna(s.median())
        return df
    raise ValueError(f"unsupported strategy for this project: {strategy!r}")


def clean_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Run PROJECT_STRATEGIES against `df`, in a deterministic order:
    drop_row first (so we don't impute medians using rows that will be dropped),
    then the median fills."""
    strategies_applied: dict[str, str] = {}
    # drop_row first — shrinks the frame, so subsequent medians reflect the
    # final (kept) population only.
    for col, strategy in PROJECT_STRATEGIES.items():
        if strategy != "drop_row":
            continue
        if col in df.columns:
            df = apply_strategy(df, col, strategy)
            strategies_applied[col] = strategy
    # Then numeric imputations.
    for col, strategy in PROJECT_STRATEGIES.items():
        if strategy == "drop_row":
            continue
        if col in df.columns:
            df = apply_strategy(df, col, strategy)
            strategies_applied[col] = strategy
    return df, strategies_applied


# ============================================================================
# CLI entrypoint
# ============================================================================


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", required=True, help="Directory containing trial_data_messy.csv")
    p.add_argument("--out", required=True, help="Directory to write the parsed output into")
    # The wrapper still passes --no-interactive (and may pass --combine, etc.)
    # since it's a generic shim. We accept and ignore them — this project is
    # always single-file, always non-interactive.
    p.add_argument("--no-interactive", action="store_true", default=True, help=argparse.SUPPRESS)
    p.add_argument("--interactive", dest="no_interactive", action="store_false", help=argparse.SUPPRESS)
    p.add_argument("--strategy", default=None, help=argparse.SUPPRESS)
    p.add_argument("--combine", default="per_file", help=argparse.SUPPRESS)
    p.add_argument("--files", nargs="*", help=argparse.SUPPRESS)
    args = p.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Single source file for this project.
    src = data_dir / "trial_data_messy.csv"
    if not src.exists():
        print(f"expected input file not found: {src}")
        return 1

    print(f"reading {src}")
    df = pd.read_csv(src)

    # Pre-imputation cleanup (coerce patient_age text → NaN).
    df = apply_project_specific_cleaning(df, src)

    # Quality summary of the *cleaned* frame (after coercion, before imputation).
    report_before = quality_report(df)
    print_report(report_before)

    # Apply drop_row + median strategies.
    df_clean, strategies = clean_frame(df)
    print(f"strategies applied: {strategies}")
    print(f"rows: {report_before['n_rows']} -> {len(df_clean)} after drop_row on `notes`")

    # Write the cleaned CSV.
    target = out_dir / "trial_data_messy__parsed.csv"
    df_clean.to_csv(target, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"\nwrote {target}  ({len(df_clean)} rows, {len(df_clean.columns)} columns)")

    # Side-car meta.json — useful for debugging and downstream tools.
    meta = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_file": str(src),
        "n_rows_in": int(report_before["n_rows"]),
        "n_rows_out": int(len(df_clean)),
        "n_cols_out": int(len(df_clean.columns)),
        "dtypes": {c: str(df_clean[c].dtype) for c in df_clean.columns},
        "strategies_applied": strategies,
        "quality_report_pre_impute": report_before,
    }
    meta_path = out_dir / "trial_data_messy__parsed.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, default=str))
    print(f"wrote {meta_path}")

    # parsed_index.json — manifest. Single-file project so per_file is the
    # only mode and the canonical CSV is the lone output.
    parsed_index = {
        "generated_at": meta["generated_at"],
        "data_dir": str(data_dir),
        "combine_mode": "per_file",
        "single_file_input": True,
        "has_combined_csv": False,
        "combined_csv": None,
        "canonical_csv": "trial_data_messy__parsed.csv",
        "per_file_outputs": [
            {
                "source_file": str(src),
                "source_relative": "trial_data_messy.csv",
                "parsed_path": "trial_data_messy__parsed.csv",
                "n_rows": int(len(df_clean)),
                "n_cols": int(len(df_clean.columns)),
                "dtypes": meta["dtypes"],
                "strategies_applied": strategies,
            }
        ],
    }
    (out_dir / "parsed_index.json").write_text(json.dumps(parsed_index, indent=2, default=str))
    print(f"wrote {out_dir/'parsed_index.json'}")
    print(f"canonical: {out_dir/'trial_data_messy__parsed.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
