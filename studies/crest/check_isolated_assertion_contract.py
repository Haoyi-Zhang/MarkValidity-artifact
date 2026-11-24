#!/usr/bin/env python3
"""Direct controls for the uniform separate-namespace assertion contract."""
import json
from pathlib import Path
import reexecute_crest_isolated_assertions as producer


def main():
    producer.STATE['environment'] = producer.probe_execution_environment()
    programs = [
        ('recursive_entry_named_check',
         'def check(n):\n    return 1 if n==0 else n*check(n-1)',
         'def check(candidate):\n    assert candidate(4)==24', 'check', True),
        ('program_binding_survives_test_binding',
         'value=7\ndef f():\n    return value',
         'value=99\ndef check(candidate):\n    assert candidate()==7', 'f', True),
        ('native_values_without_encoding',
         'from collections import namedtuple, Counter\nPair=namedtuple("Pair", "x y")\n'
         'def f():\n    return (1+2j, int, Pair(1,2), Counter({"a":2}))',
         'def check(candidate):\n    z,t,p,c=candidate()\n    assert z==1+2j and t is int\n'
         '    assert type(p) is Pair and p.x==1\n    assert type(c) is Counter and c["a"]==2', 'f', True),
        ('numpy_values_keep_type',
         'import numpy as np\ndef f():\n    return np.float64(-0.0), np.float64(float("nan"))',
         'def check(candidate):\n    a,b=candidate()\n    assert type(a) is np.float64\n'
         '    assert np.signbit(a) and np.isnan(b)', 'f', True),
        ('sympy_import_available', 'from sympy import isprime\ndef f():\n    return isprime(7)',
         'def check(candidate):\n    assert candidate() is True', 'f', True),
        ('original_assertion_failure', 'def f():\n    return 1',
         'def check(candidate):\n    assert candidate()==2', 'f', False),
        ('source_compile_failure', 'def f(:\n    return 1',
         'def check(candidate):\n    assert candidate()==1', 'f', False),
        ('missing_required_entry', 'def other():\n    return 1',
         'def check(candidate):\n    assert candidate()==1', 'f', False),
        ('memory_unavailable', 'def f():\n    raise MemoryError()',
         'def check(candidate):\n    candidate()', 'f', None),
        ('broken_test_unavailable', 'def f():\n    return 1',
         'def check(:\n    pass', 'f', None),
    ]
    controls = []
    for name, source, test, entry, expected in programs:
        receipt = producer.native({'source': source, 'test': test, 'entry_point': entry})
        assert receipt['label'] is expected and receipt['evidence_rejected'] is None, name
        controls.append({'name': name, 'expected': expected, 'receipt': receipt})
    result = {'status': 'PASS', 'environment': producer.STATE['environment'],
              'native_controls': controls,
              'scope': 'Contract controls only; not empirical benchmark observations. Separate namespace bindings preserve the candidate globals; imported modules and original objects remain shared.'}
    root = Path(__file__).resolve().parent
    (root/'isolated-assertion-contract-controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'PASS','native_controls':len(controls)}))


if __name__=='__main__':
    main()
