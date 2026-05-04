#!/usr/bin/env python3
"""
Scaffold a `visualizations/` folder next to a user's `data/` folder.

Copies the template tree from ../assets/scaffolding/ into the target directory,
then stamps the data path into the shell wrappers and the README.

Usage:
    python scaffold.py <target-dir> --data-dir <abs-path-to-data>

Idempotent: refuses to overwrite an existing visualizations/ unless --force.
"""
from __future__ import annotations

import argparse
import datetime
import shutil
import sys
from pathlib import Path

THIS = Path(__file__).resolve()
SKILL_ROOT = THIS.parent.parent
SCAFFOLDING = SKILL_ROOT / "assets" / "scaffolding"


def stamp_path(text: str, data_dir: str, viz_dir: str) -> str:
    return (
        text.replace("__DATA_DIR__", data_dir)
        .replace("__VIZ_DIR__", viz_dir)
        .replace("__TIMESTAMP__", datetime.datetime.now().isoformat(timespec="seconds"))
    )


def copy_tree(src: Path, dst: Path, data_dir: str, viz_dir: str) -> list[Path]:
    """Copy src into dst, stamping placeholders in text files. Returns list of dst paths created."""
    created: list[Path] = []
    for entry in src.rglob("*"):
        rel = entry.relative_to(src)
        target = dst / rel
        if entry.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        # Stamp text files; copy binaries as-is.
        try:
            content = entry.read_text(encoding="utf-8")
            target.write_text(stamp_path(content, data_dir, viz_dir), encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(entry, target)
        # Preserve executable bit for .sh files
        if entry.suffix == ".sh":
            target.chmod(0o755)
        created.append(target)
    return created


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("target", help="Directory to create `visualizations/` in (usually the project root)")
    p.add_argument("--data-dir", required=True, help="Absolute path to the user's data directory")
    p.add_argument("--force", action="store_true", help="Overwrite existing visualizations/")
    args = p.parse_args()

    target_root = Path(args.target).resolve()
    viz_dir = target_root / "visualizations"
    data_dir = Path(args.data_dir).resolve()

    if not data_dir.exists():
        print(f"WARNING: data dir does not exist yet: {data_dir}", file=sys.stderr)

    if viz_dir.exists():
        if not args.force:
            print(f"refusing to overwrite existing {viz_dir} (use --force or pick a different target)", file=sys.stderr)
            return 1
        shutil.rmtree(viz_dir)

    viz_dir.mkdir(parents=True)

    if not SCAFFOLDING.exists():
        print(f"missing scaffolding source: {SCAFFOLDING}", file=sys.stderr)
        return 2

    created = copy_tree(SCAFFOLDING, viz_dir, str(data_dir), str(viz_dir))

    # Empty placeholder dirs that rglob misses if they're empty in the template
    for sub in ("intermediate_data", "plots", "streamlit/pages"):
        (viz_dir / sub).mkdir(parents=True, exist_ok=True)

    print(f"scaffolded {len(created)} files into {viz_dir}")
    print(f"  data dir wired up:  {data_dir}")
    print(f"  next step:          edit visualizations/info/context.md, then run one of the .sh wrappers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
