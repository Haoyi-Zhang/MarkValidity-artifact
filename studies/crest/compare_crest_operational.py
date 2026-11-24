#!/usr/bin/env python3
"""Run existing shared/independent audit policies on two actual CREST catalogues.

All selection and state code is imported unchanged from the main artifact.
Exact source/reference/contract bytes define shared groups. Validity observations
are held in a separate oracle and disclosed only after each public query choice.
An independent mathematical implementation checks every endpoint and selection.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def serial(value):
    if isinstance(value,Fraction):return str(value)
    if isinstance(value,dict):return {k:serial(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [serial(x) for x in value]
    return value


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True)
    p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--ablation',type=Path,required=True)
    p.add_argument('--theory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise ValueError('Output must be new')
    module=args.artifact.resolve()/'external-studies/sew_natural/analysis/natural_analysis.py'
    spec=importlib.util.spec_from_file_location('crest_markvalidity_api',module)
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    sys.path.insert(0,str(args.artifact.resolve()/'external-studies/sew_natural/comparison_costs'))
    from policies import target_bounds,policy_name,IndependentJointWidth,IndependentConditionalWidth
    sys.path.insert(0,str(args.theory.resolve()))
    from operational_state import OperationalPairState
    from adaptive_policy import AdaptiveConditionalPolicy
    from paired_conditional import PairedEnvelope
    from verify_native_conditional import independent_paired
    from summarize_crest_evidence import emission
    import independent as receiver
    inputs={'stock':args.stock.resolve(),'catalogue_ablation':args.ablation.resolve()}
    rows={name:json.loads((root/'results.json').read_text()) for name,root in inputs.items()}
    key=lambda r:(r['dataset'],str(r['task_id']))
    mapped={name:{key(r):r for r in data} for name,data in rows.items()}
    if set(mapped['stock'])!=set(mapped['catalogue_ablation']):raise ValueError('Unequal input populations')
    tasks={name:{key(t):t for t in json.loads((root/'tasks.json').read_text())} for name,root in inputs.items()}
    public,observations=[],{}
    identity_members=defaultdict(list)
    terminal=[]
    for pair in sorted(mapped['stock'],key=lambda k:(k[0]!='HumanEval',tasks['stock'][k]['dataset_index'])):
        for name,root in inputs.items():
            row=mapped[name][pair];task=tasks[name][pair]
            status=emission(row)
            if status=='rejected':
                terminal.append({'catalogue':name,'dataset':pair[0],'task_id':pair[1],
                                 'emission':'completed_precheck_rejection','operational_joint_contribution':0,
                                 'operational_usable_output_contribution':0,
                                 'raw_behavioral_label':None,'raw_detector_decision':None})
                continue
            if status!='emitted':raise ValueError('Unresolved emission must not be turned into terminal zero')
            if not row['qualified_reference'] or type(row['validity']) is not bool:raise ValueError('Unqualified/incomplete behavioral observation')
            contract={k:task[k] for k in ('test','entry_point','test_imports','test_list','context_prompt') if k in task}
            ref_observer=row['reference_native']['observer_source_sha256']
            cand_observer=row['candidate_native']['observer_source_sha256']
            ref_env=row['reference_native']['execution_environment']
            cand_env=row['candidate_native']['execution_environment']
            if ref_observer!=cand_observer or ref_env!=cand_env:raise ValueError('Reference/candidate execution contract differs')
            identity=((root/row['reference_source']).read_bytes(),(root/row['candidate_source']).read_bytes(),
                      json.dumps(contract,sort_keys=True,separators=(',',':')).encode(),
                      cand_observer.encode(),json.dumps(cand_env,sort_keys=True).encode())
            identity_members[identity].append((name,pair,row,task))
    identities={identity:'g%04d'%index for index,identity in enumerate(sorted(identity_members),1)}
    groups={}
    for identity,members in identity_members.items():
        group=identities[identity]
        labels={row['validity'] for name,pair,row,task in members}
        if len(labels)!=1:raise ValueError('Identical source/reference/contract has contradictory received observations')
        observations[group]=labels.pop()
        name,pair,row,task=members[0]
        groups[group]={'source_study':name,'reference_source':row['reference_source'],
                       'candidate_source':row['candidate_source'],'dataset':pair[0],'task_id':pair[1],
                       'contract':{k:task[k] for k in ('test','entry_point','test_imports','test_list','context_prompt') if k in task},
                       'observer_source_sha256':row['candidate_native']['observer_source_sha256'],
                       'execution_environment':row['candidate_native']['execution_environment'],
                       'reference_identical_candidate':identity[0]==identity[1],
                       'rows':len(members),'represented_catalogues':sorted({m[0] for m in members})}
        for name,pair,row,task in members:
            detected={m:row['classifiers'][m]['detected'] for m in ('rf','logreg_l1','logreg_l2')}
            if any(type(v)is not bool for v in detected.values()):raise ValueError('Detector evidence unavailable')
            public.append({'dataset':pair[0],'task_id':pair[1],'catalogue':name,'group':group,'detected':detected})
    args.output.mkdir(parents=True)
    write(args.output/'public-registry.json',{'groups':groups,'rows':public,'terminal_no_output':terminal,
          'group_order':'Lexicographic exact reference/candidate/contract/observer/environment identity, assigned ordinal identifiers before outcome disclosure.',
          'terminal_policy':'Completed no-output attempts remain in the scheduled denominator and have known zero operational yield. They have no behavioral group or invented V/D label.'})
    write(args.output/'oracle-labels.json',observations)
    reports=[];prefix_checks=0;selection_checks=0
    for scope in ('HumanEval','MBPP','pooled'):
        scoped=[r for r in public if scope=='pooled' or r['dataset']==scope]
        full_n=sum(scope=='pooled' or pair[0]==scope for pair in mapped['stock'])
        zeros={name:sum(r['catalogue']==name and (scope=='pooled' or r['dataset']==scope) for r in terminal) for name in inputs}
        for model in ('rf','logreg_l1','logreg_l2'):
            coefficients={name:defaultdict(lambda:[0,0]) for name in inputs}
            for row in scoped:
                value=coefficients[row['catalogue']][row['group']]
                value[0]+=row['detected'][model];value[1]+=1
            left,right=({g:tuple(v) for g,v in coefficients[name].items()} for name in inputs)
            n=sum(v[1] for v in left.values())
            union=set(left)|set(right)
            initial={g:True for g in union if groups[g]['reference_identical_candidate']}
            complete={}
            for name,side in [('stock',left),('catalogue_ablation',right)]:
                joint=sum(a*observations[g] for g,(a,b) in side.items())
                valid=sum(b*observations[g] for g,(a,b) in side.items())
                complete[name]={'J_count':joint,'usable_outputs':valid,'N':full_n,
                                'emitted':sum(b for a,b in side.values()),'terminal_no_output':zeros[name],
                                'J':str(Fraction(joint,full_n)),'C':str(Fraction(joint,valid)) if valid else None}
            for method in ('coupled','independent','adaptive'):
                for target in (('C',) if method=='adaptive' else ('J','C')):
                    state=OperationalPairState(api,left,right,full_n,left_terminal_zero=zeros['stock'],
                                               right_terminal_zero=zeros['catalogue_ablation'])
                    for g,value in sorted(initial.items()):state.reveal(g,value)
                    effective_method='coupled' if method=='adaptive' else method
                    paired_certificate=target=='C' and method!='independent'
                    if paired_certificate:state=PairedEnvelope(state)
                    if method=='independent':
                        policy=IndependentJointWidth(state) if target=='J' else IndependentConditionalWidth(state)
                    else:
                        original_policy=api.AuditPolicy('joint_width_per_suite' if target=='J' else 'conditional_differences_first',state,sorted(union))
                        policy=(AdaptiveConditionalPolicy(state,original_policy,IndependentConditionalWidth(state))
                                if method=='adaptive' else original_policy)
                    admitted=dict(initial);attempted=set(initial)
                    trace=[];first=None
                    while True:
                        if paired_certificate:
                            bounds=state.certify()
                            expected=independent_paired(left,right,admitted,receiver)
                            if serial(bounds)!=serial(expected):
                                raise ValueError('Independent paired-envelope receiver disagrees')
                        else:
                            bounds=target_bounds(api,state,effective_method,target)
                            expected=receiver.bounds(left,right,admitted,effective_method,target)
                            receiver.check_bounds(serial(bounds),expected)
                        prefix_checks+=1
                        step=len(attempted)-len(initial)
                        record={'step':step,'bounds':serial(bounds)}
                        if first is None and bounds['decision'] in api.CERTIFICATES:
                            first={'suite_queries':step,**serial(bounds)}
                        if target=='J':record['full_scheduled_attempt_J_rate_bounds']=[str(Fraction(bounds['lower'],full_n)),str(Fraction(bounds['upper'],full_n))]
                        selector_method=effective_method
                        if method=='adaptive':
                            from conditional_bounds import conditional_bounds
                            exact_scores=[conditional_bounds(model) for model in receiver.compact_pair(left,right,admitted)]
                            singleton=any(s['defined_for_some_completion'] and s['lower']==s['upper'] for s in exact_scores)
                            selector_method='independent' if singleton else 'coupled'
                        selected=policy.next_group(state)
                        expected_next=receiver.next_query(left,right,admitted,attempted,selector_method,target)
                        if selected!=expected_next:raise ValueError('Independent receiver disagrees with public policy')
                        selection_checks+=1
                        if selected is None:
                            trace.append(record);break
                        # Only this line accesses the oracle for a chosen query.
                        label=observations[selected]
                        record.update(selected_group=selected,disclosed_label=label)
                        if method=='adaptive':record['public_selection_branch']=policy.last_branch
                        trace.append(record)
                        state.reveal(selected,label);attempted.add(selected);admitted[selected]=label
                    name=scope.lower()+'-'+model+'-'+method+'-'+target
                    write(args.output/'traces'/(name+'.json'),trace)
                    report={'scope':scope,'classifier':model,'method':method,'target':target,
                            'policy':'point_interval_adaptive' if method=='adaptive' else policy_name(method,target),
                            'certificate':'paired_ratio_envelope_with_separate_fallback' if paired_certificate else
                                          ('separate_conditional_intervals' if target=='C' else 'joint_difference'),
                            'emitted_attempts':{name:sum(b for a,b in side.values()) for name,side in [('stock',left),('catalogue_ablation',right)]},
                            'scheduled_attempts_per_catalogue':full_n,'completed_no_output':zeros,
                            'source_contract_groups':len(union),'shared_groups':len(set(left)&set(right)),
                            'free_reference_identity_groups':len(initial),'first_certificate':first,
                            'complete_operational_scores':complete,'trace':'traces/'+name+'.json'}
                    if method=='adaptive':report['selection_branch_counts']=policy.branch_counts
                    reports.append(report)
                    print(json.dumps({k:report[k] for k in ('scope','classifier','method','target','first_certificate')}),flush=True)
    write(args.output/'summary.json',{'status':'PASS','reports':reports,'independent_prefix_checks':prefix_checks,
          'independent_selection_checks':selection_checks,'candidate_executions_by_this_analysis':0,
          'scope':'Retrospective disclosure of fresh measured emitted-program outcomes over the complete scheduled population. Completed no-output attempts have known zero operational yield and remain in N; they do not create artificial behavioral labels. Shared source groups also bind observer and execution environment.',
          'source':{'state':str(module.relative_to(args.artifact.resolve())),
                    'policies':'external-studies/sew_natural/comparison_costs/policies.py',
                    'receiver':'external-studies/sew_natural/comparison_costs/independent.py',
                    'conditional_certificate':'paired_conditional.py',
                    'conditional_certificate_receiver':'verify_native_conditional.py:independent_paired'}})
    print(json.dumps({'status':'PASS','comparisons':len(reports),'prefix_checks':prefix_checks,'selection_checks':selection_checks}))


if __name__=='__main__':main()
