"""Part 2: repository-derived empirical null for the real (pinned stock) SEW detector.

Runs sew.detect(code, 'python', key) on every unwatermarked source of the declared
populations under all 1,003 declared keys. Requires tree-sitter==0.23.2 and
tree-sitter-python==0.23.6. POSIX only (SIGALRM guard). Usage (artifact root):

    python -B studies/null-calibration/run_sew_null.py --out results/null-calibration --workers 16
"""
from __future__ import annotations

import argparse
import csv
import datetime
import gzip
import hashlib
import importlib.metadata
import json
import multiprocessing
import platform
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "studies" / "sew" / "variants" / "stock"
HE_DATA = ROOT / "results" / "sew" / "humaneval" / "data" / "HumanEval.jsonl.gz"
HE_DATA_SHA = "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"
HE_REFS = ROOT / "results" / "sew" / "humaneval" / "references.json"
MBPP_DATA = ROOT / "studies" / "sew" / "mbpp" / "sanitized-mbpp.json"
MBPP_REFS = ROOT / "results" / "sew" / "mbpp" / "factors" / "stock" / "references.json"
MANIFEST = ROOT / "corpus" / "transfer_manifest.csv"
TRANSFER = ROOT / "corpus" / "transfer"
SPEC = ROOT / "results" / "sew" / "humaneval" / "specification.json"
TIMEOUT = 60
VERDICT_CODE = {"Watermark detected": "D", "No watermark evidence": "N", "Insufficient evidence": "I"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def declared_keys():
    keys = [("upstream_default", bytes.fromhex("76" * 16)), ("integer_0", (0).to_bytes(16, "big")),
            ("integer_1", (1).to_bytes(16, "big"))]
    keys += [("integer_%d" % i, i.to_bytes(16, "big")) for i in range(2, 1002)]
    assert len(keys) == 1003 and len({k for _, k in keys}) == 1003
    return keys


def vendor_check():
    spec = json.loads(SPEC.read_text())
    stock = [v for v in spec["variants"] if v["variant"] == "stock"][0]["vendor_files_sha256"]
    actual = {p.relative_to(VENDOR).as_posix(): sha(p.read_bytes()) for p in sorted(VENDOR.rglob("*"))
              if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    if actual != stock:
        raise SystemExit("stock SEW vendor files differ from the recorded specification")
    return actual


def build_population():
    units = []
    raw = HE_DATA.read_bytes()
    assert sha(raw) == HE_DATA_SHA
    tasks = [json.loads(x) for x in gzip.decompress(raw).decode().splitlines()]
    retained = {r["task_id"]: r["reference_sha256"] for r in json.loads(HE_REFS.read_text())}
    assert len(tasks) == 164
    for t in tasks:
        src = t["prompt"] + t["canonical_solution"]
        s = sha(src.encode())
        units.append({"corpus": "humaneval", "source_id": t["task_id"], "sha256": s,
                      "identity_ok": retained.get(t["task_id"]) == s, "source": src,
                      "origin": "results/sew/humaneval/data/HumanEval.jsonl.gz prompt+canonical_solution"})
    mbpp = json.loads(MBPP_DATA.read_text())
    assert len(mbpp) == 427
    retained = {r["task_id"]: r["source_sha256"] for r in json.loads(MBPP_REFS.read_text())}
    for t in mbpp:
        src = t["code"]
        s = sha(src.encode())
        units.append({"corpus": "mbpp", "source_id": "MBPP/%d" % t["task_id"], "sha256": s,
                      "identity_ok": retained.get(t["task_id"]) == s, "source": src,
                      "origin": "studies/sew/mbpp/sanitized-mbpp.json code"})
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 120
    for r in rows:
        rel = "corpus/transfer/%s/module-%s.py" % (r["project_slug"], r["module_id"].rsplit("-", 1)[1])
        unit = {"corpus": "projects", "source_id": r["module_id"], "project": r["project"], "path": rel,
                "expected_sha256": r["source_sha256"], "origin": rel}
        p = ROOT / rel
        if not p.is_file():
            unit.update(identity_ok=False, unavailable_reason="file missing", sha256=None, source=None)
        else:
            b = p.read_bytes()
            unit["sha256"] = sha(b)
            unit["identity_ok"] = unit["sha256"] == r["source_sha256"]
            try:
                unit["source"] = b.decode("utf-8")
            except UnicodeDecodeError as exc:
                unit.update(source=None, unavailable_reason="utf-8 decode error: %s" % exc)
        units.append(unit)
    for u in units:
        if not u["identity_ok"] and "unavailable_reason" not in u:
            u["unavailable_reason"] = "source SHA-256 differs from retained identity"
    return units


_detect = None


def _init():
    global _detect
    sys.path.insert(0, str(VENDOR))
    from sew import detect
    _detect = detect


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout("detect() exceeded %d s" % TIMEOUT)


def process(job):
    index, unit, keys = job
    out = {k: v for k, v in unit.items() if k != "source"}
    out["index"] = index
    if unit.get("unavailable_reason"):
        out.update(status="unavailable", results=None)
        return out
    started = time.monotonic()
    results, invariant = [], None
    signal.signal(signal.SIGALRM, _alarm)
    for ki, (key_id, key) in enumerate(keys):
        signal.setitimer(signal.ITIMER_REAL, TIMEOUT)
        try:
            d = _detect(unit["source"], "python", key)
            err = None
        except BaseException as exc:  # noqa: BLE001 - every failure is recorded as unavailable
            d, err = None, "%s: %s" % (type(exc).__name__, exc)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        if d is None:
            results.append(["U", err])
            continue
        if d.get("reason") == "parse":
            inv = {"parse_abstention": True, "n_grades": d["n_grades"]}
            row = [VERDICT_CODE[d["verdict"]], d["p"], None, None, None, None]
            assert set(d) == {"verdict", "reason", "p", "n_grades"}
        else:
            inv = {"parse_abstention": False, "n_grades": d["n_grades"], "n_syntax": d["n_syntax"], "n_sites": d["n_sites"]}
            assert set(d) == {"verdict", "p", "p_all", "p_syntax", "n_grades", "k_grades", "n_syntax", "k_syntax", "n_sites"}
            row = [VERDICT_CODE[d["verdict"]], d["p"], d["p_all"], d["p_syntax"], d["k_grades"], d["k_syntax"]]
        if invariant is None:
            invariant = inv
        elif inv != invariant:
            row.append(inv)  # key-specific structural fields (not expected; retained if it happens)
        results.append(row)
    out.update(status="available" if invariant is not None else "unavailable", structure=invariant, results=results,
               elapsed_seconds=round(time.monotonic() - started, 3))
    if invariant is None:
        out["unavailable_reason"] = "every detect() call failed: " + str(results[0][1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    vendor = vendor_check()
    keys = declared_keys()
    units = build_population()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    for name in ("sew-null-humaneval.jsonl.gz", "sew-null-mbpp.jsonl.gz", "sew-null-projects.jsonl.gz"):
        if (out / name).exists():
            raise SystemExit("refusing to overwrite " + name)
    protocol = ROOT / "studies" / "null-calibration" / "protocol.json"
    run = {"schema": "markvalidity-null-calibration-sew-run-v1", "protocol_sha256": sha(protocol.read_bytes()),
           "producer_sha256": sha(Path(__file__).read_bytes()),
           "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "python": platform.python_version(), "implementation": platform.python_implementation(),
           "platform": platform.platform(),
           "tree_sitter": importlib.metadata.version("tree-sitter"),
           "tree_sitter_python": importlib.metadata.version("tree-sitter-python"),
           "vendor": "studies/sew/variants/stock", "vendor_files_sha256": vendor,
           "detect_call": "sew.detect(source, 'python', key) with defaults (calibrate=True, alpha=config.ALPHA=0.01)",
           "timeout_seconds_per_call": TIMEOUT, "workers": args.workers,
           "keys": [{"index": i, "key_id": k, "hex": v.hex()} for i, (k, v) in enumerate(keys)],
           "row_format": "results[key_index] = [verdict_code, p, p_all, p_syntax, k_grades, k_syntax] (parse abstention: p_all..k_syntax null) or ['U', error]; verdict_code D=Watermark detected, N=No watermark evidence, I=Insufficient evidence, U=unavailable",
           "population_counts": {c: sum(u["corpus"] == c for u in units) for c in ("humaneval", "mbpp", "projects")}}
    start = time.monotonic()
    jobs = [(i, u, keys) for i, u in enumerate(units)]
    done = []
    with multiprocessing.Pool(args.workers, initializer=_init) as pool:
        for r in pool.imap_unordered(process, jobs, chunksize=1):
            done.append(r)
            if len(done) % 50 == 0:
                print(json.dumps({"sources_done": len(done), "elapsed": round(time.monotonic() - start, 1)}), flush=True)
    done.sort(key=lambda r: r["index"])
    for corpus in ("humaneval", "mbpp", "projects"):
        path = out / ("sew-null-%s.jsonl.gz" % corpus)
        with gzip.GzipFile(path, "wb", compresslevel=9, mtime=0) as f:
            for r in done:
                if r["corpus"] == corpus:
                    f.write((json.dumps(r, sort_keys=True) + "\n").encode("utf-8"))
        run.setdefault("files_sha256", {})[path.name] = sha(path.read_bytes())
    run["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    run["elapsed_seconds"] = round(time.monotonic() - start, 1)
    (out / "sew-run.json").write_text(json.dumps(run, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"complete": len(done), "elapsed": run["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
