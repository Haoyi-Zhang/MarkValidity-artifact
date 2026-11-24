#!/usr/bin/env python3
"""Receive CREST source/contract observations and independently re-score models."""
import argparse
import collections
import json
from pathlib import Path
import warnings

import joblib
import sklearn

# The saved scores were computed on an x86-64 CPU with AVX-512, where OpenBLAS
# (DYNAMIC_ARCH, bundled with numpy 2.3.5) selects its SkylakeX ddot kernel.
# CPUs without AVX-512 use the Haswell/Zen kernel, whose different summation
# order changes LogReg scores in the last bits (observed: <= 1.6e-16 absolute).
# Bitwise-equal scores are reported as such; otherwise this absolute tolerance
# is applied, and every detector decision must still be identical.
PROBABILITY_ABS_TOLERANCE = 1e-15


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def receive_native(record, task):
    if record['returncode'] != 0 or record['interruption']:
        return None
    if 'test' in task:
        obj = json.loads(record['stdout'])
        if obj.get('schema') in ('crest-original-assertion-suite','crest-isolated-original-assertions'):
            require(type(obj.get('check_finished')) is bool,'malformed direct-assertion completion marker')
            if obj['status']=='passed':
                require(obj['check_finished'] and obj['error'] is None,
                        'direct-assertion success lacks original check completion')
                return True
            if obj['status']=='failed':
                phases=({'compile_check_program','execute_check_program'} if
                        obj['schema']=='crest-original-assertion-suite' else
                        {'compile_source','initialize_source','resolve_entry_point','original_suite'})
                require(not obj['check_finished'] and not obj['error'].get('reason') and
                        obj['error']['phase'] in phases and
                        obj['error']['type'] not in {'builtins.MemoryError','builtins.KeyboardInterrupt'},
                        'direct-assertion failure is an observer/resource event')
                return False
            require(obj['status']=='unavailable' and not obj['check_finished'] and
                    obj['error']['reason'] in {'resource_unavailable','interrupted','harness_or_contract_error'},
                    'direct-assertion unavailable record has no declared reason')
            return None
        require(isinstance(obj['observations'], list), 'malformed HumanEval observations')
        if obj['status'] == 'passed':
            require(obj['error'] is None, 'contradictory HumanEval success')
            return True
        if obj['status'] == 'failed':
            require(obj['error']['phase'] in {'compile_source', 'initialize_source', 'original_suite'},
                    'unadmissible HumanEval program failure')
            require(obj['error']['type'] not in {'builtins.MemoryError', 'builtins.KeyboardInterrupt'},
                    'resource exception is not program failure')
            return False
        return None
    events = [json.loads(line) for line in record['stdout'].splitlines() if line.strip()]
    compile_events = [e for e in events if e['event'] == 'source_compile']
    tests = [e for e in events if e['event'] == 'test_result']
    terminals = [e for e in events if e['event'] == 'complete']
    require(len(compile_events) == 1 and len(terminals) == 1 and terminals[0] is events[-1],
            'missing or repeated MBPP lifecycle events')
    terminal = terminals[0]
    expected = len(task['test_list'])
    require(terminal['scheduled_tests'] == expected and terminal['completed_tests'] == len(tests),
            'incorrect MBPP event counts')
    indices = [e['test_index'] for e in tests]
    require(len(indices) == len(set(indices)) and all(0 <= i < expected for i in indices),
            'duplicated or invalid MBPP assertion')
    counts = collections.Counter(e['status'] for e in tests)
    for status, key in [('passed','passed_tests'),('failed','failed_tests'),('unavailable','unavailable_tests')]:
        require(terminal[key] == counts[status], 'incorrect MBPP summary count')
    failures = [e for e in compile_events + tests if e['status'] == 'failed']
    for event in failures:
        require(event['error']['phase'] in {'compile_source','initialize_source','original_assertion'},
                'unadmissible MBPP program failure')
        require(event['error']['type'] not in {'builtins.MemoryError','builtins.KeyboardInterrupt'},
                'resource exception is not program failure')
    if failures:
        require(terminal['status'] == 'failed', 'failed MBPP evidence conflicts with terminal')
        return False
    if terminal['status'] == 'passed':
        require(compile_events[0]['status'] == 'passed' and counts['passed'] == expected and len(tests) == expected,
                'MBPP success missing tests')
        return True
    return None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study',type=Path,required=True)
    p.add_argument('--upstream',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    require(sklearn.__version__=='1.7.2', 'Use the estimator training environment scikit-learn 1.7.2')
    tasks=json.loads((args.study/'tasks.json').read_text())
    rows=json.loads((args.study/'results.json').read_text())
    protocol=json.loads((args.study/'protocol.json').read_text())
    key=lambda r:(r.get('cohort',''),r['dataset'],str(r['task_id']))
    taskmap={key(t):t for t in tasks}
    require(len(taskmap)==len(tasks)==len(rows), 'missing, duplicated, or extra tasks')
    require(set(map(key,rows))==set(taskmap),'task population changed')
    model_files={'rf':'model_random_forest.pkl','logreg_l1':'model_logreg_l1.pkl','logreg_l2':'model_logreg_l2.pkl'}
    display={'rf':'Random Forest','logreg_l1':'LogReg L1 (Lasso)','logreg_l2':'LogReg L2 (Ridge)'}
    thresholds=json.loads((args.upstream/'crest/models/thresholds.json').read_text())
    models={}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for name,file in model_files.items():
            models[name]=joblib.load(args.upstream/'crest/models'/file)
            require(models[name].classes_.tolist()==[0,1],
                    'positive-probability column requires the declared class order [0, 1]')
    require(not caught,'estimator loading produced a compatibility warning')
    scores=0
    tolerated=0
    max_difference=0.0
    model_calls=0
    score_cache={}
    native_suites=0
    unique_features=set()
    labels={}
    for row in rows:
        task=taskmap[key(row)]
        require((args.study/row['reference_source']).read_text()==task['source'],'reference bytes changed')
        ref_label=receive_native(row['reference_native'],task);native_suites+=1
        require(ref_label==row['reference_native']['label'],'reference admission mismatch')
        if 'candidate_native' in row:
            label=receive_native(row['candidate_native'],task);native_suites+=1
            require(label==row['candidate_native']['label'],'candidate admission mismatch')
            require(row['source_changed']==((args.study/row['candidate_source']).read_text()!=task['source']),
                    'wrong source-change indicator')
        else:
            label=None
        validity=label if ref_label is True else None
        require(validity==row['validity'],'qualification/validity mismatch')
        labels[key(row)]=validity
        for side in ('reference_detector','candidate_detector'):
            record=row.get(side,{})
            if record.get('status')!='completed':
                continue
            features=record['features']
            require(len(features)==49 and all(type(v)is int and v in(0,1) for v in features),'invalid feature vector')
            unique_features.add(tuple(features))
            for name in models:
                cache_key=(name,tuple(features))
                if cache_key not in score_cache:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore',category=UserWarning)
                        score_cache[cache_key]=float(models[name].predict_proba([features])[0][1])
                    model_calls+=1
                probability=score_cache[cache_key]
                saved=record['classifiers'][name]
                if probability!=saved['probability']:
                    difference=abs(probability-saved['probability'])
                    require(difference<=PROBABILITY_ABS_TOLERANCE,
                            f'{name} probability changed under training-compatible environment')
                    tolerated+=1
                    max_difference=max(max_difference,difference)
                configured=thresholds[display[name]]
                constraint=next(k for k in ('fpr_1pct','fpr_5pct','default') if configured.get(k))
                threshold=configured[constraint] if constraint=='default' else configured[constraint]['threshold']
                require(saved['constraint']==constraint and saved['threshold']==threshold,'changed operating point')
                require(saved['detected']==(probability>=threshold)==(saved['probability']>=threshold),
                        'wrong detector decision')
                scores+=1
        for name in models:
            d=row.get('candidate_detector',{}).get('classifiers',{}).get(name,{}).get('detected')
            j=False if validity is False or d is False else (True if validity is True and d is True else None)
            require(row['classifiers'][name]=={'detected':d,'joint':j},'joint observation mismatch')
    result={'status':'PASS','task_rows':len(rows),'native_suites_received':native_suites,
            'saved_probabilities_verified':scores,'actual_classifier_evaluations':model_calls,
            'distinct_feature_vectors':len(unique_features),
            'training_compatible_sklearn':sklearn.__version__,'model_loading_warnings':0,
            'probabilities_bitwise_equal_to_saved_python_floats':tolerated==0,
            'probabilities_within_tolerance_not_bitwise':tolerated,
            'probability_abs_tolerance':PROBABILITY_ABS_TOLERANCE,
            'max_abs_probability_difference':max_difference,
            'detector_decisions_identical':True,
            'summary':'Native outcome envelopes, retained reference text, all saved classifier scores and upstream thresholds received without output-based exclusion. Exact archived input/contract/native-request/observer binding is checked by the separate provenance receiver; feature re-extraction is not claimed here.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
