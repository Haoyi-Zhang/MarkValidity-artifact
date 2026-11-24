"""Versioned observations for trusted, terminating owned Python programs.

The fresh contract creates a new module namespace, function object, defaults,
and builtin mapping for every input. It does not isolate arbitrary programs
from the host: ambient-state dependence, imports with external state, tracing,
and resource observations are outside this owned-program execution contract.
"""
from __future__ import annotations

import builtins
import copy
import hashlib
import json


LEGACY_OBSERVATION_RULE_ID = 'covewm-return-or-exception-type-and-message-canonical-json-v1'
V2_OBSERVATION_RULE_ID = 'covewm-tagged-return-or-exception-type-and-message-canonical-json-v2'
FRESH_MODULE_INITIALIZATION_ID = 'covewm-fresh-module-instance-per-input-v1'


def canonical_observation(observation):
    """Serialize a tagged return or exception; reject an ambiguous record."""
    if type(observation) is not dict:
        raise ValueError('tagged observation object required')
    kind = observation.get('kind')
    if kind == 'return':
        if set(observation) != {'kind', 'value'}:
            raise ValueError('return observation requires exactly kind and value')
    elif kind == 'exception':
        if (set(observation) != {'kind', 'type', 'message'}
                or type(observation['type']) is not str
                or not observation['type']
                or type(observation['message']) is not str):
            raise ValueError('exception observation requires a type and message')
    else:
        raise ValueError('unknown observation kind')
    try:
        return json.dumps(observation, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError('execution observation is outside the finite JSON contract') from exc


def read_canonical_observation(text):
    if type(text) is not str:
        raise ValueError('canonical serialized execution observation required')
    try:
        observation = json.loads(text)
    except (TypeError, ValueError) as exc:
        raise ValueError('invalid serialized execution observation') from exc
    if canonical_observation(observation) != text:
        raise ValueError('noncanonical execution observation')
    return observation


def observe_python_fresh(source, cases):
    """Observe each input on a separately initialized module instance.

    Only the immutable compiled module code is reused. Each result is serialized
    before the next call, so a later mutation cannot alter an earlier record.
    The caller supplies owned terminating code whose behavior does not depend
    on ambient external state. This routine is not an untrusted-code sandbox.
    """
    if type(source) is not str:
        raise ValueError('candidate source must be text')
    code = compile(source, '<covewm-fresh-input>', 'exec')
    outputs = []
    digest = hashlib.sha256()
    for args in cases:
        namespace = {'__builtins__': vars(builtins).copy()}
        try:
            exec(code, namespace)
            function = namespace.get('solve')
            if not callable(function):
                raise ValueError('solve function missing')
            value = function(*copy.deepcopy(args))
            observation = {'kind': 'return', 'value': value}
        except Exception as exc:
            observation = {'kind': 'exception', 'type': type(exc).__name__,
                           'message': str(exc)}
        serialized = canonical_observation(observation)
        outputs.append(serialized)
        digest.update(serialized.encode('utf-8'))
        digest.update(b'\n')
    return tuple(outputs), digest.hexdigest()
