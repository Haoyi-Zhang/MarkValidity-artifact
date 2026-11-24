"""Five controls for distinguishing program behavior from observation failure."""
import argparse
import importlib.util
import json
from pathlib import Path
import signal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("enhanced_observer_control_target", args.runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    signal.signal(signal.SIGALRM, module.alarm_handler)
    cases = [
        ("large_integer", "def f():\n    return 2 ** 20000\n", lambda r: r["status"] == "observed" and r["outcome"][0] == "return" and r["outcome"][1][0] == "int_hex"),
        ("program_exception", "def f():\n    raise ValueError('program sentinel')\n", lambda r: r["status"] == "observed" and r["outcome"] == ["exception", "builtins.ValueError", "program sentinel"]),
        ("unsupported_return", "def f():\n    return object()\n", lambda r: r["status"] == "unavailable" and r["phase"] == "encode_return_value"),
        ("initialization_error", "raise ValueError('initialization sentinel')\ndef f(): return 0\n", lambda r: r["status"] == "unavailable" and r["phase"] == "initialize_source"),
        ("timeout", "def f():\n    while True: pass\n", lambda r: r["status"] == "unavailable" and r["reason"] == "per_invocation_guard"),
    ]
    results = []
    for name, source, check in cases:
        record = module.observe(compile(source, "<observer-control>", "exec"), "f", [], .05)
        passed = check(record)
        results.append({"control": name, "source": source, "passed": passed, "observation": record})
        assert passed, name
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({"controls": len(results), "passed": sum(r["passed"] for r in results)}))


if __name__ == "__main__":
    main()
