#!/usr/bin/env python3
"""Programmatic grader for research-viz iteration-N runs.

For each (eval, config) pair, run the assertions defined here against the
files under <eval>/<config>/outputs/ and emit grading.json with the
expected schema (text, passed, evidence).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable

import pandas as pd

WS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "iteration-1"

EVALS = [
    {"id": 1, "name": "parser-messy-clinical-csv"},
    {"id": 2, "name": "plotgen-multi-panel-flowers"},
    {"id": 3, "name": "interactive-streamlit-sensor-log"},
]

CONFIGS = ["with_skill", "without_skill"]


def grade_one(out_dir: Path, eval_id: int) -> list[dict]:
    """Return a list of {text, passed, evidence}."""
    results: list[dict] = []
    viz = out_dir / "visualizations"

    def add(text: str, passed: bool, evidence: str) -> None:
        # numpy/pandas booleans aren't JSON-serializable — coerce.
        results.append({"text": text, "passed": bool(passed), "evidence": str(evidence)})

    def file_exists(p: Path) -> bool:
        return p.exists() and p.is_file()

    def grep_any(p: Path, patterns: list[str]) -> tuple[bool, str]:
        if not p.exists():
            return False, f"{p} missing"
        text = p.read_text(encoding="utf-8", errors="replace")
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return True, f"matched /{pat}/i in {p.name}"
        return False, f"none of {patterns} found in {p.name}"

    def find_pattern_in_dir(d: Path, pattern: str, suffixes: tuple[str, ...] = (".py",)) -> tuple[bool, str]:
        if not d.exists():
            return False, f"{d} missing"
        for f in d.rglob("*"):
            if f.is_file() and (not suffixes or f.suffix in suffixes):
                try:
                    text = f.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                if re.search(pattern, text, re.IGNORECASE):
                    return True, f"matched /{pattern}/i in {f.relative_to(d.parent)}"
        return False, f"pattern /{pattern}/ not found in any file under {d}"

    # ============================================================
    # Common assertions — only require subskill-specific files when the
    # eval's user prompt actually asked for that subskill. The skill's
    # "trim unused subskills" rule means an agent who only ran the parser
    # is allowed to delete plot_gen.py / generate_plot.sh / streamlit/.
    # ============================================================
    needs_plotgen = eval_id == 2
    needs_streamlit = eval_id == 3

    add("visualizations/ directory exists at the project root",
        viz.is_dir(), f"viz dir exists: {viz.is_dir()}")
    add("visualizations/scripts/parser.py exists",
        file_exists(viz / "scripts" / "parser.py"),
        f"path: {viz/'scripts'/'parser.py'}")
    if needs_plotgen:
        add("visualizations/scripts/plot_gen.py exists",
            file_exists(viz / "scripts" / "plot_gen.py"),
            f"path: {viz/'scripts'/'plot_gen.py'}")
    # helpers/utils.py is only required when plot_gen.py ships with the
    # project — its main consumers were `set_research_theme` / `slugify` for
    # plot recipes. A streamlit-only or parser-only run is allowed to trim it.
    if needs_plotgen:
        add("visualizations/scripts/helpers/utils.py exists",
            file_exists(viz / "scripts" / "helpers" / "utils.py"),
            f"path: {viz/'scripts'/'helpers'/'utils.py'}")
    add("visualizations/parse_input.sh exists",
        file_exists(viz / "parse_input.sh"),
        f"path: {viz/'parse_input.sh'}")
    if needs_plotgen:
        add("visualizations/generate_plot.sh exists",
            file_exists(viz / "generate_plot.sh"),
            f"path: {viz/'generate_plot.sh'}")
    if needs_streamlit:
        add("visualizations/interactive_page.sh exists",
            file_exists(viz / "interactive_page.sh"),
            f"path: {viz/'interactive_page.sh'}")
    add("visualizations/info/context.md exists",
        file_exists(viz / "info" / "context.md"),
        f"path: {viz/'info'/'context.md'}")
    add("visualizations/info/how_to_use.md exists",
        file_exists(viz / "info" / "how_to_use.md"),
        f"path: {viz/'info'/'how_to_use.md'}")

    # ============================================================
    # Helper: locate the parsed CSV under either the new convention
    # (`<dataset>__parsed.csv`, possibly listed in parsed_index.json) or
    # the legacy `parsed_results.csv` from earlier iterations.
    # ============================================================
    def find_parsed_csv(dataset_stem: str) -> Path | None:
        inter = viz / "intermediate_data"
        if not inter.exists():
            return None
        # 1) New canonical-CSV manifest
        idx = inter / "parsed_index.json"
        if idx.exists():
            try:
                manifest = json.loads(idx.read_text())
                cand = manifest.get("canonical_csv")
                if cand and (inter / cand).exists():
                    return inter / cand
                for entry in manifest.get("per_file_outputs", []):
                    p = entry.get("parsed_path")
                    if p and (inter / p).exists():
                        return inter / p
            except Exception:
                pass
        # 2) New naming directly: <dataset>__parsed.csv anywhere under intermediate_data/
        for cand in inter.rglob(f"{dataset_stem}__parsed.csv"):
            return cand
        for cand in inter.rglob("*__parsed.csv"):
            return cand
        # 3) Legacy: parsed_results.csv
        legacy = inter / "parsed_results.csv"
        if legacy.exists():
            return legacy
        return None

    # ============================================================
    # Per-eval extras
    # ============================================================
    if eval_id == 1:
        import json
        parsed = find_parsed_csv("trial_data_messy")
        meta = viz / "intermediate_data" / (parsed.stem.replace("__parsed", "__parsed.meta") + ".json") if parsed else None
        if not (meta and meta.exists()):
            # Either the legacy meta name or the new parsed_index.json with strategies
            legacy_meta = viz / "intermediate_data" / "parsed_results.meta.json"
            new_index = viz / "intermediate_data" / "parsed_index.json"
            meta = legacy_meta if legacy_meta.exists() else new_index
        add("intermediate_data parsed CSV exists (new <dataset>__parsed.csv or legacy parsed_results.csv)",
            parsed is not None and parsed.exists(),
            f"found: {parsed}" if parsed else "no parsed CSV under intermediate_data/")
        meta_records_strategies = False
        if meta and meta.exists():
            mt = meta.read_text()
            meta_records_strategies = ("strategies_applied" in mt) or ("PROJECT_STRATEGIES" in mt)
        add("strategies are recorded (meta.json or parsed_index.json)",
            meta_records_strategies, f"path: {meta}")
        if parsed and parsed.exists():
            try:
                df = pd.read_csv(parsed)
                add("parsed CSV has 200 rows or fewer (drop_row may shrink)",
                    len(df) <= 200, f"rows={len(df)}, cols={len(df.columns)}")
                pa_numeric = "patient_age" in df.columns and pd.api.types.is_numeric_dtype(df["patient_age"])
                add("patient_age column is numeric",
                    pa_numeric,
                    f"dtype={df['patient_age'].dtype if 'patient_age' in df.columns else 'MISSING'}")
                bp_no_nan = ("blood_pressure" in df.columns) and df["blood_pressure"].isna().sum() == 0
                add("blood_pressure has no NaN (median was applied)",
                    bp_no_nan,
                    f"NaN count={df['blood_pressure'].isna().sum() if 'blood_pressure' in df.columns else 'col missing'}")
            except Exception as e:
                add("parsed CSV readable", False, f"error: {e}")
        else:
            add("parsed CSV has 200 rows or fewer", False, "file missing")
            add("patient_age numeric", False, "file missing")
            add("blood_pressure no NaN", False, "file missing")

        ok, ev = grep_any(viz / "info" / "context.md",
                          [r"parser", r"parsing", r"clean", r"strateg"])
        add("context.md mentions parser/parsing/cleaning", ok, ev)

    if eval_id == 2:
        parsed = find_parsed_csv("flowers")
        if parsed and parsed.exists():
            try:
                df = pd.read_csv(parsed)
                add("parsed CSV has 150 rows", len(df) == 150,
                    f"rows={len(df)} (file: {parsed.name})")
            except Exception as e:
                add("parsed CSV readable (150 rows)", False, str(e))
        else:
            add("parsed CSV exists with 150 rows", False, "file missing")

        plots_dir = viz / "plots"
        scatter_ok = False
        scatter_ev = "no plots dir"
        violin_ok = False
        violin_ev = "no plots dir"
        each_has_csv = False
        if plots_dir.exists():
            subdirs = [d for d in plots_dir.iterdir() if d.is_dir()]
            for d in subdirs:
                slug = d.name.lower()
                pngs = list(d.glob("*.png"))
                if pngs and ("scatter" in slug or ("petal" in slug and ("vs" in slug or "_v_" in slug or "_x_" in slug))):
                    scatter_ok = True
                    scatter_ev = f"png in {d.relative_to(viz)}"
                if pngs and ("violin" in slug or ("sepal" in slug and ("species" in slug or "per_" in slug))):
                    violin_ok = True
                    violin_ev = f"png in {d.relative_to(viz)}"
            csvs_per_subdir = [bool(list(d.glob("*.csv"))) for d in subdirs if list(d.glob("*.png"))]
            each_has_csv = bool(csvs_per_subdir) and all(csvs_per_subdir)

        add("a plot subfolder under visualizations/plots/ contains a scatter PNG (petal length vs width)",
            scatter_ok, scatter_ev)
        add("a plot subfolder under visualizations/plots/ contains a violin PNG (sepal length per species)",
            violin_ok, violin_ev)
        add("each plot subfolder contains a tidy data.csv next to figure.png",
            each_has_csv,
            "all png-bearing subdirs have a CSV" if each_has_csv else "at least one is missing CSV")
        ok, ev = grep_any(viz / "info" / "context.md",
                          [r"scatter", r"violin", r"plot"])
        add("context.md mentions both plots", ok, ev)

    if eval_id == 3:
        parsed = find_parsed_csv("sensor_log")
        if parsed and parsed.exists():
            try:
                df = pd.read_csv(parsed)
                add("parsed CSV has 800 rows", len(df) == 800,
                    f"rows={len(df)} (file: {parsed.name})")
            except Exception as e:
                add("parsed CSV readable (800 rows)", False, str(e))
        else:
            add("parsed CSV exists with 800 rows", False, "file missing")

        st_index = viz / "streamlit" / "index.py"
        add("visualizations/streamlit/index.py exists", file_exists(st_index),
            f"path: {st_index}")

        streamlit_dir = viz / "streamlit"
        ok_filter, ev_filter = find_pattern_in_dir(
            streamlit_dir,
            r"selectbox|multiselect|radio|checkbox",
        )
        # Stronger: must reference site/sensor in widget
        ok_filter2, ev_filter2 = find_pattern_in_dir(
            streamlit_dir, r"(site|sensor)"
        )
        add("streamlit code has filter widgets (selectbox/multiselect/radio)",
            ok_filter, ev_filter)
        add("streamlit code references the 'site' and/or 'sensor' columns",
            ok_filter2, ev_filter2)

        ok_ts, ev_ts = find_pattern_in_dir(
            streamlit_dir,
            r"line_chart|altair_chart|plotly_chart|sns\.lineplot|st\.line",
        )
        add("streamlit code plots a time-series of value (line/altair chart)",
            ok_ts, ev_ts)

        ok, ev = grep_any(viz / "info" / "context.md",
                          [r"streamlit", r"dashboard", r"interactive"])
        add("context.md mentions the streamlit dashboard", ok, ev)

    return results


def main() -> int:
    for ev in EVALS:
        for cfg in CONFIGS:
            run_dir = WS / f"eval-{ev['id']}-{ev['name']}" / cfg
            if not run_dir.exists():
                continue  # iteration-2 may only have with_skill
            out_dir = run_dir / "outputs"
            assertions = grade_one(out_dir, ev["id"])
            passed = sum(1 for a in assertions if a["passed"])
            total = len(assertions)
            grading = {
                "expectations": assertions,
                "summary": {
                    "passed": passed,
                    "failed": total - passed,
                    "total": total,
                    "pass_rate": round(passed / total, 4) if total else 0,
                },
            }
            (run_dir / "grading.json").write_text(json.dumps(grading, indent=2))
            print(f"{ev['name']} / {cfg}: {passed}/{total}  ({100*passed/total:.0f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
