"""Exact finite-ledger bounds and label-blind source-contract audit schedules.

Only the loader and SealedOracle see saved validity labels. PublicRow, PairState
and AuditPolicy deliberately omit labels, measured execution time, observation
contents and measured invocation counts. A policy may use disclosed labels via
PairState. The command-line experiment retrospectively discloses saved labels;
it does not execute candidate programs. All planning costs are declared suites.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from fractions import Fraction
import gzip
import hashlib
import io
from itertools import combinations
import json
import os
from pathlib import Path
import re
import time
from typing import Callable, Iterable, Mapping

VARIANTS = ('stock', 's1', 's4', 's1_s4')
ALIASES = {'stock': 'stock', 's1': 's1', 's1_literal_predecessor': 's1',
           's4': 's4', 's4_return_boundary': 's4', 's1_s4': 's1_s4'}
CERTIFICATES = {'left_strict', 'right_strict', 'tie'}
SHA = re.compile(r'^[0-9a-f]{64}$')


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':')).encode('utf-8')


def digest(value: bytes):
    return hashlib.sha256(value).hexdigest()


def source_contract_id(reference_sha256, candidate_sha256, contract_sha256):
    return digest(canonical_bytes(dict(reference_sha256=reference_sha256,
                                       candidate_sha256=candidate_sha256,
                                       contract_sha256=contract_sha256)))


def relation(lower, upper):
    return ('left_strict' if lower > 0 else 'right_strict' if upper < 0
            else 'tie' if lower == upper == 0 else 'unresolved')


def parse_validity(value):
    if type(value) is bool:
        return value
    if type(value) is int and value in (0, 1):
        return bool(value)
    if value == 'supported':
        return True
    if value == 'contradicted':
        return False
    if value is None or value == 'unavailable':
        return None
    raise ValueError(f'unrecognized validity label {value!r}')


def safe_path(root: Path, relative: str):
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValueError('asset paths must be relative to the declared asset root')
    result = (root / candidate).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError('asset path escapes declared root')
    return result


@dataclass(frozen=True)
class PublicRow:
    dataset: str
    task_id: str
    key_id: str
    key_hex: str
    variant: str
    original_variant: str
    group: str
    detected: bool
    suite_cost: int
    input_index: int
    row_index: int

    @property
    def workload(self):
        return self.dataset, self.task_id, self.key_id, self.key_hex


@dataclass
class PublicLedger:
    rows: tuple[PublicRow, ...]
    # This metadata is for receiving/replay only, never passed to AuditPolicy.
    groups: dict[str, dict]
    inputs: list[dict]

    def scope(self, dataset=None):
        return tuple(r for r in self.rows if dataset is None or r.dataset == dataset)


class SealedOracle:
    """Sequential saved-label receiver; query is its only public data operation."""
    def __init__(self, labels: Mapping[str, bool | None]):
        self.__labels = dict(labels)
        self.requests: list[str] = []
        self.__requested = set()

    def query(self, identity):
        if identity in self.__requested:
            raise ValueError('a source-contract group was queried twice')
        self.requests.append(identity)
        self.__requested.add(identity)
        return self.__labels[identity]


def load_ledgers(inputs: Iterable[tuple[Path, Path]]):
    """Validate normalized identities/assets, then separate public and sealed data.

    Supported input labels are bool, integer 0/1, and supported/contradicted/
    unavailable. Unknown is not converted to false. An observed failure only
    admits false when the paired reference passed and the source/contract and
    observation identities have been checked. This receiver verifies the saved
    envelope; native reexecution is a separate experiment.
    """
    public, groups, sealed, metadata = [], {}, {}, []
    byte_cache, parsed_cache = {}, {}

    def checked_bytes(path, expected):
        if not isinstance(expected, str) or not SHA.fullmatch(expected):
            raise ValueError('invalid expected SHA-256')
        if path not in byte_cache:
            byte_cache[path] = path.read_bytes()
        content = byte_cache[path]
        if digest(content) != expected:
            raise ValueError(f'asset SHA-256 mismatch: {path}')
        return content

    def checked_json(path, expected, canonical=False):
        key = (path, expected, canonical)
        if key in parsed_cache:
            return parsed_cache[key]
        data = path.read_bytes() if canonical else checked_bytes(path, expected)
        if path.suffix == '.gz':
            data = gzip.decompress(data)
        value = json.loads(data)
        if canonical and digest(canonical_bytes(value)) != expected:
            raise ValueError(f'canonical JSON SHA-256 mismatch: {path}')
        parsed_cache[key] = value
        return value

    for input_index, (path, asset_root) in enumerate(inputs):
        path, asset_root = path.resolve(), asset_root.resolve()
        raw_bytes = path.read_bytes()
        records = json.loads(raw_bytes)
        if not isinstance(records, list) or not records:
            raise ValueError('each normalized ledger must be a nonempty row list')
        reference_index = {}
        ref_file = asset_root / 'references.json'
        if ref_file.exists():
            reference_index = {(r['task_id'], r['reference_sha256'], r['contract_sha256']): r
                               for r in json.loads(ref_file.read_text())}
        datasets = set()
        for row_index, record in enumerate(records):
            dataset, task, key = record['dataset'], record['task_id'], record['key_id']
            datasets.add(dataset)
            original_variant = record['variant']
            if original_variant not in ALIASES:
                raise ValueError(f'unrecognized variant {original_variant}')
            variant = ALIASES[original_variant]
            if type(record['detected']) is not bool:
                raise ValueError('detected must be an observed Boolean')
            if type(record.get('suite_cost')) is not int or record['suite_cost'] != 1:
                raise ValueError('this equal-suite experiment requires suite_cost=1')
            hashes = [record[field] for field in
                      ('reference_sha256', 'candidate_sha256', 'contract_sha256')]
            if any(not isinstance(h, str) or not SHA.fullmatch(h) for h in hashes):
                raise ValueError('missing or malformed identity hash')
            reference_hash, candidate_hash, contract_hash = hashes
            identity = source_contract_id(*hashes)
            if identity != record['source_contract_sha256']:
                raise ValueError('source-contract identity omits or changes a declared component')
            source_path = safe_path(asset_root, record['source_path'])
            reference_record = reference_index.get((task, reference_hash, contract_hash), {})
            reference_relative = record.get('reference_path', reference_record.get(
                'source_path', f'sources/{reference_hash}.py'))
            reference_path = safe_path(asset_root, reference_relative)
            contract_relative = record.get('contract_path', f'contracts/{contract_hash}.json')
            contract_path = safe_path(asset_root, contract_relative)
            checked_bytes(source_path, candidate_hash)
            checked_bytes(reference_path, reference_hash)
            contract = checked_json(contract_path, contract_hash, canonical=True)
            if ('reference_source_sha256' in contract
                    and contract['reference_source_sha256'] != reference_hash):
                raise ValueError('contract reference does not match group identity')
            observation_path = safe_path(asset_root, record['observation_path'])
            observation = checked_json(observation_path, record['observation_sha256'])
            if 'semantic_observation_sha256' in record:
                if digest(canonical_bytes(observation)) != record['semantic_observation_sha256']:
                    raise ValueError('semantic observation hash mismatch')
            reference_observation_relative = record.get(
                'reference_observation_path', reference_record.get('observations_path'))
            reference_observation_hash = record.get(
                'reference_observation_sha256', reference_record.get('observations_sha256'))
            if not reference_observation_relative or not reference_observation_hash:
                raise ValueError('paired reference observation is required')
            reference_observation_path = safe_path(asset_root, reference_observation_relative)
            reference_observation = checked_json(reference_observation_path, reference_observation_hash)
            if reference_observation.get('status') != 'passed' or record.get('reference_status') != 'passed':
                raise ValueError('a supported reference suite is required for admission')
            if record.get('candidate_status') != observation.get('status'):
                raise ValueError('row candidate status disagrees with saved observation')
            label = parse_validity(record['validity_label'])
            if label is True and observation.get('status') != 'passed':
                raise ValueError('supported label requires a passing candidate suite')
            if label is False and observation.get('status') != 'failed':
                raise ValueError('contradicted label requires a failing candidate suite')
            if 'joint' in record and label is not None:
                if type(record['joint']) not in (bool, int) or record['joint'] not in (0, 1):
                    raise ValueError('malformed stored joint field')
                if bool(record['joint']) != (label and record['detected']):
                    raise ValueError('stored joint field disagrees with independent reconstruction')
            if candidate_hash == reference_hash and label is False:
                raise ValueError('identical source/reference has inconsistent admitted outcomes under one contract')
            if identity in sealed and sealed[identity] is not None and label is not None:
                if sealed[identity] != label:
                    raise ValueError('one source-contract identity has inconsistent validity labels')
            if identity not in sealed or sealed[identity] is None:
                sealed[identity] = label
            group_info = dict(source_contract_sha256=identity, reference_sha256=reference_hash,
                              candidate_sha256=candidate_hash, contract_sha256=contract_hash,
                              dataset=dataset, task_id=task, suite_cost=1,
                              input_index=input_index, representative_row_index=row_index,
                              source_path=record['source_path'], reference_path=reference_relative,
                              contract_path=contract_relative, observation_path=record['observation_path'],
                              reference_observation_path=reference_observation_relative)
            groups.setdefault(identity, group_info)
            public.append(PublicRow(dataset, task, key, record['key_hex'], variant,
                                    original_variant, identity, record['detected'], 1,
                                    input_index, row_index))
        metadata.append(dict(rows_path=os.path.relpath(path, Path.cwd()),
                             asset_root=os.path.relpath(asset_root, Path.cwd()), rows_sha256=digest(raw_bytes),
                             rows=len(records), datasets=sorted(datasets)))
    result = PublicLedger(tuple(public), groups, metadata)
    validate_workload(result.rows)
    return result, sealed


def validate_workload(rows):
    by_version = {v: set() for v in VARIANTS}
    for row in rows:
        if row.workload in by_version[row.variant]:
            raise ValueError('duplicate attempted workload/version row')
        by_version[row.variant].add(row.workload)
    if any(by_version[v] != by_version[VARIANTS[0]] for v in VARIANTS):
        raise ValueError('versions must have the same attempted workload and key support')


class ScoreState:
    """Integer count model; common workload denominator cancels from C."""
    def __init__(self, coefficients: Mapping[str, tuple[int, int]]):
        if any(type(a) is not int or type(b) is not int or not 0 <= a <= b
               for a, b in coefficients.values()):
            raise ValueError('coefficient counts require integers 0 <= detected <= rows')
        self.coefficients = {g: tuple(c) for g, c in coefficients.items() if c[1]}
        self.unknown = set(self.coefficients)
        self.joint = self.valid = 0
        self.unknown_joint = sum(a for a, b in self.coefficients.values())
        self.unknown_valid = sum(b for a, b in self.coefficients.values())
        self.buckets = defaultdict(lambda: [0, 0])
        self.ratios = {}
        for g, (a, b) in self.coefficients.items():
            ratio = Fraction(a, b)
            self.ratios[g] = ratio
            self.buckets[ratio][0] += a
            self.buckets[ratio][1] += b
        self.sorted_ratios = sorted(self.buckets)

    def reveal(self, group, label):
        if label is None or group not in self.unknown:
            return
        if type(label) is not bool:
            raise ValueError('disclosed label must be Boolean or unavailable')
        a, b = self.coefficients[group]
        self.unknown.remove(group)
        self.unknown_joint -= a
        self.unknown_valid -= b
        self.buckets[self.ratios[group]][0] -= a
        self.buckets[self.ratios[group]][1] -= b
        if label:
            self.joint += a
            self.valid += b

    def conditional(self):
        # Whole equal-ratio buckets may be selected together: within one bucket,
        # adding mass changes the running ratio monotonically toward its ratio.
        # Hence checking its endpoints is exact even for binary source groups.
        def extremum(reverse):
            n, b = self.joint, self.valid
            best = (n, b) if b else None
            ratios = reversed(self.sorted_ratios) if reverse else self.sorted_ratios
            for ratio in ratios:
                a_add, b_add = self.buckets[ratio]
                if b_add == 0:
                    continue
                n, b = n + a_add, b + b_add
                if best is None or ((n * best[1] > best[0] * b) if reverse
                                    else (n * best[1] < best[0] * b)):
                    best = (n, b)
            return Fraction(*best) if best else None
        lower, upper = extremum(False), extremum(True)
        return dict(lower=lower, upper=upper, defined_all=self.valid > 0,
                    defined_some=self.valid + self.unknown_valid > 0)


class LinearState:
    def __init__(self, coefficients, constant=0):
        self.coefficients = dict(coefficients)
        self.unknown = set(coefficients)
        self.lower = constant + sum(min(0, c) for c in coefficients.values())
        self.upper = constant + sum(max(0, c) for c in coefficients.values())

    def reveal(self, group, label):
        if label is None or group not in self.unknown:
            return
        c = self.coefficients[group]
        self.lower += c * label - min(0, c)
        self.upper += c * label - max(0, c)
        self.unknown.remove(group)


def independent_conditional(left, right):
    if not left['defined_some'] or not right['defined_some']:
        return dict(lower=None, upper=None, decision='undefined_everywhere_for_at_least_one_side',
                    relation_on_defined=None)
    lower = left['lower'] - right['upper']
    upper = left['upper'] - right['lower']
    rel = relation(lower, upper)
    decision = rel if left['defined_all'] and right['defined_all'] else 'undefined_possible'
    return dict(lower=lower, upper=upper, decision=decision, relation_on_defined=rel)


class PairState:
    """Public coefficients and already disclosed labels for one comparison."""
    def __init__(self, left_coefficients, right_coefficients, denominator):
        if denominator <= 0:
            raise ValueError('a nonempty common workload is required')
        self.denominator = denominator
        self.left = ScoreState(left_coefficients)
        self.right = ScoreState(right_coefficients)
        if self.left.unknown_valid != denominator or self.right.unknown_valid != denominator:
            raise ValueError('each version must have the declared common workload mass')
        self.groups = set(self.left.coefficients) | set(self.right.coefficients)
        zero = (0, 0)
        self.pairs = {g: (self.left.coefficients.get(g, zero),
                          self.right.coefficients.get(g, zero)) for g in self.groups}
        self.joint = LinearState({g: l[0] - r[0] for g, (l, r) in self.pairs.items()})
        self.behavior = LinearState({g: l[1] - r[1] for g, (l, r) in self.pairs.items()})
        self.different = {g for g, (l, r) in self.pairs.items() if l != r}
        self.attempted = set()
        self.admitted = {}
        self.margin = None
        self._initialize_common_remainder()

    def _initialize_common_remainder(self):
        if self.margin is not None or self.different:
            return
        nl, al, nr, ar = self.left.joint, self.left.valid, self.right.joint, self.right.valid
        coefficients = {g: (nl - nr) * self.pairs[g][0][1]
                         + (ar - al) * self.pairs[g][0][0]
                        for g in self.groups - set(self.admitted)}
        self.margin = LinearState(coefficients, nl * ar - nr * al)

    def reveal(self, group, label):
        if group not in self.groups or group in self.attempted:
            raise ValueError('query must name an unattempted public group')
        if label is not None and type(label) is not bool:
            raise ValueError('disclosed label must be Boolean or unavailable')
        self.attempted.add(group)
        if label is None:
            return
        self.admitted[group] = label
        self.left.reveal(group, label)
        self.right.reveal(group, label)
        self.joint.reveal(group, label)
        self.behavior.reveal(group, label)
        if self.margin is not None:
            self.margin.reveal(group, label)
        self.different.discard(group)
        self._initialize_common_remainder()

    def common_conditional(self):
        if self.margin is None:
            raise ValueError('coefficient-different groups must be resolved first')
        defined_all = self.left.valid > 0 and self.right.valid > 0
        unknown = self.margin.unknown
        defined_some = defined_all or bool(unknown)
        if not defined_some:
            return dict(route='exact_common_remainder', lower=None, upper=None,
                        decision='undefined_everywhere_for_at_least_one_side', relation_on_defined=None)
        lower, upper = self.margin.lower, self.margin.upper
        if not defined_all:
            # A positive common group must be selected. All union groups here
            # have equal positive mass on both sides; zero-mass rows are absent.
            coefficients = [self.margin.coefficients[g] for g in unknown]
            if not any(c < 0 for c in coefficients):
                lower += min(coefficients)
            if not any(c > 0 for c in coefficients):
                upper += max(coefficients)
        rel = relation(lower, upper)
        return dict(route='exact_common_remainder', lower=lower, upper=upper,
                    decision=rel if defined_all else 'undefined_possible', relation_on_defined=rel)

    def snapshot(self):
        lc, rc = self.left.conditional(), self.right.conditional()
        independent_c = independent_conditional(lc, rc)
        coupled_c = (self.common_conditional() if self.margin is not None
                     else dict(route='individual_intervals_sufficient_only', **independent_c))
        independent_j = (self.left.joint - self.right.joint - self.right.unknown_joint,
                         self.left.joint + self.left.unknown_joint - self.right.joint)
        independent_a = (self.left.valid - self.right.valid - self.right.unknown_valid,
                         self.left.valid + self.left.unknown_valid - self.right.valid)
        return dict(
            left_joint=[self.left.joint, self.left.joint + self.left.unknown_joint],
            left_valid=[self.left.valid, self.left.valid + self.left.unknown_valid], left_C=lc,
            right_joint=[self.right.joint, self.right.joint + self.right.unknown_joint],
            right_valid=[self.right.valid, self.right.valid + self.right.unknown_valid], right_C=rc,
            independent_J=dict(lower=independent_j[0], upper=independent_j[1], decision=relation(*independent_j)),
            coupled_J=dict(lower=self.joint.lower, upper=self.joint.upper, decision=relation(self.joint.lower, self.joint.upper)),
            independent_A=dict(lower=independent_a[0], upper=independent_a[1], decision=relation(*independent_a)),
            coupled_A=dict(lower=self.behavior.lower, upper=self.behavior.upper, decision=relation(self.behavior.lower, self.behavior.upper)),
            independent_C=independent_c, coupled_C=coupled_c,
            coefficient_different_unresolved=len(self.different), groups_resolved=len(self.admitted))


class AuditPolicy:
    """Query ordering from public coefficients and already disclosed state only."""
    def __init__(self, name, state: PairState, configuration_order=()):
        self.name = name
        self.phase_two = None
        groups = state.groups - state.attempted
        if name == 'configuration_first':
            self.order = [g for g in dict.fromkeys(configuration_order) if g in groups]
            if set(self.order) != groups:
                raise ValueError('configuration order must cover exactly the pair groups')
        elif name.startswith('hash_'):
            seed = int(name.split('_')[1])
            self.order = sorted(groups, key=lambda g: (digest(f'MarkValidity-natural-audit-v1/{seed}/{g}'.encode()), g))
        elif name in ('joint_width_per_suite', 'behavior_width_per_suite'):
            coordinate = 0 if name.startswith('joint') else 1
            self.order = sorted(groups, key=lambda g: (-abs(state.pairs[g][0][coordinate] - state.pairs[g][1][coordinate]), g))
        elif name == 'conditional_differences_first':
            self.order = sorted(state.different, key=lambda g: (
                -sum(abs(l - r) for l, r in zip(*state.pairs[g])), g))
        else:
            raise ValueError(f'unknown policy {name}')
        self.index = 0
        self.phase_two_index = 0

    def next_group(self, state: PairState):
        if self.index < len(self.order):
            group = self.order[self.index]
            self.index += 1
            return group
        if self.name != 'conditional_differences_first':
            return None
        if self.phase_two is None:
            remaining = state.groups - state.attempted
            if state.margin is not None:
                self.phase_two = sorted(remaining, key=lambda g: (-abs(state.margin.coefficients[g]), g))
            else:
                # An unavailable coefficient-difference label cannot be guessed.
                # Common-remainder inference remains unavailable; try other
                # public groups in deterministic identity order.
                self.phase_two = sorted(remaining)
        if self.phase_two_index >= len(self.phase_two):
            return None
        group = self.phase_two[self.phase_two_index]
        self.phase_two_index += 1
        return group


def pair_coefficients(rows, left, right):
    counts = {left: defaultdict(lambda: [0, 0]), right: defaultdict(lambda: [0, 0])}
    configuration_order = []
    denominator = Counter()
    for row in rows:
        if row.variant not in counts:
            continue
        pair = counts[row.variant][row.group]
        pair[0] += row.detected
        pair[1] += 1
        denominator[row.variant] += 1
        configuration_order.append(row.group)
    if denominator[left] != denominator[right] or denominator[left] == 0:
        raise ValueError('pair workloads must have equal nonzero size')
    return (dict(counts[left]), dict(counts[right]), denominator[left],
            list(dict.fromkeys(configuration_order)))


def serial(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {str(k): serial(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serial(v) for v in value]
    return value


TRACE_FIELDS = ['step', 'group_index', 'received_label', 'groups_resolved',
                'coefficient_different_unresolved']
for _side in ('left', 'right'):
    TRACE_FIELDS += [f'{_side}_J_lower_count', f'{_side}_J_upper_count',
                     f'{_side}_A_lower_count', f'{_side}_A_upper_count',
                     f'{_side}_C_lower', f'{_side}_C_upper', f'{_side}_C_defined_all']
for _method in ('independent', 'coupled'):
    for _metric in ('J', 'A'):
        TRACE_FIELDS += [f'{_method}_{_metric}_lower', f'{_method}_{_metric}_upper',
                         f'{_method}_{_metric}_decision']
TRACE_FIELDS += ['independent_C_lower', 'independent_C_upper', 'independent_C_decision',
                 'coupled_C_separate_gap_lower', 'coupled_C_separate_gap_upper',
                 'coupled_C_margin_lower', 'coupled_C_margin_upper', 'coupled_C_decision',
                 'coupled_C_route', 'coupled_C_relation_on_defined']


def trace_row(step, selected, label, snapshot):
    result = [step, selected if selected is not None else '',
              '' if selected is None else '?' if label is None else int(label),
              snapshot['groups_resolved'], snapshot['coefficient_different_unresolved']]
    for side in ('left', 'right'):
        c = snapshot[f'{side}_C']
        result += snapshot[f'{side}_joint'] + snapshot[f'{side}_valid']
        result += ['' if c['lower'] is None else str(c['lower']),
                   '' if c['upper'] is None else str(c['upper']), int(c['defined_all'])]
    for method in ('independent', 'coupled'):
        for metric in ('J', 'A'):
            part = snapshot[f'{method}_{metric}']
            result += [str(part['lower']), str(part['upper']), part['decision']]
    independent = snapshot['independent_C']
    result += ['' if independent['lower'] is None else str(independent['lower']),
               '' if independent['upper'] is None else str(independent['upper']), independent['decision']]
    coupled = snapshot['coupled_C']
    endpoints = ['' if coupled['lower'] is None else str(coupled['lower']),
                 '' if coupled['upper'] is None else str(coupled['upper'])]
    # Never mix a rate difference and a cross-product margin in one CSV column.
    result += (['', ''] + endpoints if coupled['route'] == 'exact_common_remainder'
               else endpoints + ['', ''])
    result += [coupled['decision'], coupled['route'], coupled['relation_on_defined']]
    return result


def run_schedule(coefficients, policy_name, oracle: SealedOracle, group_index,
                 trace_path: Path | None = None, initial_labels=None):
    left, right, denominator, configuration_order = coefficients
    state = PairState(left, right, denominator)
    for identity, initial_label in sorted((initial_labels or {}).items()):
        if identity in state.groups:
            state.reveal(identity, initial_label)
    policy = AuditPolicy(policy_name, state, configuration_order)
    first = {}
    schedule = []
    trace_file = None
    if trace_path is not None:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        binary = gzip.GzipFile(filename=str(trace_path), mode='wb', mtime=0)
        trace_file = io.TextIOWrapper(binary, encoding='utf-8', newline='')
        writer = csv.writer(trace_file)
        writer.writerow(TRACE_FIELDS)
    snapshot = state.snapshot()
    try:
        step, selected, label = 0, None, None
        while True:
            if trace_file is not None:
                writer.writerow(trace_row(step, group_index[selected] if selected else None, label, snapshot))
            for method in ('independent', 'coupled'):
                for metric in ('J', 'A', 'C'):
                    key = f'{method}_{metric}'
                    if key not in first and snapshot[key]['decision'] in CERTIFICATES:
                        first[key] = dict(suite_queries=step, groups_resolved=snapshot['groups_resolved'],
                                          decision=snapshot[key]['decision'], snapshot=serial(snapshot),
                                          schedule_prefix_sha256=digest(canonical_bytes(schedule)))
            selected = policy.next_group(state)
            if selected is None:
                break
            # Selection is complete before the sealed oracle is called.
            label = oracle.query(selected)
            state.reveal(selected, label)
            schedule.append(group_index[selected])
            step += 1
            snapshot = state.snapshot()
    finally:
        if trace_file is not None:
            trace_file.close()
    result = dict(policy=policy_name, denominator=denominator, suite_queries=len(schedule),
                  initially_admitted_groups=len(set(initial_labels or {}) & state.groups),
                  labels_admitted=len(state.admitted), schedule=schedule,
                  schedule_sha256=digest(canonical_bytes(schedule)), first_certificates=first,
                  final_snapshot=serial(snapshot))
    if trace_path is not None:
        result['trace_file'] = trace_path.name
        result['trace_sha256'] = digest(trace_path.read_bytes())
    return result


def complete_scores(rows, labels):
    """For reporting only; callers never pass this result to policy selection."""
    result = {}
    for variant in VARIANTS:
        selected = [row for row in rows if row.variant == variant]
        unknown = sum(labels[row.group] is None for row in selected)
        valid = sum(labels[row.group] is True for row in selected)
        joint = sum(labels[row.group] is True and row.detected for row in selected)
        result[variant] = dict(rows=len(selected), detected=sum(row.detected for row in selected),
                               valid=valid, joint=joint, unavailable_rows=unknown,
                               A=str(Fraction(valid, len(selected))) if not unknown else None,
                               J=str(Fraction(joint, len(selected))) if not unknown else None,
                               C=str(Fraction(joint, valid)) if valid and not unknown else None,
                               C_undefined=not unknown and valid == 0)
    return result


def write_json(path, value):
    path.write_text(json.dumps(serial(value), indent=2, ensure_ascii=False) + '\n')


def analyze(ledger: PublicLedger, labels, output: Path, include_pool=True, hash_orders=16,
            initialization='reference_identity_known'):
    if initialization not in ('reference_identity_known', 'all_withheld'):
        raise ValueError('unknown initialization mode')
    initial_labels = ({g: True for g, info in ledger.groups.items()
                       if info['candidate_sha256'] == info['reference_sha256']}
                      if initialization == 'reference_identity_known' else {})
    if output.exists():
        raise ValueError('analysis output must be a new directory')
    output.mkdir(parents=True)
    identities = sorted(ledger.groups)
    group_index = {g: i for i, g in enumerate(identities)}
    group_records = [dict(index=i, **ledger.groups[g]) for i, g in enumerate(identities)]
    write_json(output / 'group_index.json', group_records)
    policies = ['configuration_first'] + [f'hash_{i:02d}' for i in range(hash_orders)] + [
        'joint_width_per_suite', 'behavior_width_per_suite', 'conditional_differences_first']
    datasets = sorted({row.dataset for row in ledger.rows})
    scopes = [(dataset.lower().replace('_sanitized', ''), ledger.scope(dataset)) for dataset in datasets]
    if include_pool and len(datasets) > 1:
        scopes.append(('pooled', ledger.rows))
    scope_reports, comparison_reports, summary_rows = {}, {}, []
    start = time.perf_counter()
    for scope, rows in scopes:
        validate_workload(rows)
        scope_reports[scope] = dict(rows=len(rows), workload_per_version=len(rows) // len(VARIANTS),
                                    unique_source_contract_groups=len({r.group for r in rows}),
                                    reference_identity_known_groups=len({r.group for r in rows} & set(initial_labels)),
                                    additional_unique_groups_after_reference=len({r.group for r in rows} - set(initial_labels)),
                                    tasks=len({(r.dataset, r.task_id) for r in rows}),
                                    complete_scores=complete_scores(rows, labels))
        for left, right in combinations(VARIANTS, 2):
            coefficients = pair_coefficients(rows, left, right)
            initial = PairState(*coefficients[:3])
            for identity, label in sorted(initial_labels.items()):
                if identity in initial.groups:
                    initial.reveal(identity, label)
            case = f'{scope}__{left}__{right}'
            report = dict(scope=scope, left=left, right=right, denominator=coefficients[2],
                          full_row_suite_requests=2 * coefficients[2],
                          full_unique_group_suite_requests=len(initial.groups),
                          initialization=initialization,
                          reference_identity_known_groups=len(initial.admitted),
                          full_unique_group_suites_after_reference=len(initial.groups) - len(initial.admitted),
                          full_row_suites_after_reference=sum(r.group not in initial_labels for r in rows if r.variant in (left, right)),
                          J_gap_influential_groups=sum(initial.joint.coefficients[g] != 0 for g in initial.joint.unknown),
                          A_gap_influential_groups=sum(initial.behavior.coefficients[g] != 0 for g in initial.behavior.unknown),
                          C_coefficient_different_groups=len(initial.different),
                          initial_snapshot=serial(initial.snapshot()), schedules={})
            for policy in policies:
                oracle = SealedOracle(labels)
                path = output / 'traces' / f'{case}__{policy}.csv.gz'
                result = run_schedule(coefficients, policy, oracle, group_index, path, initial_labels)
                report['schedules'][policy] = result
                for metric in ('J', 'A', 'C'):
                    entry = dict(case=case, scope=scope, left=left, right=right,
                                 denominator=coefficients[2], policy=policy, metric=metric,
                                 full_row_suites=2 * coefficients[2], full_unique_group_suites=len(initial.groups),
                                 initialization=initialization, reference_identity_known_groups=len(initial.admitted),
                                 full_unique_group_suites_after_reference=report['full_unique_group_suites_after_reference'],
                                 full_row_suites_after_reference=report['full_row_suites_after_reference'],
                                 J_gap_influential_groups=report['J_gap_influential_groups'],
                                 A_gap_influential_groups=report['A_gap_influential_groups'],
                                 C_coefficient_different_groups=report['C_coefficient_different_groups'])
                    for method in ('independent', 'coupled'):
                        cert = result['first_certificates'].get(f'{method}_{metric}')
                        entry[f'{method}_first_suites'] = cert['suite_queries'] if cert else ''
                        entry[f'{method}_decision'] = cert['decision'] if cert else result['final_snapshot'][f'{method}_{metric}']['decision']
                    summary_rows.append(entry)
            comparison_reports[case] = report
            print(f'{case}: {len(initial.groups)} groups, J influential {report["J_gap_influential_groups"]}, C differences {report["C_coefficient_different_groups"]}', flush=True)
    write_json(output / 'scope_scores.json', scope_reports)
    write_json(output / 'comparisons.json', comparison_reports)
    with (output / 'comparison_summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)
    source = Path(__file__).resolve()
    manifest = dict(schema='markvalidity-natural-partial-evidence-v2', inputs=ledger.inputs,
                    analysis_source_sha256=digest(source.read_bytes()), total_rows=len(ledger.rows),
                    total_source_contract_groups=len(identities), policies=policies,
                    initialization=initialization, initially_admitted_reference_identity_groups=len(initial_labels),
                    input_path_base_from_analysis=os.path.relpath(Path.cwd(), output.resolve()),
                    scope_order=[name for name, _ in scopes], variants=VARIANTS,
                    original_variant_map=ALIASES, seconds=time.perf_counter() - start,
                    cost_unit='one candidate execution of its full declared source-contract suite',
                    cost_scope='Additional candidate suites after source generation, detector observation and paired reference qualification. Reference setup is common and excluded. Exact candidate=reference source identities reuse the admitted reference at zero additional candidate cost in the primary initialization.',
                    design='Retrospective disclosure of saved labels; no new native suites executed by this script.',
                    validity='Passing/failing the exact finite original suite with the bound reference, initialization and runtime contract. No unlimited equivalence claim.',
                    weights='Each attempted task-key configuration has equal weight within its scope. Pooled scope weights all task-key rows equally, not corpora equally.',
                    policies_label_blind='Public coefficients, identities, declared suite_cost=1 and already disclosed labels only. No unrevealed validity, elapsed time or measured function/test-entry counts enter selection.',
                    trace_units={'J_and_A': 'integer difference or score counts; divide by the case denominator for rates',
                                 'individual_C': 'exact rational conditional rate on positive-valid-mass completions',
                                 'independent_C': 'exact separately attainable rate endpoints, used as sufficient comparison bounds',
                                 'coupled_C': 'when route=exact_common_remainder: cross-product margin in squared count units, NOT the numeric conditional-rate difference; otherwise same sufficient interval as independent_C'},
                    certificate_meaning='Strict or tie decision holds for every completion of remaining source-group labels and, for C, both denominators are positive for every completion.',
                    known_label_reuse='Both independent and coupled methods receive exactly the same queried group labels propagated within and across versions. Their differences isolate unresolved-label coupling from memoization.',
                    stopping='First certificates are recorded along each schedule. Full suffix disclosure is retained only for retrospective matched-budget comparison; an online receiver stops at its chosen certificate.',
                    limitations=['General coupled C difference bounds are not claimed; comparison is sharp after all unequal coefficient-pair groups resolve.',
                                 'Unit suite costs make width and width/cost the same ordering; no measured elapsed-cost advantage or earliest-certificate optimality is claimed.',
                                 'Hash orders describe sensitivity on these fixed ledgers, not a population confidence interval.'])
    write_json(output / 'manifest.json', manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', nargs=2, action='append', metavar=('ROWS_JSON', 'ASSET_ROOT'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-pool', action='store_true')
    parser.add_argument('--hash-orders', type=int, default=16)
    parser.add_argument('--initialization', choices=('reference_identity_known', 'all_withheld'),
                        default='reference_identity_known')
    args = parser.parse_args()
    if not 1 <= args.hash_orders <= 100:
        parser.error('--hash-orders must be between 1 and 100')
    loaded, labels = load_ledgers((Path(p), Path(root)) for p, root in args.ledger)
    print(json.dumps(analyze(loaded, labels, args.output, not args.no_pool, args.hash_orders, args.initialization), indent=2))


if __name__ == '__main__':
    main()
