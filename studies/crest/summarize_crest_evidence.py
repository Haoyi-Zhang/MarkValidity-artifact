#!/usr/bin/env python3
"""Report full denominators, qualification and exact missing-evidence bounds."""
import argparse
import collections
from fractions import Fraction
import json
from pathlib import Path


def fraction(n,d):
    return None if not d else str(Fraction(n,d))


def outcome_bounds(pairs):
    n=len(pairs)
    if not n:return {'attempts':0,'conditional_defined':False}
    counts=collections.Counter((v,d) for v,d in pairs)
    vp=sum(v is True for v,d in pairs);vu=sum(v is None for v,d in pairs)
    dp=sum(d is True for v,d in pairs);du=sum(d is None for v,d in pairs)
    jp=counts[(True,True)]
    ju=sum(v is not False and d is not False and (v is None or d is None) for v,d in pairs)
    p,q,r=counts[(True,True)],counts[(True,False)],counts[(True,None)]
    u1,u0,uu=counts[(None,True)],counts[(None,False)],counts[(None,None)]
    if vp+vu:
        low_den=p+q+r+u0+uu
        high_den=p+q+r+u1+uu
        lower=fraction(p,low_den) if low_den else '1'
        upper=fraction(p+r+u1+uu,high_den) if high_den else '0'
    else:lower=upper=None
    return {'attempts':n,'valid_supported':vp,'valid_contradicted':n-vp-vu,'valid_unknown':vu,
            'detected':dp,'detector_unknown':du,'joint_supported':jp,'joint_unknown':ju,
            'detected_invalid':counts[(False,True)],
            'V_bounds':[fraction(vp,n),fraction(vp+vu,n)],
            'D_bounds':[fraction(dp,n),fraction(dp+du,n)],
            'J_bounds':[fraction(jp,n),fraction(jp+ju,n)],
            'C_observed':fraction(jp,vp),
            'C_observed_denominator':vp,'C_bounds':[lower,upper],
            'C_defined_for_all_completions':vp>0,'C_defined_for_some_completion':vp+vu>0}


def emission(row):
    if row['embedding']['status']=='completed' and 'candidate_source' in row:
        result='emitted'
    elif (row['embedding']['status']=='error' and row['embedding'].get('error','').startswith('Error:') and
          row['embedding']['error'].endswith(' is not a valid Python file.') and 'traceback' not in row['embedding']):
        if 'candidate_source' in row or 'candidate_native' in row:raise ValueError('Rejected emission carries a partial candidate')
        result='rejected'
    else:result='unavailable'
    if 'emission' in row and row['emission']!=result:raise ValueError('Emission field contradicts actual pipeline record')
    return result


def operational_pair(row,model):
    e=emission(row)
    if e=='rejected':return False,False
    if e=='unavailable':return None,None
    return row.get('candidate_native',{}).get('label'),row['classifiers'][model]['detected']


def operational_summary(rows,model):
    result=outcome_bounds([operational_pair(r,model) for r in rows])
    names={'valid_supported':'usable_outputs','valid_contradicted':'known_unsuccessful_outputs',
           'valid_unknown':'output_utility_unknown','detected':'detected_outputs',
           'detector_unknown':'detected_output_unknown','joint_supported':'joint_outputs',
           'joint_unknown':'joint_output_unknown','detected_invalid':'detected_but_suite_failed',
           'V_bounds':'usable_output_rate_bounds','D_bounds':'detected_output_rate_bounds',
           'J_bounds':'joint_output_rate_bounds','C_observed':'conditional_detection_observed',
           'C_observed_denominator':'observed_usable_output_denominator','C_bounds':'conditional_detection_bounds'}
    result={names.get(k,k):v for k,v in result.items()}
    result['estimand']='E times suite-pass, E times detector-positive, and E times suite-pass times detector-positive per scheduled input. Completed E=0 rejections are known zero yields; raw V/D remain N/A.'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study',type=Path,required=True)
    p.add_argument('--label',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    rows=json.loads((args.study/'results.json').read_text())
    tasks=json.loads((args.study/'tasks.json').read_text())
    taskmap={(t['dataset'],str(t['task_id'])):t for t in tasks}
    reports=[]
    for dataset in ('HumanEval','MBPP','pooled'):
        selected=[r for r in rows if dataset=='pooled' or r['dataset']==dataset]
        qualified=[r for r in selected if r['qualified_reference']]
        emitted=[r for r in selected if emission(r)=='emitted']
        qualified_emitted=[r for r in qualified if emission(r)=='emitted']
        identity_groups={}
        for row in emitted:
            task=taskmap[(row['dataset'],str(row['task_id']))]
            contract={k:task[k] for k in ('test','entry_point','test_imports','test_list','context_prompt') if k in task}
            identity=((args.study/row['reference_source']).read_bytes(),
                      (args.study/row['candidate_source']).read_bytes(),
                      json.dumps(contract,sort_keys=True,separators=(',',':')))
            identity_groups.setdefault(identity,[]).append(row['task_id'])
        for model in ('rf','logreg_l1','logreg_l2'):
            pairs=[(r['validity'],r['classifiers'][model]['detected']) for r in qualified_emitted]
            name=lambda v:'passed' if v is True else 'failed' if v is False else 'unavailable'
            after_name=lambda r:'not_emitted' if emission(r)=='rejected' else name(r.get('candidate_native',{}).get('label'))
            transitions=collections.Counter((name(r['reference_native']['label']),after_name(r)) for r in selected)
            operational_transitions=collections.Counter((name(r['reference_native']['label']),name(operational_pair(r,model)[0])) for r in selected)
            input_d=[r.get('reference_detector',{}).get('classifiers',{}).get(model,{}).get('detected') for r in selected]
            observed_input=len(input_d)-input_d.count(None)
            report={'study':args.label,'dataset':dataset,'classifier':model,'scheduled_attempts':len(selected),
                    'input_suite_passed':len(qualified),
                    'input_suite_failed':sum(r['reference_native']['label'] is False for r in selected),
                    'input_suite_unavailable':sum(r['reference_native']['label'] is None for r in selected),
                    'emitted_candidates':len(emitted),
                    'known_emission_rejections':sum(emission(r)=='rejected' for r in selected),
                    'emission_unavailable':sum(emission(r)=='unavailable' for r in selected),
                    'candidate_suite_passed_all_inputs':sum(r.get('candidate_native',{}).get('label') is True for r in selected),
                    'candidate_suite_failed_all_inputs':sum(r.get('candidate_native',{}).get('label') is False for r in selected),
                    'candidate_suite_unavailable_or_not_emitted_all_inputs':sum(r.get('candidate_native',{}).get('label') is None for r in selected),
                    'detector_positive_all_inputs':sum(r['classifiers'][model]['detected'] is True for r in selected),
                    'raw_detector_unavailable_on_emitted':sum(r['classifiers'][model]['detected'] is None for r in emitted),
                    'raw_detector_not_applicable_to_rejected_emission':sum(emission(r)=='rejected' for r in selected),
                    'overall_task_utility':operational_summary(selected,model),
                    'qualified_input_output_retention':operational_summary(qualified,model),
                    'emitted_qualified_preservation':outcome_bounds(pairs),
                    'qualified_inputs':len(qualified),'qualified_emitted_inputs':len(qualified_emitted),
                    'qualified_known_emission_rejections':sum(emission(r)=='rejected' for r in qualified),
                    'before_after_transition_matrix':{
                        before:{after:transitions[(before,after)] for after in ('passed','failed','unavailable','not_emitted')}
                        for before in ('passed','failed','unavailable')},
                    'before_after_operational_transition_matrix':{
                        before:{after:operational_transitions[(before,after)] for after in ('passed','failed','unavailable')}
                        for before in ('passed','failed','unavailable')},
                    'transition_policy':'The native matrix separates no emission from program failure and unavailable execution. The operational matrix counts deterministic no-output as an unsuccessful attempt. Failed inputs that later pass are not counted as watermark-induced failures.',
                    'input_detector_control':{'positive':input_d.count(True),'observed':observed_input,
                                              'unknown':input_d.count(None),'scheduled':len(input_d),
                                              'observed_positive_fraction':fraction(input_d.count(True),observed_input),
                                              'interpretation':'Fixed released operating-point observations; not a calibrated population false-positive rate.'},
                    'source_contract_groups':len(identity_groups),
                    'emitted_rows_sharing_another_source_contract':sum(len(v)-1 for v in identity_groups.values()),
                    'qualified_failure_task_ids':[r['task_id'] for r in qualified if r['validity'] is False]}
            reports.append(report)
    result={'status':'COMPLETE','study':args.label,'rows':len(rows),
            'reporting_policy':'All scheduled inputs retained. Primary overall task utility and qualified-input output retention explicitly include emission E: completed no-output rejection has zero operational yield, while raw behavioral V and detector D are N/A. Program-preservation outcomes are also reported on all emitted candidates from passing originals. True unavailability remains unknown.',
            'reports':reports}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'COMPLETE','study':args.label,'rows':len(rows),'reports':len(reports)}))


if __name__=='__main__':main()
