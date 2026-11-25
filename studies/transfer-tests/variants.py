"""Materialize the three audited transfer-audit variants for every frozen module.

The variant bytes are produced by the exact functions used by the audited
transfer run (``covewm.extended``) and are checked against the retained
``candidate_sha256`` values in ``results/controlled/raw/project_transfer.csv``.
Standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

ARTIFACT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARTIFACT / "src"))

from covewm.extended import (  # noqa: E402
    inert_trailing_comment,
    scope_blind_identifier_collapse,
    syntax_aware_local_rename,
)

INTERVENTIONS = (
    "inert-trailing-comment",
    "syntax-aware-local-rename",
    "scope-blind-identifier-collapse",
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_manifest(artifact: Path = ARTIFACT) -> list[dict[str, str]]:
    with (artifact / "corpus/transfer_manifest.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def module_path(artifact: Path, record: dict[str, str]) -> Path:
    return artifact / "corpus/transfer" / record["project_slug"] / f"module-{int(record['selection_rank']):02d}.py"


def materialize(record: dict[str, str], source: str) -> dict[str, str]:
    """Return {intervention: variant text}, exactly as in covewm.extended.run_transfer_audit."""
    return {
        "inert-trailing-comment": inert_trailing_comment(source),
        "syntax-aware-local-rename": syntax_aware_local_rename(
            source,
            int(record["rename_function_line"]),
            record["rename_parameter"],
            "cvlocal" + record["source_sha256"][:7],
        ),
        "scope-blind-identifier-collapse": scope_blind_identifier_collapse(source),
    }


def retained_hashes(artifact: Path = ARTIFACT) -> dict[tuple[str, str], str]:
    path = artifact / "results/controlled/raw/project_transfer.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return {(row["module_id"], row["intervention"]): row["candidate_sha256"] for row in csv.DictReader(handle)}


def all_variants(artifact: Path = ARTIFACT) -> dict[str, dict[str, object]]:
    """module_id -> {record, source, variants}; raises on any hash mismatch."""
    retained = retained_hashes(artifact)
    out: dict[str, dict[str, object]] = {}
    for record in read_manifest(artifact):
        source = module_path(artifact, record).read_text(encoding="utf-8")
        if sha256_text(source) != record["source_sha256"]:
            raise AssertionError(f"frozen source hash mismatch: {record['module_id']}")
        variants = materialize(record, source)
        for intervention, text in variants.items():
            if sha256_text(text) != retained[(record["module_id"], intervention)]:
                raise AssertionError(f"variant hash differs from audited bytes: {record['module_id']} {intervention}")
        out[record["module_id"]] = {"record": record, "source": source, "variants": variants}
    return out


def export(destination: Path) -> None:
    """Write originals and variants as raw UTF-8 bytes (no newline translation)."""
    for module_id, item in all_variants().items():
        folder = destination / module_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "original.py").write_bytes(str(item["source"]).encode("utf-8"))
        for intervention, text in item["variants"].items():  # type: ignore[union-attr]
            (folder / f"{intervention}.py").write_bytes(text.encode("utf-8"))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        export(Path(sys.argv[1]))
    items = all_variants()
    print(f"modules={len(items)} variants={3 * len(items)} all audited hashes match")
