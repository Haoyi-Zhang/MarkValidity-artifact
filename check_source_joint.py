"""Reconstruct source-level detection and bind its semantic evidence.

Every frozen configuration is rendered and decoded from its actual source.
Python sources are checked by the restricted receiver-reference AST erasure
rule; JavaScript validity is known only for source-identical retained execution
links.  No task program or upstream watermark system is executed here.

The reported quantity is joint yield, E[valid AND detected], not P(detected |
valid).  Repeated configurations are not independent source programs.  The
compressed source inventory retains the exact text behind every source hash.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import io
import itertools
import json
from pathlib import Path
import platform
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'src'))
from covewm.benchmark import (ALPHA, ATTACKS, MIXTURE_WEIGHTS, PAYLOAD_BITS,
    PAYLOAD_COUNT, SCHEMES, SEVERITIES, CarrierState, attacked_states, channels,
    detector, extract_carriers, payload_bits, render_program)
from covewm.external_replay import validate_detection_row
from covewm.evidence_status import classify_python_evidence, OBSERVATION_RULE_ID
from covewm.tasks import TASK_BY_NAME, domain_cases
from covewm.source_groups import source_group_bounds
from check_source_detection import analyze as source_bridge
from check_source_detection import checked_input, read_table

KEY_FIELDS = ('task', 'language', 'scheme', 'attack', 'severity', 'payload_index')
LANGUAGES = ('python', 'javascript')
MODEL_FIELDS = ('surviving_sites', 'match_count', 'detected')


def identity(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def key(row):
    return tuple(str(row[field]) for field in KEY_FIELDS)


def expected_keys():
    return set(itertools.product(TASK_BY_NAME, LANGUAGES, SCHEMES, ATTACKS,
        (f'{v:.1f}' for v in SEVERITIES), (str(p) for p in range(PAYLOAD_COUNT))))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n',
                    encoding='utf-8', newline='\n')


@contextmanager
def gzip_text(path):
    """Deterministic gzip bytes: no wall-clock timestamp or local filename."""
    with path.open('wb') as binary:
        with gzip.GzipFile(filename='', fileobj=binary, mode='wb', mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding='utf-8', newline='') as text:
                yield text


def assess_source(task, language, source, bits, scheme):
    """Decode actual text; proof rejection leaves validity unknown.

    This receiving step does not accept state-model observations as extraction.
    A failed restricted proof does not establish semantic inequivalence.
    """
    if language not in LANGUAGES or scheme not in SCHEMES:
        raise ValueError('unregistered language or carrier')
    if len(bits) != PAYLOAD_BITS or any(type(bit) is not int or bit not in (0, 1) for bit in bits):
        raise ValueError('exactly 24 binary target bits required')
    extracted = extract_carriers(source, language)
    if any(type(i) is not int or not 0 <= i < PAYLOAD_BITS or type(v) is not int
           or v not in (0, 1) for i, v in extracted.items()):
        raise ValueError('invalid indexed source extraction')
    validity, proof_reason, semantic_status = None, 'no JavaScript erasure rule', 'unavailable'
    if language == 'python':
        admitted = classify_python_evidence(task,source)
        semantic_status,proof_reason = admitted.status,admitted.reason
        if admitted.status == 'supported':
            if admitted.observed_bits != extracted:
                raise ValueError('AST and marker-assisted extraction disagree')
            validity = True
        elif admitted.status == 'contradicted':
            validity = False
    states = [CarrierState(i, channel, bits[i], extracted.get(i, 0),
                i in extracted, 'source-extracted')
              for i, channel in enumerate(channels(scheme))]
    return dict(proof_validity=validity, proof_reason=proof_reason,
                semantic_status=semantic_status, extracted=extracted, detection=detector(states))


def bind_execution(row_key, source_hash, detection, executed):
    """Require both the exact configuration and source before reusing a label."""
    old = executed.get(row_key)
    if old is None:
        return None
    if source_hash != old['source_sha256']:
        raise ValueError('retained execution belongs to different source text')
    if any(int(old[field]) != detection[field] for field in MODEL_FIELDS):
        raise ValueError('retained executed source has different detector observations')
    if old['retained_semantic_label'] is not True:
        raise ValueError('retained execution is not an admitted validity label')
    return True


def bind_identical_source(task, language, source, executed_sources):
    """Reuse a retained label only for identical text under the fixed contract."""
    record = executed_sources.get((task, language, identity(source)))
    if record is None:
        return None
    if record['source'] != source:
        raise ValueError('source identity is not backed by identical source bytes')
    return record['origins']


def semantic_contract(task, language, reference_hash, runtime_hash):
    domain = json.dumps(domain_cases(task), ensure_ascii=False, separators=(',',':'))
    contract = dict(task=task, language=language, reference_sha256=reference_hash,
        domain_sha256=identity(domain), runtime_record_sha256=runtime_hash,
        observation_rule=OBSERVATION_RULE_ID,
        observations='serialized return or normalized exception on the frozen finite domain; resource and frame observations excluded')
    return identity(json.dumps(contract,sort_keys=True,separators=(',',':')))


def fraction_fields(value):
    return dict(numerator=value.numerator, denominator=value.denominator,
                exact=str(value), decimal=f'{float(value):.12f}')


def aggregate(rows):
    """Equal task/payload/severity weights within each declared attack family."""
    groups = defaultdict(list)
    for row in rows:
        groups[(row['language'], row['scheme'], row['attack'])].append(row)
    family, family_values = [], {}
    for group, values in sorted(groups.items()):
        n = len(values)
        known = sum(r['validity_status'] != 'unknown' for r in values)
        lower = sum(r['joint_lower'] for r in values)
        upper = sum(r['joint_upper'] for r in values)
        detected = sum(r['detected'] for r in values)
        family_values[group] = Fraction(lower, n), Fraction(upper, n)
        family.append(dict(language=group[0], scheme=group[1], attack=group[2],
            configurations=n, known_validity=known, unknown_validity=n-known,
            source_detections=detected, joint_lower_count=lower, joint_upper_count=upper,
            joint_lower_exact=str(Fraction(lower,n)), joint_upper_exact=str(Fraction(upper,n)),
            joint_lower=f'{lower/n:.12f}', joint_upper=f'{upper/n:.12f}'))
    mixture = []
    for language in LANGUAGES:
        for name, weights in MIXTURE_WEIGHTS.items():
            exact_weights = {a: Fraction(str(w)) for a,w in weights.items()}
            if sum(exact_weights.values()) != 1:
                raise ValueError('mixture weights must sum to one')
            for scheme in SCHEMES:
                lo = sum((w * family_values[(language, scheme, attack)][0]
                          for attack,w in exact_weights.items()), Fraction())
                hi = sum((w * family_values[(language, scheme, attack)][1]
                          for attack,w in exact_weights.items()), Fraction())
                mixture.append(dict(language=language, mixture=name, scheme=scheme,
                    joint_lower_exact=str(lo), joint_upper_exact=str(hi),
                    joint_lower=f'{float(lo):.12f}', joint_upper=f'{float(hi):.12f}',
                    point_identified=lo == hi))
    # Both languages have the same complete design, so pooled weighting is
    # exactly one half per language, not a ratio of admitted source counts.
    language_rows = list(mixture)
    for name in MIXTURE_WEIGHTS:
        for scheme in SCHEMES:
            pair = [r for r in language_rows if r['mixture'] == name and r['scheme'] == scheme]
            lo = sum((Fraction(r['joint_lower_exact']) for r in pair), Fraction()) / 2
            hi = sum((Fraction(r['joint_upper_exact']) for r in pair), Fraction()) / 2
            mixture.append(dict(language='combined', mixture=name, scheme=scheme,
                joint_lower_exact=str(lo), joint_upper_exact=str(hi),
                joint_lower=f'{float(lo):.12f}', joint_upper=f'{float(hi):.12f}',
                point_identified=lo == hi))
    return family, mixture


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def grouped_pairwise_bounds(rows):
    """One unknown validity bit per exact source/receiver contract, across carriers."""
    output = []
    scopes = {'python':('python',), 'javascript':('javascript',), 'combined':LANGUAGES}
    positive_groups = defaultdict(set)
    for row in rows:
        if row['validity_status'] == 'unknown' and row['detected']:
            g = (row['task'],row['language'],row['semantic_contract_id'],row['source_sha256'])
            positive_groups[g].add(row['scheme'])
    for scope, languages in scopes.items():
        subset = [r for r in rows if r['language'] in languages]
        denominators = defaultdict(int)
        for r in subset: denominators[(r['scheme'],r['attack'])] += 1
        for mixture, weights in MIXTURE_WEIGHTS.items():
            for left,right in itertools.combinations(SCHEMES,2):
                observations = []
                for r in subset:
                    if r['scheme'] not in (left,right): continue
                    weight = Fraction(str(weights.get(r['attack'],0)))
                    coefficient = weight * r['detected'] / denominators[(r['scheme'],r['attack'])]
                    if r['scheme'] == right: coefficient = -coefficient
                    g = (r['task'],r['language'],r['semantic_contract_id'],r['source_sha256'])
                    observations.append((g,coefficient,True if r['validity_status']=='valid' else None))
                bounded = source_group_bounds(observations)
                preferred = left if bounded.lower > 0 else right if bounded.upper < 0 else ''
                output.append(dict(language=scope, mixture=mixture, left=left, right=right,
                    lower_exact=str(bounded.lower), upper_exact=str(bounded.upper),
                    lower=f'{float(bounded.lower):.12f}', upper=f'{float(bounded.upper):.12f}',
                    preferred=preferred, distinct_source_groups=bounded.groups,
                    unknown_source_groups=bounded.unknown_groups))
    sharing = dict(unknown_source_groups_with_positive_decision=len(positive_groups),
        unknown_positive_source_groups_shared_across_carriers=sum(len(v)>1 for v in positive_groups.values()),
        group_identity='task, language, receiver observation/runtime contract, exact source text',
        sharpness_scope='one binary validity per unlabelled exact source under the fixed contract; no generic program-semantics realizability claim')
    return output,sharing


def paper_outputs(out, summary, mixtures):
    """Compact paper inputs, all derived from source-bound joint outcomes."""
    coverage = []
    for language in LANGUAGES:
        values = summary['languages'][language]
        coverage.append(dict(language=language, configurations=values['configurations'],
            distinct_task_source_identities=values['distinct_task_source_identities'],
            behavioral_basis='restricted AST erasure' if language == 'python' else 'retained bounded execution',
            known_validity=values['known_validity'], unknown_validity=values['unknown_validity'],
            source_detections=values['positive_source_decisions'],
            joint_lower_count=values['joint_lower_count'], joint_upper_count=values['joint_upper_count'],
            joint_lower=fraction_fields(Fraction(values['joint_lower_count'],values['configurations'])),
            joint_upper=fraction_fields(Fraction(values['joint_upper_count'],values['configurations']))))
    outcomes = []
    for mixture in MIXTURE_WEIGHTS:
        subset = [r for r in mixtures if r['mixture'] == mixture and r['language'] == 'combined']
        winners = []
        gaps = {}
        for row in subset:
            margin = Fraction(row['joint_lower_exact']) - max(Fraction(other['joint_upper_exact'])
                     for other in subset if other['scheme'] != row['scheme'])
            gaps[row['scheme']] = fraction_fields(margin)
            if margin > 0: winners.append(row['scheme'])
        outcomes.append(dict(mixture=mixture,
            python=[r for r in mixtures if r['language'] == 'python' and r['mixture'] == mixture],
            combined=subset, certified_combined_winners=winners,
            lower_minus_largest_competitor_upper=gaps))
    report = dict(quantity='joint yield E[validity AND source detection]',
        source_coverage=coverage, evidence_policies=summary['evidence_policies'],
        mixtures=outcomes, source_state_disagreements=0,
        source_identity_unit='task and language and exact candidate source',
        program_executions_in_this_analysis=0)
    write_json(out/'paper_summary.json',report)
    table = [r'\begin{tabular}{@{}lrrrl@{}}', r'\toprule',
             r'Language & Configurations & Sources & Validity known & Basis \\', r'\midrule']
    for row in coverage:
        basis = 'AST erasure' if row['language'] == 'python' else 'Execution'
        table.append(f"{row['language'].capitalize()} & {row['configurations']:,} & "
            f"{row['distinct_task_source_identities']:,} & {row['known_validity']:,} & {basis} " + r'\\')
    table += [r'\bottomrule',r'\end{tabular}']
    (out/'source_coverage_table.tex').write_text('\n'.join(table)+'\n',encoding='utf-8',newline='\n')
    table = [r'\begin{tabular}{@{}lrrr@{}}',r'\toprule',
             r'Mixture & Lexical & Structural & Hybrid \\',r'\midrule']
    for outcome in outcomes:
        values = {r['scheme']:Fraction(r['joint_lower_exact']) for r in outcome['python']}
        table.append(outcome['mixture'].capitalize()+' & '+' & '.join(f'{float(values[s]):.6f}' for s in SCHEMES)+r' \\')
    table += [r'\bottomrule',r'\end{tabular}']
    (out/'python_joint_table.tex').write_text('\n'.join(table)+'\n',encoding='utf-8',newline='\n')
    table = [r'\begin{tabular}{@{}lcccl@{}}',r'\toprule',
             r'Mixture & Lexical & Structural & Hybrid & Certified \\',r'\midrule']
    for outcome in outcomes:
        values = {r['scheme']:r for r in outcome['combined']}
        cells = [f"$[{float(Fraction(values[s]['joint_lower_exact'])):.6f},"
                 f"{float(Fraction(values[s]['joint_upper_exact'])):.6f}]$" for s in SCHEMES]
        winner = ', '.join(outcome['certified_combined_winners']) or 'None'
        table.append(outcome['mixture'].capitalize()+' & '+' & '.join(cells)+' & '+winner+r' \\')
    table += [r'\bottomrule',r'\end{tabular}']
    (out/'combined_joint_table.tex').write_text('\n'.join(table)+'\n',encoding='utf-8',newline='\n')
    return report


def run(results, out):
    results, out = Path(results).resolve(), Path(out).resolve()
    if out.exists() or out.is_relative_to(results) or results.is_relative_to(out):
        raise ValueError('fresh output disjoint from retained inputs required')
    started = time.monotonic()
    manifest_rows = read_table(results / 'results_manifest.csv')
    manifest = {r['relative_path']: r for r in manifest_rows}
    if len(manifest) != len(manifest_rows):
        raise ValueError('duplicate input manifest member')
    raw = checked_input(results, 'raw/robustness.csv', manifest)
    records = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    keys = [key(r) for r in records]
    if len(keys) != len(set(keys)) or set(keys) != expected_keys():
        raise ValueError('complete and unique frozen configuration support required')
    bridge_rows, bridge_sources, bridge_summary = source_bridge(results)
    runtime_bytes = (results/'environment.json').read_bytes()
    runtime_hash = hashlib.sha256(runtime_bytes).hexdigest()
    bridge_summary['input_sha256']['environment.json'] = runtime_hash
    executed = {key(dict(r, attack=r['condition'])): r for r in bridge_rows if r['dense_linked']}
    if len(executed) != 432:
        raise ValueError('retained executed link inventory mismatch')
    executed_sources = {}
    for snapshot in bridge_sources:
        g = snapshot['task'],snapshot['language'],snapshot['source_sha256']
        if g not in executed_sources:
            executed_sources[g] = dict(source=snapshot['source'],origins=[])
        elif executed_sources[g]['source'] != snapshot['source']:
            raise ValueError('historical identity has conflicting source text')
        executed_sources[g]['origins'].append(snapshot['scheme']+':'+snapshot['condition'])
    out.mkdir(parents=True, exist_ok=False)
    registration = dict(configurations=76032, python_erasure_configurations=38016,
        selection='entire frozen factorial grid, selected before source-level outcomes',
        task_program_executions=0, upstream_system_executions=0,
        quantity='joint yield E[validity AND source detection], not conditional detection',
        missing_validity='unrestricted binary completion after observing source detection',
        python_contract='restricted inert-prefix erasure, frozen receiver task, builtin input values, result-only observation',
        javascript_contract='exact-source closure of all 504 retained bounded execution observations, including carrier-only controls; original directly linked keys remain 216',
        mixture_weights=MIXTURE_WEIGHTS,
        wall_limit_seconds=480,
        input_sha256=bridge_summary['input_sha256'])
    write_json(out / 'registration.json', registration)
    cached, sources, rows, contracts = {}, {}, [], {}
    summary = dict(status='FAILED_OR_PARTIAL', registration=registration)
    try:
        for number, raw_row in enumerate(sorted(records, key=key), 1):
            if time.monotonic() - started > 480:
                raise TimeoutError('source joint analysis exceeded 480-second limit')
            model = validate_detection_row(raw_row, require_decision=True)
            task, language, scheme, attack, severity, payload_text = key(raw_row)
            payload = int(payload_text)
            bits = payload_bits(task, language, payload)
            states, _ = attacked_states(bits, scheme, attack, float(severity), task, language, payload)
            spec = TASK_BY_NAME[task]
            template = spec.python_reference if language == 'python' else spec.javascript_reference
            source = render_program(template, language, states, formatted=attack == 'format')
            source_hash = identity(source)
            reference_hash = identity(render_program(template, language, None))
            if (task,language) not in contracts:
                contracts[(task,language)] = semantic_contract(task,language,reference_hash,runtime_hash)
            contract_id = contracts[(task,language)]
            # Reuse only exact task/language/source text, never a matching row
            # count, state decision, or a hash from another configuration.
            cache_key = task, language, source
            if cache_key not in cached:
                assessed = assess_source(task, language, source, bits, scheme)
                cached[cache_key] = (assessed['proof_validity'], assessed['proof_reason'], assessed['extracted'])
            proof_validity, proof_reason, extracted = cached[cache_key]
            if language == 'python' and proof_validity is not True:
                raise ValueError('frozen Python source fails its registered erasure contract: ' + proof_reason)
            observed = [CarrierState(i, channel, bits[i], extracted.get(i, 0),
                         i in extracted, 'source-extracted')
                        for i, channel in enumerate(channels(scheme))]
            actual = detector(observed)
            if extracted != {s.index:s.observed for s in states if s.present}:
                raise ValueError('source extraction disagrees with state-model observation')
            if any(actual[field] != model[field] for field in MODEL_FIELDS):
                raise ValueError('source detection disagrees with state-model decision')
            execution_validity = bind_execution(key(raw_row), source_hash, actual, executed)
            origins = bind_identical_source(task,language,source,executed_sources)
            identity_validity = origins is not None
            known = proof_validity is True or identity_validity
            basis = ('proof+retained-execution' if proof_validity and identity_validity else
                     'restricted-erasure-proof' if proof_validity else
                     'retained-bounded-execution' if identity_validity else 'unknown')
            row = dict(zip(KEY_FIELDS, (task, language, scheme, attack, severity, payload)))
            row.update(source_sha256=source_hash, receiver_reference_sha256=reference_hash,
                semantic_contract_id=contract_id,
                source_extraction=''.join(str(extracted[i]) if i in extracted else '-' for i in range(PAYLOAD_BITS)),
                validity_status='valid' if known else 'unknown', evidence_kind=basis,
                execution_link_kind='direct-configuration' if execution_validity else 'identical-source' if identity_validity else 'none',
                execution_origins='|'.join(origins) if origins is not None else '',
                **actual, joint_lower=actual['detected'] if known else 0,
                joint_upper=actual['detected'])
            rows.append(row)
            source_key = (task, language, source_hash)
            if source_key in sources and sources[source_key]['source'] != source:
                raise ValueError('distinct source text shares a source identity')
            sources[source_key] = dict(task=task, language=language, source_sha256=source_hash,
                receiver_reference_sha256=reference_hash, semantic_contract_id=contract_id, source=source)
            if number % 8000 == 0:
                print(json.dumps(dict(processed=number, distinct_task_language_sources=len(sources))), flush=True)
        family, mixtures = aggregate(rows)
        with gzip_text(out / 'rows.csv.gz') as stream:
            writer = csv.DictWriter(stream, list(rows[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        with gzip_text(out / 'sources.jsonl.gz') as stream:
            for source_key in sorted(sources):
                stream.write(json.dumps(sources[source_key], ensure_ascii=False, sort_keys=True) + '\n')
        write_csv(out / 'family_scores.csv', family)
        write_csv(out / 'mixture_scores.csv', mixtures)
        pairwise,sharing = grouped_pairwise_bounds(rows)
        write_csv(out/'pairwise_source_bounds.csv',pairwise)
        all_lower = sum(r['joint_lower'] for r in rows)
        all_upper = sum(r['joint_upper'] for r in rows)
        summary.update(status='PASS', source_configurations=len(rows),
            distinct_task_language_source_identities=len(sources),
            source_state_observation_disagreements=0, source_state_detection_disagreements=0,
            source_group_sharing=sharing,
            retained_execution_links_reused=len(executed), historical_execution_labels_changed=False,
            task_program_executions=0, upstream_system_executions=0,
            joint_yield_full_universe=dict(lower=fraction_fields(Fraction(all_lower,len(rows))),
                upper=fraction_fields(Fraction(all_upper,len(rows))), lower_count=all_lower,
                upper_count=all_upper, configurations=len(rows)),
            languages={})
        executed_positive = sum(row['detected'] for row in bridge_rows if row['dense_linked'])
        known = sum(r['validity_status'] == 'valid' for r in rows)
        direct_known = sum(r['language']=='python' or r['execution_link_kind']=='direct-configuration' for r in rows)
        direct_positive = sum(r['detected'] for r in rows if r['language']=='python' or r['execution_link_kind']=='direct-configuration')
        closure_known = sum(r['execution_link_kind']!='none' for r in rows)
        closure_positive = sum(r['detected'] for r in rows if r['execution_link_kind']!='none')
        summary['evidence_policies'] = [
            dict(policy='historical source subset', source_decisions_known=432,
                 validity_known=432, lower_count=executed_positive,
                 upper_count=executed_positive+len(rows)-432, denominator=len(rows)),
            dict(policy='all-source extraction, retained executions only', source_decisions_known=len(rows),
                 validity_known=432, lower_count=executed_positive,
                 upper_count=all_upper, denominator=len(rows)),
            dict(policy='all-source extraction, exact-source execution closure', source_decisions_known=len(rows),
                 validity_known=closure_known, lower_count=closure_positive,
                 upper_count=all_upper, denominator=len(rows)),
            dict(policy='all-source extraction, Python erasure plus directly linked executions',
                 source_decisions_known=len(rows), validity_known=direct_known,
                 lower_count=direct_positive, upper_count=all_upper, denominator=len(rows)),
            dict(policy='all-source extraction, Python erasure plus exact-source execution closure',
                 source_decisions_known=len(rows), validity_known=known,
                 lower_count=all_lower, upper_count=all_upper, denominator=len(rows))]
        for language in LANGUAGES:
            subset = [r for r in rows if r['language'] == language]
            summary['languages'][language] = dict(configurations=len(subset),
                distinct_task_source_identities=sum(k[1] == language for k in sources),
                known_validity=sum(r['validity_status'] == 'valid' for r in subset),
                unknown_validity=sum(r['validity_status'] == 'unknown' for r in subset),
                direct_execution_configurations=sum(r['execution_link_kind']=='direct-configuration' for r in subset),
                execution_supported_configurations_after_identity_closure=sum(r['execution_link_kind']!='none' for r in subset),
                identity_reused_execution_configurations=sum(r['execution_link_kind']=='identical-source' for r in subset),
                positive_source_decisions=sum(r['detected'] for r in subset),
                joint_lower_count=sum(r['joint_lower'] for r in subset),
                joint_upper_count=sum(r['joint_upper'] for r in subset),
                per_scheme={s:dict(configurations=sum(r['scheme'] == s for r in subset),
                    detected=sum(r['detected'] for r in subset if r['scheme'] == s)) for s in SCHEMES})
        summary['python_mixture_scores'] = [r for r in mixtures if r['language'] == 'python']
        summary['combined_mixture_bounds'] = [r for r in mixtures if r['language'] == 'combined']
        summary['pairwise_source_bounds'] = pairwise
        paper_outputs(out, summary, mixtures)
        summary['outputs_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(out.iterdir()) if p.is_file()}
    except BaseException as exc:
        summary.update(completed_configurations=len(rows), error=dict(type=type(exc).__name__, message=str(exc)))
        raise
    finally:
        summary['producer_sha256'] = {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
            for name in ('check_source_joint.py', 'check_source_detection.py',
                'src/covewm/benchmark.py', 'src/covewm/source_admission.py', 'src/covewm/evidence_status.py',
                'src/covewm/source_groups.py', 'src/covewm/tasks.py')}
        write_json(out / 'summary.json', summary)
        write_json(out / 'environment.json', dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),
            python=platform.python_version(), platform=platform.platform(),
            elapsed_seconds=time.monotonic()-started,
            command='python -B check_source_joint.py --results <RESULTS> --out <FRESH_OUTPUT>'))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=HERE/'results/revision-reproduction')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.results, args.out), sort_keys=True))
