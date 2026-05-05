#!/usr/bin/env python3
"""parser.py — read `data/sensor_log.csv` and write
`intermediate_data/sensor_log__parsed.csv` plus a `parsed_index.json` manifest.

This is a single-file project: one CSV in, one cleaned CSV out. There are no
missing values in the source, the only cleaning step is parsing the `ts` column
to pandas datetime so downstream time-series charts can use it directly.

`data/` is treated as read-only — all outputs land under `--out`
(typically `intermediate_data/`).
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


# Single source file for this project.
SOURCE_NAME = "sensor_log.csv"


def apply_project_specific_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """Project-specific transforms applied right after load.

    The sensor log is already tidy (site, sensor, value, ok, ts); the only
    fix-up is converting `ts` from string to datetime so the streamlit page
    can plot a real time axis instead of sorted strings.
    """
    # Parse the timestamp column. Source format is ISO-like ("YYYY-MM-DD HH:MM:SS")
    # so pandas' default parser works without a format string.
    df["ts"] = pd.to_datetime(df["ts"])

    # Sort by timestamp so any later groupby + plot lands in chronological order.
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", required=True, help="Directory containing sensor_log.csv")
    p.add_argument("--out", required=True, help="Directory to write the parsed CSV + index into")
    args = p.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    source = data_dir / SOURCE_NAME
    if not source.exists():
        raise SystemExit(f"expected {source} not found")

    # Load + clean.
    df = pd.read_csv(source)
    df = apply_project_specific_cleaning(df)

    # Quick console summary so a human running the wrapper can sanity-check.
    print(f"loaded {source}")
    print(f"  rows={len(df)}  cols={len(df.columns)}")
    print(f"  ts range: {df['ts'].min()} -> {df['ts'].max()}")
    print(f"  sites:    {sorted(df['site'].unique())}")
    print(f"  sensors:  {sorted(df['sensor'].unique())}")

    # Write per-file output following the `<dataset>__parsed.csv` convention.
    target = out_dir / "sensor_log__parsed.csv"
    df.to_csv(target, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"wrote {target}")

    # parsed_index.json is the manifest downstream tools (streamlit/index.py) read.
    timestamp = datetime.now().isoformat(timespec="seconds")
    parsed_index = {
        "generated_at": timestamp,
        "data_dir": str(data_dir),
        "combine_mode": "per_file",
        "single_file_input": True,
        "has_combined_csv": False,
        "combined_csv": None,
        "canonical_csv": "sensor_log__parsed.csv",
        "per_file_outputs": [
            {
                "source_file": str(source),
                "source_relative": SOURCE_NAME,
                "parsed_path": "sensor_log__parsed.csv",
                "n_rows": int(len(df)),
                "n_cols": int(len(df.columns)),
                "dtypes": {c: str(df[c].dtype) for c in df.columns},
                "strategies_applied": {},
            }
        ],
    }
    (out_dir / "parsed_index.json").write_text(json.dumps(parsed_index, indent=2, default=str))
    print(f"wrote {out_dir/'parsed_index.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
