"""Download the pinned sdist of each transfer project from PyPI and extract it.

Each archive is verified against the PyPI-published sha256 and extracted into
its own new, empty directory with tarfile's 'data' filter.  Usage:

    python3 -I fetch_sources.py <artifact-root> <work-dir>

Writes <work-dir>/sources.json describing every archive.  Standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path


GIT_TAGS = {
    "rich": ("https://github.com/Textualize/rich/archive/refs/tags/v15.0.0.tar.gz", "test-source"),
    "asn1crypto": ("https://github.com/wbond/asn1crypto/archive/refs/tags/1.5.1.tar.gz", "test-source"),
    "httpx": ("https://github.com/encode/httpx/archive/refs/tags/0.28.1.tar.gz", "declarations-only"),
    # added by deviations.json: the sdist test tree lacks tests/__init__.py
    "jmespath": ("https://github.com/jmespath/jmespath.py/archive/refs/tags/1.1.0.tar.gz", "test-source (deviation)"),
}


def main() -> int:
    artifact, work = Path(sys.argv[1]), Path(sys.argv[2])
    rows = list(csv.DictReader((artifact / "corpus/project_manifest.csv").open(encoding="utf-8", newline="")))
    out = {}
    for row in rows:
        name, version = row["project"], row["version"]
        meta = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=60))
        sdists = [u for u in meta["urls"] if u["packagetype"] == "sdist"]
        if len(sdists) != 1:
            out[name] = {"version": version, "error": f"{len(sdists)} sdists"}
            continue
        info = sdists[0]
        archive_dir = work / "archives" / name
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive = archive_dir / info["filename"]
        if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != info["digests"]["sha256"]:
            data = urllib.request.urlopen(info["url"], timeout=300).read()
            archive.write_bytes(data)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != info["digests"]["sha256"]:
            raise SystemExit(f"digest mismatch for {name}")
        target = work / "pristine" / name
        if not target.exists():
            target.mkdir(parents=True)
            if archive.name.endswith(".zip"):
                with zipfile.ZipFile(archive) as handle:
                    for member in handle.namelist():
                        if member.startswith("/") or ".." in Path(member).parts:
                            raise SystemExit(f"unsafe member {member}")
                    handle.extractall(target)
            else:
                with tarfile.open(archive) as handle:
                    handle.extractall(target, filter="data")
        roots = [p for p in target.iterdir() if p.is_dir()]
        out[name] = {
            "version": version,
            "sdist_filename": info["filename"],
            "sdist_url": info["url"],
            "sdist_sha256": digest,
            "upload_time": info.get("upload_time_iso_8601", ""),
            "root": str(roots[0]) if len(roots) == 1 else "",
        }
        print(name, version, info["filename"], flush=True)
    # Official-repository tag archives: used as the test source when the sdist
    # ships no tests (rich, asn1crypto) and, for httpx, only to read the
    # test-requirement declaration that the sdist omits.
    for name, (url, role) in GIT_TAGS.items():
        archive_dir = work / "archives" / (name + "-gittag")
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive = archive_dir / url.rsplit("/", 1)[1]
        if not archive.exists():
            archive.write_bytes(urllib.request.urlopen(url, timeout=300).read())
        target = work / "pristine-gittag" / name
        if not target.exists():
            target.mkdir(parents=True)
            with tarfile.open(archive) as handle:
                handle.extractall(target, filter="data")
        roots = [p for p in target.iterdir() if p.is_dir()]
        out[name]["git_tag"] = {
            "url": url,
            "role": role,
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "root": str(roots[0]) if len(roots) == 1 else "",
        }
        print(name, "git tag", url, flush=True)
    (work / "sources.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
