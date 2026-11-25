"""Run the pre-declared transfer-tests study (see protocol.json).

Phases (each idempotent, state kept under --work):
  setup       build one isolated venv per project, record resolved versions
  baseline    run each project's suite twice on unmodified code, decide eligibility
  variants    clone eligible environments, run every (module, intervention) cell
  export      write raw records and baseline sets into --results

Usage (Linux/WSL):
  python3 -I run_transfer_tests.py --work DIR --results DIR PHASE [--projects a,b]
Standard library only; pytest runs inside the per-project venvs.
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures as cf
import gzip
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from variants import INTERVENTIONS, all_variants  # noqa: E402

PROTOCOL = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
DEVIATIONS = json.loads((HERE / "deviations.json").read_text(encoding="utf-8"))
for _name, _dev in DEVIATIONS["projects"].items():
    PROTOCOL["projects"][_name] = dict(PROTOCOL["projects"][_name], **_dev["override"])
PLUGIN_DIR = HERE / "plugin"
DEPS = Path.home() / "deps/MarkValidity_TOSEM"
UV = DEPS / "bin/uv"
PYTHON = DEPS / "python/cpython-3.12.14-linux-x86_64-gnu/bin/python3.12"
EXCLUDE_NEWER = "2026-11-24T00:00:00Z"
TIMEOUT = int(PROTOCOL["test_command"]["timeout_seconds"])
MAX_PARALLEL = 18
PROXY = "http://127.0.0.1:7897"
LOCK = threading.Lock()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def log(msg: str) -> None:
    with LOCK:
        print(time.strftime("%H:%M:%S"), msg, flush=True)


def jdump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def jload(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


# ---------------------------------------------------------------- setup ---

def find_by_hash(root: Path, wanted: dict[str, str]) -> dict[str, list[str]]:
    """module_id -> relative paths under root whose UTF-8 text hash matches."""
    by_hash: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.py")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        by_hash.setdefault(sha_text(text), []).append(str(path.relative_to(root)))
    return {mid: by_hash.get(h, []) for mid, h in wanted.items()}


def site_packages(venv: Path) -> Path:
    return venv / "lib/python3.12/site-packages"


def setup_project(name: str, work: Path, items: dict) -> dict:
    cfg = PROTOCOL["projects"][name]
    sources = jload(work / "sources.json")
    pdir = work / "envs" / name
    state_path = pdir / "setup.json"
    state = jload(state_path)
    if state and state.get("status") in ("ok", "failed"):
        return state
    if pdir.exists():
        shutil.rmtree(pdir)
    c0 = pdir / "c0"
    c0.mkdir(parents=True)
    src_root = Path(sources[name]["git_tag"]["root"]) if cfg["source"] == "git-tag" else Path(sources[name]["root"])
    state = {"project": name, "source": cfg["source"], "source_root": str(src_root), "status": "failed"}
    shutil.copytree(src_root, c0 / "src", symlinks=True)
    shutil.copytree(src_root, pdir / "build-src", symlinks=True)
    mods = {mid: it["record"]["source_sha256"] for mid, it in items.items() if it["record"]["project"] == name}
    located = find_by_hash(c0 / "src", mods)
    state["modules_in_test_tree"] = located
    venv = c0 / "venv"
    env = dict(os.environ, UV_CACHE_DIR=str(DEPS / "uv-cache"), https_proxy=PROXY, http_proxy=PROXY,
               HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY, **cfg.get("install_env", {}))
    logs: list[str] = []

    def run(cmd, cwd, extra_env=None, timeout=3600):
        proc = subprocess.run(cmd, cwd=cwd, env=dict(env, **(extra_env or {})), capture_output=True, text=True, timeout=timeout)
        logs.append("$ " + " ".join(map(str, cmd)) + f"\n[exit {proc.returncode}]\n" + proc.stdout[-4000:] + proc.stderr[-8000:])
        return proc.returncode

    if run([UV, "venv", "--python", PYTHON, venv], cwd=pdir) != 0:
        state["reason"] = "install failure (venv)"
    else:
        target = str(pdir / "build-src")
        if cfg.get("extras"):
            target += "[" + ",".join(cfg["extras"]) + "]"
        deps = list(cfg["deps"])
        state["exclude_newer"] = cfg.get("exclude_newer", EXCLUDE_NEWER)
        base = [UV, "pip", "install", "--python", venv / "bin/python", "--exclude-newer", state["exclude_newer"]]
        rc = run(base + [target] + deps, cwd=c0 / "src")
        state["resolution"] = "declared"
        if rc != 0:
            loose = []
            skip = False
            for dep in deps:
                if skip:
                    skip = False
                    loose.append(dep)
                    continue
                if dep == "-r":
                    skip = True
                    loose.append(dep)
                    continue
                loose.append(re.split(r"[ <>=!~;]", dep.strip(), maxsplit=1)[0])
            if any(d == "-r" for d in deps):
                # unpin a lock file by stripping its specifiers into a temporary list
                expanded = []
                for i, dep in enumerate(deps):
                    if dep == "-r":
                        continue
                    if i > 0 and deps[i - 1] == "-r":
                        for line in (c0 / "src" / dep).read_text(encoding="utf-8").splitlines():
                            line = line.split("#", 1)[0].strip()
                            if line and not line.startswith("-"):
                                expanded.append(re.split(r"[ <>=!~;\[]", line, maxsplit=1)[0])
                    else:
                        expanded.append(re.split(r"[ <>=!~;]", dep.strip(), maxsplit=1)[0])
                loose = expanded
            state["resolution"] = "unpinned-fallback"
            state["fallback_deps"] = loose
            rc = run(base + [target] + loose, cwd=c0 / "src")
        if rc != 0:
            state["reason"] = "install failure"
        else:
            setup_ok = True
            for cmd in cfg.get("setup", []):
                cmd = [str(venv / "bin/python") if part == "python" else part for part in cmd]
                if run(cmd, cwd=c0 / "src") != 0:
                    setup_ok = False
            if not setup_ok:
                state["reason"] = "setup failure"
            else:
                freeze = subprocess.run([UV, "pip", "freeze", "--python", venv / "bin/python"], env=env, capture_output=True, text=True)
                state["resolved"] = sorted(line for line in freeze.stdout.splitlines() if line.strip())
                state["modules_in_site_packages"] = find_by_hash(site_packages(venv), mods)
                hyp = subprocess.run([venv / "bin/python", "-c", "import hypothesis"], capture_output=True)
                state["hypothesis"] = hyp.returncode == 0
                state["status"] = "ok"
    (pdir / "setup.log").write_text("\n\n".join(logs), encoding="utf-8")
    jdump(state_path, state)
    log(f"setup {name}: {state['status']} {state.get('reason', '')} {state.get('resolution', '')}")
    return state


# ----------------------------------------------------------------- runs ---

def clone_paths(work: Path, name: str, idx: int) -> tuple[Path, Path]:
    c = work / "envs" / name / f"c{idx}"
    return c / "src", c / "venv"


def module_files(work: Path, name: str, idx: int, module_id: str, setup: dict) -> list[Path]:
    src, venv = clone_paths(work, name, idx)
    files = [src / rel for rel in setup["modules_in_test_tree"].get(module_id, [])]
    files += [site_packages(venv) / rel for rel in setup.get("modules_in_site_packages", {}).get(module_id, [])]
    return files


def all_targets(work: Path, name: str, idx: int, setup: dict) -> list[Path]:
    out: list[Path] = []
    for mid in sorted(setup["modules_in_test_tree"]):
        out += module_files(work, name, idx, mid, setup)
    return out


def clear_bytecode(path: Path) -> None:
    cache = path.parent / "__pycache__"
    if cache.is_dir():
        for pyc in cache.glob(path.stem + ".*.pyc"):
            pyc.unlink()


def pytest_command(name: str, venv: Path, setup: dict) -> list[str]:
    cfg = PROTOCOL["projects"][name]
    cmd = [str(venv / "bin/python"), "-m", "pytest", "-p", "no:cacheprovider", "-p", "no:randomly", "-p", "tt_monitor",
           "-q", "--tb=line", "-rN", "--continue-on-collection-errors"]
    if setup.get("hypothesis"):
        cmd.append("--hypothesis-seed=0")
    cmd += cfg.get("pytest_args", [])
    return cmd


def run_suite(work: Path, name: str, idx: int, setup: dict, label: str) -> dict:
    src, venv = clone_paths(work, name, idx)
    cdir = src.parent
    # short TMPDIR: AF_UNIX socket paths are limited to 108 bytes
    home, tmp = cdir / "home", Path("/tmp/tt") / f"{name}-c{idx}"
    tmp.parent.mkdir(exist_ok=True)
    for d in (home, tmp):
        if d.exists():
            subprocess.run(["chmod", "-R", "u+rwX", str(d)], capture_output=True)
            shutil.rmtree(d, ignore_errors=True)
        d.mkdir(exist_ok=True)
    report = work / "reports" / name / f"{label}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    if report.exists():
        report.unlink()
    env = {
        "PATH": f"{venv / 'bin'}:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "VIRTUAL_ENV": str(venv),
        "PYTHONPATH": str(PLUGIN_DIR),
        "TT_REPORT": str(report),
        "TT_TARGETS": os.pathsep.join(str(p) for p in all_targets(work, name, idx, setup)),
        "HOME": str(home), "TMPDIR": str(tmp),
    }
    env.update(PROTOCOL["environment"]["fixed_env"])
    env["HOME"], env["TMPDIR"] = str(home), str(tmp)
    env.update(PROTOCOL["projects"][name].get("env", {}))
    uid, gid = os.getuid(), os.getgid()
    # loopback plus an unrouted dummy interface: getaddrinfo(AI_ADDRCONFIG)
    # resolves 'localhost' only when a non-loopback address exists; there is
    # still no route and no reachable resolver, so the Internet stays unreachable.
    inner = ('ip link set lo up && ip link add tt0 type dummy && ip addr add 10.213.0.1/24 dev tt0'
             ' && ip addr add fd00:7474::1/64 dev tt0 nodad && ip link set tt0 up'
             f' && exec unshare --user --map-user={uid} --map-group={gid} -- "$@"')
    cmd = ["unshare", "-rn", "sh", "-c", inner, "sh"] + pytest_command(name, venv, setup)
    start = time.monotonic()
    out_path = work / "reports" / name / f"{label}.out"
    with out_path.open("wb") as out:
        proc = subprocess.Popen(cmd, cwd=src, env=env, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        timed_out = False
        try:
            proc.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    duration = round(time.monotonic() - start, 1)
    data = jload(report) if report.exists() and not timed_out else None
    return {"label": label, "clone": idx, "returncode": proc.returncode, "timed_out": timed_out,
            "duration_s": duration, "report": data}


def counts(data: dict | None) -> dict:
    keys = ("passed", "failed", "error", "skipped", "xfailed", "xpassed")
    c = {k: 0 for k in keys}
    if data:
        for entry in data["tests"].values():
            c[entry["outcome"] if entry["outcome"] in c else "error"] += 1
    c["run"] = c["passed"] + c["failed"] + c["error"] + c["xfailed"] + c["xpassed"]
    c["collect_errors"] = len(data["collect_errors"]) if data else 0
    return c


def passed_set(data: dict | None) -> set[str]:
    if not data:
        return set()
    return {nid for nid, e in data["tests"].items() if e["outcome"] == "passed"}


def target_first_line(source: str, line: int) -> tuple[str, int]:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.lineno == line:
            return node.name, min([line] + [d.lineno for d in node.decorator_list])
    raise ValueError("target not found")


def exercise(data: dict | None, files: list[Path], fname: str, fline: int) -> dict:
    out = {"imported": False, "exercised": False, "target_function_executed": False, "functions_executed": 0}
    if not data:
        return out
    seen = set()
    for f in files:
        for co_name, firstline, newlocals in data["executed"].get(os.path.normpath(f), []):
            seen.add((co_name, firstline, newlocals))
    out["imported"] = any(n == "<module>" for n, _, _ in seen)
    funcs = {(n, l) for n, l, nl in seen if nl}
    out["exercised"] = bool(funcs)
    out["functions_executed"] = len(funcs)
    out["target_function_executed"] = (fname, fline) in funcs
    return out


def baseline_project(name: str, work: Path) -> dict:
    pdir = work / "envs" / name
    setup = jload(pdir / "setup.json")
    path = pdir / "baseline.json"
    state = jload(path)
    if state:
        return state
    state = {"project": name, "eligible": False}
    if setup["status"] != "ok":
        state["reason"] = setup.get("reason", "install failure")
        jdump(path, state)
        return state
    runs = []
    for k in (1, 2):
        r = run_suite(work, name, 0, setup, f"baseline{k}")
        runs.append(r)
        log(f"baseline {name} #{k}: rc={r['returncode']} t={r['duration_s']} {counts(r['report'])}")
    state["runs"] = [{k: v for k, v in r.items() if k != "report"} | {"counts": counts(r["report"])} for r in runs]
    if any(r["timed_out"] for r in runs):
        state["reason"] = "baseline timeout"
    elif any(r["report"] is None or counts(r["report"])["passed"] == 0 for r in runs):
        state["reason"] = "baseline did not complete"
    else:
        state["eligible"] = True
        base = sorted(passed_set(runs[0]["report"]) & passed_set(runs[1]["report"]))
        state["baseline_passing"] = base
        state["flaky_excluded"] = sorted(passed_set(runs[0]["report"]) ^ passed_set(runs[1]["report"]))
        d = runs[0]["duration_s"]
        state["clones"] = 1 if d <= 60 else 3 if d <= 300 else 5
    jdump(path, state)
    return state


def make_clone(work: Path, name: str, idx: int) -> None:
    c0 = work / "envs" / name / "c0"
    ci = work / "envs" / name / f"c{idx}"
    if (ci / "ready").exists():
        return
    if ci.exists():
        shutil.rmtree(ci)
    ci.mkdir()
    shutil.copytree(c0 / "src", ci / "src", symlinks=True)
    shutil.copytree(c0 / "venv", ci / "venv", symlinks=True)
    old, new = str(c0 / "venv"), str(ci / "venv")
    for script in (ci / "venv/bin").iterdir():
        if script.is_file() and not script.is_symlink():
            data = script.read_bytes()
            if data.startswith(b"#!") and old.encode() in data[:4096]:
                script.write_bytes(data.replace(old.encode(), new.encode()))
    for cfgfile in [ci / "venv/pyvenv.cfg", ci / "venv/bin/activate"]:
        if cfgfile.exists():
            cfgfile.write_text(cfgfile.read_text().replace(old, new))
    (ci / "ready").write_text("ok")


def run_cell(work: Path, name: str, idx: int, setup: dict, base: set[str], item: dict, intervention: str) -> dict:
    record = item["record"]
    mid = record["module_id"]
    variant = item["variants"][intervention]
    files = module_files(work, name, idx, mid, setup)
    fname, fline = target_first_line(item["source"], int(record["rename_function_line"]))
    rec = {"project": name, "version": record["version"], "module_id": mid, "intervention": intervention,
           "variant_sha256": sha_text(variant), "source_sha256": record["source_sha256"], "clone": idx,
           "module_paths": [str(f.relative_to(work / "envs" / name / f"c{idx}")) for f in files]}
    if not files or not setup["modules_in_test_tree"].get(mid):
        rec.update(outcome="unavailable", reason="module not located")
        return rec
    originals = {f: f.read_bytes() for f in files}
    for f, raw in originals.items():
        if sha_text(raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")) != record["source_sha256"]:
            raise AssertionError(f"original mismatch {f}")
    rec["original_newlines_normalized"] = all(b"\r" not in raw for raw in originals.values())
    attempts = []
    try:
        for attempt in (1, 2):
            for f in files:
                f.write_bytes(variant.encode("utf-8"))
                clear_bytecode(f)
            r = run_suite(work, name, idx, setup, f"{mid}.{intervention}.{attempt}")
            for f, raw in originals.items():
                f.write_bytes(raw)
                clear_bytecode(f)
            data = r["report"]
            lost = sorted(base - passed_set(data)) if not r["timed_out"] else []
            a = {"attempt": attempt, "returncode": r["returncode"], "timed_out": r["timed_out"],
                 "duration_s": r["duration_s"], "counts": counts(data), "report_written": data is not None,
                 "not_preserved": len(lost), "not_preserved_sha256": sha_text("\n".join(lost)),
                 "not_preserved_ids": lost[:25],
                 "not_preserved_messages": [{"nodeid": n, "outcome": (data["tests"].get(n, {}).get("outcome") if data else None) or "absent",
                                             "message": (data["tests"].get(n, {}).get("message", "") if data else "")[:240]} for n in lost[:10]],
                 "collect_error_messages": [e["message"][:240] for e in (data["collect_errors"] if data else [])][:5],
                 "variant_exercise": exercise(data, files, fname, fline)}
            attempts.append((a, set(lost)))
            if r["timed_out"] or not lost:
                break
    finally:
        for f, raw in originals.items():
            f.write_bytes(raw)
            clear_bytecode(f)
    rec["restored_ok"] = all(f.read_bytes() == raw for f, raw in originals.items())
    rec["attempts"] = [a for a, _ in attempts]
    first = attempts[0][0]
    if any(a["timed_out"] for a, _ in attempts):
        rec.update(outcome="unavailable", reason="timeout")
    elif first["not_preserved"] == 0:
        rec.update(outcome="preserved", reason="")
    else:
        both = sorted(attempts[0][1] & attempts[1][1])
        rec["reproducible_breaks"] = len(both)
        rec["reproducible_breaks_sha256"] = sha_text("\n".join(both))
        rec["reproducible_break_ids"] = both[:25]
        if both:
            rec.update(outcome="contradicted", reason="")
        else:
            rec.update(outcome="unavailable", reason="failures did not reproduce")
    log(f"{name} {mid} {intervention}: {rec['outcome']} {rec.get('reason', '')} np={first['not_preserved']} t={first['duration_s']}")
    return rec


def variants_phase(work: Path, names: list[str], items: dict) -> None:
    eligible = {}
    for name in names:
        b = jload(work / "envs" / name / "baseline.json")
        if b and b.get("eligible"):
            eligible[name] = b
    queues: dict[tuple[str, int], list] = {}
    for name, b in eligible.items():
        setup = jload(work / "envs" / name / "setup.json")
        k = b["clones"]
        for idx in range(1, k):
            make_clone(work, name, idx)
        mods = sorted((it for it in items.values() if it["record"]["project"] == name), key=lambda it: int(it["record"]["selection_rank"]))
        cells = [(it, iv) for it in mods for iv in INTERVENTIONS]
        for n, cell in enumerate(cells):
            queues.setdefault((name, n % k), []).append(cell)
    out_dir = work / "cells"

    def worker(key):
        name, idx = key
        setup = jload(work / "envs" / name / "setup.json")
        b = eligible[name]
        base = set(b["baseline_passing"])
        for it, iv in queues[key]:
            path = out_dir / name / f"{it['record']['module_id']}.{iv}.json"
            if path.exists():
                continue
            jdump(path, run_cell(work, name, idx, setup, base, it, iv))
        ctrl = out_dir / name / f"post_control.c{idx}.json"
        if not ctrl.exists():
            r = run_suite(work, name, idx, setup, f"post_control.c{idx}")
            lost = sorted(base - passed_set(r["report"])) if not r["timed_out"] else None
            jdump(ctrl, {"project": name, "clone": idx, "timed_out": r["timed_out"], "duration_s": r["duration_s"],
                         "counts": counts(r["report"]), "drift": None if lost is None else len(lost), "drift_ids": (lost or [])[:25]})
            log(f"post-control {name} c{idx}: drift={None if lost is None else len(lost)}")

    # longest projects first so they start early
    order = sorted(queues, key=lambda key: (-eligible[key[0]]["runs"][0]["duration_s"], key))
    with cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        for fut in [pool.submit(worker, key) for key in order]:
            fut.result()


# --------------------------------------------------------------- export ---

def export(work: Path, results: Path, names: list[str], items: dict) -> None:
    results.mkdir(parents=True, exist_ok=True)
    sources = jload(work / "sources.json")
    projects, runs = [], []
    for name in names:
        setup = jload(work / "envs" / name / "setup.json") or {}
        b = jload(work / "envs" / name / "baseline.json") or {}
        rows = {"project": name, "version": sources[name]["version"], "source": setup.get("source"),
                "sdist_sha256": sources[name]["sdist_sha256"], "sdist_filename": sources[name]["sdist_filename"],
                "git_tag": sources[name].get("git_tag", {}).get("url") if "git_tag" in sources[name] else None,
                "git_tag_role": sources[name].get("git_tag", {}).get("role"),
                "git_tag_archive_sha256": sources[name].get("git_tag", {}).get("archive_sha256"),
                "setup_status": setup.get("status"), "resolution": setup.get("resolution"),
                "exclude_newer": setup.get("exclude_newer", EXCLUDE_NEWER),
                "deviation": DEVIATIONS["projects"].get(name, {}).get("deviation"),
                "deps": PROTOCOL["projects"][name]["deps"], "extras": PROTOCOL["projects"][name].get("extras", []),
                "deps_declared_in": PROTOCOL["projects"][name]["deps_declared_in"],
                "resolved_environment": setup.get("resolved", []), "hypothesis_seeded": setup.get("hypothesis", False),
                "test_command": pytest_command(name, Path("<venv>"), setup) if setup else None,
                "env": PROTOCOL["projects"][name].get("env", {}),
                "modules_in_test_tree": setup.get("modules_in_test_tree"),
                "modules_in_site_packages": setup.get("modules_in_site_packages"),
                "eligible": bool(b.get("eligible")), "ineligible_reason": None if b.get("eligible") else b.get("reason"),
                "baseline_runs": b.get("runs", []), "baseline_passing": len(b.get("baseline_passing", [])),
                "flaky_excluded": len(b.get("flaky_excluded", [])), "clones": b.get("clones")}
        if b.get("eligible"):
            base = b["baseline_passing"]
            rows["baseline_passing_sha256"] = sha_text("\n".join(base))
            bdir = results / "baseline"
            bdir.mkdir(exist_ok=True)
            with gzip.GzipFile(bdir / f"{name}.json.gz", "wb", mtime=0) as gz:
                gz.write(json.dumps({"project": name, "baseline_passing": base, "flaky_excluded": b["flaky_excluded"]}, indent=0).encode())
            rows["post_controls"] = [jload(p) for p in sorted((work / "cells" / name).glob("post_control.*.json"))]
        projects.append(rows)
        mods = sorted((it for it in items.values() if it["record"]["project"] == name), key=lambda it: int(it["record"]["selection_rank"]))
        base_report = jload(work / "reports" / name / "baseline1.json") if b.get("eligible") else None
        for it in mods:
            record = it["record"]
            fname, fline = target_first_line(it["source"], int(record["rename_function_line"]))
            for iv in INTERVENTIONS:
                cell = jload(work / "cells" / name / f"{record['module_id']}.{iv}.json")
                if cell is None:
                    cell = {"project": name, "version": record["version"], "module_id": record["module_id"], "intervention": iv,
                            "variant_sha256": sha_text(it["variants"][iv]), "source_sha256": record["source_sha256"],
                            "outcome": "unavailable", "reason": f"project ineligible: {rows['ineligible_reason']}"}
                cell["selection_rank"] = int(record["selection_rank"])
                cell["rename_function"] = fname
                cell["rename_function_first_line"] = fline
                cell["rename_parameter"] = record["rename_parameter"]
                if base_report is not None:
                    files = [work / "envs" / name / "c0" / "src" / rel for rel in (setup.get("modules_in_test_tree") or {}).get(record["module_id"], [])]
                    files += [site_packages(work / "envs" / name / "c0" / "venv") / rel for rel in (setup.get("modules_in_site_packages") or {}).get(record["module_id"], [])]
                    cell["baseline_exercise"] = exercise(base_report, files, fname, fline)
                    cell["baseline_passing"] = len(b["baseline_passing"])
                else:
                    cell["baseline_exercise"] = None
                runs.append(cell)
    with (results / "runs.jsonl").open("w", encoding="utf-8") as handle:
        for row in runs:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with (results / "projects.jsonl").open("w", encoding="utf-8") as handle:
        for row in projects:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    jdump(results / "summary.json", summarize(runs, projects))
    log(f"exported {len(runs)} cells, {len(projects)} projects")


KEYWORD_PATTERNS = ("unexpected keyword argument", "got multiple values for argument")


def keyword_break(cell: dict) -> bool:
    if cell.get("outcome") != "contradicted":
        return False
    msgs = []
    for a in cell.get("attempts", []):
        msgs += [m["message"] for m in a.get("not_preserved_messages", [])]
        msgs += a.get("collect_error_messages", [])
    return any(p in m for m in msgs for p in KEYWORD_PATTERNS)


def summarize(runs: list[dict], projects: list[dict]) -> dict:
    eligible = sorted(p["project"] for p in projects if p["eligible"])
    per = {}
    for iv in INTERVENTIONS:
        cells = [c for c in runs if c["intervention"] == iv]
        ex = lambda c: bool(c.get("baseline_exercise") and c["baseline_exercise"]["exercised"])  # noqa: E731
        s = {
            "cells": len(cells),
            "cells_in_eligible_projects": sum(c["project"] in eligible for c in cells),
            "modules_with_suites_exercising_them": sum(ex(c) for c in cells),
            "preserved": sum(c["outcome"] == "preserved" and ex(c) for c in cells),
            "contradicted": sum(c["outcome"] == "contradicted" for c in cells),
            "contradicted_exercised": sum(c["outcome"] == "contradicted" and ex(c) for c in cells),
            "contradicted_not_exercised": sum(c["outcome"] == "contradicted" and not ex(c) for c in cells),
            "unavailable": sum(c["outcome"] == "unavailable" for c in cells),
            "unavailable_by_reason": {},
            "not_exercised": sum(c["outcome"] == "preserved" and not ex(c) for c in cells),
            "keyword_break_cells": sum(keyword_break(c) for c in cells),
            "contradicted_module_ids": sorted(c["module_id"] for c in cells if c["outcome"] == "contradicted"),
        }
        for c in cells:
            if c["outcome"] == "unavailable":
                key = c["reason"].split(":")[0]
                s["unavailable_by_reason"][key] = s["unavailable_by_reason"].get(key, 0) + 1
        per[iv] = s
    module_cells = [c for c in runs if c["intervention"] == INTERVENTIONS[0]]
    return {
        "study": "transfer-tests",
        "protocol": "studies/transfer-tests/protocol.json",
        "deviations": "studies/transfer-tests/deviations.json",
        "deviation_projects": sorted(p["project"] for p in projects if p.get("deviation")),
        "projects_attempted": len(projects),
        "projects_eligible": len(eligible),
        "eligible_projects": eligible,
        "ineligible_projects": {p["project"]: p["ineligible_reason"] for p in projects if not p["eligible"]},
        "modules_attempted": len(module_cells),
        "modules_in_eligible_projects": sum(c["project"] in eligible for c in module_cells),
        "modules_imported_by_suite": sum(bool(c.get("baseline_exercise") and c["baseline_exercise"]["imported"]) for c in module_cells),
        "modules_exercised_by_suite": sum(bool(c.get("baseline_exercise") and c["baseline_exercise"]["exercised"]) for c in module_cells),
        "rename_target_function_executed": sum(bool(c.get("baseline_exercise") and c["baseline_exercise"]["target_function_executed"]) for c in module_cells),
        "cells": len(runs),
        "variant_runs_executed": sum(len(c.get("attempts", [])) for c in runs),
        "baseline_passing_tests": {p["project"]: p["baseline_passing"] for p in projects if p["eligible"]},
        "baseline_passing_tests_total": sum(p["baseline_passing"] for p in projects if p["eligible"]),
        "post_control_max_drift": {p["project"]: max((pc["drift"] if pc["drift"] is not None else -1) for pc in p.get("post_controls", [])) if p.get("post_controls") else None for p in projects if p["eligible"]},
        "keyword_patterns": list(KEYWORD_PATTERNS),
        "per_intervention": per,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["setup", "baseline", "variants", "export"])
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--results", type=Path, default=ARTIFACT / "results/transfer-tests")
    ap.add_argument("--projects", default="")
    args = ap.parse_args()
    items = all_variants()  # aborts on any hash mismatch with the audited variants
    names = sorted(PROTOCOL["projects"])
    if args.projects:
        names = [n for n in names if n in args.projects.split(",")]
    if args.phase == "setup":
        with cf.ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(lambda n: setup_project(n, args.work, items), names))
    elif args.phase == "baseline":
        with cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
            list(pool.map(lambda n: baseline_project(n, args.work), names))
    elif args.phase == "variants":
        variants_phase(args.work, names, items)
    else:
        export(args.work, args.results, names, items)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
