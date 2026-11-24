"""Execute each unchanged MBPP assertion in a fresh source namespace.

An input request contains the exact candidate source, test_imports and test_list.
Each test has fresh source globals and a fresh builtin map. This is an original-
assertion contract, not complete-domain program equivalence. JSONL events retain
completed tests if the enclosing process is stopped by its resource guard.
"""
import builtins
import contextlib
import io
import json
import random
import resource
import sys
import time
import traceback


def emit(record):
    print(json.dumps(record, sort_keys=True, ensure_ascii=False), flush=True)


def error(exc, phase):
    return {'phase': phase, 'type': type(exc).__module__ + '.' + type(exc).__qualname__,
            'message': str(exc), 'traceback': traceback.format_exc()}


def main():
    if not __debug__:
        raise RuntimeError('Original assert statements require non-optimized Python')
    request = json.load(sys.stdin)
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    started = time.monotonic()
    try:
        source_code = compile(request['source'], '<mbpp-candidate>', 'exec')
    except BaseException as exc:
        emit({'event': 'source_compile', 'status': 'failed', 'error': error(exc, 'compile_source')})
        emit({'event': 'complete', 'status': 'failed', 'scheduled_tests': len(request['test_list']),
              'completed_tests': 0, 'passed_tests': 0, 'failed_tests': 0,
              'elapsed_seconds': round(time.monotonic() - started, 6)})
        return
    emit({'event': 'source_compile', 'status': 'passed', 'error': None})
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
            status, problem = 'failed', error(exc, phase)
        result = {'event': 'test_result', 'test_index': index, 'status': status, 'error': problem,
                  'assertion_reached': phase == 'original_assertion', 'stdout': stdout.getvalue(),
                  'stderr': stderr.getvalue(), 'elapsed_seconds': round(time.monotonic() - begin, 6)}
        outcomes.append(result)
        emit(result)
    passed = sum(x['status'] == 'passed' for x in outcomes)
    emit({'event': 'complete', 'status': 'passed' if passed == len(outcomes) else 'failed',
          'scheduled_tests': len(request['test_list']), 'completed_tests': len(outcomes),
          'passed_tests': passed, 'failed_tests': len(outcomes) - passed,
          'elapsed_seconds': round(time.monotonic() - started, 6)})


if __name__ == '__main__':
    main()
