"""Verify delivered source-joint evidence directly from its stored sources.

This receiver does not call the source-joint producer, carrier renderer, attack
generator, detector, or aggregation routine. It independently reconstructs
targets, binomial decisions, and weighted bounds. The declared source extractor
and restricted AST admission rule are reused explicitly. Task programs do not
execute, and hashes are checked for identity, not treated as execution proof.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from fractions import Fraction
import gzip
import hashlib
import itertools
import json
from math import comb
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'src'))
from covewm.benchmark import extract_carriers
from covewm.source_admission import admit_python
from covewm.evidence_status import OBSERVATION_RULE_ID
from covewm.tasks import TASK_BY_NAME, domain_cases

LANGUAGES = ('python', 'javascript')
SCHEMES = ('lexical', 'structural', 'hybrid')
ATTACKS = ('format', 'rename', 'normalize', 'random_flip', 'strip', 'mixed')
WEIGHTS = {
    'balanced': {a:Fraction(1,5) for a in ATTACKS if a != 'format'},
    'rename-heavy': {'rename':Fraction(54,100), 'random_flip':Fraction(24,100), 'strip':Fraction(22,100)},
    'structure-heavy': {'normalize':Fraction(54,100), 'random_flip':Fraction(24,100), 'strip':Fraction(22,100)}}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def table(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def verify(directory, results):
    directory, results = Path(directory), Path(results)
    summary = json.loads((directory/'summary.json').read_text(encoding='utf-8'))
    need(summary['status'] == 'PASS', 'producer did not complete')
    for name, digest in summary['outputs_sha256'].items():
        need(hashlib.sha256((directory/name).read_bytes()).hexdigest() == digest, 'output identity mismatch: '+name)
    for name, digest in summary['producer_sha256'].items():
        need(hashlib.sha256((HERE/name).read_bytes()).hexdigest() == digest, 'producer source changed: '+name)
    for name, digest in summary['registration']['input_sha256'].items():
        need(hashlib.sha256((results/name).read_bytes()).hexdigest() == digest, 'retained input changed: '+name)

    audits = table(results/'raw/semantic_audit.csv')
    observed, observed_sources = {}, {}
    for audit in audits:
        need(audit['parse_ok'] == 'True' and audit['bounded_equivalent'] == 'True', 'invalid historical label')
        need(int(audit['domain_cases']) == TASK_BY_NAME[audit['task']].domain_size, 'historical domain mismatch')
        source_key = audit['task'],audit['language'],audit['source_sha256']
        observed_sources.setdefault(source_key,[]).append(audit['scheme']+':'+audit['condition'])
        if audit['condition'] != 'carrier_only':
            k = (audit['task'], audit['language'], audit['scheme'], audit['condition'], '1.0', '0')
            need(k not in observed, 'duplicate historical execution key')
            observed[k] = audit['source_sha256']
    need(len(observed) == 432, 'historical execution inventory mismatch')

    sources, proof_count, contracts = {}, 0, {}
    runtime_hash = hashlib.sha256((results/'environment.json').read_bytes()).hexdigest()
    with gzip.open(directory/'sources.jsonl.gz', 'rt', encoding='utf-8') as stream:
        for line in stream:
            record = json.loads(line)
            task, language, text = record['task'], record['language'], record['source']
            digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
            need(digest == record['source_sha256'], 'stored source digest mismatch')
            spec = TASK_BY_NAME[task]
            template = spec.python_reference if language == 'python' else spec.javascript_reference
            reference = template.replace('__CARRIERS__', '').rstrip()+'\n'
            need(hashlib.sha256(reference.encode()).hexdigest() == record['receiver_reference_sha256'], 'receiver reference mismatch')
            if (task,language) not in contracts:
                domain = json.dumps(domain_cases(task),ensure_ascii=False,separators=(',',':'))
                contract = dict(task=task,language=language,reference_sha256=record['receiver_reference_sha256'],
                    domain_sha256=hashlib.sha256(domain.encode()).hexdigest(),runtime_record_sha256=runtime_hash,
                    observation_rule=OBSERVATION_RULE_ID,
                    observations='serialized return or normalized exception on the frozen finite domain; resource and frame observations excluded')
                contracts[(task,language)] = hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            need(record['semantic_contract_id'] == contracts[(task,language)], 'source observation contract mismatch')
            extracted = extract_carriers(text, language)
            need(all(type(i) is int and 0 <= i < 24 and type(v) is int and v in (0,1)
                     for i,v in extracted.items()), 'invalid source extraction')
            if language == 'python':
                admitted = admit_python(task, text)
                need(admitted['admitted'] is True and admitted['observed'] == extracted, 'stored Python source not admitted')
                proof_count += 1
            k = task, language, digest
            need(k not in sources, 'duplicate source inventory key')
            sources[k] = (extracted, record['receiver_reference_sha256'])
    seen, used, by_family = set(), set(), defaultdict(lambda:[0,0,0,0,0])
    by_source = {}
    language_counts = defaultdict(lambda:[0,0,0,0,0])
    with gzip.open(directory/'rows.csv.gz', 'rt', encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            k = tuple(row[f] for f in ('task','language','scheme','attack','severity','payload_index'))
            task, language, scheme, attack, severity, payload = k
            need(k not in seen, 'duplicate configuration')
            seen.add(k)
            source_key = task, language, row['source_sha256']
            need(source_key in sources, 'row has no stored source')
            used.add(source_key)
            extracted, reference_hash = sources[source_key]
            need(row['receiver_reference_sha256'] == reference_hash, 'row points to a different receiver reference')
            need(row['semantic_contract_id'] == contracts[(task,language)], 'row uses a different observation contract')
            encoded = ''.join(str(extracted[i]) if i in extracted else '-' for i in range(24))
            need(row['source_extraction'] == encoded, 'stored extraction differs from actual source')
            target = [int.from_bytes(hashlib.sha256(f'payload|{task}|{language}|{payload}|{i}'.encode()).digest()[:8], 'big') & 1
                      for i in range(24)]
            n, m = len(extracted), sum(extracted[i] == target[i] for i in extracted)
            p = Fraction(sum(comb(n,j) for j in range(m,n+1)), 2**n)
            d = int(p <= Fraction(1,10000))
            need((int(row['surviving_sites']),int(row['match_count']),int(row['detected'])) == (n,m,d), 'source detector mismatch')
            need(abs(float(row['p_value'])-float(p)) < 1e-16, 'binomial tail mismatch')
            need(int(row['deletions']) == 24-n and int(row['realized_bit_changes']) == n-m, 'operation count mismatch')
            linked = k in observed
            if linked:
                need(observed[k] == row['source_sha256'], 'execution label reused on changed source')
            identity_linked = source_key in observed_sources
            valid = language == 'python' or identity_linked
            basis = ('proof+retained-execution' if language == 'python' and identity_linked else
                     'restricted-erasure-proof' if language == 'python' else
                     'retained-bounded-execution' if identity_linked else 'unknown')
            need(row['validity_status'] == ('valid' if valid else 'unknown') and row['evidence_kind'] == basis, 'invalid evidence label')
            need(row['execution_link_kind'] == ('direct-configuration' if linked else 'identical-source' if identity_linked else 'none'), 'source-identity reuse mode mismatch')
            origins = sorted(row['execution_origins'].split('|')) if row['execution_origins'] else []
            need(origins == sorted(observed_sources.get(source_key,[])), 'execution source origins mismatch')
            lo, hi = (d if valid else 0), d
            need(int(row['joint_lower']) == lo and int(row['joint_upper']) == hi, 'joint endpoint mismatch')
            counts = [1,int(valid),d,lo,hi]
            for bucket in (by_family[(language,scheme,attack)],language_counts[language]):
                for i,value in enumerate(counts): bucket[i] += value
            if source_key not in by_source:
                by_source[source_key] = dict(language=language,valid=valid,schemes=set(),positive_schemes=set(),counts=defaultdict(int))
            source_group = by_source[source_key]
            need(source_group['valid'] == valid, 'one exact source has inconsistent validity')
            source_group['schemes'].add(scheme)
            if d: source_group['positive_schemes'].add(scheme)
            source_group['counts'][(scheme,attack)] += d
    expected = set(itertools.product(TASK_BY_NAME, LANGUAGES, SCHEMES, ATTACKS,
        (f'{i/10:.1f}' for i in range(11)), (str(i) for i in range(16))))
    need(seen == expected, 'frozen grid coverage mismatch')
    need(used == set(sources), 'unreferenced or missing stored source')

    families = table(directory/'family_scores.csv')
    need(len(families) == len(by_family) == 36, 'family coverage mismatch')
    family_keys = set()
    for row in families:
        k = row['language'],row['scheme'],row['attack']
        need(k not in family_keys, 'duplicate family key'); family_keys.add(k)
        n,v,d,lo,hi = by_family[k]
        need(tuple(int(row[f]) for f in ('configurations','known_validity','source_detections','joint_lower_count','joint_upper_count'))
             == (n,v,d,lo,hi), 'family counts mismatch')
        need(Fraction(row['joint_lower_exact']) == Fraction(lo,n) and Fraction(row['joint_upper_exact']) == Fraction(hi,n), 'family rate mismatch')
    mixtures = table(directory/'mixture_scores.csv')
    mix_keys = set()
    for row in mixtures:
        lang, name, scheme = row['language'],row['mixture'],row['scheme']
        k = lang,name,scheme
        need(k not in mix_keys, 'duplicate mixture key'); mix_keys.add(k)
        endpoints = []
        for column in (3,4):
            selected_languages = LANGUAGES if lang == 'combined' else (lang,)
            endpoints.append(sum((w*Fraction(by_family[(selected,scheme,a)][column],by_family[(selected,scheme,a)][0])
                for selected in selected_languages for a,w in WEIGHTS[name].items()), Fraction())/len(selected_languages))
        need(Fraction(row['joint_lower_exact']) == endpoints[0] and Fraction(row['joint_upper_exact']) == endpoints[1], 'mixture endpoints mismatch')
        need(row['point_identified'] == str(endpoints[0] == endpoints[1]), 'identification flag mismatch')
    need(mix_keys == set(itertools.product(LANGUAGES+('combined',), WEIGHTS, SCHEMES)), 'mixture coverage mismatch')
    for lang, counts in language_counts.items():
        retained = summary['languages'][lang]
        need(tuple(retained[f] for f in ('configurations','known_validity','positive_source_decisions','joint_lower_count','joint_upper_count'))
             == tuple(counts), 'language summary mismatch')
    pairwise = table(directory/'pairwise_source_bounds.csv')
    pair_keys = set()
    for row in pairwise:
        scope,name,left,right = (row[f] for f in ('language','mixture','left','right'))
        pair_key = scope,name,left,right
        need(pair_key not in pair_keys, 'duplicate source-group contrast'); pair_keys.add(pair_key)
        selected_languages = LANGUAGES if scope == 'combined' else (scope,)
        lo=hi=Fraction(); groups=unknown=0
        for group in by_source.values():
            if group['language'] not in selected_languages or not (group['schemes'] & {left,right}): continue
            groups += 1
            coefficient = Fraction()
            for scheme,sign in ((left,1),(right,-1)):
                for attack,weight in WEIGHTS[name].items():
                    denominator = sum(by_family[(lang,scheme,attack)][0] for lang in selected_languages)
                    coefficient += sign*weight*Fraction(group['counts'].get((scheme,attack),0),denominator)
            if group['valid']:
                lo += coefficient; hi += coefficient
            else:
                unknown += 1
                if coefficient < 0: lo += coefficient
                if coefficient > 0: hi += coefficient
        need(Fraction(row['lower_exact']) == lo and Fraction(row['upper_exact']) == hi, 'shared-source contrast bound mismatch')
        need(int(row['distinct_source_groups']) == groups and int(row['unknown_source_groups']) == unknown, 'source-group count mismatch')
        need(row['preferred'] == (left if lo>0 else right if hi<0 else ''), 'source-group preference mismatch')
    need(pair_keys == {(lang,name,left,right) for lang in LANGUAGES+('combined',)
        for name in WEIGHTS for left,right in itertools.combinations(SCHEMES,2)},'source-group contrast coverage mismatch')
    shared = sum(not g['valid'] and len(g['positive_schemes'])>1 for g in by_source.values())
    need(shared == summary['source_group_sharing']['unknown_positive_source_groups_shared_across_carriers'], 'cross-carrier source sharing mismatch')
    paper_summary = json.loads((directory/'paper_summary.json').read_text(encoding='utf-8'))
    for outcome in paper_summary['mixtures']:
        subset = [r for r in mixtures if r['language'] == 'combined' and r['mixture'] == outcome['mixture']]
        winners = [r['scheme'] for r in subset if Fraction(r['joint_lower_exact']) >
                   max(Fraction(o['joint_upper_exact']) for o in subset if o['scheme'] != r['scheme'])]
        need(winners == outcome['certified_combined_winners'], 'paper winner differs from exact endpoint comparison')
    return dict(status='PASS', source_configurations_verified=len(seen),
        distinct_stored_sources_verified=len(sources), python_ast_proofs_revalidated=proof_count,
        source_bound_execution_links=432, family_summaries_verified=len(families),
        mixture_summaries_verified=len(mixtures), shared_source_contrasts_verified=len(pairwise),
        unknown_positive_sources_shared_across_carriers=shared, task_program_executions=0,
        scope='stored source identity, declared extraction, exact detector decisions, restricted AST proofs, label linkage, and weighted joint bounds')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=HERE/'results/revision-source-joint')
    parser.add_argument('--results', type=Path, default=HERE/'results/revision-reproduction')
    args = parser.parse_args()
    print(json.dumps(verify(args.evidence,args.results), indent=2, sort_keys=True))
