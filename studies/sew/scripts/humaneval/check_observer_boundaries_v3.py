"""Native event-matrix controls for the two HumanEval observation contracts.

The controls are separate diagnostic programs, never natural-corpus rows.
Resource cases execute under the actual workers' limits. Ordinary program
exceptions remain distinct from unavailable observations.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--primary-runner', type=Path, required=True)
    parser.add_argument('--enhanced-runner', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONOPTIMIZE', None)
    env['PYTHONHASHSEED'] = '0'
    primary = []
    enhanced = []
    def p(name, source, test, expected, phase=None):
        primary.append(dict(name=name, source=source, test=test, expected=expected, phase=phase))
    def e(name, source, expected, phase=None, inputs=None):
        enhanced.append(dict(name=name, source=source, expected=expected, phase=phase, inputs=[[]] if inputs is None else inputs))
    call = 'def check(candidate): candidate()\n'
    small = 'def f(): return 4\n'
    huge = 'def f(): return 2 ** 20000\n'
    shape = "def f(): return ['exception', 'builtins.ValueError', 'payload']\n"
    memory = 'def f(): return bytearray(2**31)\n'
    enomem = 'import mmap\ndef f(): return mmap.mmap(-1, 2**31)\n'
    interrupt = 'def f(): raise KeyboardInterrupt()\n'
    io_error = "def f(): raise OSError(5, 'ordinary I/O error')\n"
    value_error = "def f(): raise ValueError('program sentinel')\n"
    bad_message = "class Bad(Exception):\n    def __str__(self): raise ValueError('message observer failed')\ndef f(): raise Bad()\n"
    caught_memory = 'import mmap\ndef f():\n    try: mmap.mmap(-1, 2**31)\n    except OSError: return 7\n'
    p('normal_return', small, 'def check(candidate): assert candidate() == 4\n', 'passed')
    p('large_integer', huge, 'def check(candidate): assert candidate().bit_length() == 20001\n', 'passed')
    p('exception_shaped_return', shape, "def check(candidate): assert candidate()[0] == 'exception'\n", 'passed')
    p('program_name_error', 'def f(): return nonexistent_name\n', call, 'failed', 'original_suite')
    p('program_assertion_failure', small, 'def check(candidate): assert candidate() == 5\n', 'failed', 'original_suite')
    p('ordinary_oserror', io_error, call, 'failed', 'original_suite')
    p('program_value_error', value_error, call, 'failed', 'original_suite')
    p('expected_program_exception', value_error, 'def check(candidate):\n    try: candidate()\n    except ValueError: pass\n    else: assert False\n', 'passed')
    p('source_syntax_error', 'def f(: pass\n', call, 'failed', 'compile_source')
    p('test_syntax_error', small, 'def check(: pass\n', 'unavailable', 'compile_tests')
    p('initialization_error', "raise ValueError('initialization')\ndef f(): return 4\n", call, 'failed', 'initialize_source')
    p('real_memory_error', memory, call, 'unavailable', 'invoke_program')
    p('real_os_enomem', enomem, call, 'unavailable', 'invoke_program')
    p('keyboard_interrupt', interrupt, call, 'unavailable', 'invoke_program')
    p('resource_caught_inside_program', caught_memory, 'def check(candidate): assert candidate() == 7\n', 'passed')
    p('resource_caught_by_original_suite', enomem, 'def check(candidate):\n    try: candidate()\n    except BaseException: pass\n', 'unavailable', 'invoke_program')
    p('before_encoding_failure', 'def f(x): return 1\n', 'def check(candidate): assert candidate(object()) == 1\n', 'unavailable', 'encode_arguments_before')
    p('copy_failure', "class Uncopyable:\n    def __deepcopy__(self,memo): raise ValueError('copy failed')\ndef f(x): return 1\n", 'def check(candidate): assert candidate(Uncopyable()) == 1\n', 'unavailable', 'encode_arguments_before')
    p('post_encoding_failure', 'def f(x):\n    x.append(object())\n    return 1\n', 'def check(candidate): assert candidate([]) == 1\n', 'unavailable', 'encode_argument_poststate')
    p('return_encoding_failure', 'def f(): return object()\n', 'def check(candidate): assert candidate() is not None\n', 'unavailable', 'encode_return_value')
    p('exception_message_encoding_failure', bad_message, call, 'unavailable', 'encode_program_exception')
    p('observer_failure_caught_broadly', 'def f(x): return 1\n', 'def check(candidate):\n    try: candidate(object())\n    except BaseException: pass\n', 'unavailable', 'encode_arguments_before')
    p('cpu_limit', 'def f():\n    while True: pass\n', call, 'process_unavailable')
    p('wall_limit', 'import time\ndef f(): time.sleep(30)\n', call, 'wall_unavailable')

    e('normal_return', small, 'observed_return')
    e('large_integer', huge, 'observed_return')
    e('exception_shaped_return', shape, 'observed_return')
    e('program_name_error', 'def f(): return nonexistent_name\n', 'observed_exception')
    e('program_assertion_error', 'def f(): assert False\n', 'observed_exception')
    e('ordinary_oserror', io_error, 'observed_exception')
    e('program_value_error', value_error, 'observed_exception')
    e('source_syntax_error', 'def f(: pass\n', 'compile_unavailable')
    e('initialization_error', "raise ValueError('initialization')\ndef f(): return 4\n", 'unavailable', 'initialize_source')
    e('real_memory_error', memory, 'unavailable', 'invoke_program')
    e('real_os_enomem', enomem, 'unavailable', 'invoke_program')
    e('keyboard_interrupt', interrupt, 'unavailable', 'invoke_program')
    e('resource_caught_inside_program', caught_memory, 'observed_return')
    e('return_encoding_failure', 'def f(): return object()\n', 'unavailable', 'encode_return_value')
    e('post_encoding_failure', 'def f(x):\n    x.append(object())\n    return 1\n', 'unavailable', 'encode_argument_poststate', [[[]]])
    e('exception_message_encoding_failure', bad_message, 'unavailable', 'encode_program_exception')
    e('per_invocation_guard', 'def f():\n    while True: pass\n', 'unavailable', 'invoke_program')
    # Deliver the actual callback synchronously to guarantee that this control
    # enters the catch branch; asynchronous expiry is exercised independently.
    e('per_invocation_guard_caught_broadly', "import __main__\ndef f():\n    try:\n        __main__.alarm_handler(14, None)\n    except BaseException:\n        print('caught alarm')\n        return 7\n", 'unavailable', 'invoke_program')
    e('cpu_limit_with_flushed_prefix', 'import signal\ndef f(x):\n    if x == 0: return 0\n    signal.signal(signal.SIGALRM, signal.SIG_IGN)\n    while True: pass\n', 'process_unavailable', inputs=[[0],[1]])
    e('wall_limit_with_flushed_prefix', 'import signal,time\ndef f(x):\n    if x == 0: return 0\n    signal.signal(signal.SIGALRM, signal.SIG_IGN)\n    time.sleep(30)\n', 'wall_unavailable', inputs=[[0],[1]])

    def run_control(item):
        family, case = item
        runner = args.primary_runner.resolve() if family == 'primary' else args.enhanced_runner.resolve()
        if family == 'primary':
            request={'source':case['source'],'test':case['test'],'entry_point':'f'}
            wall=15
        else:
            request={'reference':case['source'],'candidate':case['source'],'entry_point':'f',
                     'base_input':case['inputs'],'plus_input':[],'invocation_seconds':.05}
            wall=math.ceil(15+len(case['inputs'])*(.1+.02))
        with tempfile.TemporaryDirectory(prefix='he-observer-v3-control-') as temporary:
            raw=Path(temporary)/'stdout.jsonl'
            with raw.open('w') as output:
                child=subprocess.Popen([sys.executable,'-B','-S',str(runner)],cwd=temporary,env=env,
                    stdin=subprocess.PIPE,stdout=output,stderr=subprocess.PIPE,text=True)
                timed_out=False
                try: _,stderr=child.communicate(json.dumps(request),timeout=wall)
                except subprocess.TimeoutExpired:
                    timed_out=True;child.kill();_,stderr=child.communicate()
            records=[json.loads(line) for line in raw.read_text().splitlines() if line.strip()]
        expected=case['expected']
        if expected=='wall_unavailable':
            assert timed_out, (family,case,records,child.returncode)
        elif expected=='process_unavailable':
            assert not timed_out and child.returncode<0,(family,case,records,child.returncode)
        elif expected=='compile_unavailable':
            assert child.returncode==0 and len(records)==1 and records[0]['status']=='compile_unavailable'
        elif family=='primary':
            assert child.returncode==0 and records[0]['status']==expected,(family,case,records)
            if case['phase']:assert records[0]['error']['phase']==case['phase'],(case,records)
            if case['name']=='exception_shaped_return':assert records[0]['observations'][0]['result'][0]=='return'
        else:
            assert child.returncode==0,(family,case,stderr)
            pairs=[r for r in records if r.get('kind')=='pair']
            assert len(pairs)==1,(case,records)
            for side in ('reference','candidate'):
                result=pairs[0][side]
                if expected=='unavailable':
                    assert result['status']=='unavailable',(case,result)
                    if case['phase']:assert result['phase']==case['phase'],(case,result)
                    if case['name']=='per_invocation_guard_caught_broadly':assert result['stdout']=='caught alarm\n',(case,result)
                else:
                    assert result['status']=='observed' and result['outcome'][0]==expected.removeprefix('observed_'),(case,result)
            if expected=='unavailable':assert pairs[0]['return_equal'] is None
            else:assert pairs[0]['return_equal'] is True
        if family=='enhanced' and expected in ('wall_unavailable','process_unavailable'):
            pairs=[r for r in records if r.get('kind')=='pair']
            assert len(pairs)==1 and pairs[0]['index']==0 and pairs[0]['return_equal'] is True,(case,records)
        return {'family':family,'control':case['name'],'passed':True,'expected':expected,
                'source':case['source'],'request':request,'wall_limit':wall,'wall_timeout':timed_out,
                'returncode':child.returncode,'stderr':stderr,'records':records}

    with ThreadPoolExecutor(max_workers=6) as pool:
        records=list(pool.map(run_control, [('primary',c) for c in primary]+[('enhanced',c) for c in enhanced]))
    # JSON datasets cannot contain user-defined deepcopy objects. Exercise this
    # observer operation directly with a bounded input, separate from native cases.
    spec=importlib.util.spec_from_file_location('enhanced_v3_copy_control',args.enhanced_runner)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    previous=signal.signal(signal.SIGALRM,module.alarm_handler)
    class Uncopyable:
        def __deepcopy__(self,memo):raise ValueError('copy control')
    try:
        result=module.observe(compile('def f(x): return 1\n','<copy-control>','exec'),'f',[Uncopyable()],.05)
    finally:signal.signal(signal.SIGALRM,previous)
    assert result['status']=='unavailable' and result['phase']=='copy_arguments'
    records.append({'family':'enhanced','control':'copy_failure','passed':True,'expected':'unavailable',
                    'native_request_roundtrip':False,'scope':'Direct bounded observer unit: custom deepcopy objects cannot occur in the JSON input asset.',
                    'records':[result]})
    report={'status':'PASS','controls':len(records),'primary_controls':len(primary),'enhanced_controls':len(enhanced)+1,
            'primary_observer_sha256':digest(args.primary_runner),'enhanced_observer_sha256':digest(args.enhanced_runner),
            'classification_policy':'Only uncaught resource/interruption events are unavailable; a program that handles such an event and returns normally can still satisfy its contract. Caught observer failures or elapsed observer guards cannot become support.',
            'records':records}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','controls','primary_controls','enhanced_controls','primary_observer_sha256','enhanced_observer_sha256')}))


if __name__=='__main__':main()
