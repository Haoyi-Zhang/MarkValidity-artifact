"""Receive complete native JavaScript evidence without importing its producer.

The verifier reopens every stored typed observation vector, compares its values
with the reference, checks source/domain/runtime linkage and exact source and
configuration coverage, and independently recomputes all weighted results.
It does not execute task programs and is not execution attestation. The native
producer is trusted to have performed the calls recorded in its raw stream.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from fractions import Fraction
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'src'))
from covewm.tasks import TASK_BY_NAME,domain_cases

OBSERVATION_RULE='covewm-tagged-return-or-exception-type-and-message-canonical-json-v2'
INITIALIZATION_RULE='covewm-fresh-module-instance-per-input-v1'
SCHEMES=('lexical','structural','hybrid')
ATTACKS=('format','rename','normalize','random_flip','strip','mixed')
WEIGHTS={
    'balanced': {a:Fraction(1,5) for a in ATTACKS if a!='format'},
    'rename-heavy': {'rename':Fraction(27,50),'random_flip':Fraction(6,25),'strip':Fraction(11,50)},
    'structure-heavy': {'normalize':Fraction(27,50),'random_flip':Fraction(6,25),'strip':Fraction(11,50)},
}

def need(condition,message):
    if not condition:raise ValueError(message)

def sha(data):
    return hashlib.sha256(data.encode('utf-8') if isinstance(data,str) else data).hexdigest()

def canon(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def csv_rows(path):
    with Path(path).open(encoding='utf-8',newline='') as handle:return list(csv.DictReader(handle))

def compressed_json_rows(path):
    with gzip.open(path,'rt',encoding='utf-8') as handle:return [json.loads(line) for line in handle]

def validate_json_value(value):
    if value is None or type(value) in (str,bool,int):return
    if type(value) is float:
        need(math.isfinite(value),'nonfinite return value');return
    if type(value) is list:
        for entry in value:validate_json_value(entry)
        return
    if type(value) is dict:
        need(all(type(key) is str for key in value),'nonstring key')
        for entry in value.values():validate_json_value(entry)
        return
    raise ValueError('non-JSON return value')

def validate_observation(serialized):
    need(type(serialized) is str,'serialized observation required')
    observation=json.loads(serialized)
    need(type(observation) is dict,'observation envelope required')
    if observation.get('kind')=='return':
        need(set(observation)=={'kind','value'},'invalid return envelope')
        validate_json_value(observation['value'])
    elif observation.get('kind')=='exception':
        need(set(observation)=={'kind','type','message'},'invalid exception envelope')
        need(type(observation['type']) is str and type(observation['message']) is str,'invalid exception description')
    else:raise ValueError('unknown observation kind')
    need(canon(observation)==serialized,'noncanonical observation')
    return observation

def vector_digest(vector):
    return sha(''.join(value+'\n' for value in vector))

def legacy_projection_digest(vector):
    values=[]
    for serialized in vector:
        value=json.loads(serialized)
        legacy=value['value'] if value['kind']=='return' else {'exception':value['type'],'message':value['message']}
        values.append(canon(legacy))
    return vector_digest(values)

def check_program(record,vector,reference,cases,cache=None):
    """Reconstruct semantic status from the entire received vectors."""
    n=len(cases)
    need(len(vector)==len(reference)==n,'incomplete observation vector')
    need(record['completed_cases']==record['factory_initializations']==n,'incomplete/fresh-input call count')
    need(record['parse_ok'] is True,'program did not parse')
    cache_key=(id(vector),id(reference))
    if cache is not None and cache_key in cache:
        observed_hash,legacy_hash,mismatches,kinds=cache[cache_key]
    else:
        observed_hash=vector_digest(vector);legacy_hash=legacy_projection_digest(vector)
        mismatches=[i for i,(a,b) in enumerate(zip(vector,reference)) if a!=b]
        kinds=Counter(json.loads(value)['kind'] for value in vector)
        if cache is not None:cache[cache_key]=(observed_hash,legacy_hash,mismatches,kinds)
    need(record['observation_hash']==observed_hash,'program output vector mismatch')
    need(record['legacy_observation_hash']==legacy_hash,'legacy projection mismatch')
    first=mismatches[0] if mismatches else None
    need(record['mismatch_count']==len(mismatches),'mismatch count differs from actual observations')
    need(record['first_mismatch_index']==first,'first mismatch index differs')
    need(record['first_mismatch_input']==(cases[first] if first is not None else None),'witness input differs')
    need(record['first_reference_observation']==(reference[first] if first is not None else None),'reference witness differs')
    need(record['first_candidate_observation']==(vector[first] if first is not None else None),'candidate witness differs')
    need(record['validity']==('contradicted' if mismatches else 'supported'),'semantic status differs from observations')
    need(record['return_observations']==kinds['return'] and record['exception_observations']==kinds['exception'],'observation-kind counts differ')
    return not mismatches

def verify(out,evidence,retained):
    out,evidence,retained=map(Path,(out,evidence,retained))
    summary=json.loads((out/'summary.json').read_text());registration=json.loads((out/'registration.json').read_text())
    need(summary['status']=='PASS','native run did not finish')
    need(registration['observation_rule']==OBSERVATION_RULE and registration['initialization_rule']==INITIALIZATION_RULE,'contract mismatch')
    for name,digest in registration['input_sha256'].items():
        need(sha((HERE/name).read_bytes())==digest,'changed registered input '+name)
    for name,digest in registration['producer_sha256'].items():
        need(sha((HERE/name).read_bytes())==digest,'changed native producer '+name)
    for name,digest in summary['outputs_sha256'].items():
        need(not Path(name).is_absolute() and '..' not in Path(name).parts,'unsafe output locator')
        need(sha((out/name).read_bytes())==digest,'changed native output '+name)
    tasks=registration['tasks'];need(set(tasks).issubset(TASK_BY_NAME) and len(set(tasks))==len(tasks),'task coverage')
    need(registration['complete_frozen_design']==(set(tasks)==set(TASK_BY_NAME)),'complete-study flag mismatch')
    with gzip.open(out/'reference-domains.json.gz','rt',encoding='utf-8') as handle:domains=json.load(handle)
    need(set(domains)==set(tasks),'reference/domain snapshot coverage')
    source_inventory={}
    for row in compressed_json_rows(evidence/'sources.jsonl.gz'):
        if row['language']=='javascript' and row['task'] in tasks:
            need(sha(row['source'])==row['source_sha256'],'saved source digest differs')
            key=row['task'],row['source_sha256'];need(key not in source_inventory,'duplicate stored source')
            source_inventory[key]=row['source']
    labels={};all_programs={};nominal={};reference_records={};total_vectors=0;observations_received=0
    finishes=[];execution_receipts={r['task']:r for r in json.loads((out/'execution.json').read_text())}
    need(set(execution_receipts)==set(tasks),'missing task execution receipt')
    for task in tasks:
        frozen=TASK_BY_NAME[task];d=domains[task]
        reference=frozen.javascript_reference.replace('__CARRIERS__','').rstrip()+'\n'
        cases=domain_cases(task)
        need(d['reference']==reference and d['reference_sha256']==sha(reference),'reference snapshot differs')
        need(d['cases']==cases and d['domain_sha256']==sha(json.dumps(cases,ensure_ascii=False,separators=(',',':'))),'input domain snapshot differs')
        need(d['mutants']==list(frozen.javascript_mutants),'owned mutant snapshot differs')
        need(d['nominal_cases']==[list(args) for args in frozen.nominal_cases],'nominal input snapshot differs')
        stream=compressed_json_rows(out/'raw'/f'{task}.jsonl.gz')
        need(stream[0]['type']=='start' and stream[-1]['type']=='finish','truncated native task stream')
        start,finish=stream[0],stream[-1];finishes.append(finish)
        need(start==execution_receipts[task]['worker_start'] and finish==execution_receipts[task]['worker_finish'],'execution receipt differs')
        need(start['task']==task and start['reference_sha256']==sha(reference) and start['domain_sha256']==d['domain_sha256'],'task/contract binding differs')
        need(start['node_version']==registration['runtime']['node'] and start['v8_version']==registration['runtime']['v8'],'runtime mismatch')
        need(start['observation_rule']==OBSERVATION_RULE and start['initialization_rule']==INITIALIZATION_RULE,'worker observation contract mismatch')
        expected_programs=[dict(id='reference',role='reference',source=reference,source_sha256=sha(reference))]
        expected_programs.extend(dict(id=f'mutant-{i}',role='mutant',source=s,source_sha256=sha(s)) for i,s in enumerate(frozen.javascript_mutants,1))
        expected_programs.extend(dict(id=h,role='candidate',source=s,source_sha256=h) for (t,h),s in sorted(source_inventory.items()) if t==task)
        spec=dict(task=task,cases=cases,domain_sha256=d['domain_sha256'],nominal_cases=d['nominal_cases'],reference_sha256=sha(reference),
            observation_rule=OBSERVATION_RULE,initialization_rule=INITIALIZATION_RULE,programs=expected_programs)
        need(sha(canon(spec))==start['spec_sha256']==execution_receipts[task]['spec_sha256'],'exact executed specification mismatch')
        expected={(p['role'],p['id']):p for p in expected_programs};received={};vectors={};ref_vector=None;ref_nominal=None;vector_checks={}
        for record in stream[1:-1]:
            kind=record['type'];need(record['task']==task,'cross-task record')
            if kind=='observation_vector':
                h=record['observation_hash'];vector=record['observations']
                need(h not in vectors and len(vector)==len(cases),'duplicate/incomplete observed vector')
                for value in vector:validate_observation(value)
                need(vector_digest(vector)==h,'observed vector digest differs')
                vectors[h]=vector;total_vectors+=1;observations_received+=len(vector)
            elif kind=='program':
                key=record['role'],record['id'];need(key in expected and key not in received,'duplicate/unregistered native program')
                need(record['source_sha256']==expected[key]['source_sha256'],'native program source differs')
                need(record['reference_sha256']==sha(reference) and record['domain_sha256']==d['domain_sha256'],'native program contract differs')
                vector=vectors[record['observation_hash']]
                if key[0]=='reference':ref_vector=vector;reference_records[task]=record
                need(ref_vector is not None,'reference must precede candidates')
                valid=check_program(record,vector,ref_vector,cases,vector_checks)
                received[key]=record;all_programs[(task,*key)]=record
                if key[0]=='candidate':labels[(task,record['source_sha256'])]=int(valid)
            elif kind=='nominal_program':
                key=record['role'],record['id'];need(key in received and key[0]!='candidate','unregistered nominal program')
                need((task,*key) not in nominal and record['source_sha256']==expected[key]['source_sha256'],'duplicate/stale nominal source')
                vector=record['observations'];need(len(vector)==record['completed_cases']==len(d['nominal_cases']),'nominal coverage mismatch')
                for value in vector:validate_observation(value)
                need(vector_digest(vector)==record['observation_hash'],'nominal observation hash differs')
                if key[0]=='reference':ref_nominal=vector
                need(ref_nominal is not None,'nominal reference order')
                mismatches=[i for i,(x,y) in enumerate(zip(vector,ref_nominal)) if x!=y]
                need(record['mismatch_count']==len(mismatches) and record['first_mismatch_index']==(mismatches[0] if mismatches else None),'nominal mismatch reconstruction')
                need(record['nominal_equal']==(not mismatches),'nominal equality reconstruction')
                nominal[(task,*key)]=record
            else:raise ValueError('unexpected native record kind')
        need(set(received)==set(expected),'native program coverage incomplete')
        n_candidates=sum(key[0]=='candidate' for key in received)
        need(start['programs']==len(expected) and finish['candidate_sources_executed']==n_candidates and
            finish['mutant_sources_executed']==3 and finish['reference_sources_executed']==1,'native role counts differ')
        need(finish['total_input_calls']==len(expected)*len(cases),'native call total differs')
        need(finish['nominal_input_calls']==4*len(d['nominal_cases']),'native nominal call total differs')
        need(finish['unique_observation_vectors']==len(vectors),'vector inventory differs')
    need(set(labels)==set(source_inventory),'source-label coverage differs')
    need(len(labels)==summary['javascript_candidate_sources_executed']==registration['candidate_sources'],'source count differs')
    actual_calls=sum(len(domains[t]['cases']) for t,h in labels)
    need(actual_calls==summary['javascript_candidate_input_calls']==registration['planned_candidate_input_calls'],'candidate-call count differs')
    label_table=csv_rows(out/'source_labels.csv');need(len(label_table)==len(labels),'label table row count')
    seen=set()
    for row in label_table:
        key=row['task'],row['source_sha256'];need(key in labels and key not in seen,'label table source coverage');seen.add(key)
        original=all_programs[(key[0],'candidate',key[1])]
        for field,value in row.items():
            expected=original[field]
            need(value==('' if expected is None else str(expected)),'label table differs '+field)
    controls=csv_rows(out/'mutant_controls.csv');need(len(controls)==3*len(tasks),'mutant controls coverage')
    seen=set()
    for row in controls:
        key=row['task'],'mutant',row['id'];need(key in all_programs and key not in seen,'mutant control identity');seen.add(key)
        original=all_programs[key];nr=nominal[key]
        for field in ('source_sha256','validity','completed_cases','observation_hash','legacy_observation_hash','mismatch_count','first_mismatch_index'):
            need(row[field]==('' if original[field] is None else str(original[field])),'mutant control field '+field)
        need(row['nominal_equal']==str(nr['nominal_equal']) and row['nominal_observation_hash']==nr['observation_hash'],'mutant nominal linkage')
    old_rows=[]
    with gzip.open(evidence/'rows.csv.gz','rt',encoding='utf-8',newline='') as handle:
        old_rows=[r for r in csv.DictReader(handle) if r['task'] in tasks]
    with gzip.open(out/'completed_rows.csv.gz','rt',encoding='utf-8',newline='') as handle:new_rows=list(csv.DictReader(handle))
    fields=('task','language','scheme','attack','severity','payload_index')
    key=lambda r:tuple(r[f] for f in fields)
    old_map={key(r):r for r in old_rows};new_map={key(r):r for r in new_rows}
    need(len(old_rows)==len(old_map)==len(new_rows)==len(new_map) and set(old_map)==set(new_map),'configuration support differs')
    expected_grid=set(itertools.product(tasks,('python','javascript'),SCHEMES,ATTACKS,(f'{i/10:.1f}' for i in range(11)),map(str,range(16))))
    need(set(new_map)==expected_grid,'frozen factorial grid differs')
    counts=defaultdict(lambda:[0,0,0,0]);unknown_completed=0
    for k,row in new_map.items():
        old=old_map[k];task,language,scheme,attack,*_=k
        need(row['source_sha256']==old['source_sha256'] and row['legacy_semantic_contract_id']==old['semantic_contract_id'],'configuration source/contract linkage differs')
        need(row['prior_validity_status']==old['validity_status'] and row['prior_evidence_kind']==old['evidence_kind'],'earlier policy status differs')
        if language=='javascript':
            v=labels[(task,row['source_sha256'])];native=all_programs[(task,'candidate',row['source_sha256'])]
            need(row['observation_hash']==native['observation_hash'] and row['completed_behavioral_basis']=='fresh-input-complete-native-execution','native label linkage differs')
            unknown_completed+=old['validity_status']=='unknown'
        else:
            need(old['validity_status']=='valid' and row['observation_hash']=='' and row['completed_behavioral_basis']=='retained-restricted-erasure-proof','retained Python proof linkage differs')
            v=1
        d=int(old['detected']);need((int(row['validity']),int(row['detected']),int(row['joint']))==(v,d,v*d),'configuration joint target differs')
        for i,value in enumerate((1,v,d,v*d)):counts[(language,scheme,attack)][i]+=value
    family_rows=csv_rows(out/'family_scores.csv');need(len(family_rows)==36,'family table coverage')
    seen=set()
    for row in family_rows:
        k=row['language'],row['scheme'],row['attack'];need(k in counts and k not in seen,'family key coverage');seen.add(k)
        n,v,d,j=counts[k]
        need(tuple(int(row[f]) for f in ('configurations','validity_supported','detected','joint_count'))==(n,v,d,j),'family counts differ')
        need(Fraction(row['joint_exact'])==Fraction(j,n),'family exact score differs')
    scores={}
    for lang in ('python','javascript','combined'):
        for mixture,weights in WEIGHTS.items():
            for scheme in SCHEMES:
                langs=('python','javascript') if lang=='combined' else (lang,)
                score=sum((weight*Fraction(counts[(l,scheme,a)][3],counts[(l,scheme,a)][0])/len(langs)
                    for l in langs for a,weight in weights.items()),Fraction())
                scores[(lang,mixture,scheme)]=score
    old_scores={(r['language'],r['mixture'],r['scheme']):r for r in csv_rows(evidence/'mixture_scores.csv')}
    score_rows=csv_rows(out/'mixture_scores.csv');need(len(score_rows)==27,'mixture table coverage');seen=set()
    for row in score_rows:
        k=row['language'],row['mixture'],row['scheme'];need(k in scores and k not in seen,'mixture key coverage');seen.add(k)
        need(Fraction(row['joint_exact'])==scores[k],'completed weighted score differs')
        if registration['complete_frozen_design']:
            old=old_scores[k]
            need(row['earlier_lower_exact']==old['joint_lower_exact'] and row['earlier_upper_exact']==old['joint_upper_exact'],'earlier mixture bounds differ')
            covered=Fraction(old['joint_lower_exact'])<=scores[k]<=Fraction(old['joint_upper_exact'])
            need(row['contained_in_earlier_interval']==str(covered) and covered,'completion outside earlier mixture interval')
    old_gaps={(r['language'],r['mixture'],r['left'],r['right']):r for r in csv_rows(evidence/'pairwise_source_bounds.csv')}
    gap_rows=csv_rows(out/'pairwise_gaps.csv');need(len(gap_rows)==27,'gap table coverage');seen=set()
    for row in gap_rows:
        k=row['language'],row['mixture'],row['left'],row['right'];need(k not in seen and k in old_gaps,'gap key coverage');seen.add(k)
        a,b=scores[k[:2]+(k[2],)],scores[k[:2]+(k[3],)];gap=a-b
        need(Fraction(row['gap_exact'])==gap,'completed gap differs')
        need(row['preferred']==(k[2] if gap>0 else k[3] if gap<0 else ''),'completed pair ordering differs')
        if registration['complete_frozen_design']:
            old=old_gaps[k];need(row['earlier_lower_exact']==old['lower_exact'] and row['earlier_upper_exact']==old['upper_exact'],'earlier gap bounds differ')
            covered=Fraction(old['lower_exact'])<=gap<=Fraction(old['upper_exact'])
            need(row['contained_in_earlier_interval']==str(covered) and covered,'completion outside earlier gap interval')
    old_audits=[r for r in csv_rows(retained/'raw/semantic_audit.csv') if r['language']=='javascript' and r['task'] in tasks]
    links=csv_rows(out/'previous_execution_links.csv');need(len(links)==len(old_audits),'historical linkage coverage')
    for row,old in zip(links,old_audits):
        for field in ('task','scheme','condition','source_sha256'):need(row[field]==old[field],'historical source link mismatch')
        native=all_programs[(old['task'],'candidate',old['source_sha256'])]
        need(row['fresh_input_validity']==native['validity'] and row['fresh_observation_hash']==native['observation_hash'],'fresh audit label differs')
        need(row['fresh_legacy_projection_hash']==native['legacy_observation_hash'] and row['same_domain_case_count']=='True','fresh audit scope differs')
    parity={r['task']:r for r in csv_rows(retained/'raw/cross_language_parity.csv')}
    for task,record in reference_records.items():
        need(record['legacy_observation_hash']==parity[task]['javascript_hash'],'fresh reference differs from legacy result projection')
    n=sum(x[0] for x in counts.values());joint=sum(x[3] for x in counts.values())
    need(summary['all_source_configurations']==n and summary['joint_count']==joint and Fraction(summary['joint_exact'])==Fraction(joint,n),'global summary target differs')
    need(summary['prior_unknown_javascript_configurations_completed']==unknown_completed,'unknown-label completion count differs')
    need(summary['javascript_mutant_nominal_survivors']==sum(r['nominal_equal']=='True' for r in controls),'nominal survivor count differs')
    candidate_counts=Counter('supported' if value else 'contradicted' for value in labels.values())
    mutant_counts=Counter(r['validity'] for r in controls)
    need(summary['candidate_statuses']==dict(candidate_counts) and summary['mutant_control_statuses']==dict(mutant_counts),'top-level semantic status counts differ')
    need(summary['javascript_reference_sources_executed']==len(reference_records) and summary['javascript_reference_input_calls']==sum(len(domains[t]['cases']) for t in tasks),'reference execution counts differ')
    need(summary['javascript_mutant_control_sources_executed']==len(controls) and summary['javascript_mutant_control_input_calls']==3*sum(len(domains[t]['cases']) for t in tasks),'mutant execution counts differ')
    need(summary['nominal_input_calls']==sum(r['completed_cases'] for r in nominal.values()),'nominal execution total differs')
    need(summary['javascript_configurations']==sum(r['language']=='javascript' for r in new_rows),'JavaScript configuration total differs')
    need(summary['previous_executed_javascript_rows_linked']==len(links),'historical link summary differs')
    need(summary['complete_frozen_design']==registration['complete_frozen_design'],'top-level design completeness differs')
    if registration['complete_frozen_design']:
        need(summary['old_mixture_intervals_checked']==27 and summary['old_pairwise_intervals_checked']==27 and summary['completed_scores_contained_in_prior_intervals'] is True,'earlier-interval summary differs')
    nested=summary['combined_mixtures']
    need(len(nested)==9 and {(r['mixture'],r['scheme']) for r in nested}=={(m,s) for m in WEIGHTS for s in SCHEMES},'nested combined-score coverage differs')
    for row in nested:
        need(row['language']=='combined' and Fraction(row['joint_exact'])==scores[('combined',row['mixture'],row['scheme'])],'nested combined score differs')
    need(set(summary['combined_winners'])==set(WEIGHTS),'combined winner coverage differs')
    for mixture,winner in summary['combined_winners'].items():
        need(winner in SCHEMES and all(scores[('combined',mixture,winner)]>scores[('combined',mixture,other)] for other in SCHEMES if other!=winner),'combined strict winner differs')
    report=dict(status='PASS',source_identities_verified=len(labels),source_configurations_verified=n,
        native_candidate_input_calls_recorded=actual_calls,retained_distinct_output_vectors=total_vectors,
        stored_typed_observations_checked=observations_received,mutant_controls_verified=len(controls),
        nominal_survivors=sum(r['nominal_equal']=='True' for r in controls),previous_audit_rows_linked=len(links),
        family_scores_recomputed=36,mixture_scores_recomputed=27,pairwise_gaps_recomputed=27,
        all_prior_intervals_contain_completion=True if registration['complete_frozen_design'] else None,
        task_program_executions_in_this_verifier=0,
        scope='Actual stored typed observation vectors, complete source/input coverage, frozen reference/source/runtime/contract linkage, new labels and exact weighted targets. Native producer is trusted; hashes are identity checks, not execution attestation.')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/revision-native-completion')
    parser.add_argument('--evidence',type=Path,default=HERE/'results/revision-source-joint')
    parser.add_argument('--retained',type=Path,default=HERE/'results/revision-reproduction')
    args=parser.parse_args();print(json.dumps(verify(args.out,args.evidence,args.retained),indent=2,sort_keys=True))
