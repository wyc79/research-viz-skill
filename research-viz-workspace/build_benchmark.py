#!/usr/bin/env python3
"""Build benchmark.json for an iteration directory in the schema the eval-viewer expects."""
from __future__ import annotations

import datetime
import json
import statistics
import sys
from pathlib import Path


def aggregate(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0, "stddev": 0, "min": 0, "max": 0}
    return {
        "mean": round(statistics.mean(values), 4),
        "stddev": round(statistics.pstdev(values), 4) if len(values) > 1 else 0,
        "min": min(values),
        "max": max(values),
    }


def main() -> int:
    iter_dir = Path(sys.argv[1])
    skill_name = sys.argv[2] if len(sys.argv) > 2 else "research-viz"

    runs = []
    by_cfg: dict[str, dict[str, list]] = {}

    eval_dirs = sorted([d for d in iter_dir.iterdir() if d.is_dir() and d.name.startswith("eval-")])
    for ed in eval_dirs:
        # extract id and name
        parts = ed.name.split("-", 2)
        eval_id = int(parts[1])
        eval_name = parts[2]
        for cfg_dir in [d for d in ed.iterdir() if d.is_dir()]:
            cfg = cfg_dir.name
            grading_file = cfg_dir / "grading.json"
            timing_file = cfg_dir / "timing.json"
            if not grading_file.exists() or not timing_file.exists():
                continue
            grading = json.loads(grading_file.read_text())
            timing = json.loads(timing_file.read_text())
            summary = grading.get("summary", {})
            run = {
                "eval_id": eval_id,
                "eval_name": eval_name,
                "configuration": cfg,
                "run_number": 1,
                "result": {
                    "pass_rate": summary.get("pass_rate", 0),
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "total": summary.get("total", 0),
                    "time_seconds": timing.get("total_duration_seconds", 0),
                    "tokens": timing.get("total_tokens", 0),
                    "tool_calls": 0,
                    "errors": 0,
                },
                "expectations": grading.get("expectations", []),
                "notes": [],
            }
            runs.append(run)
            by_cfg.setdefault(cfg, {"pass_rate": [], "time": [], "tokens": []})
            by_cfg[cfg]["pass_rate"].append(run["result"]["pass_rate"])
            by_cfg[cfg]["time"].append(run["result"]["time_seconds"])
            by_cfg[cfg]["tokens"].append(run["result"]["tokens"])

    run_summary: dict[str, dict] = {}
    for cfg, vals in by_cfg.items():
        run_summary[cfg] = {
            "pass_rate": aggregate(vals["pass_rate"]),
            "time_seconds": aggregate(vals["time"]),
            "tokens": aggregate(vals["tokens"]),
        }

    # delta = with_skill - without_skill (when both exist)
    delta = {}
    if "with_skill" in run_summary and "without_skill" in run_summary:
        a = run_summary["with_skill"]
        b = run_summary["without_skill"]
        delta = {
            "pass_rate": f"{a['pass_rate']['mean'] - b['pass_rate']['mean']:+.2f}",
            "time_seconds": f"{a['time_seconds']['mean'] - b['time_seconds']['mean']:+.1f}",
            "tokens": f"{int(a['tokens']['mean'] - b['tokens']['mean']):+d}",
        }
    if delta:
        run_summary["delta"] = delta

    out = {
        "metadata": {
            "skill_name": skill_name,
            "skill_path": str((Path.cwd() / ".." / skill_name).resolve()),
            "executor_model": "claude-opus-4-7",
            "analyzer_model": "claude-opus-4-7",
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds") + "Z",
            "evals_run": [r["eval_id"] for r in runs if r["configuration"] == "with_skill"],
            "runs_per_configuration": 1,
        },
        "runs": runs,
        "run_summary": run_summary,
        "notes": [],
    }
    bench = iter_dir / "benchmark.json"
    bench.write_text(json.dumps(out, indent=2))
    print(f"wrote {bench}")
    print(f"  configurations: {list(run_summary.keys())}")
    for cfg, s in run_summary.items():
        if cfg == "delta":
            continue
        print(f"  {cfg}: pass_rate={s['pass_rate']['mean']:.2f}, time={s['time_seconds']['mean']:.1f}s, tokens={int(s['tokens']['mean'])}")
    if delta:
        print(f"  delta: {delta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
