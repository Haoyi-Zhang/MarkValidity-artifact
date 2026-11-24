import contextlib
import copy
import io
import json
import random
import resource
import sys
import time


def encode(value):
    if value is None: return ['none']
    if type(value) is bool: return ['bool', value]
    if type(value) is int: return ['int', str(value)]
    if type(value) is float: return ['float', value.hex()]
    if type(value) is str: return ['str', value]
    if type(value) is bytes: return ['bytes', value.hex()]
    if type(value) in (tuple, list): return [type(value).__name__, [encode(x) for x in value]]
    if type(value) is dict: return ['dict', [[encode(k), encode(v)] for k, v in value.items()]]
    if type(value) in (set, frozenset):
        return [type(value).__name__, sorted([encode(x) for x in value], key=lambda x: json.dumps(x, sort_keys=True))]
    raise TypeError('Unsupported observed builtin type: ' + type(value).__qualname__)


def main():
    request = json.load(sys.stdin)
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    random.seed(0)
    namespace = {}
    observations = []
    stdout, stderr = io.StringIO(), io.StringIO()
    phase = 'compile_source'
    start = time.monotonic()
    try:
        code = compile(request['source'], '<frozen-humaneval-source>', 'exec')
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            phase = 'initialize_source'
            exec(code, namespace)
            function = namespace[request['entry_point']]

            def observed(*args, **kwargs):
                before = {'args': encode(copy.deepcopy(args)), 'kwargs': encode(copy.deepcopy(kwargs))}
                try:
                    result = function(*args, **kwargs)
                except BaseException as exc:
                    observations.append({'before': before, 'result': ['exception', type(exc).__module__ + '.' + type(exc).__qualname__, str(exc)],
                                         'after': {'args': encode(args), 'kwargs': encode(kwargs)}})
                    raise
                observations.append({'before': before, 'result': ['return', encode(result)],
                                     'after': {'args': encode(args), 'kwargs': encode(kwargs)}})
                return result

            phase = 'compile_tests'
            test_code = compile(request['test'], '<original-humaneval-tests>', 'exec')
            phase = 'initialize_tests'
            exec(test_code, namespace)
            phase = 'original_suite'
            namespace['check'](observed)
        status, error = 'passed', None
    except BaseException as exc:
        status, error = 'failed', {'phase': phase, 'type': type(exc).__module__ + '.' + type(exc).__qualname__, 'message': str(exc)}
    print(json.dumps({'status': status, 'error': error, 'observations': observations,
                      'stdout': stdout.getvalue(), 'stderr': stderr.getvalue(),
                      'elapsed_seconds': round(time.monotonic() - start, 6)}, sort_keys=True, separators=(',', ':')))


if __name__ == '__main__': main()
