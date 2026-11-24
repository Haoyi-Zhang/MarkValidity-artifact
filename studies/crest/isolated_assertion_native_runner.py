"""Evaluate original assertions with isolated program and test namespaces.

The prompt and completion execute in their own globals. The original entry
object is retained, and the unchanged original test executes in a shallow copy
of those globals. No function wrapper or argument/return encoding is introduced;
the candidate's own globals are never overwritten by test definitions.
"""
import contextlib
import errno
import io
import json
import random
import resource
import sys
import time


def detail(exception):
    try:
        message = str(exception)
    except BaseException:
        message = '<exception message unavailable>'
    return {'type': type(exception).__module__ + '.' + type(exception).__qualname__,
            'message': message}


def unavailable(exception):
    if isinstance(exception, MemoryError) or (
            isinstance(exception, OSError) and exception.errno == errno.ENOMEM):
        return 'resource_unavailable'
    if isinstance(exception, KeyboardInterrupt):
        return 'interrupted'
    return None


def main():
    start = time.monotonic()
    phase = 'receive_request'
    status, error = 'unavailable', None
    check_finished = False
    output, diagnostics = io.StringIO(), io.StringIO()
    try:
        request = json.load(sys.stdin)
        if (not isinstance(request, dict) or set(request) != {'source', 'test', 'entry_point'} or
                not all(isinstance(request[k], str) for k in request) or
                not request['entry_point'].isidentifier()):
            raise ValueError('Malformed original-suite request')
        phase = 'validate_original_test'
        tests = compile(request['test'], '<original-mxeval-assertions>', 'exec')
        phase = 'configure_execution'
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        random.seed(0)
        phase = 'compile_source'
        code = compile(request['source'], '<published-source-with-original-prompt>', 'exec')
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostics):
            program_globals = {}
            phase = 'initialize_source'
            exec(code, program_globals)
            phase = 'resolve_entry_point'
            candidate = program_globals[request['entry_point']]
            # A shallow namespace copy shares the original objects, including
            # the unchanged candidate function and its original __globals__.
            # Test definitions replace only bindings in the test namespace.
            test_globals = dict(program_globals)
            phase = 'initialize_tests'
            exec(tests, test_globals)
            original_check = test_globals['check']
            phase = 'original_suite'
            original_check(candidate)
        check_finished = True
        status = 'passed'
    except BaseException as exception:
        reason = unavailable(exception)
        error = {'phase': phase, **detail(exception)}
        if reason:
            status, error['reason'] = 'unavailable', reason
        elif phase not in ('compile_source', 'initialize_source', 'resolve_entry_point', 'original_suite'):
            status, error['reason'] = 'unavailable', 'harness_or_contract_error'
        else:
            status = 'failed'
    print(json.dumps({'schema': 'crest-isolated-original-assertions', 'status': status,
                      'error': error, 'check_finished': check_finished,
                      'stdout': output.getvalue(), 'stderr': diagnostics.getvalue(),
                      'elapsed_seconds': round(time.monotonic() - start, 6)},
                     sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
