"""Independent native controls for the primary observer's admission boundary."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cases = [
        ("small_integer_stable", "def f(): return 4\n", "def check(candidate): assert candidate() == 4\n", "passed", None),
        ("large_integer", "def f(): return 2 ** 20000\n", "def check(candidate): assert candidate().bit_length() == 20001\n", "passed", None),
        ("unsupported_return", "def f(): return object()\n", "def check(candidate): assert candidate() is not None\n", "unavailable", "encode_return_value"),
        ("unsupported_argument_before", "def f(x): return 1\n", "def check(candidate): assert candidate(object()) == 1\n", "unavailable", "encode_arguments_before"),
        ("unsupported_argument_after", "def f(x):\n    x.append(object())\n    return 1\n", "def check(candidate):\n    x=[]\n    assert candidate(x) == 1\n    assert len(x) == 1\n", "unavailable", "encode_argument_poststate"),
        ("program_exception", "def f(): raise ValueError('program sentinel')\n", "def check(candidate): candidate()\n", "failed", "original_suite"),
        ("expected_program_exception", "def f(): raise ValueError('program sentinel')\n", "def check(candidate):\n    try:\n        candidate()\n    except ValueError:\n        pass\n    else:\n        assert False\n", "passed", None),
        ("observer_like_program_message", "def f(): raise TypeError('Unsupported observed builtin type: object')\n", "def check(candidate): candidate()\n", "failed", "original_suite"),
        ("caught_observer_failure", "def f(x): return 1\n", "def check(candidate):\n    try:\n        candidate(object())\n    except BaseException:\n        pass\n", "unavailable", "encode_arguments_before"),
        ("memory_unavailable", "def f(): raise MemoryError('controlled resource event')\n", "def check(candidate): candidate()\n", "unavailable", "invoke_program"),
        ("syntax_error", "def f(:\n    return 1\n", "def check(candidate): candidate()\n", "failed", "compile_source"),
    ]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONOPTIMIZE", None)
    env["PYTHONHASHSEED"] = "0"
    records = []
    for name, source, test, expected, expected_phase in cases:
        namespace = {}
        try:
            exec(source, namespace)
            exec(test, namespace)
            namespace["check"](namespace["f"])
            unwrapped = {"status": "passed"}
        except BaseException as exc:
            unwrapped = {"status": "failed", "type": type(exc).__module__ + "." + type(exc).__qualname__, "message": str(exc)}
        with tempfile.TemporaryDirectory(prefix="primary-observer-control-") as temporary:
            process = subprocess.run([sys.executable, "-B", "-S", str(args.runner.resolve())],
                                     cwd=temporary, env=env, text=True, capture_output=True, timeout=15,
                                     input=json.dumps({"source": source, "test": test, "entry_point": "f"}))
        assert process.returncode == 0, (name, process.stderr)
        observed = json.loads(process.stdout)
        assert observed["status"] == expected, (name, observed)
        if expected_phase is not None:
            assert observed["error"]["phase"] == expected_phase, (name, observed)
        if name == "small_integer_stable":
            assert observed["observations"][0]["result"] == ["return", ["int", "4"]]
        if name == "large_integer":
            assert observed["observations"][0]["result"][1][0] == "int_hex"
        if name in ("program_exception", "expected_program_exception", "observer_like_program_message"):
            assert observed["observations"][0]["result"][0] == "exception"
        if expected == "unavailable" and name != "memory_unavailable":
            assert observed["error"]["reason"] == "observer_error"
        records.append({"control": name, "source": source, "original_test": test, "unwrapped": unwrapped,
                        "expected_observer_status": expected, "expected_phase": expected_phase, "passed": True, "observation": observed})
    report = {"status": "PASS", "controls": len(records), "observer_sha256": hashlib.sha256(args.runner.read_bytes()).hexdigest(), "records": records}
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "controls": len(records), "observer_sha256": report["observer_sha256"]}))


if __name__ == "__main__":
    main()
