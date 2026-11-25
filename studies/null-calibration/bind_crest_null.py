"""Part 3: bind the retained CREST detector readings on UNMODIFIED programs.

The artifact already records, for every row of studies/crest/accepted/{reference,gpt4o,qwen}/results.json,
`reference_detector` = the three released CREST heads applied to the original (unwatermarked) program at
the released thresholds. This script only extracts those retained readings (no model is re-run).
Standard library only. Usage (artifact root):

    python3 -B -S studies/null-calibration/bind_crest_null.py --out results/null-calibration/crest-unmarked-programs.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDIES = ("reference", "gpt4o", "qwen")
HEADS = ("rf", "logreg_l1", "logreg_l2")


def extract(root: Path):
    out = {"schema": "markvalidity-null-calibration-crest-binding-v1", "heads": list(HEADS), "studies": {}}
    for study in STUDIES:
        path = root / "studies" / "crest" / "accepted" / study / "results.json"
        raw = path.read_bytes()
        rows = json.loads(raw)
        items = []
        for r in rows:
            det = r.get("reference_detector") or {}
            item = {"dataset": r.get("dataset"), "task_id": r.get("task_id"), "dataset_index": r.get("dataset_index"),
                    "reference_source": r.get("reference_source"), "qualified_reference": r.get("qualified_reference"),
                    "reference_detector_status": det.get("status"), "heads": {}}
            for h in HEADS:
                c = (det.get("classifiers") or {}).get(h)
                item["heads"][h] = None if c is None else {"probability": c.get("probability"), "threshold": c.get("threshold"),
                                                            "constraint": c.get("constraint"), "detected": c.get("detected")}
            items.append(item)
        out["studies"][study] = {"source": path.relative_to(root).as_posix(), "source_sha256": hashlib.sha256(raw).hexdigest(),
                                 "rows": items}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    data = extract(ROOT)
    args.out.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print({s: len(v["rows"]) for s, v in data["studies"].items()})


if __name__ == "__main__":
    main()
