"""Part B: render -> text-level attack -> extract -> detect, compared with the state model."""
from __future__ import annotations

import hashlib
import itertools

from common import SCHEMES, ATTACKS, LANGUAGES, Rule
from source_attacks import attack_source

from covewm.benchmark import (CarrierState, attacked_states, carrier_only_states, detector,
                              extract_carriers, payload_bits, render_program)
from covewm.tasks import TASK_BY_NAME

SEVERITIES = ("0.2", "0.4", "0.5", "0.6", "0.8")
PAYLOADS = tuple(range(16))
VARIANTS = {"format_whitespace": "format", "strip_statement_only": "strip", "rename_no_digit_split": "rename"}
PRIMARY_FIELDS = ("surviving_sites", "match_count", "detected")
SECONDARY_FIELDS = ("realized_bit_changes", "deletions", "p_value")
STRATA = {
    "carrier": ("scheme",),
    "attack": ("attack",),
    "severity": ("severity",),
    "language": ("language",),
    "carrier_x_attack": ("scheme", "attack"),
    "attack_x_severity": ("attack", "severity"),
    "carrier_x_attack_x_language": ("scheme", "attack", "language"),
    "carrier_x_attack_x_severity_x_language": ("scheme", "attack", "severity", "language"),
}


def sample(variants: bool = False):
    tasks = sorted(TASK_BY_NAME)
    if not variants:
        for scheme, attack, sev, task, lang, pi in itertools.product(SCHEMES, ATTACKS, SEVERITIES, tasks, LANGUAGES, PAYLOADS):
            yield "primary", scheme, attack, sev, task, lang, pi
    else:
        for variant, base in VARIANTS.items():
            for scheme, sev, task, lang, pi in itertools.product(SCHEMES, SEVERITIES, tasks, LANGUAGES, PAYLOADS):
                yield variant, scheme, base, sev, task, lang, pi


def python_syntax_ok(source: str) -> int:
    try:
        compile(source, "<source-attacked>", "exec")
        return 1
    except SyntaxError:
        return 0


def evaluate(rule: Rule, dense: dict, variant, scheme, attack, severity, task, language, payload_index):
    spec = TASK_BY_NAME[task]
    template = spec.python_reference if language == "python" else spec.javascript_reference
    expected = payload_bits(task, language, payload_index)
    states0 = carrier_only_states(expected, scheme)
    source0 = render_program(template, language, states0)
    source1, log = attack_source(source0, language, rule, scheme, attack, severity, task, payload_index, variant)
    extracted = extract_carriers(source1, language)
    observed = [CarrierState(i, s.channel, expected[i], extracted.get(i, 0), i in extracted, "source-extracted")
                for i, s in enumerate(states0)]
    src = detector(observed)
    src["p_value"] = f"{src['p_value']:.18g}"
    row = dense[(scheme, attack, severity, task, language, payload_index)]
    # Diagnostics only: state-model per-site prediction and its rendering.
    pstates, _ = attacked_states(expected, scheme, attack, float(severity), task, language, payload_index)
    predicted = {s.index: s.observed for s in pstates if s.present}
    bad_sites = sorted(i for i in range(24) if predicted.get(i, None) != extracted.get(i, None))
    state_render = render_program(template, language, pstates)
    rec = {"variant": variant, "scheme": scheme, "attack": attack, "severity": severity, "task": task,
           "language": language, "payload_index": payload_index,
           "selected_sites": len(log), "text_changing_ops": sum(1 for _, _, c in log if c),
           "op_log": ";".join(f"{k}:{op}:{int(c)}" for k, op, c in log),
           "source_sha256": hashlib.sha256(source1.encode("utf-8")).hexdigest()}
    for f in PRIMARY_FIELDS + SECONDARY_FIELDS:
        rec[f"source_{f}"] = src[f]
        rec[f"state_{f}"] = row[f]
    for f in PRIMARY_FIELDS + SECONDARY_FIELDS:
        rec[f"agree_{f}"] = int(str(src[f]) == str(row[f]))
    rec["agree_primary"] = int(all(rec[f"agree_{f}"] for f in PRIMARY_FIELDS))
    rec["agree_secondary"] = int(all(rec[f"agree_{f}"] for f in SECONDARY_FIELDS))
    rec["sites_agreeing_with_state"] = 24 - len(bad_sites)
    rec["disagreeing_sites"] = ";".join(map(str, bad_sites))
    rec["byte_identical_to_state_render"] = "" if attack == "format" else int(source1 == state_render)
    rec["python_syntax_ok"] = python_syntax_ok(source1) if language == "python" else ""
    rec["javascript_syntax_ok"] = ""  # filled by the Node batch
    rec["cause"] = classify(rec, log, pstates, predicted, extracted) if (bad_sites or not rec["agree_primary"]) else ""
    return rec, source1


def classify(rec, log, pstates, predicted, extracted) -> str:
    """Pre-declared cause categories for any per-site or primary disagreement."""
    state_ops = {s.index: s.operation for s in pstates if s.operation != "none"}
    text_ops = {k: op for k, op, _ in log if op not in ("format_padding", "format_whitespace")}
    if state_ops != text_ops:
        return "selection_or_eligibility_mismatch"
    if any(i in extracted and i not in predicted for i in range(24)):
        return "marker_statement_attribution_shift"
    if any(i in predicted and extracted.get(i) != predicted[i] for i in range(24)):
        return "extractor_does_not_recognize_transformed_form"
    return "other"


def strata_summary(records, fields=PRIMARY_FIELDS):
    out = {}
    for name, dims in STRATA.items():
        cells = {}
        for r in records:
            key = "|".join(str(r[d]) for d in dims)
            c = cells.setdefault(key, {"n": 0, "agree_primary": 0, **{f"agree_{f}": 0 for f in fields}})
            c["n"] += 1
            c["agree_primary"] += r["agree_primary"]
            for f in fields:
                c[f"agree_{f}"] += r[f"agree_{f}"]
        out[name] = dict(sorted(cells.items()))
    return out
