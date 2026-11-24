#!/usr/bin/env python3
"""Run every unittest method in a fresh interpreter.

The scientific assertions remain unchanged. Process isolation prevents mocks,
module caches, temporary paths, and large parsed evidence objects from leaking
between otherwise independent tests. A timeout is a failure, never a skip.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest


def flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item.id()


def choose_tests(repo: Path) -> tuple[Path, Path]:
    candidates = [
        repo / ".worktree" / "artifact" / "tests",
        repo / ".worktree" / "tests",
        repo / "artifact" / "tests",
        repo / "tests",
    ]
    for tests in candidates:
        if tests.is_dir() and any(tests.glob("test_*.py")):
            project = tests.parent.parent if tests.parent.name == "artifact" else tests.parent
            return project.resolve(), tests.resolve()
    found = sorted(repo.rglob("test_*.py"))
    if not found:
        raise SystemExit("No unittest files were found. Run the repository preparation step first.")
    tests = found[0].parent
    return tests.parent.resolve(), tests.resolve()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--pattern", default="test_*.py")
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    project, tests = choose_tests(repo)
    sys.path[:0] = [str(project), str(tests.parent), str(tests)]
    suite = unittest.TestLoader().discover(str(tests), pattern=args.pattern)
    ids = list(flatten(suite))
    if not ids:
        raise SystemExit(f"No tests matched {args.pattern!r} beneath {tests}")

    env = os.environ.copy()
    roots = [str(project), str(tests.parent), str(tests), str(repo)]
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(roots + [env.get("PYTHONPATH", "")]))
    outdir = repo / ".worktree" / "test-results"
    outdir.mkdir(parents=True, exist_ok=True)
    records = []
    started = time.monotonic()

    for index, test_id in enumerate(ids, 1):
        print(f"[{index:03d}/{len(ids):03d}] {test_id}", flush=True)
        begin = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, "-X", "faulthandler", "-m", "unittest", "-v", test_id],
                cwd=project,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=args.timeout,
            )
            status = "passed" if proc.returncode == 0 else "failed"
            code = proc.returncode
            output = proc.stdout
        except subprocess.TimeoutExpired as exc:
            status = "timed_out"
            code = 124
            output = (exc.stdout or "") + (exc.stderr or "")
        elapsed = time.monotonic() - begin
        log = outdir / f"{index:03d}.log"
        log.write_text(output, encoding="utf-8", errors="replace")
        records.append({
            "test": test_id,
            "status": status,
            "returncode": code,
            "seconds": round(elapsed, 3),
            "log": str(log.relative_to(repo)),
        })
        if status != "passed":
            print(output, file=sys.stderr)
            break

    total = time.monotonic() - started
    summary = {
        "runner": "one unittest method per fresh interpreter",
        "tests_discovered": len(ids),
        "tests_executed": len(records),
        "passed": sum(r["status"] == "passed" for r in records),
        "failed": sum(r["status"] == "failed" for r in records),
        "timed_out": sum(r["status"] == "timed_out" for r in records),
        "seconds": round(total, 3),
        "records": records,
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if len(records) != len(ids) or any(r["status"] != "passed" for r in records):
        return 1
    print(f"PASS: {len(ids)} tests in {total:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
