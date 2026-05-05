#!/usr/bin/env python3
"""
parser.py — load `data/flowers.csv` and write a cleaned copy to
`intermediate_data/flowers__parsed.csv` plus a `parsed_index.json` manifest.

The flowers dataset is a single CSV with one row per observation:
  species (str)         — one of {setosa, versicolor, virginica}
  sepal_length (float)  — cm
  sepal_width  (float)  — cm
  petal_length (float)  — cm
  petal_width  (float)  — cm

The user verified the file is already clean: no missing values, no dtype
issues, no garbage rows. So this parser does the lightweight thing — load,
sanity-check (assert no nulls and the expected schema), and write the
canonical CSV. No imputation, no row drops, no reorganization. If the data
ever stops being clean, the assertion will fail loudly rather than silently
masking the problem.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

EXPECTED_COLUMNS = ["species", "sepal_length", "sepal_width", "petal_length", "petal_width"]
EXPECTED_SPECIES = {"setosa", "versicolor", "virginica"}


def load_and_check(path: Path) -> pd.DataFrame:
    """Load flowers.csv and assert the schema and cleanliness the user promised."""
    df = pd.read_csv(path)

    # Schema check — exact column set in expected order.
    assert list(df.columns) == EXPECTED_COLUMNS, (
        f"unexpected columns: {list(df.columns)} (expected {EXPECTED_COLUMNS})"
    )

    # Numeric columns must really be numeric (no stray strings sneaking in).
    for col in EXPECTED_COLUMNS[1:]:
        assert pd.api.types.is_numeric_dtype(df[col]), f"{col} is not numeric: {df[col].dtype}"

    # Species labels must be the three known iris species — guard against typos.
    species_set = set(df["species"].unique())
    assert species_set == EXPECTED_SPECIES, (
        f"unexpected species labels: {species_set} (expected {EXPECTED_SPECIES})"
    )

    # User said the data is clean — verify no missing values before downstream plots.
    assert df.isna().sum().sum() == 0, "found missing values; the dataset was supposed to be clean"

    return df


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", required=True, help="Directory containing flowers.csv")
    p.add_argument("--out", required=True, help="Directory to write parsed outputs into")
    args = p.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    source = data_dir / "flowers.csv"
    if not source.exists():
        raise SystemExit(f"flowers.csv not found at {source}")

    df = load_and_check(source)

    # Single-file project — write the canonical CSV directly under intermediate_data/
    # using the `<dataset>__parsed.csv` naming convention.
    target = out_dir / "flowers__parsed.csv"
    df.to_csv(target, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"wrote {target}  ({len(df)} rows, {len(df.columns)} columns)")

    # parsed_index.json is the handoff to plot_gen / interactive — `canonical_csv`
    # is what they read by default.
    parsed_index = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_dir": str(data_dir),
        "canonical_csv": "flowers__parsed.csv",
        "per_file_outputs": [
            {
                "source_file": str(source),
                "source_relative": "flowers.csv",
                "parsed_path": "flowers__parsed.csv",
                "n_rows": int(len(df)),
                "n_cols": int(len(df.columns)),
                "dtypes": {c: str(df[c].dtype) for c in df.columns},
            }
        ],
    }
    (out_dir / "parsed_index.json").write_text(json.dumps(parsed_index, indent=2, default=str))
    print(f"wrote {out_dir / 'parsed_index.json'}")
    print(f"canonical: {out_dir / 'flowers__parsed.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
