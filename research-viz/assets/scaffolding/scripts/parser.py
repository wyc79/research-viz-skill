#!/usr/bin/env python3
"""
parser.py — read raw tabular files (csv/tsv/txt/xlsx) from a read-only
`data/` directory, run quality checks, handle missing data, and write
cleaned outputs into `intermediate_data/` using the naming convention
`<original_dataset_name>__parsed.csv` (one per input file).

`data/` is never written to, renamed, or deleted from. Anything produced
by this script lives under `--out` (typically `intermediate_data/`).

Designed to be both:
  - **interactive** — prompts the user per column for a missing-data strategy, and
  - **scriptable** — accepts `--strategy '{"col":"mean", ...}'` and runs unattended.

Adapt this script for the specific dataset (e.g. add custom dtype coercions,
drop garbage columns, parse weird date formats) but keep the high-level shape
so future reruns are predictable. Follow-on transforms (reshape, imputation
pass, normalization, …) should write *new* files alongside the parsed ones
using the same suffix convention: `<dataset>__long.csv`, `<dataset>__imputated.csv`,
`<dataset>__zscored.csv`, etc. Never overwrite `__parsed.csv`.
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


# ============================================================================
# PROJECT-SPECIFIC CONFIG — edit this block for your dataset.
#
# Once an agent (or you) has decided on cleaning rules for this project, write
# them here so `bash parse_input.sh` reproduces the same cleaned output every
# time, without having to remember --strategy flags.
# ============================================================================

# Default per-column missing-data strategies. Used as the default for --strategy
# AND as the fallback when --no-interactive is passed. Empty dict = ask the user.
# Example: {"temperature_C": "median", "comment": "drop_col", "patient_age": "drop_row"}
PROJECT_STRATEGIES: dict[str, str] = {}

# When True, skip the interactive prompts even without --no-interactive on the
# command line. Set this to True after you've populated PROJECT_STRATEGIES so
# `bash parse_input.sh` runs end-to-end unattended.
PROJECT_NONINTERACTIVE_DEFAULT: bool = False


def apply_project_specific_cleaning(df: pd.DataFrame, source_path: Path) -> pd.DataFrame:
    """Project-specific transformations applied to every loaded DataFrame BEFORE
    quality reporting and missing-data handling.

    Edit this for your dataset. Common things to do here:
      - rename columns: df = df.rename(columns={"old": "new"})
      - coerce types: df["age"] = pd.to_numeric(df["age"], errors="coerce")
      - parse dates: df["visit_date"] = pd.to_datetime(df["visit_date"], errors="coerce")
      - drop junk columns: df = df.drop(columns=["unnamed_3"], errors="ignore")
      - clip / sentinel-replace: df["temp_c"] = df["temp_c"].replace(-999, pd.NA)

    `source_path` is provided so you can branch on filename when the same
    parser runs against heterogeneous files.
    """
    return df


def project_reorganize(source_relative: Path) -> Path:
    """Map a source file's path (relative to data/) to the path it should land at
    under intermediate_data/, MINUS the `__parsed.csv` suffix.

    Default behavior mirrors data/'s structure. Override this if data/ has an
    awkward layout (flat dump, opaque names, mixed concerns) and you want a
    cleaner tree under intermediate_data/.

    Example for a flat data/ dump where filenames encode subject/session like
    `S01_run2_eeg.csv`:

        def project_reorganize(source_relative):
            stem = source_relative.stem  # 'S01_run2_eeg'
            subject, run, modality = stem.split('_')
            return Path(modality) / subject / run

    Returns a path *without* extension; the parser appends `__parsed.csv`.
    """
    # Default: mirror data/. Strip the suffix; the caller adds `__parsed.csv`.
    return source_relative.parent / source_relative.stem


# ============================================================================
# End of project-specific config.
# ============================================================================


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
    p.add_argument(
        "--no-interactive",
        action="store_true",
        default=PROJECT_NONINTERACTIVE_DEFAULT,
        help="Apply PROJECT_STRATEGIES (then 'ignore' for anything not listed) without prompting. "
        "Defaults to PROJECT_NONINTERACTIVE_DEFAULT in this file.",
    )
    p.add_argument(
        "--interactive",
        dest="no_interactive",
        action="store_false",
        help="Force interactive prompts even if PROJECT_NONINTERACTIVE_DEFAULT is True.",
    )
    p.add_argument(
        "--combine",
        choices=("per_file", "concat", "first", "both"),
        default="per_file",
        help=(
            "How to handle multiple input files: "
            "'per_file' (default) — clean each file independently and mirror data/ structure under --out, "
            "useful when sessions/patients shouldn't be aggregated; "
            "'concat' — stack everything into a single combined__parsed.csv with a __source__ column; "
            "'first' — only use the first discovered file; "
            "'both' — write per-file outputs AND combined__parsed.csv. "
            "Per-file outputs are always named '<original_dataset_name>__parsed.csv'."
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

    # Strategy precedence: CLI --strategy overrides PROJECT_STRATEGIES, which
    # overrides the per-column interactive prompt (or 'ignore' if --no-interactive).
    strategy_overrides: dict[str, str] = dict(PROJECT_STRATEGIES)
    strategy_overrides.update(parse_strategy_arg(args.strategy))
    if PROJECT_STRATEGIES:
        print(f"PROJECT_STRATEGIES baked into parser.py: {PROJECT_STRATEGIES}")
    index_entries: list[dict[str, Any]] = []  # for parsed_index.json
    timestamp = datetime.now().isoformat(timespec="seconds")

    # Decide effective mode. Single-file input is always written as a per-file output
    # (named after the dataset) — there's no point in a separate combined twin.
    single_file = len(files) == 1
    if single_file:
        write_per_file, write_combined = True, False
    else:
        write_per_file = args.combine in {"per_file", "both"}
        write_combined = args.combine in {"concat", "both", "first"}

    COMBINED_NAME = "combined__parsed.csv"
    COMBINED_META = "combined__parsed.meta.json"

    def parsed_path_for(rel: Path) -> Path:
        """rel is the source file's path relative to data_dir.
        Returns the path (under out_dir) where its cleaned CSV will land.
        Defaults to mirroring data/'s structure, but the per-project
        `project_reorganize()` hook above can override the layout (without
        touching data/ itself)."""
        base = project_reorganize(rel)
        return base.with_name(f"{base.name}__parsed.csv")

    # Sweep stale outputs from a previous run that don't fit the current mode.
    # The parser is the source of truth for `intermediate_data/` — anything it
    # produced before that the current invocation won't reproduce should go.
    prev_index_path = out_dir / "parsed_index.json"

    def _try_unlink(p: Path, label: str) -> None:
        try:
            p.unlink()
            print(f"removed stale {label}")
        except OSError as e:
            # Filesystem may not allow deletes (e.g. cowork mount, mounted read-only volumes).
            print(f"warning: could not remove stale {label}: {e}", file=sys.stderr)

    if prev_index_path.exists():
        try:
            prev = json.loads(prev_index_path.read_text())
        except Exception:
            prev = {}
        # Clean up the previous combined CSV+meta if this run isn't producing one.
        # Cover both the new name (combined__parsed.csv) and the legacy name (parsed_results.csv).
        if not write_combined:
            prev_combined = prev.get("combined_csv") or COMBINED_NAME
            for stale_name in {prev_combined, COMBINED_NAME, "parsed_results.csv"}:
                stale = out_dir / stale_name
                if stale.exists():
                    _try_unlink(stale, stale.name)
            for stale_meta_name in {COMBINED_META, "parsed_results.meta.json"}:
                stale = out_dir / stale_meta_name
                if stale.exists():
                    _try_unlink(stale, stale.name)
        # Clean up previous per-file mirrors that aren't going to be re-produced.
        current_targets = {
            str(parsed_path_for(f.relative_to(data_dir))) if data_dir in f.parents or f.parent == data_dir else f"{f.stem}__parsed.csv"
            for f in files
        } if write_per_file else set()
        for entry in prev.get("per_file_outputs", []):
            old_path = entry.get("parsed_path", "")
            if old_path and old_path not in current_targets:
                stale = out_dir / old_path
                if stale.exists() and stale.is_file():
                    _try_unlink(stale, old_path)

    # ---------- per-file mode ----------
    if write_per_file:
        for f in files:
            try:
                rel = f.relative_to(data_dir)
            except ValueError:
                rel = Path(f.name)
            target = out_dir / parsed_path_for(rel)
            target.parent.mkdir(parents=True, exist_ok=True)

            df = load_one(f)
            df = apply_project_specific_cleaning(df, f)
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
    combined_meta_summary: dict[str, Any] | None = None
    if write_combined:
        frames = []
        chosen_files = files[:1] if args.combine == "first" else files
        for f in chosen_files:
            df = load_one(f)
            df = apply_project_specific_cleaning(df, f)
            try:
                src = str(f.relative_to(data_dir))
            except ValueError:
                src = f.name
            df["__source__"] = src
            frames.append(df)

        df_all = frames[0] if len(frames) == 1 else pd.concat(frames, ignore_index=True, sort=False)
        report_all = quality_report(df_all)
        if not write_per_file:
            print_report(report_all)
        df_all, strategies_all = clean_one_frame(df_all, report_all, strategy_overrides, args.no_interactive)

        out_csv = out_dir / COMBINED_NAME
        out_meta = out_dir / COMBINED_META
        df_all.to_csv(out_csv, index=False, quoting=csv.QUOTE_MINIMAL)
        combined_meta_summary = {
            "generated_at": timestamp,
            "source_files": [str(f) for f in chosen_files],
            "n_rows_after": int(len(df_all)),
            "n_cols_after": int(len(df_all.columns)),
            "dtypes": {c: str(df_all[c].dtype) for c in df_all.columns},
            "strategies_applied": strategies_all,
            "quality_report": report_all,
        }
        out_meta.write_text(json.dumps(combined_meta_summary, indent=2, default=str))
        print(f"\nwrote {out_csv}  ({len(df_all)} rows, {len(df_all.columns)} columns)")
        print(f"wrote {out_meta}")
        if strategies_all:
            print("strategies applied (combined):")
            for c, s in strategies_all.items():
                print(f"  {c}: {s}")

    # Pick the canonical file: combined if it exists, else the lone per-file output if there's
    # exactly one, else null (multi-file per_file mode — downstream tools must pick a file).
    canonical_csv: str | None = None
    if write_combined:
        canonical_csv = COMBINED_NAME
    elif len(index_entries) == 1:
        canonical_csv = index_entries[0]["parsed_path"]

    parsed_index = {
        "generated_at": timestamp,
        "data_dir": str(data_dir),
        "combine_mode": args.combine,
        "single_file_input": single_file,
        "has_combined_csv": bool(write_combined),
        "combined_csv": COMBINED_NAME if write_combined else None,
        "canonical_csv": canonical_csv,
        "per_file_outputs": index_entries,
    }
    (out_dir / "parsed_index.json").write_text(json.dumps(parsed_index, indent=2, default=str))
    print(f"wrote {out_dir/'parsed_index.json'}")
    if canonical_csv:
        print(f"canonical: {out_dir/canonical_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
