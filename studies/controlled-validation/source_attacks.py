"""Text-level counterparts of the controlled attacks (part B, reviewer R6).

Every function here operates on rendered program TEXT. It never calls
covewm.benchmark.attacked_states and never renders an attacked carrier state:
carrier statements are located through their WM_SITE comment lines, their
lexical/structural shape is decided from the statement text, and sites are
selected with the declared rule of protocol.json (common.Rule).
Stdlib only.
"""
from __future__ import annotations

import re

from common import Rule

MARKER = re.compile(r"WM_SITE\s+\d+\s+(?:LEXICAL|STRUCTURAL)")

PY_DECL = re.compile(r"^(\s*)([A-Za-z_]\w*)(\s*=\s*)(.*)$")
PY_IF = re.compile(r"^(\s*)if\s+False\s*:\s*$")
PY_FOR = re.compile(r"^(\s*)for\s+([A-Za-z_]\w*)\s+in\s+\(\s*\)\s*:\s*$")
JS_DECL = re.compile(r"^(\s*)(const|let|var)(\s+)([A-Za-z_$][\w$]*)(\s*=\s*)(.*)$")
JS_IF = re.compile(r"^(\s*)if\s*\(\s*false\s*\)\s*\{\s*\}\s*$")
JS_FOR = re.compile(r"^(\s*)for\s*\(\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s+of\s+\[\s*\]\s*\)\s*\{\s*\}\s*$")


def _parts(name: str, digit_split: bool = True) -> list[str]:
    pattern = r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+" if digit_split else r"[A-Z]+(?![a-z0-9])|[A-Z]?[a-z0-9]+|\d+"
    out: list[str] = []
    for chunk in name.split("_"):
        out.extend(re.findall(pattern, chunk))
    return out


def to_snake(name: str, digit_split: bool = True) -> str:
    return "_".join(p.lower() for p in _parts(name, digit_split))


def to_camel(name: str) -> str:
    parts = [p.lower() for p in _parts(name)]
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def _comment(language: str) -> str:
    return "#" if language == "python" else "//"


def _is_skippable(line: str, language: str) -> bool:
    s = line.strip()
    return not s or s.startswith(("#", "//"))


class Program:
    """Line-based view of a rendered program with located carrier sites."""

    def __init__(self, source: str, language: str):
        self.language = language
        self.lines: list[str | None] = source.split("\n")
        self.sites: list[dict] = []
        for pos, line in enumerate(self.lines):
            if MARKER.search(line):
                self.sites.append({"marker": pos})
        for k, site in enumerate(self.sites):
            cursor = site["marker"] + 1
            while _is_skippable(self.lines[cursor], language):
                cursor += 1
            site["start"] = cursor
            site["end"] = self._statement_end(cursor)
            site["kind"] = self.shape(k)

    def _statement_end(self, start: int) -> int:
        """Inclusive last line of the statement starting at `start`."""
        line = self.lines[start]
        if self.language == "python":
            if not line.rstrip().endswith(":"):
                return start
            indent = len(line) - len(line.lstrip())
            end = start
            cursor = start + 1
            while cursor < len(self.lines):
                nxt = self.lines[cursor]
                if nxt is not None and nxt.strip() and len(nxt) - len(nxt.lstrip()) > indent:
                    end = cursor
                    cursor += 1
                else:
                    break
            return end
        depth, cursor = 0, start
        while True:
            depth += self.lines[cursor].count("{") - self.lines[cursor].count("}")
            if depth <= 0:
                return cursor
            cursor += 1

    def head(self, k: int) -> str:
        return self.lines[self.sites[k]["start"]]

    def shape(self, k: int) -> str:
        h = self.head(k)
        if self.language == "python":
            if PY_IF.match(h):
                return "control_conditional"
            if PY_FOR.match(h):
                return "control_loop"
            if PY_DECL.match(h):
                return "declaration"
        else:
            if JS_IF.match(h):
                return "control_conditional"
            if JS_FOR.match(h):
                return "control_loop"
            if JS_DECL.match(h):
                return "declaration"
        raise ValueError(f"unrecognized carrier statement shape: {h!r}")

    def declared_name(self, k: int) -> str:
        h = self.head(k)
        return PY_DECL.match(h).group(2) if self.language == "python" else JS_DECL.match(h).group(4)

    # --- identifier operations (whole-word, every occurrence) -------------
    def rename_identifier(self, old: str, new: str) -> bool:
        if old == new:
            return False
        pattern = re.compile(r"(?<![\w$])" + re.escape(old) + r"(?![\w$])")
        for i, line in enumerate(self.lines):
            if line is None or MARKER.search(line):
                continue
            self.lines[i] = pattern.sub(new, line)
        return True

    def canonicalize_identifier(self, k: int, digit_split: bool = True) -> bool:
        name = self.declared_name(k)
        return self.rename_identifier(name, to_snake(name, digit_split))

    def flip_identifier(self, k: int) -> bool:
        name = self.declared_name(k)
        new = to_camel(name) if name == to_snake(name) else to_snake(name)
        return self.rename_identifier(name, new)

    # --- control operations -------------------------------------------------
    def _set_head(self, k: int, text: str) -> None:
        self.lines[self.sites[k]["start"]] = text

    def _indent(self, k: int) -> str:
        h = self.head(k)
        return h[: len(h) - len(h.lstrip())]

    def to_conditional(self, k: int) -> bool:
        if self.sites[k]["kind"] == "control_conditional":
            return False
        ind = self._indent(k)
        self._set_head(k, ind + ("if False:" if self.language == "python" else "if (false) {}"))
        self.sites[k]["kind"] = "control_conditional"
        return True

    def to_loop(self, k: int) -> bool:
        if self.sites[k]["kind"] == "control_loop":
            return False
        ind = self._indent(k)
        var = f"_wm_{k:02d}"
        self._set_head(k, ind + (f"for {var} in ():" if self.language == "python" else f"for (const {var} of []) {{}}"))
        self.sites[k]["kind"] = "control_loop"
        return True

    def flip_control(self, k: int) -> bool:
        return self.to_loop(k) if self.sites[k]["kind"] == "control_conditional" else self.to_conditional(k)

    # --- deletion / formatting ------------------------------------------------
    def strip(self, k: int, keep_marker: bool = False) -> bool:
        site = self.sites[k]
        first = site["start"] if keep_marker else site["marker"]
        for i in range(first, site["end"] + 1):
            self.lines[i] = None
        return True

    def format_padding(self, k: int) -> bool:
        site = self.sites[k]
        ind = self._indent(k)
        marker = self.lines[site["marker"]]
        self.lines[site["marker"]] = f"{ind}{_comment(self.language)} format-only padding for site {k:02d}\n{marker}"
        self.lines[site["end"]] = self.lines[site["end"]] + "\n"
        return True

    def format_whitespace(self, k: int) -> bool:
        h = self.head(k)
        kind = self.sites[k]["kind"]
        if self.language == "python":
            if kind == "declaration":
                m = PY_DECL.match(h)
                new = f"{m.group(1)}{m.group(2)}={m.group(4)}"
            elif kind == "control_conditional":
                new = PY_IF.match(h).group(1) + "if False :"
            else:
                m = PY_FOR.match(h)
                new = f"{m.group(1)}for {m.group(2)} in ( ) :"
        else:
            if kind == "declaration":
                m = JS_DECL.match(h)
                new = f"{m.group(1)}{m.group(2)} {m.group(4)}={m.group(6)}"
            elif kind == "control_conditional":
                new = JS_IF.match(h).group(1) + "if(false){}"
            else:
                m = JS_FOR.match(h)
                new = f"{m.group(1)}for(const {m.group(2)} of[]){{}}"
        self._set_head(k, new)
        return h != new

    def text(self) -> str:
        return "\n".join(line for line in self.lines if line is not None)


def attack_source(source: str, language: str, rule: Rule, scheme: str, attack: str, severity: str,
                  task: str, payload_index: int, variant: str = "primary") -> tuple[str, list[tuple[int, str, bool]]]:
    """Apply a text-level attack to the rendered source. Returns (text, op log).

    The op log lists (site ordinal, operation, changed_text) for every selected site.
    """
    prog = Program(source, language)
    key = rule.key(scheme, attack, severity, task, language, payload_index)
    p = rule.probability(scheme, attack, severity)
    log: list[tuple[int, str, bool]] = []
    for k in range(len(prog.sites)):
        kind = prog.sites[k]["kind"]
        is_decl = kind == "declaration"
        if attack == "rename" and not is_decl:
            continue
        if attack == "normalize" and is_decl:
            continue
        if not rule.selected(key, attack, k, p):
            continue
        if attack == "format":
            if variant == "format_whitespace":
                log.append((k, "format_whitespace", prog.format_whitespace(k)))
            else:
                log.append((k, "format_padding", prog.format_padding(k)))
        elif attack == "rename":
            log.append((k, "lexical_canonicalize", prog.canonicalize_identifier(k, variant != "rename_no_digit_split")))
        elif attack == "normalize":
            log.append((k, "structural_canonicalize", prog.to_conditional(k)))
        elif attack == "random_flip":
            log.append((k, "bit_flip", prog.flip_identifier(k) if is_decl else prog.flip_control(k)))
        elif attack == "strip":
            log.append((k, "delete", prog.strip(k, keep_marker=variant == "strip_statement_only")))
        elif attack == "mixed":
            u = rule.mixed_selector(key, k)
            if u < 0.25:
                if is_decl:
                    log.append((k, "lexical_canonicalize", prog.canonicalize_identifier(k)))
                else:
                    log.append((k, "bit_flip", prog.flip_control(k)))
            elif u < 0.50:
                if not is_decl:
                    log.append((k, "structural_canonicalize", prog.to_conditional(k)))
                else:
                    log.append((k, "bit_flip", prog.flip_identifier(k)))
            elif u < 0.75:
                log.append((k, "bit_flip", prog.flip_identifier(k) if is_decl else prog.flip_control(k)))
            else:
                log.append((k, "delete", prog.strip(k)))
        else:
            raise KeyError(attack)
    return prog.text(), log
