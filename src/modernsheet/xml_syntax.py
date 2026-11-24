"""MusicXML sources in the app's editor (read only, SPEC §8.2): syntax highlighting tokens and
indentation for display (one element per line). Standard library only.

Token kinds: text, comment, decl (<?xml …?>, <!DOCTYPE …>), brace (< </ > />), tag, attr, value,
entity (&amp; …).
"""
from __future__ import annotations

import re

_NAME = r"[A-Za-z_][\w.\-]*"
_PIECE_RE = re.compile(
    r"(?P<comment><!--.*?(?:-->|\Z))"
    r"|(?P<decl><[?!][^>]*(?:>|\Z))"
    r"|(?P<tag></?" + _NAME + r"[^<>]*(?:>|(?=<)|\Z)|</?(?=\s|$|>))"
    r"|(?P<entity>&#?\w+;)"
    r"|(?P<text>[^<&]+|[<&])",
    re.DOTALL,
)
_TAG_PARTS_RE = re.compile(
    r"(?P<open></?)(?P<name>" + _NAME + r")?"
    r"|(?P<attr>" + _NAME + r")(?P<eq>\s*=\s*)?(?P<value>\"[^\"]*\"?|'[^']*'?)?"
    r"|(?P<close>/?>)"
    r"|(?P<space>\s+|.)",
    re.DOTALL,
)


def tokens(text: str) -> list[tuple[str, str]]:
    """Split a MusicXML source into (kind, text) runs that together give back `text` exactly.
    An unclosed tag or comment is coloured up to where the next one starts (or the end)."""
    out: list[tuple[str, str]] = []

    def add(kind: str, s: str):
        if not s:
            return
        if out and out[-1][0] == kind:
            out[-1] = (kind, out[-1][1] + s)
        else:
            out.append((kind, s))

    for m in _PIECE_RE.finditer(text):
        kind, s = m.lastgroup, m.group()
        if kind != "tag":
            add(kind, s)
            continue
        for p in _TAG_PARTS_RE.finditer(s):
            if p.group("open") is not None:
                add("brace", p.group("open"))
                add("tag", p.group("name") or "")
            elif p.group("attr") is not None:
                add("attr", p.group("attr"))
                add("brace", p.group("eq") or "")
                add("value", p.group("value") or "")
            elif p.group("close") is not None:
                add("brace", p.group("close"))
            else:
                add("text", p.group("space"))
    return out


# ---------------------------------------------------------------- indentation
INDENT = "  "
_STRUCT_RE = re.compile(
    r"(?P<comment><!--.*?-->)"
    r"|(?P<cdata><!\[CDATA\[.*?\]\]>)"
    r"|(?P<decl><[?!][^>]*>)"
    r"|(?P<end></(?P<ename>" + _NAME + r")\s*>)"
    r"|(?P<start><(?P<sname>" + _NAME + r")(?:\"[^\"]*\"|'[^']*'|[^<>\"'])*?(?P<empty>/?)>)"
    r"|(?P<text>[^<]+)",
    re.DOTALL,
)


def xml_error(text: str) -> tuple[int, str] | None:
    """(line, message) if `text` is not well-formed XML, else None."""
    import xml.etree.ElementTree as ET
    try:
        ET.fromstring(text.encode("utf-8"))
    except ET.ParseError as err:
        return err.position[0], str(err)
    return None


def format_xml(text: str) -> str:
    """Re-indent a well-formed XML source: one element per line, INDENT per level; an element holding
    only text stays on one line (<step>C</step>). Tags, attributes, text and comments are kept as they
    are; only the whitespace between elements changes. Check `xml_error` first: on a malformed source
    the result is a best effort."""
    kinds = []
    for m in _STRUCT_RE.finditer(text):
        kind = next(k for k in ("comment", "cdata", "decl", "end", "start", "text") if m.group(k) is not None)
        if kind == "text" and not m.group().strip():
            continue                                    # whitespace between elements: rebuilt below
        kinds.append((kind, m))
    lines: list[str] = []
    depth, i = 0, 0
    while i < len(kinds):
        kind, m = kinds[i]
        s = m.group()
        if kind == "start" and not m.group("empty"):
            name = m.group("sname")
            nxt = kinds[i + 1] if i + 1 < len(kinds) else None
            nxt2 = kinds[i + 2] if i + 2 < len(kinds) else None
            if nxt and nxt[0] == "end" and nxt[1].group("ename") == name:
                lines.append(INDENT * depth + s + nxt[1].group())
                i += 2
                continue
            if nxt and nxt[0] in ("text", "cdata") and nxt2 and nxt2[0] == "end" and nxt2[1].group("ename") == name:
                lines.append(INDENT * depth + s + nxt[1].group() + nxt2[1].group())
                i += 3
                continue
            lines.append(INDENT * depth + s)
            depth += 1
        elif kind == "end":
            depth = max(0, depth - 1)
            lines.append(INDENT * depth + s)
        elif kind == "text":
            lines.append(INDENT * depth + s.strip())    # mixed content (not used by MusicXML)
        else:
            lines.append(INDENT * depth + s)
        i += 1
    return "\n".join(lines) + "\n"
