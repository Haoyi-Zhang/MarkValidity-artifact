"""pytest plugin for the transfer-tests study (loaded with -p tt_monitor).

Environment:
  TT_REPORT   path of the JSON report to write at session end
  TT_TARGETS  os.pathsep-separated absolute paths of watched module files

Records each test node id's final outcome and, via sys.monitoring (tool id 4,
PY_START), which code objects from the watched files started executing in
this process.  Standard library + pytest only.
"""
from __future__ import annotations

import json
import os
import sys

_TOOL = 4
_REPORT = os.environ.get("TT_REPORT", "")
_TARGETS = {os.path.normpath(p) for p in os.environ.get("TT_TARGETS", "").split(os.pathsep) if p}
_seen: dict[str, set] = {path: set() for path in _TARGETS}
_monitoring = False
_CO_NEWLOCALS = 0x2


def _on_start(code, offset):  # noqa: ARG001
    # Pure string operations only: no filesystem access inside the callback
    # (a stat call here would be flagged by blocking-call detectors such as
    # blockbuster that some suites enable inside their event loops).
    filename = code.co_filename
    key = _alias.get(filename)
    if key is None:
        key = _alias.setdefault(filename, os.path.normpath(filename) if filename.startswith("/") else "")
    if key in _seen:
        _seen[key].add((code.co_name, code.co_firstlineno, bool(code.co_flags & _CO_NEWLOCALS)))
    return sys.monitoring.DISABLE


_alias: dict[str, str] = {}

if _TARGETS and hasattr(sys, "monitoring"):
    try:
        sys.monitoring.use_tool_id(_TOOL, "tt_monitor")
        sys.monitoring.register_callback(_TOOL, sys.monitoring.events.PY_START, _on_start)
        sys.monitoring.set_events(_TOOL, sys.monitoring.events.PY_START)
        _monitoring = True
    except Exception as exc:  # pragma: no cover
        _monitor_error = repr(exc)

_outcomes: dict[str, dict] = {}
_order: list[str] = []


def _line(report) -> str:
    try:
        text = report.longreprtext or ""
    except Exception:
        text = ""
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return (lines[-1] if lines else "")[:300]


def pytest_runtest_logreport(report):
    nodeid = report.nodeid
    entry = _outcomes.get(nodeid)
    if entry is None:
        entry = {"outcome": None, "message": ""}
        _outcomes[nodeid] = entry
        _order.append(nodeid)
    xfail = hasattr(report, "wasxfail")
    if report.when == "call":
        if report.passed:
            outcome = "xpassed" if xfail else "passed"
        elif report.skipped:
            outcome = "xfailed" if xfail else "skipped"
        else:
            outcome = "failed"
        if entry["outcome"] != "error":
            entry["outcome"] = outcome
        if outcome == "failed":
            entry["message"] = _line(report)
    elif report.when == "setup":
        if report.skipped:
            entry["outcome"] = "xfailed" if xfail else "skipped"
        elif report.failed:
            entry["outcome"] = "error"
            entry["message"] = _line(report)
    else:  # teardown
        if report.failed:
            entry["outcome"] = "error"
            entry["message"] = entry["message"] or _line(report)


def pytest_collectreport(report):
    if report.failed:
        _collect_errors.append({"nodeid": report.nodeid, "message": _line(report)})


_collect_errors: list[dict] = []


def pytest_sessionfinish(session, exitstatus):
    if not _REPORT:
        return
    if _monitoring:
        try:
            sys.monitoring.set_events(_TOOL, 0)
        except Exception:
            pass
    data = {
        "exitstatus": int(exitstatus),
        "tests": {nodeid: _outcomes[nodeid] for nodeid in _order},
        "collect_errors": _collect_errors,
        "monitoring": _monitoring,
        "executed": {path: sorted([list(item) for item in items]) for path, items in _seen.items()},
    }
    tmp = _REPORT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    os.replace(tmp, _REPORT)
