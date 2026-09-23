#!/usr/bin/env python3
"""Trigger-evaluation harness for opencode.

Tests whether a skill's description causes opencode to invoke the skill for a
set of queries. It mirrors the skill-creator's `run_eval.py`, but drives the
`opencode` CLI instead of `claude`, so results match what opencode users see.

How it works: for each query it runs `opencode run "<query>" --format json` in a
temporary project that contains a copy of the skill under `.agents/skills/<name>/`,
then scans the JSON event stream for a `skill` tool call naming the skill.

Eval set format (same as skill-creator):
    [{"query": "...", "should_trigger": true}, ...]

Usage:
    python tools/trigger_eval_opencode.py \
        --skill-path skills/project-react-architecture \
        --eval-set evals/project-react-architecture/trigger_eval.json \
        [--runs-per-query 3] [--workers 3] [--timeout 180] [--model provider/model]

Exit code is 0 when every query passes, 1 otherwise.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def read_skill_name(skill_path: Path) -> str:
    text = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"Could not find 'name:' in {skill_path / 'SKILL.md'}")


def setup_project(project_dir: Path, skill_path: Path, skill_name: str) -> None:
    if project_dir.exists():
        shutil.rmtree(project_dir)
    dest = project_dir / ".agents" / "skills" / skill_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_path, dest)


def run_query(project_dir: Path, skill_name: str, query: str, timeout: int, model):
    cmd = ["opencode", "run", query, "--format", "json", "--dir", str(project_dir)]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except FileNotFoundError:
        return False, "opencode CLI not found"

    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = event.get("part") or {}
        if part.get("tool") == "skill":
            name = ((part.get("state") or {}).get("input") or {}).get("name")
            if name == skill_name:
                return True, "skill invoked"
    return False, "no skill invocation"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=180, help="seconds per query run")
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--model", default=None, help="opencode model as provider/model (default: configured)")
    parser.add_argument("--output", default=None, help="write full JSON results here")
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()
    skill_name = read_skill_name(skill_path)
    eval_set = json.loads(Path(args.eval_set).read_text())

    project_dir = Path(tempfile.mkdtemp(prefix="opencode-trigger-")) / "project"
    setup_project(project_dir, skill_path, skill_name)

    jobs = [(item, run_idx) for item in eval_set for run_idx in range(args.runs_per_query)]
    triggers = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(run_query, project_dir, skill_name, item["query"], args.timeout, args.model): item
            for item, _ in jobs
        }
        for future in as_completed(futures):
            item = futures[future]
            triggers.setdefault(item["query"], []).append(future.result()[0])

    results = []
    passed = 0
    for item in eval_set:
        runs = triggers.get(item["query"], [])
        rate = sum(runs) / len(runs) if runs else 0.0
        should = item["should_trigger"]
        ok = rate >= args.trigger_threshold if should else rate < args.trigger_threshold
        passed += ok
        results.append({"query": item["query"], "should_trigger": should,
                        "trigger_rate": round(rate, 3), "triggers": sum(runs), "runs": len(runs), "pass": ok})
        print(f"[{'PASS' if ok else 'FAIL'}] rate={sum(runs)}/{len(runs)} expected={should}: {item['query'][:70]}")

    total = len(results)
    print(f"\n{passed}/{total} queries passed")
    output = {"skill_name": skill_name, "summary": {"passed": passed, "total": total}, "results": results}
    if args.output:
        Path(args.output).write_text(json.dumps(output, indent=2) + "\n")
    shutil.rmtree(project_dir.parent, ignore_errors=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
