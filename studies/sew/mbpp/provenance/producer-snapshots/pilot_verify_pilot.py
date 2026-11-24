"""Receive a complete frozen MBPP pilot; replay saved sources and stock pipeline.

Does not import the study producer. Native replay intentionally uses the same
explicit test-contract runner. Elapsed times and traceback paths are diagnostic,
not compared behavioral observations. Prints a report without editing the study.
"""
from pathlib import Path
import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]
VENDOR = BASE / 'work/MarkValidity_TOSEM/artifact/external-studies/sew_aliasing/vendor'


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(value): return hashlib.sha256(value).hexdigest()

def canonical(value): return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def observed_signature(result):
    def item(event):
        x = {k: v for k, v in event.items() if k not in ('elapsed_seconds', 'error')}
        if 'error' in event:
            x['error'] = None if event['error'] is None else {k:v for k,v in event['error'].items() if k != 'traceback'}
        return x
    return {'status': result['status'], 'returncode': result['returncode'], 'stderr': result['stderr'],
            'events': [item(x)for x in result['events']]}


def replay(job):
    source, task, saved = job
    env = os.environ.copy(); env.pop('PYTHONPATH', None)
    env.update(PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    with tempfile.TemporaryDirectory(prefix='markvalidity-mbpp-receiver-') as temp:
        proc = subprocess.run([sys.executable, '-B', '-S', str(HERE / 'native_runner.py')],
            cwd=temp, env=env, input=json.dumps({'source': source, 'test_imports': task['test_imports'], 'test_list': task['test_list']}),
            text=True, capture_output=True, timeout=15)
    events = [json.loads(x)for x in proc.stdout.splitlines()if x.strip()]
    complete = [e for e in events if e.get('event') == 'complete']
    require(proc.returncode == 0 and len(complete) == 1, 'Replay did not complete for task ' + str(task['task_id']))
    actual = {'status': complete[0]['status'], 'returncode': proc.returncode, 'stderr': proc.stderr, 'events': events}
    require(observed_signature(actual) == observed_signature(saved), 'Native observation mismatch for task ' + str(task['task_id']))
    return sum(e['event'] == 'test_result' and e['assertion_reached'] for e in events)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--results',type=Path,required=True);parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args();out=args.results.resolve();start=time.monotonic()
    manifest=json.loads((out/'files-sha256.json').read_text())
    actual_files={p.relative_to(out).as_posix()for p in out.rglob('*')if p.is_file() and p.name!='files-sha256.json'}
    require(set(manifest)==actual_files,'Frozen file set differs')
    for rel,digest in manifest.items():require(sha((out/rel).read_bytes())==digest,'File digest differs: '+rel)
    tasks=json.loads((HERE.parent/'sanitized-mbpp.json').read_text());by_task={t['task_id']:t for t in tasks}
    spec=json.loads((out/'specification.json').read_text());refs=json.loads((out/'references.json').read_text());rows=json.loads((out/'rows.json').read_text());summary=json.loads((out/'summary.json').read_text())
    require(spec['dataset_sha256']==sha((HERE.parent/'sanitized-mbpp.json').read_bytes()),'Dataset binding differs')
    require(spec['producer_sha256']==sha((HERE/'run_pilot.py').read_bytes()),'Producer snapshot differs')
    require(spec['native_runner_sha256']==sha((HERE/'native_runner.py').read_bytes()),'Native contract runner differs')
    require(spec['task_ids_in_frozen_order']==[t['task_id']for t in tasks],'Task selection/order differs')
    expected={(t['task_id'],k['key_id'])for t in tasks for k in spec['keys']}
    got=[(r['task_id'],r['key_id'])for r in rows]
    require(len(got)==len(set(got)) and set(got)==expected,'Missing/duplicate configuration')
    require([r['task_id']for r in refs]==[t['task_id']for t in tasks],'Reference inventory differs')
    ref_map={r['task_id']:r for r in refs};jobs=[]
    for ref in refs:
        task=by_task[ref['task_id']];source=(out/ref['source_path']).read_text()
        require(source==task['code'],'Reference source differs from official record')
        require(sha(source.encode())==ref['source_sha256'],'Reference digest differs')
        saved=json.loads((out/ref['observation_path']).read_text());require(saved['status']==ref['status'],'Reference status differs')
        contract=json.loads((out/'contracts'/('MBPP-%04d.json'%ref['task_id'])).read_text())
        require(contract['test_list']==task['test_list'] and contract['test_imports']==task['test_imports'],'Test contract differs')
        require(sha(canonical(contract))==ref['contract_sha256'],'Contract digest differs')
        jobs.append((source,task,saved))
    sys.path.insert(0,str(VENDOR))
    from sew import embed,detect
    replayed=0
    for row in rows:
        task=by_task[row['task_id']];ref=ref_map[row['task_id']]
        require(row['reference_sha256']==ref['source_sha256'] and row['contract_sha256']==ref['contract_sha256'],'Row obligation differs')
        require(row['reference_status']==ref['status'],'Row reference status differs')
        require(row['candidate_status'] in ('passed','failed'),'This receiver requires the complete observed pilot, not an unavailable row')
        source=(out/row['candidate_path']).read_text();saved=json.loads((out/row['observations_path']).read_text())
        require(sha(source.encode())==row['candidate_sha256'],'Candidate digest differs')
        require(saved['status']==row['candidate_status'],'Candidate status differs')
        expected_validity='unavailable' if ref['status']!='passed' else ('supported' if saved['status']=='passed' else 'contradicted')
        require(row['validity_status']==expected_validity,'Validity label does not match reference/observations')
        require(row['joint_supported']==(expected_validity=='supported' and row['detected'] is True),'Joint outcome differs')
        require(row['failed_test_indices']==[e['test_index']for e in saved['events']if e['event']=='test_result' and e['status']=='failed'],'Failure indices differ')
        key=bytes.fromhex(row['key_hex']);emitted=embed(task['code'],'python',key)
        require(emitted['code']==source,'Stock embedding did not reproduce exact candidate')
        require({k:v for k,v in emitted.items()if k!='code'}==row['embedding'],'Embedding metadata differs')
        require(detect(source,'python',key)==row['detector'],'Stock candidate detection differs')
        require(detect(task['code'],'python',key)==row['reference_detector'],'Reference detection differs')
        require(row['detected']==(row['detector']['verdict']=='Watermark detected'),'Recorded detection flag differs')
        jobs.append((source,task,saved));replayed+=1
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        assertions=sum(pool.map(replay,jobs))
    counts=summary['all_scheduled_attempts']
    for key,val in {'attempts':len(rows),'detected':sum(r['detected']for r in rows),'joint_supported':sum(r['joint_supported']for r in rows),'detected_contradicted':sum(r['detected']and r['validity_status']=='contradicted'for r in rows)}.items():require(counts[key]==val,'Summary differs: '+key)
    require(counts['candidate_statuses']==dict(collections.Counter(r['candidate_status']for r in rows)),'Summary statuses differ')
    print(json.dumps({'status':'PASS','scope':'Full saved-source native replay under the shared explicit assertion contract plus exact stock embedding and detector replay; source/contract/configuration/count linkage independently reconstructed.','manifest_files_checked':len(manifest),'reference_sources_reexecuted':len(refs),'candidate_sources_reexecuted':len(rows),'original_assertions_reexecuted':assertions,'upstream_embedding_detection_pairs_replayed':replayed,'candidate_statuses':counts['candidate_statuses'],'detected':counts['detected'],'joint_supported':counts['joint_supported'],'detected_contradicted':counts['detected_contradicted'],'summary_sha256':sha((out/'summary.json').read_bytes()),'receiver_sha256':sha(Path(__file__).read_bytes()),'elapsed_seconds':round(time.monotonic()-start,3)},indent=2))


if __name__=='__main__':main()
