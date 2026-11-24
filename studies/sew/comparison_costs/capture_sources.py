#!/usr/bin/env python3
"""Preserve exact producer bytes already bound by a native run protocol.

The first native driver predates in-driver snapshotting. This companion checks
every current dependency against that run's pre-execution SHA before preserving
it. The complementary driver captures its own snapshots before executing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact.resolve()
    protocol_bytes = (args.native / 'protocol.json').read_bytes()
    protocol = json.loads(protocol_bytes)
    receipt = json.loads((args.native / 'receipt.json').read_text())
    if (receipt.get('status') != 'COMPLETE'
            or receipt.get('protocol_sha256') != hashlib.sha256(protocol_bytes).hexdigest()):
        raise ValueError('a completed native run bound to this protocol is required')
    directory = Path('external-studies/sew_natural/comparison_costs')
    names = {name: directory / name for name in ('native_timing.py', 'native_timing_reverse.py',
                                                'policies.py', 'analyze.py', 'admission.py')}
    names.update(natural_analysis=Path('external-studies/sew_natural/analysis/natural_analysis.py'))
    names['natural_analysis.py'] = names.pop('natural_analysis')
    names.update(humaneval_runner=Path('external-studies/sew_natural/scripts/humaneval/native_runner_v3.py'),
                 mbpp_runner=Path('external-studies/sew_natural/mbpp/scripts/native_runner_v2.py'))
    if args.out.exists():
        raise ValueError('fresh source snapshot output required')
    contents = {}
    for name, expected in protocol['source_sha256'].items():
        content = (root / names[name]).read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError('current bytes differ from the run protocol: ' + name)
        contents[name] = content
    args.out.mkdir(parents=True)
    inventory = {}
    for name, content in contents.items():
        (args.out / name).write_bytes(content)
        inventory[name] = {'original_path': names[name].as_posix(), 'snapshot_file': name,
                           'sha256': hashlib.sha256(content).hexdigest()}
    manifest = {'schema': 'markvalidity-native-source-snapshots-v1',
                'capture_scope': 'Captured after the first block; every byte matches its pre-execution protocol hash and its end-of-execution source check.',
                'protocol_sha256': hashlib.sha256(protocol_bytes).hexdigest(), 'files': inventory}
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'sources_captured': len(inventory), 'output': str(args.out)}))


if __name__ == '__main__':
    main()
