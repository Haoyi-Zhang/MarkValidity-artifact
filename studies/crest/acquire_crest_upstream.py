#!/usr/bin/env python3
"""Acquire the exact public upstream files recorded by the original study."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    source = args.evidence/'provenance/generation-records/full-study/protocol.json'
    if not source.exists():
        source = args.evidence/'full-study/protocol.json'
    protocol = json.loads(source.read_text())
    if protocol['source'] != 'https://github.com/niccap/crest':
        raise ValueError('Unexpected upstream acquisition record')
    target = args.output or args.evidence/'upstream'
    for relative, expected in protocol['upstream_files'].items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Invalid upstream path')
        destination = target/path
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == expected:
            continue
        url = 'https://raw.githubusercontent.com/niccap/crest/'+protocol['upstream_commit']+'/'+relative
        for attempt in range(6):  # transient HTTP 5xx / connection errors are retried
            try:
                with urllib.request.urlopen(url, timeout=60) as response:
                    content = response.read()
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                if attempt == 5 or (isinstance(error, urllib.error.HTTPError) and error.code < 500):
                    raise
                time.sleep(2 ** attempt)
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError('Acquired bytes do not match the recorded upstream input: '+relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    print(json.dumps({'status':'PASS','acquired_core_model_threshold_files':len(protocol['upstream_files']),
                      'upstream':str(target)}))


if __name__=='__main__':
    main()
