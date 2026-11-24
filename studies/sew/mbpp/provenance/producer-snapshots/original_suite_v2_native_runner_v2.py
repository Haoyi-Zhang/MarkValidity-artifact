"""Execute unchanged MBPP assertions with explicit evidence/error boundaries.

Uncaught resource exceptions and observation failures leave evidence unavailable.
Malformed test text is rejected evidence. A genuine program failure remains a
contradiction even if another test is unavailable; rejected contracts take no
behavioral label. Each original test uses a fresh source namespace, as in v1.
"""
import builtins
import contextlib
import errno
import io
import json
import random
import resource
import sys
import time
import traceback

SCHEMA = 'markvalidity-mbpp-original-assertions-v2'
_JSON_DUMPS = json.dumps


def unavailable_error(phase, reason):
    return {'phase': phase, 'type': 'observer_unavailable', 'message': reason, 'traceback': None}


def emit(record):
    """A failed serialization is itself a retained unavailable observation."""
    try:
        print(_JSON_DUMPS(record, sort_keys=True, ensure_ascii=True), flush=True)
        return record
    except BaseException:
        fallback = {'event': record.get('event', 'observer'), 'status': 'unavailable',
                    'error': unavailable_error('serialize_observation', 'Observation serialization or output failed')}
        if 'test_index' in record:
            fallback.update(test_index=record['test_index'], assertion_reached=record.get('assertion_reached', False),
                            stdout='', stderr='', elapsed_seconds=record.get('elapsed_seconds', 0))
        try:
            print(_JSON_DUMPS(fallback, sort_keys=True, ensure_ascii=True), flush=True)
        except BaseException:
            pass
        return fallback


def error(exc, phase):
    return {'phase': phase, 'type': type(exc).__module__ + '.' + type(exc).__qualname__,
            'message': str(exc), 'traceback': traceback.format_exc()}


def classify_exception(exc, phase):
    if isinstance(exc, (MemoryError, KeyboardInterrupt)):
        return 'unavailable'
    if isinstance(exc, OSError) and exc.errno == errno.ENOMEM:
        return 'unavailable'
    if phase == 'compile_source':
        return 'failed' if isinstance(exc, SyntaxError) else 'unavailable'
    if phase in ('compile_test_imports', 'compile_original_test'):
        return 'evidence_rejected' if isinstance(exc, SyntaxError) else 'unavailable'
    if phase == 'test_imports':
        return 'unavailable'
    if phase in ('initialize_source', 'original_assertion'):
        return 'failed'
    return 'unavailable'


def observed_exception(exc, phase):
    status = classify_exception(exc, phase)
    try:
        problem = error(exc, phase)
    except BaseException:
        return 'unavailable', unavailable_error('observe_exception', 'Exception observation failed')
    return status, problem


def complete(outcomes, count, started, override=None):
    statuses = [r['status'] for r in outcomes]
    if override is not None:
        status = override
    elif 'evidence_rejected' in statuses:
        status = 'evidence_rejected'
    elif 'failed' in statuses:
        status = 'failed'
    elif any(s != 'passed' for s in statuses):
        status = 'unavailable'
    else:
        status = 'passed'
    emit({'event': 'complete', 'status': status, 'evidence_schema': SCHEMA,
          'scheduled_tests': count, 'completed_tests': len(outcomes),
          'passed_tests': statuses.count('passed'), 'failed_tests': statuses.count('failed'),
          'unavailable_tests': statuses.count('unavailable'),
          'rejected_tests': statuses.count('evidence_rejected'),
          'elapsed_seconds': round(time.monotonic() - started, 6)})


def main():
    if not __debug__:
        raise RuntimeError('Original assert statements require non-optimized Python')
    started = time.monotonic()
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict) or not isinstance(request.get('source'), str):
            raise ValueError('Source must be a string in a request object')
        if not all(isinstance(request.get(k), list) and all(isinstance(x, str) for x in request[k])
                   for k in ('test_imports', 'test_list')):
            raise ValueError('Original imports and tests must be lists of strings')
    except BaseException:
        emit({'event': 'request', 'status': 'evidence_rejected',
              'error': unavailable_error('read_contract', 'Malformed execution request')})
        complete([], 0, started, 'evidence_rejected')
        return
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    count = len(request['test_list'])
    try:
        source_code = compile(request['source'], '<mbpp-candidate>', 'exec')
    except BaseException as exc:
        status, problem = observed_exception(exc, 'compile_source')
        event = emit({'event': 'source_compile', 'status': status, 'error': problem})
        complete([], count, started, event['status'])
        return
    compiled = emit({'event': 'source_compile', 'status': 'passed', 'error': None})
    if compiled['status'] != 'passed':
        complete([], count, started, 'unavailable')
        return
    imports = '\n'.join(request['test_imports'])
    outcomes = []
    for index, assertion in enumerate(request['test_list']):
        namespace = {'__name__': '__markvalidity_mbpp__', '__builtins__': dict(vars(builtins))}
        random.seed(0)
        stdout, stderr = io.StringIO(), io.StringIO()
        phase = 'compile_test_imports'
        begin = time.monotonic()
        try:
            import_code = compile(imports, '<mbpp-original-test-imports>', 'exec')
            phase = 'compile_original_test'
            test_code = compile(assertion, '<mbpp-original-test-%d>' % index, 'exec')
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                phase = 'test_imports'
                exec(import_code, namespace)
                phase = 'initialize_source'
                exec(source_code, namespace)
                phase = 'original_assertion'
                exec(test_code, namespace)
            status, problem = 'passed', None
        except BaseException as exc:
            status, problem = observed_exception(exc, phase)
        try:
            captured_stdout, captured_stderr = stdout.getvalue(), stderr.getvalue()
        except BaseException:
            status, problem = 'unavailable', unavailable_error('observe_streams', 'Stream observation failed')
            captured_stdout, captured_stderr = '', ''
        result = {'event': 'test_result', 'test_index': index, 'status': status, 'error': problem,
                  'assertion_reached': phase == 'original_assertion', 'stdout': captured_stdout,
                  'stderr': captured_stderr, 'elapsed_seconds': round(time.monotonic() - begin, 6)}
        outcomes.append(emit(result))
    complete(outcomes, count, started)


if __name__ == '__main__':
    main()
