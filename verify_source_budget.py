"""Independently receive every evidence-disclosure trace and its exact bounds.

This verifier imports neither audit_source_budget nor its aggregation/order
helpers. It rebuilds source coefficients from configuration rows, rechecks the
Python proof rule explicitly, and reconstructs bound endpoints and costs after
every disclosed source. It performs no task-program execution.
"""
from collections import Counter,defaultdict
import argparse
import csv
from fractions import Fraction
import gzip
import hashlib
import json
from math import lcm
from pathlib import Path
import statistics
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'src'))
from covewm.source_admission import admit_python
from covewm.tasks import TASK_BY_NAME,domain_cases

PAIRS=(('lexical','structural'),('lexical','hybrid'),('structural','hybrid'))
WEIGHTS={
 'balanced':{a:Fraction(1,5) for a in ('rename','normalize','random_flip','strip','mixed')},
 'rename-heavy':{'rename':Fraction(54,100),'random_flip':Fraction(24,100),'strip':Fraction(22,100)},
 'structure-heavy':{'normalize':Fraction(54,100),'random_flip':Fraction(24,100),'strip':Fraction(22,100)}}

def need(condition,message):
 if not condition:raise ValueError(message)
def sha(value):return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()
def table(path):
 with Path(path).open(encoding='utf-8',newline='') as stream:return list(csv.DictReader(stream))
def jsonlines(path):
 with gzip.open(path,'rt',encoding='utf-8') as stream:return [json.loads(line) for line in stream]
def group(task,language,digest):return '|'.join((task,language,digest))
def preferred(low,high,left,right):return left if low>0 else right if high<0 else ''

def verify(directory,native,evidence,retained):
 directory,native,evidence,retained=map(Path,(directory,native,evidence,retained))
 reg=json.loads((directory/'registration.json').read_text());summary=json.loads((directory/'summary.json').read_text())
 need(summary['status']=='PASS' and reg['task_program_executions']==0,'incomplete/nonreplay result')
 for path,digest in {**reg['input_sha256'],**reg['producer_sha256']}.items():need(sha((HERE/path).read_bytes())==digest,'input/producer bytes differ '+path)
 for path,digest in summary['outputs_sha256'].items():need(sha((directory/path).read_bytes())==digest,'output bytes differ '+path)
 sources={group(r['task'],r['language'],r['source_sha256']):r for r in jsonlines(evidence/'sources.jsonl.gz')}
 need(len(sources)==44149,'source inventory coverage')
 truth={group(r['task'],'javascript',r['source_sha256']):int(r['validity']=='supported') for r in table(native/'source_labels.csv')}
 proof_records=jsonlines(directory/'python-proof-rechecks.jsonl.gz');seen=set()
 for record in proof_records:
  key=group(record['task'],'python',record['source_sha256']);need(key not in seen and key in sources,'proof source inventory');seen.add(key)
  source=sources[key]['source'];need(sha(source)==record['source_sha256'],'proof source digest')
  admitted=admit_python(record['task'],source)
  need(admitted['admitted'] and record['validity']=='supported' and record['prefix_statements']==admitted['erased_prefix_statements'],'repeated AST admission differs')
  need(record['reference_sha256']==sources[key]['receiver_reference_sha256'],'proof reference differs')
  need(record['observation_rule']==reg['observation_rule'] and record['initialization_rule']==reg['initialization_rule'],'proof application contract differs')
  truth[key]=1
 need(len(seen)==22054 and set(truth)==set(sources),'complete truth support differs')
 seed={group(r['task'],'javascript',r['source_sha256']) for r in table(retained/'raw/semantic_audit.csv') if r['language']=='javascript'}
 known={key:v for key,v in truth.items() if '|python|' in key or key in seed};unknown={key:v for key,v in truth.items() if key not in known}
 with gzip.open(native/'completed_rows.csv.gz','rt',encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
 first={};family_counts=Counter();config_seen=set();coef={key:defaultdict(Fraction) for key in ((m,l,r) for m in WEIGHTS for l,r in PAIRS)}
 for index,row in enumerate(rows):
  key=group(row['task'],row['language'],row['source_sha256']);first.setdefault(key,index)
  config=tuple(row[f] for f in ('task','language','scheme','attack','severity','payload_index'));need(config not in config_seen,'duplicate configuration');config_seen.add(config)
  family_counts[(row['language'],row['scheme'],row['attack'])]+=1
  need(key in truth and int(row['validity'])==truth[key],'source truth differs')
  for mixture,weights in WEIGHTS.items():
   if row['attack'] not in weights:continue
   weight=weights[row['attack']]*int(row['detected'])/4224
   for left,right in PAIRS:
    sign=int(row['scheme']==left)-int(row['scheme']==right)
    if sign:coef[(mixture,left,right)][key]+=sign*weight
 need(len(config_seen)==76032 and len(family_counts)==36 and set(family_counts.values())=={2112},'factorial denominators differ')
 domains={task:len(domain_cases(task)) for task in TASK_BY_NAME}
 costs={key:domains[key.split('|')[0]] for key in truth}
 old={(r['mixture'],r['left'],r['right']):r for r in table(evidence/'pairwise_source_bounds.csv') if r['language']=='combined'}
 initial={};integer_coef={};orders={};true_gaps={};expected_summaries={};checkpoint_values={}
 for contrast,weights_by_source in coef.items():
  mixture,left,right=contrast
  denominator=4224*lcm(*(v.denominator for v in WEIGHTS[mixture].values()))
  c={key:int(value*denominator) for key,value in weights_by_source.items()}
  need(all(Fraction(c[key],denominator)==value for key,value in weights_by_source.items()),'noninteger coefficient scaling')
  k=sum(c.get(key,0)*value for key,value in known.items());u={key:c.get(key,0) for key in unknown if c.get(key,0)}
  low=k+sum(value for value in u.values() if value<0);high=k+sum(value for value in u.values() if value>0)
  initial[contrast]=(denominator,k,low,high);integer_coef[contrast]=u
  true_gaps[contrast]=sum(c.get(key,0)*value for key,value in truth.items())
  need(Fraction(low,denominator)==Fraction(old[contrast]['lower_exact']) and Fraction(high,denominator)==Fraction(old[contrast]['upper_exact']),'fresh classification changed historical interval')
  priority=sorted(u,key=lambda key:(-abs(u[key]),key));configuration=sorted(u,key=lambda key:(first[key],key))
  orders[contrast+('largest-coefficient','')]=priority;orders[contrast+('configuration-first','')]=configuration
  for seed_number in range(16):orders[contrast+('sha-random',str(seed_number))]=sorted(u,key=lambda key:(sha(f'markvalidity-audit-order-v1|{seed_number}|{key}'),key))
 with gzip.open(directory/'coefficients.csv.gz','rt',encoding='utf-8',newline='') as stream:coefficients=list(csv.DictReader(stream))
 coefficient_seen=set()
 for row in coefficients:
  contrast=row['mixture'],row['left'],row['right'];key=row['source_key'];combined=contrast+(key,)
  need(combined not in coefficient_seen,'duplicate exported source coefficient');coefficient_seen.add(combined)
  need(int(row['coefficient_numerator'])==integer_coef[contrast][key] and int(row['denominator'])==initial[contrast][0],'source coefficient differs')
  need(int(row['domain_input_calls'])==costs[key] and int(row['first_configuration'])==first[key],'cost or source order differs')
 need(coefficient_seen=={contrast+(key,) for contrast,u in integer_coef.items() for key in u},'source coefficient support differs')
 previous=None;trace_rows=0;closed_form_checks=0;width_comparisons=0
 def close_schedule():
  if previous is None:return
  contrast=previous[:3];denominator,k,_,_=initial[contrast]
  need(position==len(order) and not remaining,'incomplete disclosure schedule')
  need(lower==upper==true_gaps[contrast],'terminal gap differs')
  expected_summaries[previous]=dict(eligible_unknown_sources=len(order),first_certified_query=first_certificate,
   first_certified_additional_input_calls=first_cost,certified_preference=certified,
   final_gap_exact=str(Fraction(true_gaps[contrast],denominator)),all_eligible_input_calls=calls,
   order_sha256=sha('\n'.join(order)+'\n'))
 with gzip.open(directory/'traces.csv.gz','rt',encoding='utf-8',newline='') as stream:
  for row in csv.DictReader(stream):
   schedule=row['mixture'],row['left'],row['right'],row['policy'],row['seed'];contrast=schedule[:3]
   need(schedule in orders,'unregistered schedule');query=int(row['query']);trace_rows+=1
   if schedule!=previous:
    close_schedule();need(schedule not in expected_summaries,'noncontiguous or repeated schedule');need(query==0,'missing initial interval')
    previous=schedule;denominator,k,lower,upper=initial[contrast];order=orders[schedule];remaining=dict(integer_coef[contrast]);position=0;calls=0;known_value=k
    certified=preferred(lower,upper,contrast[1],contrast[2]);first_certificate=0 if certified else None;first_cost=0 if certified else None
    best_width=upper-lower;priority=orders[contrast+('largest-coefficient','')];priority_removed=0
    need(row['task']==row['source_sha256']==row['revealed_validity']=='','initial interval must reveal no label')
   else:
    need(query==position+1,'query sequence gap');key=group(row['task'],'javascript',row['source_sha256'])
    need(query<=len(order) and key==order[query-1] and key in remaining,'order/duplicate query mismatch')
    c=remaining.pop(key);value=truth[key]
    need(int(row['coefficient_numerator'])==c and int(row['revealed_validity'])==value,'query coefficient or disclosed truth differs')
    lower+=c*value-(c if c<0 else 0);upper+=c*value-(c if c>0 else 0);known_value+=c*value
    calls+=costs[key];position=query;priority_removed+=abs(integer_coef[contrast][priority[query-1]])
    preference_now=preferred(lower,upper,contrast[1],contrast[2])
    if first_certificate is None and preference_now:first_certificate=query;first_cost=calls;certified=preference_now
    need(upper-lower>=best_width-priority_removed,'an order beats the minimum-width lower bound');width_comparisons+=1
    if schedule[3]=='largest-coefficient':need(upper-lower==best_width-priority_removed,'priority does not attain minimum width')
    if query%128==0 or query in (first_certificate,len(order)):
     independent_lower=known_value+sum(v for v in remaining.values() if v<0)
     independent_upper=known_value+sum(v for v in remaining.values() if v>0)
     need((lower,upper)==(independent_lower,independent_upper),'closed-form bound reconstruction differs');closed_form_checks+=1
    if query in (1,2,5,10,20,50,100,200,500,1000,2000,3000,4000) or query in (first_certificate,len(order)):
     checkpoint_values[schedule+(str(query),)]=(lower,upper,calls,preferred(lower,upper,contrast[1],contrast[2]))
   need(int(row['denominator'])==denominator and int(row['lower_numerator'])==lower and int(row['upper_numerator'])==upper,'trace interval differs')
   need(int(row['width_numerator'])==upper-lower and int(row['additional_input_calls'])==calls,'trace width/cost differs')
   need(row['preferred']==preferred(lower,upper,contrast[1],contrast[2]),'trace certification differs')
 close_schedule();need(set(expected_summaries)==set(orders),'schedule coverage differs')
 summaries=table(directory/'schedule_summary.csv');seen=set()
 for row in summaries:
  key=row['mixture'],row['left'],row['right'],row['policy'],row['seed'];need(key not in seen and key in expected_summaries,'summary key coverage');seen.add(key)
  expected=expected_summaries[key]
  for field,value in expected.items():need(row[field]==('' if value is None else str(value)),'summary differs '+field)
  d,k,lo,hi=initial[key[:3]];need(Fraction(row['initial_lower_exact'])==Fraction(lo,d) and Fraction(row['initial_upper_exact'])==Fraction(hi,d),'summary initial endpoints differ')
 need(seen==set(orders),'missing schedule summary')
 checkpoints=table(directory/'checkpoints.csv');seen=set()
 for row in checkpoints:
  key=row['mixture'],row['left'],row['right'],row['policy'],row['seed'],row['queries'];need(key in checkpoint_values and key not in seen,'checkpoint coverage');seen.add(key)
  low,high,cost,pref=checkpoint_values[key];d=initial[key[:3]][0]
  need(Fraction(row['lower_exact'])==Fraction(low,d) and Fraction(row['upper_exact'])==Fraction(high,d),'checkpoint endpoints differ')
  need(Fraction(row['remaining_width_exact'])==Fraction(high-low,d) and int(row['additional_input_calls'])==cost and row['preferred']==pref,'checkpoint width/cost/preference differs')
 need(seen==set(checkpoint_values),'missing checkpoints')
 randoms=table(directory/'random_order_summary.csv');need(len(randoms)==9,'random summary coverage')
 for row in randoms:
  contrast=row['mixture'],row['left'],row['right'];qs=[expected_summaries[contrast+('sha-random',str(i))]['first_certified_query'] for i in range(16)]
  calls=[expected_summaries[contrast+('sha-random',str(i))]['first_certified_additional_input_calls'] for i in range(16)]
  for field,value in dict(queries_min=min(qs),queries_median=statistics.median(qs),queries_max=max(qs),
   input_calls_min=min(calls),input_calls_median=statistics.median(calls),input_calls_max=max(calls)).items():need(float(row[field])==value,'random descriptive summary differs')
 need(summary['contrasts']==9 and summary['schedules']==len(orders)==162 and summary['javascript_fresh_seed_sources']==len(seed),'top-level coverage differs')
 need(summary['python_source_proofs_rechecked']==len(proof_records) and summary['known_source_groups']==len(known) and summary['unknown_javascript_source_groups']==len(unknown),'top-level source counts differ')
 seed_configurations=sum(group(r['task'],r['language'],r['source_sha256']) in seed for r in rows)
 need(summary['javascript_fresh_seed_configuration_rows']==seed_configurations and summary['seed_unique_javascript_input_calls']==sum(costs[key] for key in seed),'seed coverage/cost summary differs')
 need(summary['fresh_seed_policy_matches_earlier_endpoints'] is True and summary['random_orders_per_contrast']==16,'policy bridge/random design summary differs')
 nested=summary['balanced_lexical_structural'];need(len(nested)==18,'nested balanced schedule count')
 for row in nested:
  key=row['mixture'],row['left'],row['right'],row['policy'],str(row['seed'])
  need(key[:3]==('balanced','lexical','structural') and key in expected_summaries,'nested schedule key differs')
  for field,value in expected_summaries[key].items():need(row[field]==value,'nested schedule field differs '+field)
 target_random=next(r for r in randoms if (r['mixture'],r['left'],r['right'])==('balanced','lexical','structural'))
 for field,value in summary['balanced_random_order_summary'].items():
  need(str(value)==target_random[field] or (field not in ('mixture','left','right') and float(value)==float(target_random[field])),'nested random summary differs')
 return dict(status='PASS',source_group_proofs_rechecked=22054,fresh_javascript_seed_sources=len(seed),unknown_javascript_source_groups=len(unknown),
  contrasts=9,schedules=len(orders),trace_rows_reconstructed=trace_rows,per_query_width_comparisons=width_comparisons,
  independent_closed_form_endpoint_checks=closed_form_checks,task_program_executions=0,
  scope='Source coefficients independently rebuilt from configuration-level detection; exact v2 label linkage, repeated AST admission, all disclosure orders, every bound/cost/certificate transition and descriptive seed summaries checked. No claim of execution attestation or input-cost optimality.')

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--out',type=Path,default=HERE/'results/revision-audit-budget')
 parser.add_argument('--native',type=Path,default=HERE/'results/revision-native-completion')
 parser.add_argument('--evidence',type=Path,default=HERE/'results/revision-source-joint')
 parser.add_argument('--retained',type=Path,default=HERE/'results/revision-reproduction')
 args=parser.parse_args();print(json.dumps(verify(args.out,args.native,args.evidence,args.retained),indent=2,sort_keys=True))
