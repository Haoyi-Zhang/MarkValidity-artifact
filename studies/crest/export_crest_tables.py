#!/usr/bin/env python3
"""Export paper-facing tables from the current received native studies."""
from collections import Counter
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STUDIES = {'reference': ROOT/'validated/reference', 'catalogue': ROOT/'validated/catalogue',
           'gpt4o': ROOT/'isolated/gpt4o', 'qwen': ROOT/'isolated/qwen'}
NAMES = {'reference': 'Canonical, stock', 'catalogue': 'Canonical, catalogue ablation',
         'gpt4o': 'Published GPT-4o', 'qwen': 'Published Qwen'}


def table(headers, rows):
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |']
    lines += ['| ' + ' | '.join(str(value) for value in row) + ' |' for row in rows]
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study-root',type=Path,help='Accepted interface with reference, catalogue, gpt4o, qwen, comparison and causes')
    parser.add_argument('--output',type=Path,default=ROOT)
    args=parser.parse_args()
    studies=({name:args.study_root/name for name in STUDIES} if args.study_root else STUDIES)
    comparison_root=args.study_root/'comparison' if args.study_root else ROOT/'paired-comparison'
    causes_root=args.study_root/'causes' if args.study_root else ROOT/'validated/causes'
    args.output.mkdir(parents=True,exist_ok=True)
    summaries, reports, unavailable, transitions, changes, receiving = {}, [], [], [], {}, []
    for name, folder in studies.items():
        summaries[name] = json.loads((folder/'reporting-summary.json').read_text())
        for verification in ('verification.json','provenance-verification.json'):
            value = json.loads((folder/verification).read_text())
            assert value['status'] == 'PASS'
            receiving.append({'study': name, 'receiver': verification, 'result': value})
        rows = json.loads((folder/'results.json').read_text())
        changes[name] = {'changed': sum(r.get('source_changed') is True for r in rows),
                         'unchanged': sum(r.get('source_changed') is False for r in rows)}
        for row in rows:
            for side in ('reference','candidate'):
                native = row.get(side+'_native')
                if not native or native['label'] is not None:
                    continue
                error = None
                if native['stdout']:
                    try:
                        error = json.loads(native['stdout']).get('error')
                    except (ValueError, AttributeError):
                        error = 'non-JSON native output'
                unavailable.append({'study': name, 'dataset': row['dataset'], 'task_id': row['task_id'],
                                    'side': side, 'interruption': native['interruption'],
                                    'returncode': native['returncode'], 'error': error})
        for report in summaries[name]['reports']:
            if report['classifier'] != 'rf':
                continue
            overall = report['overall_task_utility']
            qualified = report['qualified_input_output_retention']
            emitted = report['emitted_qualified_preservation']
            item = {'study': name, 'dataset': report['dataset'], 'N': report['scheduled_attempts'],
                    'input_pass': report['input_suite_passed'], 'input_fail': report['input_suite_failed'],
                    'input_unknown': report['input_suite_unavailable'], 'emitted': report['emitted_candidates'],
                    'no_output': report['known_emission_rejections'],
                    'output_pass': overall['usable_outputs'],
                    'output_fail': report['candidate_suite_failed_all_inputs'],
                    'output_unknown': overall['output_utility_unknown'],
                    'detected_outputs': overall['detected_outputs'],
                    'overall_joint_count_bounds': [overall['joint_outputs'],overall['joint_outputs']+overall['joint_output_unknown']],
                    'overall_joint_rate_bounds': overall['joint_output_rate_bounds'],
                    'qualified_retained': qualified['usable_outputs'],
                    'qualified_new_failures': emitted['valid_contradicted'],
                    'qualified_no_output': report['qualified_known_emission_rejections'],
                    'qualified_unknown': qualified['output_utility_unknown'],
                    'qualified_emitted': report['qualified_emitted_inputs'],
                    'qualified_joint_rate_bounds': qualified['joint_output_rate_bounds'],
                    'conditional_detection_bounds': qualified['conditional_detection_bounds'],
                    'input_detector_control': report['input_detector_control'],
                    'source_contract_groups': report['source_contract_groups']}
            reports.append(item)
            transitions.append({'study': name, 'dataset': report['dataset'],
                                'native': report['before_after_transition_matrix'],
                                'operational': report['before_after_operational_transition_matrix']})
    comparison = json.loads((comparison_root/'summary.json').read_text())
    assert comparison['status'] == 'PASS'
    grouped = {}
    for row in comparison['reports']:
        key = (row['scope'],row['classifier'])
        item = grouped.setdefault(key, {'dataset': key[0], 'classifier': key[1],
                                        'N': row['scheduled_attempts_per_catalogue']})
        item[row['method']+'_'+row['target']] = row['first_certificate']['suite_queries']
    comparisons = list(grouped.values())
    causes = json.loads((causes_root/'summary.json').read_text())
    result = {'status': 'COMPLETE', 'primary_classifier': 'rf',
              'current_studies': {k: os.path.relpath(v,args.output) for k,v in studies.items()},
              'outcome_tables': reports, 'transition_matrices': transitions,
              'source_changes': changes, 'unavailable_native_observations': unavailable,
              'audit_comparisons': comparisons, 'receiving': receiving,
              'causal_diagnostics': {k:v for k,v in causes.items() if k!='results'},
              'comparison_receiving': {k:comparison[k] for k in
                   ('independent_prefix_checks','independent_selection_checks','candidate_executions_by_this_analysis')}}
    (args.output/'empirical-tables.json').write_text(json.dumps(result,indent=2)+'\n')
    primary = [r for r in reports if r['dataset']=='pooled']
    text = '''# CREST empirical extension: current received evidence

The current canonical studies are `validated/reference` and `validated/catalogue`.
The current published-program functional studies are `isolated/gpt4o` and
`isolated/qwen`. Generated-program validity uses the original mxeval prompt and
assertions with separate program and test namespace bindings. The original
entry object and its globals are retained, with no wrapper or value encoding.
The preceding typed observations are
retained under `validated/gpt4o` and `validated/qwen` as additional evidence, not
as the primary functional outcomes. Every number below is exported from the
current received records by `export_crest_tables.py`.

## Full attempted populations

`N` includes every scheduled input. `E=0` is a completed precheck rejection with
no output; it has zero operational output yield and no invented V/D label.
`Pass`, `Fail`, and `Unknown` describe emitted candidate suites. A joint output
is emitted, passes the original suite, and is detector-positive. The main
detector is the unchanged upstream random forest at its released operating point.

'''
    text += table(['Cohort','N','Input pass','Emitted','E=0','Pass','Fail','Unknown','D+','Joint count bounds'],
                  [(NAMES[r['study']],r['N'],r['input_pass'],r['emitted'],r['no_output'],r['output_pass'],
                    r['output_fail'],r['output_unknown'],r['detected_outputs'],
                    str(r['overall_joint_count_bounds'])+'/'+str(r['N'])) for r in primary])
    text += '''

## Preservation and usable output retention

Qualification uses only the original program's suite outcome. The table counts
all qualified inputs, including known no-output events. An emitted program
failure is a separate mechanism from failure to emit. Results for initially
failing programs remain in the full-population table and transition matrices.

'''
    text += table(['Cohort','Qualified originals','Qualified emitted','Retained','New suite failures','No output','Unknown','Joint retention bounds'],
                  [(NAMES[r['study']],r['input_pass'],r['qualified_emitted'],r['qualified_retained'],
                    r['qualified_new_failures'],r['qualified_no_output'],r['qualified_unknown'],
                    str(r['qualified_joint_rate_bounds'])) for r in primary])
    text += '''

## Corpus-specific outcomes

'''
    text += table(['Cohort','Corpus','N','Input pass','Output pass','New suite failures','Qualified no output','Output unknown'],
                  [(NAMES[r['study']],r['dataset'],r['N'],r['input_pass'],r['output_pass'],
                    r['qualified_new_failures'],r['qualified_no_output'],r['output_unknown'])
                   for r in reports if r['dataset']!='pooled'])
    text += '''

## Causal diagnostics and catalogue tradeoff

All 15 stock failures on canonical inputs have three fresh, source-bound
interventions: the complete catalogue fails, removing the implicated rule
passes, and that rule alone fails. The 45 current native receipts are in
`validated/causes/summary.json`. Default emissions reproduce the original
candidates exactly. Rule 46 accounts for 11 cases of invalid operand reordering;
rule 24 accounts for two API/name-binding cases; rule 20 removes a loop binding
used afterward; rule 38 captures a nested enumerate binding.

The catalogue ablation removes these four rule families only from embedding.
Detection still uses the complete upstream feature extractor and unchanged
classifiers. The ablation restores all 15 observed emitted-program failures,
while its RF-positive count falls from 589 to 456. This is a measured
post-diagnosis tradeoff, not a claim that the remaining rules are universally safe.

## Full-population audit comparisons

Both catalogues retain all 591 scheduled attempts, including their two known
no-output events. The emitted candidates form 739 actual source/contract groups;
439 groups occur in both catalogues. Identity includes original and candidate
text, the complete test contract, the observer, and the execution environment.
No terminal no-output event receives a fabricated behavioral group. Query
counts below come from retrospective disclosure of fresh measurements, not
native wall-time trials. All current shared C certificates use the paired
ratio envelope and its separate-interval fallback.

'''
    text += table(['Corpus','Head','J shared','J independent','C H-first','C independent','C adaptive'],
                  [(r['dataset'],r['classifier'],r['coupled_J'],r['independent_J'],r['coupled_C'],
                    r['independent_C'],r['adaptive_C']) for r in comparisons])
    text += '''

The H-first acquisition result remains visible as an ablation. The adaptive
rule uses only public interval structure: when either defined C interval is a
singleton, it selects the separate minimax query; otherwise it follows the
coefficient-difference policy. Stopping still requires positive denominators.
An independent Fraction implementation receives every paired certificate and
every query selection, without importing the production paired implementation.

## Execution and provenance

The generated-program study covers every published HumanEval and MBPP file for
both models: 164 + 974 per model, 2,276 inputs total. No syntax, source-quality,
output, or detector filtering changes the population. The original mxeval
assembly is `prompt + completion + newline + test + newline + check(entry_point)`.
The complete literal-assembly evaluation is retained under `functional` as a
contract sensitivity study. The primary runner executes prompt plus completion
in program globals and binds the original entry object. It executes the
unchanged test in a shallow copy of those globals, then calls its check on the
original object. This separates namespace bindings while sharing imported
modules and original objects. Candidate globals are retained; arguments and
return values are never serialized. Resource limits are 10 CPU seconds, 15 wall seconds,
and 1 GiB address space; resource interruptions remain unavailable. Assertions
are enabled, hash seed and thread settings are fixed, and the worker environment
is probed with the same clean interpreter invocation used for every task.

NumPy and SymPy are available in the declared functional environment. Ten
small contract controls check recursive entry names, preserved program bindings,
native complex values, type objects, named tuples, Counters, numeric package
values, successful suites, witnessed failures, and
resource/harness unavailability. They are observer controls, not empirical
benchmark rows. Typed observations retain their original results and the two
explicit dependency amendments for auditability.

Input text uses UTF-8 decoding with Python universal-newline handling. All 974
GPT-4o MBPP archive files use CRLF and are submitted as LF text; the other 1,302
files already match the submitted UTF-8 bytes. No token-level repairs or
completion edits were applied. The provenance receiver checks archived bytes,
decoded input text, official test files, native requests, source files from the
retained generation stage, upstream implementation/model/threshold identities,
and the exact observer/environment of each original/candidate pair. Numerical
receiving independently validates native outcomes and every saved classifier
probability under the estimator's training-compatible library and class order.

Source feature extraction is additionally checked through the official CLI on
four selected original/candidate cases, including rejection and unmarked-positive
controls. This is a selected-pair conformance check, not an all-source independent
feature recomputation. The three released detector heads provide sensitivity
readings on the same programs, not three independent cohorts.

## Remaining unavailable observations

'''
    text += table(['Cohort','Task','Side','Interruption','Error'],
                  [(NAMES[r['study']],r['task_id'],r['side'],r['interruption'] or r['returncode'],
                    json.dumps(r['error'],ensure_ascii=False)) for r in unavailable]) if unavailable else 'All current native outcomes were received.\n'
    text += '''

## Evidence interpretation and source records

Four official MBPP entries (56, 349, 899, and 967) are named `check`; their test
texts also define `check(candidate)`. Literal assembly ends with `check(check)`.
All four official canonical solutions fail that assembly and pass the uniform
separate-bindings contract. The full two-model sensitivity study checks all
4,434 original/candidate observations: five input pairs (ten native labels)
change, all within these four entries, and original/candidate labels change
together. All other observations agree, including the Qwen timeout pair.
`isolated/contract-sensitivity.json` records the complete difference set and all
eight model/task combinations. These execution-contract effects are not
classified as watermark-induced failures.

These public generated programs also appear in the original CREST classifier
data workflow. Available public assets do not establish that the complete
cohorts were held out from fitting. The fixed detector readings therefore
support utility and preservation analysis on these actual published programs;
they are not an independent held-out detector-generalization estimate. Input
detector controls likewise report observed numerators and available denominators,
not a population false-positive rate. Complete transitions, including initially
failing and unavailable originals, are in `empirical-tables.json`.

The functional claim is compliance with each original benchmark assertion
contract, not unrestricted semantic equivalence. The declared observer and
execution environment are part of every obligation's identity. The complete
pipeline requires no remote service or API token for embedding/detection.
ACW was inspected but its authenticated Sourcery dependency prevented a full
execution; it is not counted as an evaluated implementation.

Primary upstream implementation: https://github.com/niccap/crest . Its README
describes the associated work as submitted; no publication venue is inferred.
Official functional contracts and assembly: https://github.com/amazon-science/mxeval .
The retained mxeval license accompanies the contract files. No top-level CREST
license was present in the acquired repository; acquisition instructions should
preserve its provenance rather than assign a new license to vendor code/models.

The current deliverable should expose only the four current study directories
listed above as primary results. Retained generation records are provenance
inputs only; old standalone and typed behavioral labels do not compete with
the final functional outcomes. Source records and their acquisition instructions
must remain available for the provenance receiver. The paired comparison is
`paired-comparison/summary.json`; the old comparison directory is historical.
'''
    if args.study_root:
        for old,new in [('validated/reference','accepted/reference'),('validated/catalogue','accepted/catalogue'),
                        ('isolated/gpt4o','accepted/gpt4o'),('isolated/qwen','accepted/qwen'),
                        ('validated/gpt4o','contract-sensitivity/typed/gpt4o'),('validated/qwen','contract-sensitivity/typed/qwen'),
                        ('validated/causes','accepted/causes'),('isolated/contract-sensitivity.json','contract-sensitivity/summary.json'),
                        ('paired-comparison/summary.json','accepted/comparison/summary.json'),
                        ('under `functional`','under `contract-sensitivity/literal`')]:
            text=text.replace(old,new)
    (args.output/'empirical-integration.md').write_text(text)
    print(json.dumps({'status':'COMPLETE','tables':len(reports),'comparisons':len(comparisons),
                      'native_unavailable_receipts':len(unavailable)}))


if __name__=='__main__':
    main()
