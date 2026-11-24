"""Native checks for the S4 return-token boundary, separate from benchmark results."""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def observe(source):
    try:
        code = compile(source, '<s4-boundary-control>', 'exec')
    except BaseException as exc:
        return {'status': 'compile_error', 'type': type(exc).__name__, 'message': str(exc)}
    namespace = {}
    try:
        exec(code, namespace)
        value = namespace['f']()
        return {'status': 'returned', 'type': type(value).__name__, 'value_repr': repr(value)}
    except BaseException as exc:
        return {'status': 'runtime_error', 'type': type(exc).__name__, 'message': str(exc)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vendor', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expect-preserved', action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(args.vendor.resolve()))
    from sew.rules.python_rules_extra import S4ReturnTuple
    from sew.rules.base import parse, apply_edits
    cases = [
        ('identifier', 'return(x, y)'),
        ('integer', 'return(1, 2)'),
        ('negative', 'return(-1, 2)'),
        ('decimal', 'return(.5, 2)'),
        ('string', 'return("x", 2)'),
        ('format_string', 'return(f"{x}", 2)'),
        ('raw_string', 'return(r"x", 2)'),
        ('byte_string', 'return(b"x", 2)'),
        ('unicode_identifier', 'return(λ, 2)'),
        ('existing_space', 'return (x, y)'),
        ('existing_tab', 'return\t(x, y)'),
        ('inner_space', 'return( x, y)'),
        ('parenthesized_first', 'return((x + 1), y)'),
        ('list_first', 'return([x], y)'),
        ('dict_first', 'return({"x": x}, y)'),
        ('none_first', 'return(None, y)'),
        ('true_first', 'return(True, y)'),
        ('underscore', 'return(_x, y)'),
        ('exponent', 'return(1e2, y)'),
    ]
    args.out.mkdir(parents=True, exist_ok=False)
    rule = S4ReturnTuple()
    records = []
    for name, statement in cases:
        source = 'def f():\n    x = 1\n    y = 2\n    λ = 3\n    _x = 4\n    ' + statement + '\n'
        tree, data = parse(source, 'python')
        sites = [s for s in rule.match(tree, data) if rule.guard(s, tree, data)]
        if len(sites) != 1 or sites[0].variant != 1:
            raise ValueError('Control must have one eligible parenthesized return tuple: ' + name)
        emitted = apply_edits(data, rule.write(sites[0], data, 0)).decode('utf-8')
        original_result, candidate_result = observe(source), observe(emitted)
        preserved = original_result == candidate_result
        if original_result['status'] != 'returned':
            raise ValueError('Invalid boundary control reference: ' + name)
        if args.expect_preserved and not preserved:
            raise ValueError('Boundary repair failed: ' + name)
        (args.out / (name + '__reference.py')).write_text(source)
        (args.out / (name + '__candidate.py')).write_text(emitted)
        records.append({'case': name, 'reference_sha256': sha(source.encode()),
                        'candidate_sha256': sha(emitted.encode()), 'site_span': sites[0].span,
                        'reference': original_result, 'candidate': candidate_result,
                        'preserved': preserved})
    report = {'scope': 'Nineteen manually specified lexical-boundary controls, not benchmark samples or a global S4 soundness claim.',
              'python': sys.version, 'vendor': str(args.vendor.resolve()),
              's4_match_sha256': sha(inspect.getsource(S4ReturnTuple.match).encode()),
              's4_guard_sha256': sha(inspect.getsource(S4ReturnTuple.guard).encode()),
              's4_emitter_sha256': sha(inspect.getsource(S4ReturnTuple.write_bytes).encode()),
              'cases': len(records), 'preserved': sum(r['preserved'] for r in records), 'records': records}
    (args.out / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'records'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
