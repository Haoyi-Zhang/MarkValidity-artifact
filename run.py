#!/usr/bin/env python3
"""Run a scientific producer or analysis against an isolated project copy.

Pass a script path relative to artifact, then its arguments after ``--``.
Clean project paths are translated to the original scientific recording paths.
Use ``{output}`` in the producer arguments for the fresh result directory.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from check import PROJECT, ROOT, restore_path, stage_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path,
                        help='New external directory for the generated files and log.')
    parser.add_argument('script', type=Path, help='Script path relative to artifact.')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output == PROJECT or output.is_relative_to(PROJECT):
        raise ValueError('Choose a new output directory outside the project')
    script = (ROOT / args.script).resolve()
    if not script.is_relative_to(ROOT) or not script.is_file() or script.suffix != '.py':
        raise ValueError('Choose a Python source file inside the artifact')
    arguments = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
    if not any('{output}' in argument for argument in arguments):
        raise ValueError('Set the producer result argument to {output}')
    layout = json.loads((ROOT / 'internal/layout.json').read_text())
    output.mkdir(parents=True)
    stage = output / 'work'
    try:
        print('Preparing an isolated scientific working copy.', flush=True)
        stage_project(stage)
        generated = stage / 'artifact' / '.generated'

        def translate(argument):
            if '{output}' in argument:
                return argument.replace('{output}', str(generated))
            if argument.startswith('--') and '=' in argument:
                flag, value = argument.split('=', 1)
                return flag + '=' + translate(value)
            candidate = ROOT / argument
            if not argument.startswith('-') and candidate.exists():
                resolved = candidate.resolve()
                if resolved.is_relative_to(PROJECT):
                    recorded = restore_path(resolved.relative_to(PROJECT), layout)
                    return str(stage / recorded)
                return str(resolved)
            return argument

        script_recorded = restore_path(script.relative_to(PROJECT), layout)
        argv = [sys.executable, '-B', str(stage / script_recorded)] + [translate(a) for a in arguments]
        log = output / 'run.log'
        started = time.monotonic()
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        print('Running ' + args.script.as_posix() + '; detailed output is saved in run.log.', flush=True)
        interrupted = False
        with log.open('w', encoding='utf-8') as stream:
            try:
                process = subprocess.run(argv, cwd=stage / 'artifact', env=env,
                                         stdout=stream, stderr=subprocess.STDOUT)
                returncode = process.returncode
            except KeyboardInterrupt:
                interrupted = True
                returncode = 130
        elapsed = time.monotonic() - started
        saved_outputs = []
        for produced in sorted(generated.parent.glob(generated.name + '*')):
            suffix = produced.name[len(generated.name):]
            name = 'results' + suffix
            if produced.is_file() and not suffix:
                try:
                    json.loads(produced.read_text())
                except (UnicodeError, ValueError):
                    name = 'result'
                else:
                    name = 'results.json'
            shutil.move(produced, output / name)
            saved_outputs.append(name)
        if returncode == 0 and not saved_outputs:
            raise ValueError('The script exited successfully without producing its declared output')
        result = {'status': 'PASS' if returncode == 0 else 'FAIL',
                  'script': args.script.as_posix(), 'seconds': round(elapsed, 3),
                  'process_exit_code': returncode, 'interrupted': interrupted,
                  'generated_outputs': saved_outputs,
                  'retained_observations_modified': False,
                  'scope': 'A fresh execution of the named producer or analysis; the detailed log and generated outputs identify its actual work.'}
        (output / 'run.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        if returncode:
            print('\n'.join(log.read_text(errors='replace').splitlines()[-24:]), file=sys.stderr)
            print('Incomplete work is retained at ' + str(stage), file=sys.stderr)
        else:
            shutil.rmtree(stage)
        return returncode
    except BaseException:
        # A preparation or persistence failure leaves the isolated tree available
        # for inspection. Never erase expensive partial producer output here.
        print('Incomplete work is retained at ' + str(stage), file=sys.stderr)
        raise


if __name__ == '__main__':
    raise SystemExit(main())
