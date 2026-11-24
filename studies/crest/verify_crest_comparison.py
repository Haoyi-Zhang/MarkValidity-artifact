#!/usr/bin/env python3
"""Receive the delivered comparison through fresh, independently checked replay."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study-root',type=Path,required=True)
    parser.add_argument('--artifact',type=Path,required=True)
    parser.add_argument('--methods',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    script=Path(__file__).resolve().parent/'compare_crest_operational.py'
    with tempfile.TemporaryDirectory(prefix='crest-comparison-receiving-') as temporary:
        replay=Path(temporary)/'replayed'
        operation=subprocess.run([sys.executable,'-B',str(script),'--artifact',str(args.artifact.resolve()),
                                  '--stock',str((args.study_root/'reference').resolve()),
                                  '--ablation',str((args.study_root/'catalogue').resolve()),
                                  '--theory',str(args.methods.resolve()),'--output',str(replay)],
                                 text=True,capture_output=True)
        if operation.returncode:
            raise ValueError('Fresh comparison receiving failed:\n'+operation.stderr)
        files=sorted(replay.rglob('*.json'))
        for file in files:
            expected=args.study_root/'comparison'/file.relative_to(replay)
            if not expected.exists() or json.loads(expected.read_text())!=json.loads(file.read_text()):
                raise ValueError('Delivered comparison differs from received source-bound replay: '+str(expected))
        summary=json.loads((replay/'summary.json').read_text())
    result={'status':'PASS','comparison_files_received':len(files),'complete_audit_traces':len(summary['reports']),
            'independent_prefix_checks':summary['independent_prefix_checks'],
            'independent_selection_checks':summary['independent_selection_checks'],
            'native_program_executions':0,
            'scope':'Reconstruct current source/contract/observer/environment groups and terminal no-output events from accepted native records; replay every public selection and compare each paired certificate to an independent Fraction reconstruction; receive all delivered registry, oracle, summary and trace values.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
