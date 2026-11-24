#!/usr/bin/env python3
"""Verify the paper's retained scientific evidence in an isolated working tree.

The delivered observations and frozen scientific code keep their original bytes.
Only their presentation directories have been shortened. The temporary tree
restores the paths recorded by those observations, allowing the original source
bindings and independent receivers to be checked without rewriting the data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent


def restore_path(relative, layout):
    name = relative.as_posix()
    if name in layout['file_map']:
        return Path(layout['file_map'][name])
    for clean, recorded in layout['directory_map']:
        if name == clean or name.startswith(clean + '/'):
            return Path(recorded + name[len(clean):])
    return relative


def scientific_file(relative):
    """Experiment data, implementations and invocation maps; editorial files are separate."""
    parts = relative.parts
    if len(parts) < 2 or parts[0] != 'artifact' or relative.suffix.lower() == '.md':
        return False
    if parts[1] in ('reporting', 'citations', 'citation-evidence'):
        return False
    return relative.as_posix() not in ('artifact/check.py', 'artifact/run.py')


# Components that read the LaTeX sources of the paper. They need a paper
# directory (default: ../paper next to this repository, or --paper DIR); in a
# standalone checkout without the paper they are reported as SKIPPED.
PAPER_BOUND = ('paper-data-consistency', 'citation-source-bindings')
PAPER = Path(os.environ.get('MARKVALIDITY_PAPER', PROJECT / 'paper'))
LOCAL_DIRS = ('.worktree', '.git', '.venv', 'venv')


def paper_available():
    return (PAPER / 'main.tex').is_file()


def stage_reporting_snapshot(destination, layout):
    """Materialize the reporting snapshot from the paper sources in the working copy.

    The repository keeps only the snapshot index (reporting/paper/manifest.json);
    the bound files themselves are taken from the paper directory, so the
    repository does not ship a second copy of the manuscript. The regression
    receivers still check every bound file against the recorded SHA-256 values.
    """
    snapshot = ROOT / 'reporting/paper'
    manifest = json.loads((snapshot / 'manifest.json').read_text())
    target_root = destination / restore_path(Path('artifact/reporting/paper'), layout)
    copied = 0
    if not paper_available():
        return copied
    for name in manifest['files_sha256']:
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe publication snapshot path')
        target = target_root / relative
        if target.exists():
            continue
        source = PAPER / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError('A bound publication file is missing from the paper directory: ' + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied += 1
    return copied


def stage_project(destination, scientific_inputs=None):
    """Copy bytes, never hard-link observations that a receiver could write."""
    layout = json.loads((ROOT / 'internal/layout.json').read_text())
    omitted = set(layout['runtime_omit'])
    copied = 0
    sources = list(ROOT.rglob('*'))
    paper = PAPER
    if paper.is_symlink():
        raise ValueError('The paper directory may not be a symbolic link')
    if paper_available():
        sources.extend(paper.rglob('*'))
    for source in sorted(sources):
        if source.is_relative_to(ROOT):
            relative = Path('artifact') / source.relative_to(ROOT)
        else:
            relative = Path('paper') / source.relative_to(paper)
        # Local, non-scientific directories (reports, VCS, virtual environments).
        if len(relative.parts) > 1 and relative.parts[1] in LOCAL_DIRS:
            continue
        if source.is_symlink():
            raise ValueError('Project contains a symbolic link: ' + str(source))
        if not source.is_file():
            continue
        if '__pycache__' in relative.parts:
            continue
        if relative.as_posix() in omitted:
            if scientific_inputs is not None and scientific_file(relative):
                scientific_inputs[relative.as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()
            continue
        target = destination / restore_path(relative, layout)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if scientific_inputs is not None and scientific_file(relative):
            scientific_inputs[relative.as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
        copied += 1
    copied += stage_reporting_snapshot(destination, layout)
    for alias in layout.get('runtime_aliases', []):
        base = ROOT / Path(alias['clean_root']).relative_to('artifact')
        for source in sorted(base.rglob('*')):
            if not source.is_file():
                continue
            if source.relative_to(base).as_posix() in alias.get('exclude', []):
                continue
            target = destination / alias['recorded_root'] / source.relative_to(base)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != source.read_bytes():
                raise ValueError('Conflicting recorded input path: ' + str(target))
            if not target.exists():
                shutil.copyfile(source, target)
                copied += 1
    return copied


def stage_crest_cache(stage, cache):
    """Copy only the exact acquired core, models and thresholds into temporary work."""
    if cache is None:
        return 0
    cache = cache.resolve()
    evidence = stage / 'artifact/studies/crest'
    protocol = json.loads((evidence / 'provenance/generation-records/full-study/protocol.json').read_text())
    if protocol['source'] != 'https://github.com/niccap/crest':
        raise ValueError('Unexpected CREST acquisition source')
    copied = 0
    for name, expected in protocol['upstream_files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe upstream cache input path')
        source = cache / relative
        content = source.read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError('The upstream cache does not match the recorded scientific input: ' + name)
        target = evidence / 'upstream' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        copied += 1
    return copied


def refresh_publication_snapshot(project=None):
    """Re-index the reporting snapshot (paper file hashes) after publication generation.

    This updates a file index, not a scientific or manual citation assessment.
    The independent reporting tests still reconstruct values from raw evidence.
    """
    project = Path(project).resolve() if project is not None else PROJECT
    snapshot = project / 'artifact/reporting/paper'
    path = snapshot / 'manifest.json'
    manifest = json.loads(path.read_text())
    if manifest['scope'] != 'current-publication':
        raise ValueError('The reporting snapshot is not the current publication')
    updated = {}
    for name in manifest['files_sha256']:
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe publication snapshot path')
        source = project / 'paper' / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError('A current publication input is missing or symbolic: ' + name)
        content = source.read_bytes()
        updated[name] = hashlib.sha256(content).hexdigest()
    manifest['files_sha256'] = updated
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    return len(updated)


def receiving_environment(choices):
    """Fail before staging a large project when CREST receiving dependencies are absent."""
    numeric = any(item['name'].startswith(('crest-native-model-', 'crest-source-contract-')) for item in choices)
    if not numeric:
        return None
    program = '''import importlib.metadata, json
import numpy, sklearn, joblib, libarchive
if sklearn.__version__ != '1.7.2':
    raise RuntimeError('CREST numerical receiving requires scikit-learn 1.7.2; found ' + sklearn.__version__)
names = ('numpy', 'scikit-learn', 'joblib', 'scipy', 'libarchive-c')
print(json.dumps({name: importlib.metadata.version(name) for name in names}))
'''
    result = subprocess.run([sys.executable, '-B', '-c', program],
                            text=True, capture_output=True, env=dict(os.environ))
    if result.returncode:
        raise RuntimeError('CREST receiving dependencies are unavailable or incompatible. Install '
                           'artifact/studies/crest/requirements.txt in this Python environment '
                           'and provide the system libarchive library.\n' + result.stdout + result.stderr)
    return json.loads(result.stdout)


def execute(args):
    plan = json.loads((ROOT / 'internal/verification-plan.json').read_text())
    choices = [item for item in plan['steps']
               if args.scope == 'all' or args.scope in item['groups'] or
               (args.scope == 'publication' and item['name'] in
                ('paper-data-consistency', 'citation-source-bindings'))]
    if args.component:
        requested = set(args.component)
        available = {item['name'] for item in choices}
        if not requested <= available:
            raise ValueError('Unknown component or component outside selected scope: ' +
                             ', '.join(sorted(requested - available)))
        choices = [item for item in choices if item['name'] in requested]
    if not choices:
        raise ValueError('No verification steps selected')
    missing_numeric = None
    try:
        dependencies = receiving_environment(choices)
    except RuntimeError as error:
        # Report the CREST numerical receivers as SKIPPED (never as PASS) and
        # still run every other selected component.
        missing_numeric = str(error).splitlines()[0]
        dependencies = {'unavailable': str(error)}
        print('CREST numerical receivers will be SKIPPED: ' + missing_numeric, flush=True)
    output = args.output.resolve() if args.output else None
    if output:
        if output == PROJECT or output.is_relative_to(PROJECT):
            raise ValueError('Choose an output directory outside the project')
        if output.exists():
            raise ValueError('Choose a new output directory')
        output.mkdir(parents=True)
    context = tempfile.TemporaryDirectory(prefix='markvalidity-check-')
    with context as temporary:
        stage = Path(temporary) / 'MarkValidity'
        print('Preparing an isolated scientific working copy.', flush=True)
        scientific_inputs = {}
        count = stage_project(stage, scientific_inputs)
        cached = stage_crest_cache(stage, args.crest_upstream_cache) if args.scope in ('all', 'primary') else 0
        log_root = output if output else Path(temporary) / 'logs'
        log_root.mkdir(exist_ok=True)
        input_index = {'scope': 'Frozen scientific artifact files, including data, methods, tests and invocation maps. Editorial text, reporting copies, citation assessments and top-level orchestration entry points are received separately.',
                       'files': scientific_inputs}
        (log_root / 'input-files.json').write_text(json.dumps(input_index, indent=2) + '\n')
        if args.scientific_inputs:
            previous = json.loads(args.scientific_inputs.read_text())['files']
            changed = sorted(name for name in set(previous) | set(scientific_inputs)
                             if previous.get(name) != scientific_inputs.get(name))
            if changed:
                raise ValueError('Previously received scientific inputs changed: ' + ', '.join(changed[:12]) +
                                 (' ...' if len(changed) > 12 else '') + '. Run the affected full receivers again.')
        print(f'Checking {len(choices)} scientific components in an isolated copy.', flush=True)
        received = []
        for item in choices:
            reason = None
            if item['name'] in PAPER_BOUND and not paper_available():
                reason = ('paper sources not found at ' + str(PAPER) +
                          ' (pass --paper DIR to run this paper-binding check)')
            elif missing_numeric and item['name'].startswith(('crest-native-model-', 'crest-source-contract-')):
                reason = 'CREST receiving dependencies unavailable: ' + missing_numeric
            if reason:
                received.append({'component': item['name'], 'status': 'SKIPPED', 'seconds': 0,
                                 'tests_executed': 0, 'process_exit_code': None, 'reason': reason})
                print(f"{item['name']}: SKIPPED ({reason})", flush=True)
                continue
            argv = [sys.executable if part == '{python}' else part for part in item['argv']]
            log_path = log_root / (item['name'] + '.log')
            env = dict(os.environ)
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            if item.get('pythonpath'):
                extra = str(stage / 'artifact' / item['pythonpath'])
                env['PYTHONPATH'] = extra + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
            started = time.monotonic()
            with log_path.open('w', encoding='utf-8') as stream:
                completed = subprocess.run(argv, cwd=stage / 'artifact', env=env,
                                           stdout=stream, stderr=subprocess.STDOUT)
            elapsed = time.monotonic() - started
            log = log_path.read_text(encoding='utf-8', errors='replace')
            test_counts = [int(value) for value in re.findall(r'Ran (\d+) tests? in ', log)]
            success = completed.returncode == 0
            if item.get('unit_tests'):
                success = success and bool(test_counts) and not re.search(r'\bskipped=\d+|\bFAILED\b', log)
            received.append({'component': item['name'], 'status': 'PASS' if success else 'FAIL',
                             'seconds': round(elapsed, 3), 'tests_executed': sum(test_counts),
                             'process_exit_code': completed.returncode})
            print(f"{item['name']}: {'PASS' if success else 'FAIL'} ({elapsed:.1f} s)", flush=True)
            if not success:
                print('\n'.join(log.splitlines()[-24:]), file=sys.stderr)
                if not args.keep_going:
                    break
        complete = len(received) == len(choices) and all(r['status'] in ('PASS', 'SKIPPED') for r in received)
        skipped = any(r['status'] == 'SKIPPED' for r in received)
        status = 'FAIL' if not complete else 'PASS_WITH_SKIPS' if skipped else 'PASS'
        if complete and all(r['status'] == 'SKIPPED' for r in received):
            status = 'SKIPPED'
        result = {'status': status, 'scope': args.scope,
                  'skipped_components': [r['component'] for r in received if r['status'] == 'SKIPPED'],
                  'failed_components': [r['component'] for r in received if r['status'] == 'FAIL'],
                  'components_completed': len(received), 'components_requested': len(choices),
                  'scientific_files_staged': count, 'results': received,
                  'externally_cached_upstream_files_verified': cached,
                  'receiving_dependencies': dependencies,
                  'scientific_files_bound': len(scientific_inputs),
                  'scientific_inputs_matched_index': True if args.scientific_inputs else None,
                  'retained_observations_modified': False,
                  'fresh_benchmark_experiments_started': False,
                  'meaning': 'Independent receiving of the retained evidence and selected mathematical/interface tests. Implementation tests may execute their own fixtures; no new benchmark experiment is started.'}
        if output:
            (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        print(f"Overall: {status}" + (f"; failed: {', '.join(result['failed_components'])}" if result['failed_components'] else '')
              + (f"; skipped: {', '.join(result['skipped_components'])}" if result['skipped_components'] else ''), flush=True)
        return 0 if complete else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', choices=('all', 'primary', 'supporting', 'tests', 'publication'), default='all')
    parser.add_argument('--output', type=Path, help='New external directory for detailed logs and the result.')
    parser.add_argument('--component', action='append',
                        help='Run this named component only; repeat to receive an explicit subset. Omit for every component in the selected scope.')
    parser.add_argument('--scientific-inputs', type=Path,
                        help='A previously checked input-files.json. Reject changed scientific files before the selected checks; useful for final publication receiving after layout changes.')
    parser.add_argument('--crest-upstream-cache', type=Path,
                        help='Optional acquired CREST root. Only recorded core/model/threshold files are copied into temporary work after exact identity checks. Otherwise the primary check acquires them online.')
    parser.add_argument('--paper', type=Path,
                        help='Directory with the paper LaTeX sources (main.tex, figdata/, ...). Default: ../paper. '
                             'Without it the paper-binding components are SKIPPED.')
    parser.add_argument('--keep-going', action='store_true',
                        help='Continue with the remaining components after a failure.')
    args = parser.parse_args()
    global PAPER
    if args.paper:
        PAPER = args.paper.resolve()
    return execute(args)


if __name__ == '__main__':
    raise SystemExit(main())
