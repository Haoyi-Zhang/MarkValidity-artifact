#!/usr/bin/env python3
"""Run the public artifact checks (smoke | full | paper).

Works on this repository alone; the paper-binding components additionally use
the paper sources (../paper or --paper DIR) when they are present.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path

ARTIFACT = Path(__file__).resolve().parents[1]
PROJECT = ARTIFACT.parent
REPORT_DIR = ARTIFACT / ".worktree"
# Fast receivers that need only this repository (no Node.js, no CREST downloads).
SMOKE_COMPONENTS = (
    "comparison-arithmetic",
    "matched-disclosure-primary",
    "paired-conditional-mathematics",
    "paired-conditional-index",
    "detector-null-enumeration",
    "source-query-budgets",
)


def run_stage(name: str, command: list[str], cwd: Path, env: dict[str, str]) -> dict[str, object]:
    print(f"\n== {name} ==", flush=True)
    print("$ " + " ".join(command), flush=True)
    started = time.time()
    proc = subprocess.run(command, cwd=cwd, env=env)
    elapsed = round(time.time() - started, 3)
    status = "passed" if proc.returncode == 0 else "failed"
    print(f"[{status}] {name} ({elapsed:.1f}s)", flush=True)
    return {"stage": name, "command": command, "returncode": proc.returncode, "seconds": elapsed}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run staged MarkValidity artifact checks.")
    parser.add_argument("level", choices=("smoke", "full", "paper"))
    parser.add_argument("--python", default=os.environ.get("PYTHON", sys.executable))
    parser.add_argument("--paper", type=Path,
                        help="Paper LaTeX sources (default: ../paper). Without them the paper-binding "
                             "components are reported as SKIPPED and the 'paper' level cannot run.")
    parser.add_argument("--crest-upstream-cache", type=Path,
                        help="Previously acquired CREST upstream files (see check.py --help); avoids the download.")
    args = parser.parse_args()
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")  # avoid locale-dependent decoding on Windows hosts
    paper = (args.paper or Path(env.get("MARKVALIDITY_PAPER", PROJECT / "paper"))).resolve()
    env["MARKVALIDITY_PAPER"] = str(paper)
    has_paper = (paper / "main.tex").is_file()
    if not has_paper:
        print(f"Note: no paper sources at {paper}; paper-binding checks will be SKIPPED "
              "(use --paper DIR to include them).", flush=True)
    py = args.python
    check = [py, "-B", "-S", "check.py"]
    smoke = [("fast evidence receivers (SEW arithmetic, paired certificates, query budgets)",
              check + ["--keep-going"] + [a for c in SMOKE_COMPONENTS for a in ("--component", c)], ARTIFACT)]
    if has_paper:
        smoke.insert(0, ("paper-data and citation bindings", check + ["--scope", "publication"], ARTIFACT))
    plans = {
        "smoke": smoke,
        "full": [
            # The tests scope is staged in the recorded layout by check.py; running
            # the unittest suites directly on the clean tree is not supported.
            ("implementation and rejection-path tests", check + ["--scope", "tests", "--keep-going"], ARTIFACT),
            ("scientific evidence receivers", check + ["--scope", "primary", "--keep-going"] +
             (["--crest-upstream-cache", str(args.crest_upstream_cache.resolve())] if args.crest_upstream_cache else []),
             ARTIFACT),
            ("supporting evidence receivers", check + ["--scope", "supporting", "--keep-going"], ARTIFACT),
        ],
        "paper": [
            ("regenerate publication material", [py, "paper/generate_publication.py", "--project", "."], PROJECT),
            ("compile manuscript and supplement", ["sh", "paper/build.sh"], PROJECT),
        ],
    }
    if args.level == "paper" and not (has_paper and paper == (PROJECT / "paper").resolve()):
        print("The 'paper' level regenerates and compiles the sibling ../paper directory of the "
              "submission package; it is not available in a standalone checkout.", file=sys.stderr)
        return 2
    REPORT_DIR.mkdir(exist_ok=True)
    results = []
    for name, command, cwd in plans[args.level]:
        result = run_stage(name, command, cwd, env)
        results.append(result)
        if result["returncode"] != 0 and args.level == "paper":
            break
    report = {
        "level": args.level,
        "status": "passed" if len(results) == len(plans[args.level]) and all(r["returncode"] == 0 for r in results) else "failed",
        "stages": results,
        "note": "Retained hosted-service outputs are not represented as fresh local executions.",
    }
    out = REPORT_DIR / f"artifact-{args.level}.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nReport: {out.relative_to(ARTIFACT)}", flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
