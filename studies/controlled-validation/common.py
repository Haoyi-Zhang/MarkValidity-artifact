"""Shared, stdlib-only helpers for the controlled-validation study.

The site-selection rule is re-implemented here from the declared protocol
(protocol.json) rather than imported, so that the source-level attack path does
not reuse the state-space attack code. Constants are cross-checked against
covewm.benchmark before use.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parent.parent
PROTOCOL_PATH = HERE / "protocol.json"

SCHEMES = ("lexical", "structural", "hybrid")
ATTACKS = ("format", "rename", "normalize", "random_flip", "strip", "mixed")
FAMILIES = ("rename", "normalize", "random_flip", "strip", "mixed")
LANGUAGES = ("python", "javascript")
OPNAME = {"rename": "rename", "normalize": "normalize", "random_flip": "flip",
          "strip": "strip", "mixed": "mixedapply", "format": "format"}
PAYLOAD_BITS = 24


def load_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def u64(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def u01(text: str) -> float:
    return u64(text) / 2**64


def bits(task: str, language: str, payload_index: int) -> list[int]:
    return [u64(f"payload|{task}|{language}|{payload_index}|{site}") & 1 for site in range(PAYLOAD_BITS)]


def site_channels(scheme: str) -> list[str]:
    if scheme == "lexical":
        return ["lexical"] * PAYLOAD_BITS
    if scheme == "structural":
        return ["structural"] * PAYLOAD_BITS
    return ["lexical"] * 12 + ["structural"] * 12


class Rule:
    """Declared deterministic site-selection rule."""

    def __init__(self, protocol: dict | None = None):
        protocol = protocol or load_protocol()
        rule = protocol["declared_site_selection_rule"]
        self.multipliers = rule["multipliers"]
        self.salts = rule["salts"]

    def key(self, scheme, attack, severity: str, task, language, payload_index) -> str:
        return f"{self.salts[scheme][attack]}|{scheme}|{attack}|{float(severity):.1f}|{task}|{language}|{payload_index}"

    def probability(self, scheme, attack, severity: str) -> float:
        return min(1.0, max(0.0, float(severity) * self.multipliers[scheme][attack]))

    def selected(self, key: str, attack: str, k: int, p: float) -> bool:
        return u01(f"{key}|{OPNAME[attack]}|{k}") < p

    @staticmethod
    def mixed_selector(key: str, k: int) -> float:
        return u01(f"{key}|mixedop|{k}")


def check_rule_against_benchmark(rule: Rule) -> None:
    """Stop if the declared constants differ from the frozen implementation."""
    from covewm import benchmark as b
    for scheme in SCHEMES:
        for attack in ATTACKS:
            if attack == "format":
                expect = (1.0, "format")
            else:
                expect = b._attack_config(scheme, attack)
            got = (rule.multipliers[scheme][attack], rule.salts[scheme][attack])
            if tuple(expect) != got:
                raise SystemExit(f"declared rule differs from benchmark for {scheme}/{attack}: {got} vs {expect}")


def predicted_state(rule: Rule, scheme, attack, severity: str, task, language, payload_index):
    """Independent re-implementation of the declared state model.

    Returns (observed, present, attempted) lists per site and the attempted
    count (sites selected among eligible sites, including no-op selections).
    """
    expected = bits(task, language, payload_index)
    chans = site_channels(scheme)
    key = rule.key(scheme, attack, severity, task, language, payload_index)
    p = rule.probability(scheme, attack, severity)
    observed, present, attempted = list(expected), [True] * PAYLOAD_BITS, 0
    for k in range(PAYLOAD_BITS):
        ch = chans[k]
        if attack == "format":
            continue
        if attack == "rename" and ch != "lexical":
            continue
        if attack == "normalize" and ch != "structural":
            continue
        if not rule.selected(key, attack, k, p):
            continue
        attempted += 1
        if attack in ("rename", "normalize"):
            observed[k] = 0
        elif attack == "random_flip":
            observed[k] = 1 - observed[k]
        elif attack == "strip":
            present[k] = False
        elif attack == "mixed":
            u = rule.mixed_selector(key, k)
            if u < 0.25:
                observed[k] = 0 if ch == "lexical" else 1 - observed[k]
            elif u < 0.50:
                observed[k] = 0 if ch == "structural" else 1 - observed[k]
            elif u < 0.75:
                observed[k] = 1 - observed[k]
            else:
                present[k] = False
    return expected, observed, present, attempted


def read_csv_bytes(data: bytes) -> list[dict]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_robustness(artifact: Path = ARTIFACT) -> tuple[list[dict], str]:
    protocol = load_protocol()
    path = artifact / protocol["inputs"]["robustness_csv"]
    data = path.read_bytes()
    digest = sha256_bytes(data)
    if digest != protocol["inputs"]["robustness_csv_sha256"]:
        raise SystemExit("robustness.csv does not match the declared SHA-256")
    rows = read_csv_bytes(data)
    if len(rows) != protocol["inputs"]["robustness_rows"]:
        raise SystemExit("robustness.csv row count differs from protocol")
    return rows, digest


def row_key(row: dict) -> tuple:
    return (row["scheme"], row["attack"], row["severity"], row["task"], row["language"], int(row["payload_index"]))
