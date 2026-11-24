"""Run the original mxeval Python check program without value instrumentation.

The declared program is prompt + completion + newline + original test + newline
+ check(entry_point). Original arguments and returns never pass through an
encoding layer. The envelope records completion or a witnessed exception;
resource and harness failures remain unavailable evidence.
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
        # Validate the fixed test independently so a broken harness cannot be
        # mislabeled as a program defect. The executed program below is still
        # the exact combined string used by mxeval, with one global namespace.
        phase = 'validate_original_test'
        compile(request['test'], '<original-test-validation>', 'exec')
        phase = 'configure_execution'
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        random.seed(0)
        program = (request['source'] + '\n' + request['test'] + '\n' +
                   'check(' + request['entry_point'] + ')')
        phase = 'compile_check_program'
        code = compile(program, '<original-mxeval-check-program>', 'exec')
        phase = 'execute_check_program'
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostics):
            exec(code, {})
        check_finished = True
        status = 'passed'
    except BaseException as exception:
        reason = unavailable(exception)
        error = {'phase': phase, **detail(exception)}
        if reason:
            status, error['reason'] = 'unavailable', reason
        elif phase not in ('compile_check_program', 'execute_check_program'):
            status, error['reason'] = 'unavailable', 'harness_or_contract_error'
        else:
            status = 'failed'
    print(json.dumps({'schema': 'crest-original-assertion-suite', 'status': status,
                      'error': error, 'check_finished': check_finished,
                      'stdout': output.getvalue(), 'stderr': diagnostics.getvalue(),
                      'elapsed_seconds': round(time.monotonic() - start, 6)},
                     sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
