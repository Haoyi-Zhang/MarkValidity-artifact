"""Replay deterministic evidence-disclosure schedules against completed labels.

All candidate behavior has already been measured. This retrospective experiment
withholds those labels, starts from fresh-contract seed evidence, and reveals
one exact JavaScript source group at a time. Orders use only known detection
coefficients or source/configuration identities; they never inspect hidden
validity labels. Input-call cost is reported, not optimized by the unit-query
coefficient ordering. No task program executes in this replay.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
from contextlib import contextmanager
import csv
from datetime import datetime,timezone
from fractions import Fraction
import gzip
import hashlib
import io
import json
from math import lcm
from pathlib import Path
import statistics
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'src'))
from covewm.source_admission import admit_python
from covewm.tasks import TASK_BY_NAME,domain_cases

SCHEMES=('lexical','structural','hybrid')
WEIGHTS={
    'balanced':{a:Fraction(1,5) for a in ('rename','normalize','random_flip','strip','mixed')},
    'rename-heavy':{'rename':Fraction(27,50),'random_flip':Fraction(6,25),'strip':Fraction(11,50)},
    'structure-heavy':{'normalize':Fraction(27,50),'random_flip':Fraction(6,25),'strip':Fraction(11,50)},
}
RANDOM_SEEDS=tuple(range(16))
OBSERVATION_RULE='covewm-tagged-return-or-exception-type-and-message-canonical-json-v2'
INITIALIZATION_RULE='covewm-fresh-module-instance-per-input-v1'

def need(condition,message):
    if not condition:raise ValueError(message)

def sha(data):return hashlib.sha256(data.encode() if isinstance(data,str) else data).hexdigest()

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def write_json(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n')

def csv_read(path):
    with Path(path).open(newline='',encoding='utf-8') as handle:return list(csv.DictReader(handle))

def csv_write(path,rows):
    with Path(path).open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)

@contextmanager
def gz_writer(path):
    with Path(path).open('wb') as binary:
        with gzip.GzipFile(filename='',fileobj=binary,mode='wb',mtime=0) as compressed:
            with io.TextIOWrapper(compressed,encoding='utf-8',newline='') as handle:yield handle

def source_key(task,language,digest):return f'{task}|{language}|{digest}'

def order_sources(coefficients,first_configuration,policy,seed=None):
    eligible=[key for key,c in coefficients.items() if c]
    if policy=='largest-coefficient':return sorted(eligible,key=lambda key:(-abs(coefficients[key]),key))
    if policy=='configuration-first':return sorted(eligible,key=lambda key:(first_configuration[key],key))
    if policy=='sha-random':
        need(seed in RANDOM_SEEDS,'unknown random seed')
        return sorted(eligible,key=lambda key:(sha(f'markvalidity-audit-order-v1|{seed}|{key}'),key))
    raise ValueError('unknown disclosure policy')

def interval(known,unknown):
    return known+sum(min(0,c) for c in unknown.values()),known+sum(max(0,c) for c in unknown.values())

def reveal(lower,upper,coefficient,validity):
    need(validity in (0,1),'binary source label required')
    return lower+coefficient*validity-min(0,coefficient),upper+coefficient*validity-max(0,coefficient)

def preference(lower,upper,left,right):return left if lower>0 else right if upper<0 else ''

def run(native,evidence,retained,out):
    native,evidence,retained,out=map(lambda p:Path(p).resolve(),(native,evidence,retained,out))
    need(not out.exists(),'fresh output required')
    ns=json.loads((native/'summary.json').read_text());nr=json.loads((native/'registration.json').read_text())
    need(ns['status']=='PASS' and ns['complete_frozen_design'],'complete native labels required')
    need(nr['observation_rule']==OBSERVATION_RULE and nr['initialization_rule']==INITIALIZATION_RULE,'fresh contract required')
    for name in ('source_labels.csv','completed_rows.csv.gz','reference-domains.json.gz'):
        need(sha((native/name).read_bytes())==ns['outputs_sha256'][name],'native evidence bytes changed')
    need(json.loads((native/'verification.json').read_text())['status']=='PASS','native receiving check required')
    out.mkdir(parents=True)
    started=time.monotonic()
    registration=dict(schema='markvalidity-evidence-budget-replay-v1',started_at_utc=datetime.now(timezone.utc).isoformat(),
        observation_rule=OBSERVATION_RULE,initialization_rule=INITIALIZATION_RULE,
        design='Retrospective release of already measured complete source labels. Ordering rules are deterministic functions of visible detection coefficients and identities only.',
        seed_policy='All saved Python sources re-admitted by restricted AST erasure; fresh JavaScript labels for exact source identities selected by the original 252-row execution inventory. Legacy behavioral flags supply no truth labels.',
        eligibility='Unknown JavaScript groups with nonzero coefficient for the fixed pair; all compared orders use the same eligible set.',
        priority='descending absolute signed source coefficient, ties by task|language|source SHA-256',
        configuration_order='first occurrence of exact source in the frozen source-configuration table',
        random_order='ascending SHA256(markvalidity-audit-order-v1|seed|task|language|source_SHA256), ties by full source key',
        random_seeds=list(RANDOM_SEEDS),random_summary_scope='16 fixed deterministic orders, descriptive range and median only; no probabilistic significance claim',
        query_cost='one source group per query; additional input-call cost equals that task frozen domain size',
        cost_optimality_claim=False,task_program_executions=0,
        input_sha256={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in [native/'summary.json',native/'registration.json',native/'verification.json',
            native/'source_labels.csv',native/'completed_rows.csv.gz',evidence/'sources.jsonl.gz',evidence/'rows.csv.gz',evidence/'pairwise_source_bounds.csv',retained/'raw/semantic_audit.csv']},
        producer_sha256={str(p.relative_to(HERE)):sha(p.read_bytes()) for p in [Path(__file__),HERE/'src/covewm/source_admission.py',HERE/'src/covewm/tasks.py']})
    write_json(out/'registration.json',registration)
    labels={source_key(r['task'],'javascript',r['source_sha256']):int(r['validity']=='supported') for r in csv_read(native/'source_labels.csv')}
    need(len(labels)==22095,'native identity coverage')
    seed_js={source_key(r['task'],'javascript',r['source_sha256']) for r in csv_read(retained/'raw/semantic_audit.csv') if r['language']=='javascript'}
    need(seed_js.issubset(labels),'seed source missing from fresh native evidence')
    proofs=0;reference_hashes={}
    with gzip.open(evidence/'sources.jsonl.gz','rt',encoding='utf-8') as handle,gz_writer(out/'python-proof-rechecks.jsonl.gz') as proofout:
        for line in handle:
            r=json.loads(line);task,lang,h=r['task'],r['language'],r['source_sha256']
            need(sha(r['source'])==h,'source identity differs')
            if lang!='python':continue
            admitted=admit_python(task,r['source']);need(admitted['admitted'] is True,'Python source lacks fresh-compatible erasure evidence')
            key=source_key(task,lang,h);need(key not in labels,'duplicate source identity');labels[key]=1;proofs+=1
            reference=TASK_BY_NAME[task].python_reference.replace('__CARRIERS__','').rstrip()+'\n'
            reference_hashes[task]=sha(reference)
            proofout.write(canonical(dict(task=task,language=lang,source_sha256=h,reference_sha256=sha(reference),
                validity='supported',prefix_statements=admitted['erased_prefix_statements'],
                observation_rule=OBSERVATION_RULE,initialization_rule=INITIALIZATION_RULE,
                basis=admitted['basis']))+'\n')
    need(proofs==22054 and len(labels)==44149,'proof/full source coverage')
    rows=[]
    with gzip.open(native/'completed_rows.csv.gz','rt',encoding='utf-8',newline='') as handle:rows=list(csv.DictReader(handle))
    need(len(rows)==76032,'configuration coverage')
    known={key:value for key,value in labels.items() if '|python|' in key or key in seed_js}
    unknown={key:value for key,value in labels.items() if '|javascript|' in key and key not in seed_js}
    first={};detected=defaultdict(Counter);family_sizes=Counter();config_keys=set()
    domain_sizes={task:len(domain_cases(task)) for task in TASK_BY_NAME}
    costs={key:domain_sizes[key.split('|')[0]] for key in labels}
    for index,row in enumerate(rows):
        config=tuple(row[f] for f in ('task','language','scheme','attack','severity','payload_index'))
        need(config not in config_keys,'duplicate configuration');config_keys.add(config)
        key=source_key(row['task'],row['language'],row['source_sha256'])
        need(key in labels and int(row['validity'])==labels[key],'configuration truth differs from source label')
        first.setdefault(key,index)
        family_sizes[(row['language'],row['scheme'],row['attack'])]+=1
        detected[key][(row['scheme'],row['attack'])]+=int(row['detected'])
    need(set(first)==set(labels) and set(family_sizes.values())=={2112},'source support or family denominator differs')
    old_bounds={(r['mixture'],r['left'],r['right']):r for r in csv_read(evidence/'pairwise_source_bounds.csv') if r['language']=='combined'}
    trace_fields=['mixture','left','right','policy','seed','query','task','source_sha256','revealed_validity','coefficient_numerator',
        'denominator','lower_numerator','upper_numerator','width_numerator','additional_input_calls','preferred']
    summaries=[];bridges=[];coefficient_rows=[];checkpoints=[]
    with gz_writer(out/'traces.csv.gz') as tracehandle:
        writer=csv.DictWriter(tracehandle,fieldnames=trace_fields,lineterminator='\n');writer.writeheader()
        for mixture,weights in WEIGHTS.items():
            scale=lcm(*(v.denominator for v in weights.values()));denominator=2*2112*scale
            integer_weights={attack:int(w*scale) for attack,w in weights.items()}
            for i,left in enumerate(SCHEMES):
                for right in SCHEMES[i+1:]:
                    coefficient={key:sum(weight*(counts[(left,attack)]-counts[(right,attack)]) for attack,weight in integer_weights.items())
                                 for key,counts in detected.items()}
                    k=sum(coefficient[key]*v for key,v in known.items())
                    u={key:coefficient[key] for key in unknown}
                    lo,hi=interval(k,u);true_gap=sum(coefficient[key]*v for key,v in labels.items())
                    old=old_bounds[(mixture,left,right)]
                    old_same=Fraction(lo,denominator)==Fraction(old['lower_exact']) and Fraction(hi,denominator)==Fraction(old['upper_exact'])
                    bridges.append(dict(mixture=mixture,left=left,right=right,denominator=denominator,seed_lower_exact=str(Fraction(lo,denominator)),
                        seed_upper_exact=str(Fraction(hi,denominator)),earlier_lower_exact=old['lower_exact'],earlier_upper_exact=old['upper_exact'],
                        same_endpoints_after_fresh_label_reclassification=old_same))
                    for key,c in sorted(u.items()):
                        if c:coefficient_rows.append(dict(mixture=mixture,left=left,right=right,source_key=key,coefficient_numerator=c,
                            denominator=denominator,domain_input_calls=costs[key],first_configuration=first[key]))
                    policies=[('largest-coefficient',None),('configuration-first',None)]+[('sha-random',seed) for seed in RANDOM_SEEDS]
                    for policy,seed in policies:
                        ordered=order_sources(u,first,policy,seed)
                        lower,upper=lo,hi;calls=0;initial_pref=preference(lower,upper,left,right)
                        first_certificate=0 if initial_pref else None;first_cost=0 if initial_pref else None
                        cert_pref=initial_pref;initial_width=hi-lo
                        common=dict(mixture=mixture,left=left,right=right,policy=policy,seed='' if seed is None else seed,denominator=denominator)
                        writer.writerow(dict(common,query=0,task='',source_sha256='',revealed_validity='',coefficient_numerator=0,
                            lower_numerator=lower,upper_numerator=upper,width_numerator=upper-lower,additional_input_calls=0,preferred=initial_pref))
                        for number,key in enumerate(ordered,1):
                            c=u[key];v=unknown[key]
                            lower,upper=reveal(lower,upper,c,v);calls+=costs[key]
                            pref=preference(lower,upper,left,right)
                            if first_certificate is None and pref:first_certificate=number;first_cost=calls;cert_pref=pref
                            task,language,h=key.split('|')
                            writer.writerow(dict(common,query=number,task=task,source_sha256=h,revealed_validity=v,coefficient_numerator=c,
                                lower_numerator=lower,upper_numerator=upper,width_numerator=upper-lower,additional_input_calls=calls,preferred=pref))
                            if number in (1,2,5,10,20,50,100,200,500,1000,2000,3000,4000) or number in (first_certificate,len(ordered)):
                                checkpoints.append(dict(common,queries=number,additional_input_calls=calls,lower_exact=str(Fraction(lower,denominator)),
                                    upper_exact=str(Fraction(upper,denominator)),remaining_width_exact=str(Fraction(upper-lower,denominator)),
                                    remaining_width_fraction=f'{(upper-lower)/initial_width:.12f}' if initial_width else '0.000000000000',preferred=pref))
                        need(lower==upper==true_gap,'completed disclosure differs from exact truth')
                        summaries.append(dict(common,eligible_unknown_sources=len(ordered),initial_lower_exact=str(Fraction(lo,denominator)),
                            initial_upper_exact=str(Fraction(hi,denominator)),first_certified_query=first_certificate,
                            first_certified_additional_input_calls=first_cost,certified_preference=cert_pref,
                            final_gap_exact=str(Fraction(true_gap,denominator)),all_eligible_input_calls=calls,
                            order_sha256=sha('\n'.join(ordered)+'\n')))
    csv_write(out/'schedule_summary.csv',summaries);csv_write(out/'fresh_policy_bridge.csv',bridges)
    with gz_writer(out/'coefficients.csv.gz') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(coefficient_rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(coefficient_rows)
    csv_write(out/'checkpoints.csv',checkpoints)
    random_rows=[]
    for bridge in bridges:
        key=bridge['mixture'],bridge['left'],bridge['right']
        subset=[r for r in summaries if (r['mixture'],r['left'],r['right'])==key and r['policy']=='sha-random']
        queries=[r['first_certified_query'] for r in subset];calls=[r['first_certified_additional_input_calls'] for r in subset]
        need(all(value is not None for value in queries),'true tie cannot be summarized as certified')
        random_rows.append(dict(mixture=key[0],left=key[1],right=key[2],orders=len(subset),queries_min=min(queries),
            queries_median=statistics.median(queries),queries_max=max(queries),input_calls_min=min(calls),
            input_calls_median=statistics.median(calls),input_calls_max=max(calls)))
    csv_write(out/'random_order_summary.csv',random_rows)
    summary=dict(status='PASS',task_program_executions=0,scope='Retrospective release of completed v2 labels; no new task execution and no inference of unknown validity from detector scores.',
        python_source_proofs_rechecked=proofs,javascript_fresh_seed_sources=len(seed_js),javascript_fresh_seed_configuration_rows=sum(source_key(r['task'],r['language'],r['source_sha256']) in seed_js for r in rows),
        known_source_groups=len(known),unknown_javascript_source_groups=len(unknown),seed_unique_javascript_input_calls=sum(costs[k] for k in seed_js),
        contrasts=len(bridges),schedules=len(summaries),random_orders_per_contrast=len(RANDOM_SEEDS),
        fresh_seed_policy_matches_earlier_endpoints=all(r['same_endpoints_after_fresh_label_reclassification'] for r in bridges),
        balanced_lexical_structural=[r for r in summaries if r['mixture']=='balanced' and r['left']=='lexical' and r['right']=='structural'],
        balanced_random_order_summary=next(r for r in random_rows if r['mixture']=='balanced' and r['left']=='lexical' and r['right']=='structural'),
        width_optimality='Largest absolute coefficient minimizes remaining interval width for a fixed number of distinct source queries; it does not necessarily minimize certification time or input-call cost.',
        wall_seconds=round(time.monotonic()-started,6))
    summary['outputs_sha256']={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='summary.json'}
    write_json(out/'summary.json',summary)
    print(canonical({k:summary[k] for k in ['status','python_source_proofs_rechecked','javascript_fresh_seed_sources','unknown_javascript_source_groups','contrasts','schedules','balanced_random_order_summary','wall_seconds']}))
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,default=HERE/'results/revision-native-completion')
    parser.add_argument('--evidence',type=Path,default=HERE/'results/revision-source-joint')
    parser.add_argument('--retained',type=Path,default=HERE/'results/revision-reproduction')
    parser.add_argument('--out',type=Path,default=HERE/'results/revision-audit-budget')
    args=parser.parse_args();run(args.native,args.evidence,args.retained,args.out)
