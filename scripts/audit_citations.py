#!/usr/bin/env python3
"""Index the shipped citations without turning retained receipts into fresh review.

Run from any directory.  Only local files are read; this is not a network or
full-text-verification tool.  Hand-reviewed source scopes live in
citation-current/verified-sources.json.  Optional claim-reviews.json records
bind a scope assessment to an exact current paragraph hash.  Missing or changed
assessments remain explicit rather than being silently renewed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def balanced(text: str, start: int) -> tuple[str, int]:
    """Return a braced BibTeX value or entry, including nested TeX braces."""
    depth = 0
    for pos in range(start, len(text)):
        char = text[pos]
        if pos and text[pos - 1] == "\\":
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:pos], pos + 1
    raise ValueError(f"Unclosed BibTeX brace at offset {start}")


def parse_bib(text: str) -> list[dict[str, str]]:
    """Read this project's conventional braced/quoted BibTeX entries."""
    entries = []
    pos = 0
    while match := re.search(r"@([A-Za-z]+)\s*\{", text[pos:]):
        kind = match.group(1).lower()
        start = pos + match.end() - 1
        body, pos = balanced(text, start)
        if kind in {"comment", "preamble", "string"}:
            continue
        key, separator, fields = body.partition(",")
        if not separator:
            raise ValueError(f"Missing fields in BibTeX entry {key}")
        entry = {"citation_key": key.strip(), "entry_type": kind}
        field_pos = 0
        while field_match := re.search(r"([A-Za-z][\w-]*)\s*=\s*", fields[field_pos:]):
            name = field_match.group(1).lower()
            value_start = field_pos + field_match.end()
            if fields[value_start] == "{":
                value, field_pos = balanced(fields, value_start)
            elif fields[value_start] == '"':
                value_end = value_start + 1
                while value_end < len(fields):
                    if fields[value_end] == '"' and fields[value_end - 1] != "\\":
                        break
                    value_end += 1
                if value_end == len(fields):
                    raise ValueError(f"Unclosed quoted field {name} in {key}")
                value = fields[value_start + 1:value_end]
                field_pos = value_end + 1
            else:
                value_end = fields.find(",", value_start)
                if value_end < 0:
                    value_end = len(fields)
                value, field_pos = fields[value_start:value_end], value_end + 1
            if name in entry:
                raise ValueError(f"Duplicate field {name} in {key}")
            entry[name] = value.strip()
        entries.append(entry)
    return entries


def normalized(value: object) -> str:
    if isinstance(value, list):
        value = " and ".join(str(v) for v in value)
    unbraced = str(value or "").replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", unbraced).strip().lower()


def remove_comments(text: str) -> str:
    # Preserve offsets and line numbers so reports link to the actual source.
    return re.sub(r"(?<!\\)%[^\n]*", lambda m: " " * len(m.group()), text)


def sources(paper: Path) -> dict[str, str]:
    result = {}
    pending = [paper / "main.tex", paper / "online-supplement.tex"]
    while pending:
        path = pending.pop(0).resolve()
        if not path.is_relative_to(paper.resolve()):
            raise ValueError(f"TeX input escapes paper directory: {path}")
        name = path.relative_to(paper.resolve()).as_posix()
        if name in result:
            continue
        text = path.read_text(encoding="utf-8")
        result[name] = text
        for target in re.findall(r"\\(?:input|include)\s*\{([^}]+)\}", remove_comments(text)):
            # TeX is built from the paper root. Nested \input filenames are
            # resolved there too, not relative to the including file.
            child = paper / target
            if not child.suffix:
                child = child.with_suffix(".tex")
            pending.append(child)
    return dict(sorted(result.items()))


def paragraphs(text: str) -> list[tuple[int, int]]:
    starts = [0]
    ends = []
    for match in re.finditer(r"\n[ \t]*\n", text):
        ends.append(match.start())
        starts.append(match.end())
    ends.append(len(text))
    return list(zip(starts, ends))


def main() -> int:
    artifact = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", type=Path, default=artifact.parent / "paper")
    parser.add_argument("--output", type=Path, default=artifact / "citation-current")
    parser.add_argument("--check", action="store_true", help="read-only check of existing audit source bindings")
    args = parser.parse_args()
    paper, output = args.paper.resolve(), args.output.resolve()
    tex_sources = sources(paper)
    source_hashes = {"paper/" + name: digest(text.encode()) for name, text in tex_sources.items()}
    bib_path = paper / "references.bib"
    bib_bytes = bib_path.read_bytes()
    bindings = {**source_hashes, "paper/references.bib": digest(bib_bytes)}
    audit_inputs = [Path(__file__).resolve(), artifact / "companion-bibliography.json",
                    artifact / "citation-current/verified-sources.json",
                    artifact / "citation-current/claim-reviews.json",
                    *sorted((artifact / "citation-evidence").glob("*.json"))]
    audit_input_bindings = {"artifact/" + path.relative_to(artifact).as_posix(): digest(path.read_bytes())
                            for path in audit_inputs if path.exists()}
    if args.check:
        saved = json.loads((output / "audit.json").read_text())
        changed = sorted(name for name in set(bindings) | set(saved["source_bindings"])
                         if bindings.get(name) != saved["source_bindings"].get(name))
        old_inputs = saved.get("audit_input_bindings", {})
        changed_inputs = sorted(name for name in set(audit_input_bindings) | set(old_inputs)
                                if audit_input_bindings.get(name) != old_inputs.get(name))
        print(json.dumps({"source_bindings_current": not changed, "changed_sources": changed,
                          "audit_inputs_current": not changed_inputs, "changed_audit_inputs": changed_inputs}))
        return int(bool(changed or changed_inputs))

    entries = parse_bib(bib_bytes.decode())
    entry_counts = Counter(e["citation_key"] for e in entries)
    bibliography = {e["citation_key"]: e for e in entries}
    retained = defaultdict(list)
    for path in sorted((artifact / "citation-evidence").glob("*.json")):
        record = json.loads(path.read_text())
        key = record.get("citation_key") or record.get("key")
        if key:
            retained[key].append((path.relative_to(artifact).as_posix(), record))
    companion = artifact / "companion-bibliography.json"
    if companion.exists():
        for record in json.loads(companion.read_text()).get("references", []):
            retained[record["citation_key"]].append((companion.name, record))
    reviewed_path = artifact / "citation-current/verified-sources.json"
    reviewed = {}
    if reviewed_path.exists():
        reviewed = {r["citation_key"]: r for r in json.loads(reviewed_path.read_text())["sources"]}
    claim_review_path = artifact / "citation-current/claim-reviews.json"
    claim_reviews = {}
    if claim_review_path.exists():
        for record in json.loads(claim_review_path.read_text()).get("reviews", []):
            claim_reviews[(record["citation_key"], record["file"], record["paragraph_sha256"])] = record

    positions = []
    cite_pattern = re.compile(r"\\(?:[cC]ite(?:p|t|alt|alp|author|yearpar|year|fullauthor|num)?|nocite)\*?(?:\[[^\]]*\])*\s*\{([^}]+)\}")
    for name, source in tex_sources.items():
        intervals = paragraphs(source)
        for match in cite_pattern.finditer(remove_comments(source)):
            begin, end = next((a, b) for a, b in intervals if a <= match.start() <= b)
            paragraph = source[begin:end].strip()
            for key in (k.strip() for k in match.group(1).split(",")):
                if key == "*":
                    continue
                row = {"citation_key": key, "file": "paper/" + name,
                       "line": source.count("\n", 0, match.start()) + 1,
                       "paragraph_sha256": digest(paragraph.encode()),
                       "paragraph": paragraph}
                review = claim_reviews.get((key, row["file"], row["paragraph_sha256"]))
                row["claim_scope_assessment"] = review.get("status") if review else "NOT_AUTOMATICALLY_ASSESSED"
                row["claim_scope_note"] = review.get("note", "") if review else ""
                positions.append(row)
    used = {row["citation_key"] for row in positions}
    references, differences = [], []
    for key, entry in sorted(bibliography.items()):
        historical = retained.get(key, [])
        review = reviewed.get(key, {})
        source_locator = (review.get("primary_url") or entry.get("url") or
                          ("https://doi.org/" + entry["doi"] if entry.get("doi") else "") or
                          next((r.get("source_locator", "") for _, r in historical if r.get("source_locator")), ""))
        historical_info = []
        for filename, record in historical:
            old_bindings = record.get("current_source_bindings", {})
            mismatches = sorted(n for n, h in old_bindings.items() if bindings.get(n) != h)
            historical_info.append({"file": filename,
                                    "receipt_sha256": digest((artifact / filename).read_bytes()),
                                    "recorded_status": record.get("verification_status", "UNSPECIFIED"),
                                    "binding_status": "UNBOUND_METADATA" if not old_bindings else
                                    ("MATCHES_CURRENT_SOURCES" if not mismatches else "HISTORICAL_SOURCE_BINDINGS_DIFFER"),
                                    "different_bindings": mismatches})
            for field, old_name in (("title", "title"), ("author", "authors"), ("year", "year")):
                old = record.get(old_name)
                if old and normalized(entry.get(field)) != normalized(old):
                    differences.append({"citation_key": key, "field": field,
                                        "current": entry.get(field, ""), "retained": old,
                                        "retained_file": filename,
                                        "resolution": review.get("metadata_note", "NOT_AUTOMATICALLY_RESOLVED")})
        references.append({"citation_key": key, "entry_type": entry["entry_type"],
                           "title": entry.get("title", ""), "year": entry.get("year", ""),
                           "identifier": "doi:" + entry["doi"] if entry.get("doi") else source_locator,
                           "source_locator": source_locator,
                           "fresh_reading_level": review.get("reading_level", "RETAINED_ONLY"),
                           "fresh_scope": review.get("supports", []),
                           "fresh_limitations": review.get("does_not_establish", []),
                           "retained_receipts": historical_info,
                           "positions": [r for r in positions if r["citation_key"] == key]})
    errors = {
        "duplicate_bibliography_keys": sorted(k for k, n in entry_counts.items() if n > 1),
        "undefined_citation_keys": sorted(used - bibliography.keys()),
        "missing_required_metadata": [{"citation_key": e["citation_key"], "field": f} for e in entries
                                      for f in ("title", "author", "year") if not e.get(f)],
        "malformed_dois": [{"citation_key": e["citation_key"], "doi": e["doi"]} for e in entries
                           if e.get("doi") and not re.fullmatch(r"10\.\d{4,9}/\S+", e["doi"])],
        "missing_source_locators": [r["citation_key"] for r in references if not r["source_locator"]],
    }
    audit = {"schema_version": "1.0", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
             "scope": "Local key, locator, metadata, and exact paragraph binding checks. Fresh selected-source readings and retained historical receipts remain separate. No automatic claim-entailment or whole-bibliography full-text verification is asserted.",
             "source_bindings": bindings, "audit_input_bindings": audit_input_bindings,
             "bibliography_entries": len(entries),
             "cited_keys": len(used), "citation_occurrences": len(positions),
             "reading_level_counts": dict(Counter(r["fresh_reading_level"] for r in references)),
             "claim_scope_counts": dict(Counter(r["claim_scope_assessment"] for r in positions)),
             "unused_bibliography_keys": sorted(bibliography.keys() - used),
             "errors": errors, "metadata_differences_from_retained_receipts": differences,
             "references": references}
    output.mkdir(parents=True, exist_ok=True)
    dump(output / "audit.json", audit)
    with (output / "citation-positions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["citation_key", "file", "line", "paragraph_sha256", "claim_scope_assessment", "claim_scope_note", "paragraph"])
        writer.writeheader()
        writer.writerows(positions)
    dump(paper / "reference-reconciliation.json", {
        "scope": audit["scope"], "bibliography_sha256": digest(bib_bytes),
        "sources": {n.removeprefix("paper/"): h for n, h in source_hashes.items()},
        "current_audit": "artifact/citation-current/audit.json", "references": references})
    print(json.dumps({k: audit[k] for k in ("bibliography_entries", "cited_keys", "citation_occurrences", "reading_level_counts", "claim_scope_counts", "unused_bibliography_keys", "errors")}, indent=2))
    return int(any(errors.values()))


if __name__ == "__main__":
    raise SystemExit(main())
