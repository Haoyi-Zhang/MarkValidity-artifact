"""Compare retained fresh-input Python and JavaScript reference observations."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify():
    py=HERE/'results/revision-python-fresh';js=HERE/'results/revision-native-completion'
    with gzip.open(py/'observations.jsonl.gz','rt',encoding='utf-8') as handle:
        python={r['task']:r for line in handle if (r:=json.loads(line))['role']=='reference'}
    rows=[]
    inputs={'results/revision-python-fresh/observations.jsonl.gz':sha(py/'observations.jsonl.gz')}
    for task,left in sorted(python.items()):
        path=js/'raw'/f'{task}.jsonl.gz';inputs[str(path.relative_to(HERE))]=sha(path)
        with gzip.open(path,'rt',encoding='utf-8') as handle:records=[json.loads(line) for line in handle]
        vectors={r['observation_hash']:r['observations'] for r in records if r['type']=='observation_vector'}
        right=next(r for r in records if r['type']=='program' and r['role']=='reference')
        nominal=next(r for r in records if r['type']=='nominal_program' and r['role']=='reference')
        right_domain=[json.loads(value) for value in vectors[right['observation_hash']]]
        right_nominal=[json.loads(value) for value in nominal['observations']]
        if left['observations']!=right_domain or left['nominal_observations']!=right_nominal:
            raise ValueError('fresh typed reference observations differ for '+task)
        if left['domain_observations_sha256']!=right['observation_hash'] or left['nominal_observations_sha256']!=nominal['observation_hash']:
            raise ValueError('fresh reference digest protocol differs for '+task)
        rows.append(dict(task=task,domain_cases=len(left['observations']),nominal_cases=len(left['nominal_observations']),
            domain_observations_equal=True,nominal_observations_equal=True,domain_observations_sha256=right['observation_hash'],
            nominal_observations_sha256=nominal['observation_hash']))
    if len(rows)!=12:raise ValueError('complete reference coverage required')
    output=js/'fresh_cross_language_parity.csv'
    with output.open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    report=dict(status='PASS',scope='Full stored typed reference vectors compared value by value under the fresh-input v2 contract; no program execution by this check.',
        tasks=len(rows),domain_observation_pairs=sum(r['domain_cases'] for r in rows),nominal_observation_pairs=sum(r['nominal_cases'] for r in rows),
        input_sha256=inputs,producer_sha256=sha(Path(__file__)),output_sha256=sha(output))
    (js/'fresh_cross_language_parity.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('input_sha256',)},indent=2))

if __name__=='__main__':verify()
