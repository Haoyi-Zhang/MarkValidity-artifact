"""Three-way semantic evidence status for the owned Python task registry.

A restricted proof miss is unavailable evidence, not a failed program.
Syntax failure or an admitted complete-domain execution mismatch contradicts
bounded validity. Supplied execution records must belong to the exact source,
receiver task, domain and runtime. This is an evidence receiver, not remote
execution attestation: the caller trusts the declared execution producer.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import platform

from .benchmark import render_program
from .observations import (FRESH_MODULE_INITIALIZATION_ID,
                           LEGACY_OBSERVATION_RULE_ID,
                           V2_OBSERVATION_RULE_ID,
                           observe_python_fresh,
                           read_canonical_observation)
from .source_admission import AdmissionError, admit_python
from .tasks import TASK_BY_NAME, domain_cases

# The source-joint files retain the identifier of their original observations.
# Newly collected BoundedExecution records use the tagged v2 contract below;
# changing a constant must never silently relabel archived execution evidence.
OBSERVATION_RULE_ID = LEGACY_OBSERVATION_RULE_ID


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def runtime_id():
    return platform.python_implementation()+' '+platform.python_version()


def receiver_contract(task):
    if type(task) is not str or task not in TASK_BY_NAME:
        raise ValueError('unknown receiver task')
    source = render_program(TASK_BY_NAME[task].python_reference,'python',None)
    cases = domain_cases(task)
    domain_hash = digest(json.dumps(cases,ensure_ascii=False,separators=(',',':')))
    return source,cases,domain_hash


@dataclass(frozen=True)
class BoundedExecution:
    task: str
    candidate_source: str
    reference_sha256: str
    domain_sha256: str
    runtime: str
    observation_rule: str
    initialization_rule: str
    outputs: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceStatus:
    status: str
    basis: str
    source_sha256: str
    reason: str
    first_mismatch_index: int | None = None
    observed_bits: dict[int,int] | None = None


def collect_owned_python_execution(task, source):
    """Execute a trusted, terminating owned example on the complete task domain.

    This helper is for the local diagnostic/test harness. It is not a sandbox
    for running untrusted arbitrary programs and is never called implicitly by
    the static source-joint analysis.
    """
    reference,cases,domain_hash = receiver_contract(task)
    if type(source) is not str:
        raise ValueError('candidate source must be text')
    outputs,_ = observe_python_fresh(source,cases)
    return BoundedExecution(task,source,digest(reference),domain_hash,runtime_id(),
                            V2_OBSERVATION_RULE_ID,FRESH_MODULE_INITIALIZATION_ID,outputs)


def classify_python_evidence(task, source, execution=None):
    """Return supported, contradicted or unavailable; reject stale evidence."""
    if type(task) is not str or task not in TASK_BY_NAME:
        raise ValueError('unknown receiver task')
    if type(source) is not str or len(source.encode('utf-8'))>65536:
        raise ValueError('candidate source type or byte bound')
    source_hash = digest(source)
    if execution is not None:
        reference,cases,domain_hash = receiver_contract(task)
        if not isinstance(execution,BoundedExecution):
            raise ValueError('typed bounded execution record required')
        if execution.task != task or execution.candidate_source != source:
            raise ValueError('execution record belongs to a different task or exact source')
        if (execution.reference_sha256 != digest(reference) or execution.domain_sha256 != domain_hash
                or execution.runtime != runtime_id()
                or execution.observation_rule != V2_OBSERVATION_RULE_ID
                or execution.initialization_rule != FRESH_MODULE_INITIALIZATION_ID):
            raise ValueError('execution observation contract or runtime differs from the receiver')
        if type(execution.outputs) is not tuple or len(execution.outputs) != len(cases):
            raise ValueError('one execution observation for every frozen input is required')
        for value in execution.outputs:
            read_canonical_observation(value)
    try:
        compile(source,'<evidence-receiver>','exec')
    except (SyntaxError,ValueError,TypeError) as exc:
        return EvidenceStatus('contradicted','syntax-failure',source_hash,type(exc).__name__)
    if execution is not None:
        expected,_ = observe_python_fresh(reference,cases)
        mismatch = next((i for i,(left,right) in enumerate(zip(expected,execution.outputs))
                         if left != right),None)
        if mismatch is not None:
            return EvidenceStatus('contradicted','complete-bounded-execution',source_hash,
                'an admitted complete-domain observation differs from the receiver reference',mismatch)
        return EvidenceStatus('supported','complete-bounded-execution',source_hash,
            'all fresh-input observations match under the source-bound runtime contract')
    try:
        proof = admit_python(task,source)
    except AdmissionError as exc:
        return EvidenceStatus('unavailable','no-admitted-validity-evidence',source_hash,str(exc))
    return EvidenceStatus('supported','restricted-AST-erasure',source_hash,proof['basis'],
                          observed_bits=proof['observed'])
