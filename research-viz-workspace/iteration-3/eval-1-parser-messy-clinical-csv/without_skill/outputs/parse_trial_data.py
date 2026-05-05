"""
Parser / cleaner for the messy clinical trial CSV.

Steps:
  1. Load data/trial_data_messy.csv
  2. Coerce patient_age to numeric (non-numeric strings like 'unknown',
     'N/A', '?', 'missing' become NaN)
  3. Drop rows where `notes` is missing
  4. Fill remaining missing numeric values with the column median
  5. Leave visit_date as-is (string)
  6. Write cleaned CSV + a short summary report to visualizations/
"""

from pathlib import Path
import pandas as pd
import numpy as np


HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "data" / "trial_data_messy.csv"
OUT_DIR = HERE / "visualizations"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CLEAN_CSV = OUT_DIR / "trial_data_clean.csv"
REPORT_TXT = OUT_DIR / "cleaning_report.txt"


def main() -> None:
    raw = pd.read_csv(DATA_PATH)
    n_raw = len(raw)

    df = raw.copy()

    # --- 1. coerce patient_age to numeric ---------------------------------
    # Track which values were non-numeric so we can report them.
    age_str = df["patient_age"].astype(str).str.strip()
    coerced = pd.to_numeric(age_str, errors="coerce")
    bad_age_mask = coerced.isna() & df["patient_age"].notna()
    bad_age_values = (
        df.loc[bad_age_mask, "patient_age"].astype(str).value_counts().to_dict()
    )
    df["patient_age"] = coerced

    # --- 2. drop rows where notes is missing ------------------------------
    notes_missing_before = df["notes"].isna().sum() + (
        df["notes"].astype(str).str.strip().eq("").sum()
        if df["notes"].dtype == object
        else 0
    )
    # Treat empty string as missing too.
    if df["notes"].dtype == object:
        df["notes"] = df["notes"].replace(r"^\s*$", np.nan, regex=True)
    n_before_drop = len(df)
    df = df.dropna(subset=["notes"]).reset_index(drop=True)
    n_dropped_notes = n_before_drop - len(df)

    # --- 3. fill remaining numeric NaNs with column medians ---------------
    numeric_cols = ["patient_age", "recovery_days", "blood_pressure"]
    fills: dict[str, float] = {}
    fill_counts: dict[str, int] = {}
    for col in numeric_cols:
        # Coerce in case anything sneaks in.
        df[col] = pd.to_numeric(df[col], errors="coerce")
        n_missing = int(df[col].isna().sum())
        if n_missing > 0:
            med = float(df[col].median())
            df[col] = df[col].fillna(med)
            fills[col] = med
            fill_counts[col] = n_missing
        else:
            fills[col] = float(df[col].median())
            fill_counts[col] = 0

    # --- 4. trial_id should be an integer ---------------------------------
    df["trial_id"] = pd.to_numeric(df["trial_id"], errors="coerce").astype("Int64")

    # --- 5. visit_date left as-is -----------------------------------------
    # (kept as string per request)

    # --- write cleaned CSV ------------------------------------------------
    df.to_csv(CLEAN_CSV, index=False)

    # --- write a short report --------------------------------------------
    lines = []
    lines.append("Clinical trial CSV cleaning report")
    lines.append("=" * 40)
    lines.append(f"Source file        : {DATA_PATH.relative_to(HERE)}")
    lines.append(f"Output (clean) file: {CLEAN_CSV.relative_to(HERE)}")
    lines.append("")
    lines.append(f"Rows in raw file   : {n_raw}")
    lines.append(f"Rows after dropping missing-notes : {len(df)}")
    lines.append(f"Rows dropped (notes missing/blank): {n_dropped_notes}")
    lines.append("")
    lines.append("patient_age coercion:")
    if bad_age_values:
        for val, cnt in sorted(bad_age_values.items()):
            lines.append(f"  - {val!r:>12s}  ->  NaN  (count = {cnt})")
    else:
        lines.append("  (no non-numeric values found)")
    lines.append("")
    lines.append("Median fills applied to numeric columns:")
    for col in numeric_cols:
        lines.append(
            f"  - {col:<15s}  filled {fill_counts[col]} value(s) "
            f"with median = {fills[col]:.3f}"
        )
    lines.append("")
    lines.append("Final dtypes:")
    for col, dtype in df.dtypes.items():
        lines.append(f"  - {col:<15s} {dtype}")
    lines.append("")
    lines.append("Final missing-value counts per column:")
    for col, miss in df.isna().sum().items():
        lines.append(f"  - {col:<15s} {int(miss)}")
    lines.append("")
    lines.append("Head of cleaned data:")
    lines.append(df.head(10).to_string(index=False))

    REPORT_TXT.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
