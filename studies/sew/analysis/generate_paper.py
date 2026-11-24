#!/usr/bin/env python3
"""Render paper tables and quantitative figures from received comparison data.

This entry point only reads results. It writes generated material below the
explicit paper directory and records the exact input digests beside it.
"""
import argparse
import csv
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import statistics

NAMES = {'stock': 'Stock', 's1': 'S1', 's4': 'S4', 's1_s4': 'S1+S4'}
SCOPES = {'humaneval': 'HumanEval', 'mbpp': 'Sanitized MBPP', 'pooled': 'Pooled'}
VARS = tuple(NAMES)


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def q(x):
    return float(Fraction(x))


def pct(x):
    return f'{100*q(x):.2f}'


def count(x):
    return f'{x:,}'.replace(',', r'\,')


def frac(x):
    f = Fraction(x)
    return str(f.numerator) if f.denominator == 1 else rf'\frac{{{f.numerator}}}{{{f.denominator}}}'


def cert(c, policy, target, kind):
    return c['schedules'][policy]['first_certificates'][kind + '_' + target]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', type=Path, required=True)
    ap.add_argument('--paper', type=Path, required=True)
    ap.add_argument('--online', type=Path)
    ap.add_argument('--all-withheld', type=Path)
    ap.add_argument('--enhanced', type=Path)
    ap.add_argument('--comparison-costs', type=Path,
                    default=Path(__file__).resolve().parents[3] / 'results/revision-sew-comparison-costs')
    a = ap.parse_args()
    data = a.paper / 'figdata'; figures = a.paper / 'figures'
    data.mkdir(parents=True, exist_ok=True); figures.mkdir(parents=True, exist_ok=True)
    comparisons = json.loads((a.analysis / 'comparisons.json').read_text())
    scores = json.loads((a.analysis / 'scope_scores.json').read_text())
    manifest = json.loads((a.analysis / 'manifest.json').read_text())
    strong_path = a.comparison_costs / 'retrospective-primary/analysis.json'
    strong = json.loads(strong_path.read_text())
    timing_path = a.comparison_costs / 'summary.json'
    cost_summary = json.loads(timing_path.read_text())
    if (cost_summary['status'] != 'COMPLETE' or
            cost_summary['receiving']['status'] != 'PASS' or
            cost_summary['input_sha256']['retrospective-primary/analysis.json'] != digest(strong_path)):
        raise ValueError('native timing is not bound to the received own-order analysis')
    timing = cost_summary['native_timing']
    if timing['counterbalance']['status'] != 'PASS':
        raise ValueError('native timing must retain both complementary order blocks')
    policy_path = a.comparison_costs / 'policy-controls.json'
    replay_path = a.comparison_costs / 'retrospective-receiving.json'
    policy_controls = json.loads(policy_path.read_text())
    replay_receiving = json.loads(replay_path.read_text())
    for path, report in ((policy_path, policy_controls), (replay_path, replay_receiving)):
        if (report['status'] != 'PASS' or
                cost_summary['input_sha256'][path.name] != digest(path)):
            raise ValueError('comparison control or replay receiving is not current')
    if (strong['initialization'] != 'reference_identity_known' or
            strong['original_comparisons_sha256'] != digest(a.analysis / 'comparisons.json') or
            set(strong['reports']) != set(comparisons)):
        raise ValueError('own-order comparisons do not bind the current complete paired study')
    def own_cert(case, target, kind):
        result = strong['reports'][case]['runs'][kind+'_'+target]['first_certificate']
        if result is None:
            raise ValueError('a current main comparison is unresolved')
        return result
    if manifest['initialization'] != 'reference_identity_known':
        raise ValueError('main paper requires free reference-identity initialization')
    for scope, record in scores.items():
        for version, s in record['complete_scores'].items():
            if s['unavailable_rows'] or s['detected'] != s['joint']:
                raise ValueError('current prose assumes complete natural cells with D=J')
            if Fraction(s['J']) != Fraction(s['joint'], s['rows']):
                raise ValueError('inconsistent joint score')
            if Fraction(s['A']) != Fraction(s['valid'], s['rows']):
                raise ValueError('inconsistent valid score')
            if Fraction(s['C']) != Fraction(s['joint'], s['valid']):
                raise ValueError('inconsistent conditional score')

    macros = {}
    for prefix, case in [('HE', 'humaneval__stock__s1'), ('MB', 'mbpp__stock__s4')]:
        c = comparisons[case]
        macros[prefix+'Rows'] = count(c['full_row_suites_after_reference'])
        macros[prefix+'Unique'] = count(c['full_unique_group_suites_after_reference'])
        macros[prefix+'Free'] = count(c['reference_identity_known_groups'])
        macros[prefix+'Influential'] = count(c['J_gap_influential_groups'])
        for target, policy in [('J', 'joint_width_per_suite'), ('C', 'conditional_differences_first')]:
            for kind, suffix in [('coupled', 'Shared'), ('independent', 'Separate')]:
                cc = own_cert(case, target, kind)
                macros[prefix+target+suffix] = count(cc['suite_queries'])
            macros[prefix+target+'MatchedSeparate'] = count(cert(c, policy, target, 'independent')['suite_queries'])
            if own_cert(case,target,'coupled')['suite_queries'] != cert(c,policy,target,'coupled')['suite_queries']:
                raise ValueError('shared own-order and retained coupled policies disagree')
            cc = cert(c, policy, target, 'coupled')
            snap = cc['snapshot']
            if target == 'J':
                for edge in ['lower','upper']:
                    macros[prefix+'J'+edge.title()] = frac(Fraction(snap['coupled_J'][edge], c['denominator']))
            else:
                if snap['coupled_C']['route'] != 'exact_common_remainder':
                    raise ValueError('conditional figure requires exact remainder route')
                for side, label in [('left','Left'),('right','Right')]:
                    macros[prefix+'C'+label+'Interval'] = (
                        '['+frac(snap[side+'_C']['lower'])+','+frac(snap[side+'_C']['upper'])+']')
                macros[prefix+'MarginLower'] = count(snap['coupled_C']['lower'])
                macros[prefix+'MarginUpper'] = count(snap['coupled_C']['upper'])
        for target in ['J','C']:
            hs = [cert(c, f'hash_{i:02d}', target, 'coupled')['suite_queries'] for i in range(16)]
            macros[prefix+target+'HashMin'] = count(min(hs))
            macros[prefix+target+'HashMax'] = count(max(hs))
            macros[prefix+target+'HashMedian'] = str(statistics.median(hs))
        for kind, suffix in [('coupled','Shared'),('independent','Separate')]:
            witness=strong['reports'][case]['hindsight_joint_witness'][kind]
            if not witness['available']:
                raise ValueError('missing completed-label witness')
            macros[prefix+'JHindsight'+suffix]=count(witness['minimum_queries'])
    macros['NaturalAbstractResult'] = (
        'With already checked reference identities admitted, shared bounds certify the stock--S1 '
        'joint-yield ordering on HumanEval after '+macros['HEJShared']+' candidate suites, compared with '
        +macros['HEJSeparate']+' for separately scheduled score bounds. The stock--S4 MBPP '
        'comparison requires '+macros['MBJShared']+' and '+macros['MBJSeparate']+' suites, respectively.')
    if a.online:
        online = json.loads(a.online.read_text())
        if online['status'] != 'PASS': raise ValueError('native replay not accepted')
        macros['OnlineTotalQueries'] = count(online['total_candidate_suite_queries'])
        cost_rows=[]
        for case in online['cases']:
            certificate=json.loads((a.online.parent/case['case']/'certificate.json').read_text())
            entries=0
            for query in certificate['queries']:
                ep=a.online.parent/query['evidence_file']
                if digest(ep)!=query['evidence_sha256']:raise ValueError('changed native evidence')
                e=json.loads(ep.read_text())
                if case['dataset']=='HumanEval':
                    entries+=len(json.loads(e['stdout'])['observations'])
                else:
                    events=[json.loads(line) for line in e['stdout'].splitlines() if line.strip()]
                    entries+=sum(event.get('event')=='test_result' and event.get('assertion_reached',False) for event in events)
            cost_rows.append(dict(case=case['case'],dataset=case['dataset'],target=case['target'],
                                  queries=case['candidate_suite_queries'],entries=entries,
                                  entry_unit='function entries' if case['dataset']=='HumanEval' else 'assertion entries'))
        table=[r'\begin{table}[ht]',r'\caption{Fresh native execution through first certification.}',
               r'\label{tab:natural-native}',r'\centering\small',r'\begin{tabular}{@{}llrrl@{}}',
               r'\toprule Comparison & Target & Suites & Entries & Entry unit\\\midrule']
        for r in cost_rows:
            name='HumanEval: stock / S1' if r['dataset']=='HumanEval' else 'MBPP: stock / S4'
            table.append(' & '.join([name,'$'+r['target']+'$',count(r['queries']),count(r['entries']),r['entry_unit']])+r'\\')
        table += [r'\bottomrule\end{tabular}',r'\end{table}']
        (data/'natural-native-costs.tex').write_text('\n'.join(table)+'\n')
        (data/'natural-native-costs.json').write_text(json.dumps(cost_rows,indent=2)+'\n')
    if a.all_withheld:
        receipts=[json.loads((p/'certificate_receiving.json').read_text()) for p in [a.analysis,a.all_withheld]]
        for suffix,key in [('Schedules','schedules'),('TraceStates','trace_states_checked'),
                           ('ReconstructedStates','independently_reconstructed_states'),
                           ('Certificates','first_certificates_checked')]:
            macros['NaturalTheory'+suffix]=count(sum(r[key] for r in receipts))
    macros['TimingRuns'] = count(timing['runs'])
    macros['TimingRepeats'] = count(timing['repeats'])
    macros['TimingSuites'] = count(timing['candidate_suite_executions'])
    preparations = {row['block']: row for row in timing['common_preparations']}
    macros['TimingSetupFirstSeconds'] = f"{preparations['native-timing']['total_seconds']:.3f}"
    macros['TimingSetupReverseSeconds'] = f"{preparations['native-timing-reverse']['total_seconds']:.3f}"
    for suffix, key in [('Assignments','hidden_assignments'),
                        ('EndpointChecks','hypothetical_endpoint_checks'),
                        ('GreedyChoices','complete_candidate_greedy_checks'),
                        ('HindsightMinima','joint_hindsight_minima'),
                        ('Subsets','joint_witness_subsets')]:
        macros['OwnPolicy'+suffix] = count(policy_controls[key])
    macros['OwnPolicyTraces'] = count(replay_receiving['schedules_received'])
    macros['OwnPolicyPrefixes'] = count(replay_receiving['prefixes_received'])
    runtime_rows = [r'\begin{table}[t]',
                    r'\caption{Measured audit time through first certification.}',
                    r'\label{tab:natural-runtime}', r'\centering\small',
                    r'\begin{tabular}{@{}llrrrr@{}}', r'\toprule',
                    r'Target & Method & Suites & Select (ms) & Worker (s) & Audit (s): median [range]\\',
                    r'\midrule']
    phase_rows = [r'\begin{table}[ht]',
                  r'\caption{Nonworker audit phases: median milliseconds over '
                  +str(timing['repeats'])+r' executions.}',
                  r'\label{tab:natural-runtime-phases}', r'\centering\small',
                  r'\begin{tabular}{@{}llrrrrr@{}}', r'\toprule',
                  r'Target & Method & Register & Select & Bounds & Receive & Record\\',
                  r'\midrule']
    scope_previous = None
    for row in timing['rows']:
        if row['repeats'] != timing['repeats'] or row['candidate_suite_queries'] != own_cert(
                row['case'], row['target'], row['method'])['suite_queries']:
            raise ValueError('timed execution and retrospective first certificate disagree')
        if row['scope'] != scope_previous:
            if scope_previous is not None:
                runtime_rows.append(r'\addlinespace')
                phase_rows.append(r'\addlinespace')
            title = 'HumanEval: stock / S1' if row['scope'] == 'humaneval' else 'MBPP: stock / S4'
            runtime_rows.append(r'\multicolumn{6}{@{}l}{\textit{'+title+r'}}\\')
            phase_rows.append(r'\multicolumn{7}{@{}l}{\textit{'+title+r'}}\\')
            scope_previous = row['scope']
        label = 'Shared' if row['method'] == 'coupled' else 'Separate'
        t = row['additional_audit_seconds']
        p = row['phase_seconds']
        cells = ['$'+row['target']+'$', label, count(row['candidate_suite_queries']),
                 f"{1000*p['select_seconds']['median']:.3f}",
                 f"{p['worker_seconds']['median']:.3f}",
                 f"{t['median']:.3f} [{t['minimum']:.3f}, {t['maximum']:.3f}]"]
        runtime_rows.append(' & '.join(cells)+r'\\')
        phase_rows.append(' & '.join(['$'+row['target']+'$', label] + [
            f"{1000*p[name+'_seconds']['median']:.3f}"
            for name in ('register', 'select', 'bounds', 'receive', 'record')])+r'\\')
        prefix = 'HE' if row['scope'] == 'humaneval' else 'MB'
        macros[prefix+row['target']+label+'Seconds'] = f"{t['median']:.3f}"
    runtime_rows += [r'\bottomrule\end{tabular}', r'\end{table}']
    phase_rows += [r'\bottomrule\end{tabular}', r'\end{table}']
    (data/'natural-runtime.tex').write_text('\n'.join(runtime_rows)+'\n')
    (data/'natural-runtime-phases.tex').write_text('\n'.join(phase_rows)+'\n')
    lines = ['% Generated from received natural-corpus results; do not edit numbers here.']
    lines += [rf'\newcommand{{\{key}}}{{{value}}}' for key,value in macros.items()]
    (data/'natural-macros.tex').write_text('\n'.join(lines)+'\n')

    lines = [r'\begin{table}[t]',r'\caption{Complete original-suite outcomes.}',r'\label{tab:natural-outcomes}',
             r'\centering\small',r'\begin{tabular}{@{}llrrrcc@{}}',r'\toprule',
             r'Corpus & Version & Attempts & Valid & Joint & $J$ (\%) & $C$ (\%)\\',r'\midrule']
    for scope in ['humaneval','mbpp']:
        for index,version in enumerate(VARS):
            s = scores[scope]['complete_scores'][version]
            lines.append(' & '.join([SCOPES[scope] if index==0 else '',NAMES[version],
                count(s['rows']),count(s['valid']),count(s['joint']),pct(s['J']),pct(s['C'])])+r'\\')
        if scope == 'humaneval': lines.append(r'\addlinespace')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (data/'natural-outcomes.tex').write_text('\n'.join(lines)+'\n')

    def cost_table(scopes, label, caption, own_order=True):
        rows = [r'\begin{table}[t]',r'\caption{'+caption+'}',r'\label{'+label+'}',
                r'\centering\small',r'\begin{tabular}{@{}lrrrrcc@{}}',r'\toprule',
                r'Comparison & Rows & Unique & $K_J$ & $|H|$ & $J$: sep./shared & $C$: sep./shared\\',r'\midrule']
        for scope in scopes:
            rows.append(r'\multicolumn{7}{@{}l}{\textit{'+SCOPES[scope]+r'}}\\')
            for case,c in comparisons.items():
                if c['scope'] != scope: continue
                items=[NAMES[c['left']]+' / '+NAMES[c['right']],
                       count(c['full_row_suites_after_reference']),
                       count(c['full_unique_group_suites_after_reference']),
                       count(c['J_gap_influential_groups']),count(c['C_coefficient_different_groups'])]
                for target,policy in [('J','joint_width_per_suite'),('C','conditional_differences_first')]:
                    items.append(' / '.join(count((own_cert(case,target,kind) if own_order else
                        cert(c,policy,target,kind))['suite_queries']) for kind in ['independent','coupled']))
                rows.append(' & '.join(items)+r'\\')
            if scope != scopes[-1]: rows.append(r'\addlinespace')
        rows += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
        return '\n'.join(rows)+'\n'
    (data/'natural-costs.tex').write_text(cost_table(['humaneval','mbpp'],'tab:natural-costs','First certificates under method-specific query policies.'))
    (data/'natural-pooled.tex').write_text(cost_table(['pooled'],'tab:natural-pooled','Pooled task-uniform comparisons with method-specific queries.'))
    withheld_path=a.comparison_costs/'retrospective-all-withheld/analysis.json'
    strong_withheld=json.loads(withheld_path.read_text())
    if strong_withheld['initialization'] != 'all_withheld':
        raise ValueError('wrong initialization in the supplementary policy comparison')
    rows=[r'\Needspace{24\baselineskip}',r'\begin{longtable}{@{}llrrcc@{}}',
          r'\caption{Separate-bound order ablation and all-withheld comparison costs.}\label{tab:natural-baseline-sensitivity}\\',
          r'\toprule & & \multicolumn{2}{c}{Matched separate} & \multicolumn{2}{c}{All withheld: sep./shared}\\',
          r'Corpus & Comparison & $J$ & $C$ & $J$ & $C$\\\midrule\endfirsthead',
          r'\toprule & & \multicolumn{2}{c}{Matched separate} & \multicolumn{2}{c}{All withheld: sep./shared}\\',
          r'Corpus & Comparison & $J$ & $C$ & $J$ & $C$\\\midrule\endhead']
    for case,c in comparisons.items():
        cells=[SCOPES[c['scope']],NAMES[c['left']]+' / '+NAMES[c['right']]]
        for target,policy in [('J','joint_width_per_suite'),('C','conditional_differences_first')]:
            cells.append(count(cert(c,policy,target,'independent')['suite_queries']))
        for target in ['J','C']:
            cells.append(' / '.join(count(strong_withheld['reports'][case]['runs'][kind+'_'+target]
                                         ['first_certificate']['suite_queries'])
                                    for kind in ['independent','coupled']))
        rows.append(' & '.join(cells)+r'\\')
    rows += [r'\bottomrule\end{longtable}',
             r'Matched separate uses the shared policy\textquotesingle s disclosures with reference-identity admission. All withheld uses each method\textquotesingle s own policy and no initial candidate labels.']
    (data/'natural-baseline-sensitivity.tex').write_text('\n'.join(rows)+'\n')
    rows=[r'\begin{table}[ht]',r'\centering\small',
          r'\caption{Joint-certificate size with completed labels and with executable policies.}',
          r'\label{tab:natural-hindsight}',r'\begin{tabular}{@{}lrrrr@{}}',
          r'\toprule & \multicolumn{2}{c}{Shared} & \multicolumn{2}{c}{Separate}\\',
          r'Comparison & Hindsight min. & Policy & Hindsight min. & Policy\\\midrule']
    for case,title in [('humaneval__stock__s1','HumanEval: stock / S1'),('mbpp__stock__s4','MBPP: stock / S4')]:
        c=strong['reports'][case]
        cells=[title]
        for kind in ['coupled','independent']:
            cells += [count(c['hindsight_joint_witness'][kind]['minimum_queries']),
                      count(c['runs'][kind+'_J']['first_certificate']['suite_queries'])]
        rows.append(' & '.join(cells)+r'\\')
    rows += [r'\bottomrule\end{tabular}',r'\end{table}']
    (data/'natural-hindsight.tex').write_text('\n'.join(rows)+'\n')
    rows=[r'\Needspace{23\baselineskip}',r'\begin{longtable}{@{}llrrrrrr@{}}',r'\caption{Sensitivity of shared certificates to sixteen fixed hash orders.}\label{tab:natural-hash}\\',
          r'\toprule Corpus & Comparison & \multicolumn{3}{c}{$J$ suites} & \multicolumn{3}{c}{$C$ suites}\\',
          r' & & Min. & Median & Max. & Min. & Median & Max.\\\midrule\endfirsthead',
          r'\toprule Corpus & Comparison & \multicolumn{3}{c}{$J$ suites} & \multicolumn{3}{c}{$C$ suites}\\',
          r' & & Min. & Median & Max. & Min. & Median & Max.\\\midrule\endhead']
    for c in comparisons.values():
        cells=[SCOPES[c['scope']],NAMES[c['left']]+' / '+NAMES[c['right']]]
        for target in ['J','C']:
            vals=[cert(c,f'hash_{i:02d}',target,'coupled')['suite_queries'] for i in range(16)]
            cells += [count(min(vals)),str(statistics.median(vals)),count(max(vals))]
        rows.append(' & '.join(cells)+r'\\')
    rows += [r'\bottomrule\end{longtable}']
    (data/'natural-hash.tex').write_text('\n'.join(rows)+'\n')
    if a.all_withheld:
        withheld=json.loads((a.all_withheld/'comparisons.json').read_text())
        rows=[r'\Needspace{12\baselineskip}',r'\begin{longtable}{@{}llrrrrrr@{}}',
              r'\caption{Query-order and initialization sensitivity.}\label{tab:natural-policy}\\',
              r'\toprule & & \multicolumn{3}{c}{$J$ shared suites} & \multicolumn{3}{c}{$C$ shared suites}\\',
              r'Corpus & Comparison & Config. & Priority & All withheld & Config. & Priority & All withheld\\\midrule\endfirsthead',
              r'\toprule & & \multicolumn{3}{c}{$J$ shared suites} & \multicolumn{3}{c}{$C$ shared suites}\\',
              r'Corpus & Comparison & Config. & Priority & All withheld & Config. & Priority & All withheld\\\midrule\endhead']
        comparison_items=list(comparisons.items())
        for index,(case,c) in enumerate(comparison_items):
            cells=[SCOPES[c['scope']],NAMES[c['left']]+' / '+NAMES[c['right']]]
            for target,policy in [('J','joint_width_per_suite'),('C','conditional_differences_first')]:
                cells += [count(cert(c,'configuration_first',target,'coupled')['suite_queries']),
                          count(cert(c,policy,target,'coupled')['suite_queries']),
                          count(cert(withheld[case],policy,target,'coupled')['suite_queries'])]
            same_scope_next = index + 1 < len(comparison_items) and comparison_items[index + 1][1]['scope'] == c['scope']
            rows.append(' & '.join(cells)+(r'\\*' if same_scope_next else r'\\'))
        rows += [r'\bottomrule\end{longtable}',
                 r'Configuration and priority admit reference-identical candidates. All withheld uses the same target-specific priority without those initial labels. Priority uses joint width for $J$ and coefficient differences for $C$.']
        (data/'natural-policy-sensitivity.tex').write_text('\n'.join(rows)+'\n')
    if a.enhanced:
        enhanced=json.loads((a.enhanced/'rows.json').read_text())
        unresolved=[r for r in enhanced if r['validity_label']=='unavailable']
        rows=[r'\begin{table}[ht]',r'\caption{Tasks with unavailable expanded-input observations.}',
              r'\label{tab:enhanced-unavailable}',r'\centering\small',
              r'\begin{tabular}{@{}lrrr@{}}',r'\toprule',
              r'HumanEval task & Declared pairs & Comparable & Unavailable\\\midrule']
        for r in unresolved:
            rows.append(' & '.join([r['task_id'].split('/')[-1],count(r['declared_input_pairs']),
                                   count(r['comparable_input_pairs']),count(r['unavailable_input_pairs'])])+r'\\')
        rows += [r'\bottomrule\end{tabular}',r'\end{table}']
        (data/'natural-enhanced-unknown.tex').write_text('\n'.join(rows)+'\n')

    import subprocess
    import sys
    renderer = Path(__file__).with_name('plot_comparisons.py')
    subprocess.run([sys.executable, '-B', str(renderer),
                    '--artifact', str(Path(__file__).resolve().parents[3]),
                    '--analysis', str(a.analysis),
                    '--comparison-costs', str(a.comparison_costs),
                    '--out', str(figures/'natural-joint-budget.pdf'),
                    '--conditional-out', str(figures/'natural-conditional.pdf')],check=True)
    binding={'schema':'markvalidity-natural-paper-bindings-v1','initialization':manifest['initialization'],
             'inputs':{name:digest(a.analysis/name) for name in ['comparisons.json','scope_scores.json','manifest.json']},
             'generator_sha256':digest(Path(__file__)), 'renderer_sha256':digest(renderer),
             'own_order_analysis_sha256':digest(strong_path),
             'own_order_all_withheld_sha256':digest(withheld_path),
             'comparison_cost_summary_sha256':digest(timing_path), 'macros':macros,
             'policy_controls_sha256':digest(policy_path),
             'own_order_receiving_sha256':digest(replay_path),
             'figure_roles':{'natural-joint-budget':'Joint-gap width trajectories in percentage points through each method-specific first certificate, plus aligned certificate-cost strips. The matched-order ablation remains in the tables.',
                             'natural-conditional':'Separate conditional-score intervals and complete paired NF count-witness intervals; distinct axes and exact fraction labels.'}}
    if a.online:binding['online_receipt_sha256']=digest(a.online)
    if a.all_withheld:binding['all_withheld_comparisons_sha256']=digest(a.all_withheld/'comparisons.json')
    if a.enhanced:binding['enhanced_rows_sha256']=digest(a.enhanced/'rows.json')
    generated_names = [
        'natural-macros.tex', 'natural-outcomes.tex', 'natural-costs.tex',
        'natural-pooled.tex', 'natural-hash.tex', 'natural-baseline-sensitivity.tex',
        'natural-hindsight.tex', 'natural-runtime.tex', 'natural-runtime-phases.tex',
    ]
    if a.all_withheld: generated_names.append('natural-policy-sensitivity.tex')
    if a.enhanced: generated_names.append('natural-enhanced-unknown.tex')
    if a.online: generated_names.extend(['natural-native-costs.tex', 'natural-native-costs.json'])
    generated_paths = [data/name for name in generated_names]
    generated_paths += [figures/(name+'.'+ext)
                        for name in ('natural-joint-budget', 'natural-conditional')
                        for ext in ('pdf', 'svg', 'png')]
    generated_paths.append(figures/'natural-joint-budget.json')
    binding['generated_outputs'] = {
        p.relative_to(a.paper).as_posix(): digest(p) for p in generated_paths
    }
    (data/'natural-bindings.json').write_text(json.dumps(binding,indent=2)+'\n')
    print(json.dumps({'status':'generated','corpora':list(scores),'comparisons':len(comparisons),'macros':len(macros)}))


if __name__=='__main__':main()
