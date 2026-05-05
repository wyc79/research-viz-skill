"""
Parser for messy clinical trial CSV data.

Cleaning rules (per user spec):
- patient_age has text mixed in (e.g., 'unknown', 'N/A', '?', 'missing'):
  coerce to numeric, treat non-numeric as missing.
- Numeric columns (patient_age, recovery_days, blood_pressure):
  fill missing values with column median.
- notes: drop rows where notes is missing.
- visit_date: keep as-is (string, no parsing).
"""

from pathlib import Path
import pandas as pd
import numpy as np


# Resolve paths relative to project root (one level up from this script).
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_CSV = PROJECT_ROOT / "data" / "trial_data_messy.csv"
OUTPUT_CSV = SCRIPT_DIR / "trial_data_clean.csv"
REPORT_TXT = SCRIPT_DIR / "cleaning_report.txt"


def main() -> None:
    raw = pd.read_csv(INPUT_CSV)
    n_raw = len(raw)

    df = raw.copy()

    # 1. patient_age has text values mixed in -> force numeric, NaN on failures.
    age_before_non_numeric = (
        pd.to_numeric(df["patient_age"], errors="coerce").isna()
        & df["patient_age"].notna()
    ).sum()
    df["patient_age"] = pd.to_numeric(df["patient_age"], errors="coerce")

    # 2. Drop rows where notes is missing (NaN OR empty string).
    notes_missing_mask = df["notes"].isna() | (df["notes"].astype(str).str.strip() == "")
    n_dropped_notes = int(notes_missing_mask.sum())
    df = df.loc[~notes_missing_mask].copy()

    # 3. Median-fill numeric columns.
    numeric_cols = ["patient_age", "recovery_days", "blood_pressure"]
    fill_summary = {}
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        n_missing = int(df[col].isna().sum())
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
        fill_summary[col] = (n_missing, median_val)

    # 4. visit_date kept as-is (string).

    df.to_csv(OUTPUT_CSV, index=False)

    # Write a small cleaning report so it's easy to audit later.
    lines = [
        "Clinical trial cleaning report",
        "=" * 40,
        f"Input rows:                 {n_raw}",
        f"Rows dropped (notes empty): {n_dropped_notes}",
        f"Output rows:                {len(df)}",
        f"patient_age non-numeric strings coerced to NaN: {age_before_non_numeric}",
        "",
        "Median-fills (after notes drop):",
    ]
    for col, (n_missing, median_val) in fill_summary.items():
        lines.append(f"  - {col}: filled {n_missing} missing with median = {median_val}")
    lines.append("")
    lines.append("visit_date: left as-is (string).")
    REPORT_TXT.write_text("\n".join(lines) + "\n")

    print("\n".join(lines))
    print(f"\nWrote cleaned CSV -> {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
