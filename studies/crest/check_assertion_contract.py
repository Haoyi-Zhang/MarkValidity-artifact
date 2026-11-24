#!/usr/bin/env python3
"""Small execution-contract controls, separate from empirical observations."""
import json
from pathlib import Path
import reexecute_crest_assertions as producer


def main():
    environment = producer.probe_execution_environment()
    producer.STATE['environment'] = environment
    programs = [
        ('native_values_without_encoding',
         'from collections import namedtuple, Counter\nPair=namedtuple("Pair", "x y")\n'
         'def f():\n    return (1+2j, int, Pair(1,2), Counter({"a":2}))',
         'def check(candidate):\n    z,t,p,c=candidate()\n    assert z==1+2j and t is int\n'
         '    assert type(p) is Pair and p.x==1\n    assert type(c) is Counter and c["a"]==2', True),
        ('numpy_values_keep_type',
         'import numpy as np\ndef f():\n    return np.float64(-0.0), np.float64(float("nan"))',
         'def check(candidate):\n    a,b=candidate()\n    assert type(a) is np.float64\n'
         '    assert np.signbit(a) and np.isnan(b)', True),
        ('sympy_import_available', 'from sympy import isprime\ndef f():\n    return isprime(7)',
         'def check(candidate):\n    assert candidate() is True', True),
        ('original_assertion_failure', 'def f():\n    return 1',
         'def check(candidate):\n    assert candidate()==2', False),
        ('source_compile_failure', 'def f(:\n    return 1',
         'def check(candidate):\n    assert candidate()==1', False),
        ('missing_required_entry', 'def other():\n    return 1',
         'def check(candidate):\n    assert candidate()==1', False),
        ('memory_unavailable', 'def f():\n    raise MemoryError()',
         'def check(candidate):\n    candidate()', None),
        ('broken_test_unavailable', 'def f():\n    return 1',
         'def check(:\n    pass', None),
    ]
    controls = []
    for name, source, test, expected in programs:
        request = {'source': source, 'test': test, 'entry_point': 'f'}
        receipt = producer.native(request)
        assert receipt['label'] is expected and receipt['evidence_rejected'] is None, name
        controls.append({'name': name, 'expected': expected, 'receipt': receipt})
    try:
        producer.receive('[]', 0, None)
    except ValueError:
        pass
    else:
        raise ValueError('Nondictionary envelope was accepted')
    result = {'status': 'PASS', 'environment': environment, 'native_controls': controls,
              'nondictionary_envelope_rejected': True,
              'scope': 'Owned contract controls only; no rows are added to the empirical population.'}
    target = Path(__file__).resolve().parent / 'assertion-contract-controls.json'
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'native_controls': len(controls),
                      'native_packages': environment['declared_dependencies']}))


if __name__ == '__main__':
    main()
