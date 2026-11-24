"""Original HumanEval suites with explicit program/observer failure boundaries.

Normal builtin traces retain the v1 representation. A value that the observer
cannot encode leaves the evidence unavailable; it never becomes a witnessed
program failure. This benchmark worker is not a general security sandbox.
"""
import contextlib
import errno
import copy
import io
import json
import random
import resource
import sys
import time


class ObservationUnavailable(BaseException):
    def __init__(self, detail):
        self.detail = detail


def encode(value):
    if value is None:
        return ["none"]
    if type(value) is bool:
        return ["bool", value]
    if type(value) is int:
        try:
            return ["int", str(value)]
        except ValueError:
            # Keep ordinary decimal traces stable while bypassing CPython's
            # decimal-conversion limit for a returned builtin integer.
            return ["int_hex", hex(value)]
    if type(value) is float:
        return ["float", value.hex()]
    if type(value) is str:
        return ["str", value]
    if type(value) is bytes:
        return ["bytes", value.hex()]
    if type(value) in (tuple, list):
        return [type(value).__name__, [encode(x) for x in value]]
    if type(value) is dict:
        return ["dict", [[encode(k), encode(v)] for k, v in value.items()]]
    if type(value) in (set, frozenset):
        return [type(value).__name__, sorted([encode(x) for x in value], key=lambda x: json.dumps(x, sort_keys=True))]
    # This extension records exact numeric NumPy scalar bytes without changing
    # the object returned to the original test. Non-numeric objects stay unknown.
    if type(value).__module__ == "numpy":
        import numpy as np
        if isinstance(value, np.generic) and value.dtype.kind in "biufc":
            return ["numpy_scalar", value.dtype.str, value.tobytes().hex()]
    raise TypeError("Unsupported observed builtin type: " + type(value).__qualname__)


def describe_error(exc):
    try:
        message = str(exc)
    except BaseException:
        message = "<exception message unavailable>"
    return {"type": type(exc).__module__ + "." + type(exc).__qualname__, "message": message}


def unavailable_reason(exc):
    if isinstance(exc, MemoryError) or (isinstance(exc, OSError) and exc.errno == errno.ENOMEM):
        return "resource_unavailable"
    if isinstance(exc, KeyboardInterrupt):
        return "interrupted"
    return None


def main():
    request = json.load(sys.stdin)
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    random.seed(0)
    namespace = {}
    observations = []
    observer_failures = []
    stdout, stderr = io.StringIO(), io.StringIO()
    phase = "compile_source"
    start = time.monotonic()

    def observe_operation(operation_phase, operation):
        try:
            return operation()
        except ObservationUnavailable:
            raise
        except BaseException as exc:
            detail = {"phase": operation_phase, "reason": "observer_error", **describe_error(exc)}
            observer_failures.append(detail)
            raise ObservationUnavailable(detail) from exc

    def record_arguments(args, kwargs):
        return {"args": encode(args), "kwargs": encode(kwargs)}

    try:
        code = compile(request["source"], "<frozen-humaneval-source>", "exec")
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            phase = "initialize_source"
            exec(code, namespace)
            phase = "resolve_entry_point"
            function = namespace[request["entry_point"]]

            def observed(*args, **kwargs):
                before = observe_operation("encode_arguments_before", lambda: record_arguments(copy.deepcopy(args), copy.deepcopy(kwargs)))
                try:
                    result = function(*args, **kwargs)
                except ObservationUnavailable:
                    raise
                except BaseException as exc:
                    unavailable = unavailable_reason(exc)
                    if unavailable is not None:
                        detail = {"phase": "invoke_program", "reason": unavailable, **describe_error(exc)}
                        observer_failures.append(detail)
                        raise ObservationUnavailable(detail) from exc
                    # This handler covers only the invocation. Encoding and
                    # exception-message extraction use the observer boundary.
                    envelope = observe_operation("encode_program_exception", lambda: ["exception", type(exc).__module__ + "." + type(exc).__qualname__, str(exc)])
                    after = observe_operation("encode_argument_poststate", lambda: record_arguments(args, kwargs))
                    observations.append({"before": before, "result": envelope, "after": after})
                    raise
                envelope = observe_operation("encode_return_value", lambda: ["return", encode(result)])
                after = observe_operation("encode_argument_poststate", lambda: record_arguments(args, kwargs))
                observations.append({"before": before, "result": envelope, "after": after})
                return result

            phase = "compile_tests"
            test_code = compile(request["test"], "<original-humaneval-tests>", "exec")
            phase = "initialize_tests"
            exec(test_code, namespace)
            phase = "original_suite"
            namespace["check"](observed)
        # A suite could catch BaseException. That cannot convert an unavailable
        # observation into support, because its failure is retained separately.
        if observer_failures:
            status, error = "unavailable", observer_failures[0]
        else:
            status, error = "passed", None
    except ObservationUnavailable as exc:
        status, error = "unavailable", exc.detail
    except BaseException as exc:
        if observer_failures:
            status, error = "unavailable", observer_failures[0]
        elif unavailable_reason(exc) is not None:
            status, error = "unavailable", {"phase": phase, "reason": unavailable_reason(exc), **describe_error(exc)}
        elif phase in ("compile_tests", "initialize_tests", "resolve_entry_point"):
            status, error = "unavailable", {"phase": phase, "reason": "test_or_entry_setup_error", **describe_error(exc)}
        else:
            status, error = "failed", {"phase": phase, **describe_error(exc)}
    print(json.dumps({"status": status, "error": error, "observations": observations,
                      "stdout": stdout.getvalue(), "stderr": stderr.getvalue(),
                      "elapsed_seconds": round(time.monotonic() - start, 6)}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
