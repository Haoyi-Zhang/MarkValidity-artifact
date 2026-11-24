"""Bounded, typed observations; program exceptions cannot absorb observer errors.

One JSON line is flushed after every completed pair.  This is a benchmark
worker, not a security sandbox for arbitrary untrusted programs.
"""
import contextlib
import copy
import io
import json
import math
import random
import resource
import signal
import sys
import time


class ObservationTimeout(BaseException):
    pass


def alarm_handler(signum, frame):
    raise ObservationTimeout()


def encode(value):
    if value is None:
        return ["none"]
    if type(value) is bool:
        return ["bool", value]
    if type(value) is int:
        # Hex avoids CPython's decimal conversion limit without changing the
        # program environment or turning an observer failure into an exception.
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
    raise TypeError("Unsupported observed builtin type: " + type(value).__qualname__)


def error_description(exc):
    return {"type": type(exc).__module__ + "." + type(exc).__qualname__, "message": str(exc)}


def observe(code, entry, inputs, invocation_seconds):
    random.seed(0)
    namespace = {}
    stdout, stderr = io.StringIO(), io.StringIO()
    phase = "copy_arguments"
    try:
        signal.setitimer(signal.ITIMER_REAL, invocation_seconds)
        args = copy.deepcopy(inputs)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            phase = "initialize_source"
            exec(code, namespace)
            phase = "resolve_entry_point"
            function = namespace[entry]
            phase = "invoke_program"
            try:
                result = function(*args)
            except ObservationTimeout:
                raise
            except BaseException as exc:
                # Only invocation exceptions are part of the program outcome.
                outcome = ["exception", type(exc).__module__ + "." + type(exc).__qualname__, str(exc)]
            else:
                phase = "encode_return_value"
                outcome = ["return", encode(result)]
        phase = "encode_argument_poststate"
        post_arguments = encode(args)
        record = {"status": "observed", "outcome": outcome, "post_arguments": post_arguments}
    except ObservationTimeout:
        record = {"status": "unavailable", "reason": "per_invocation_guard", "phase": phase}
    except BaseException as exc:
        # Source initialization / entry lookup errors and observer failures
        # remain unavailable.  They are not fabricated program exceptions.
        record = {"status": "unavailable", "reason": "initialization_or_observer_error", "phase": phase, "error": error_description(exc)}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    record["stdout"] = stdout.getvalue()
    record["stderr"] = stderr.getvalue()
    return record


def emit(value):
    print(json.dumps(value, sort_keys=True, separators=(",", ":")), flush=True)


def main():
    request = json.load(sys.stdin)
    invocation_seconds = request["invocation_seconds"]
    count = len(request["base_input"]) + len(request["plus_input"])
    # This fixed formula allows all bounded attempts.  A resource termination
    # still leaves previously flushed pair observations recoverable.
    worker_seconds = math.ceil(10 + count * (2 * invocation_seconds + .02))
    resource.setrlimit(resource.RLIMIT_CPU, (worker_seconds, worker_seconds))
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    signal.signal(signal.SIGALRM, alarm_handler)
    try:
        reference = compile(request["reference"], "<human-eval-reference>", "exec")
        candidate = compile(request["candidate"], "<stock-sew-candidate>", "exec")
    except BaseException as exc:
        emit({"kind": "worker_summary", "status": "compile_unavailable", "error": error_description(exc)})
        return
    start = time.monotonic()
    observed_pairs = 0
    for split in ("base_input", "plus_input"):
        for index, inputs in enumerate(request[split]):
            left = observe(reference, request["entry_point"], inputs, invocation_seconds)
            right = observe(candidate, request["entry_point"], inputs, invocation_seconds)
            if left["status"] == right["status"] == "observed":
                equal_return = left["outcome"] == right["outcome"]
                equal_post = left["post_arguments"] == right["post_arguments"]
                equal_streams = (left["stdout"], left["stderr"]) == (right["stdout"], right["stderr"])
            else:
                equal_return = equal_post = equal_streams = None
            emit({"kind": "pair", "split": split, "index": index, "reference": left, "candidate": right,
                  "return_equal": equal_return, "post_arguments_equal": equal_post, "streams_equal": equal_streams})
            observed_pairs += 1
    emit({"kind": "worker_summary", "status": "complete", "recorded_pairs": observed_pairs,
          "worker_cpu_seconds": worker_seconds, "elapsed_seconds": round(time.monotonic() - start, 6)})


if __name__ == "__main__":
    main()
