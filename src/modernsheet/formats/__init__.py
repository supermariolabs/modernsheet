"""Versions of the .chs format and the parser registry.

A file states its format in its first directive, `{format: v1}` (only comments and blank lines may
come before it). Files without it are format 1, the format of every file written before versioning.

Rules:
- the format number changes only with a *breaking* change (existing syntax changes meaning or is
  removed); additions (a new directive) keep the number: older software warns about the unknown
  directive and renders the rest;
- every format has its own parser module (v1.py, v2.py, …) with the signature
  parse(text, transpose=0, base_dir=None, files=None); all produce the same Song model, so
  layout and backends do not depend on the format;
- UPGRADES[n] rewrites a format-n source as format n+1; `upgrade()` chains them up to CURRENT;
- a file newer than this software is read, with a warning, by the newest parser available.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..model import Song
from . import v1

CURRENT = 1                                       # newest format this software reads and writes
PARSERS: dict[int, Callable[..., Song]] = {1: v1.parse}
UPGRADES: dict[int, Callable[[str], str]] = {}    # n -> function: format-n text -> format-(n+1) text

FORMAT_LINE_RE = re.compile(r"^\{\s*format\s*:\s*([^}]*)\}\s*$", re.IGNORECASE)
VALUE_RE = re.compile(r"v?(\d+)", re.IGNORECASE)


@dataclass
class FormatInfo:
    version: int                  # format to read the file with (1 if not stated)
    declared: bool                # the file has a valid {format: …}
    line: int | None = None       # 1-based line of the {format} directive
    problem: str | None = None    # warning about the directive itself


def label(version: int) -> str:
    return f"v{version}"


def detect(text: str) -> FormatInfo:
    """Read the {format: vN} directive. It must be the first directive; a later one still counts,
    with a warning. A missing or invalid value means format 1."""
    first = True
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = FORMAT_LINE_RE.match(line)
        if not m:
            first = False
            continue
        value = m.group(1).strip()
        v = VALUE_RE.fullmatch(value)
        if not v or int(v.group(1)) < 1:
            return FormatInfo(1, False, n, f"line {n}: invalid format '{value}' (expected v1, v2, …): reading as v1")
        problem = None if first else f"line {n}: {{format}} should be the first directive of the file"
        return FormatInfo(int(v.group(1)), True, n, problem)
    return FormatInfo(1, False)


def parse(text: str, transpose: int = 0, base_dir: Path | str | None = None,
          files: dict[Path, str] | None = None) -> Song:
    """Parse a .chs source with the parser of its format. base_dir: folder for {musicxml: …} paths;
    files: {path: content} of MusicXML files to use instead of reading them from disk (unsaved edits)."""
    info = detect(text)
    version = info.version
    notes = [info.problem] if info.problem else []
    if version > CURRENT:
        notes.append(f"line {info.line}: format {label(version)} is newer than this version of Modern Sheet "
                     f"(up to {label(CURRENT)}): reading it as {label(CURRENT)}, some parts may be wrong")
        version = CURRENT
    elif version not in PARSERS:          # a gap in the registry: should never happen
        notes.append(f"format {label(version)} is not supported: reading it as {label(CURRENT)}")
        version = CURRENT
    song = PARSERS[version](text, transpose=transpose, base_dir=base_dir, files=files)
    song.format = info.version
    song.warnings[:0] = notes
    return song


def set_format(text: str, version: int) -> str:
    """`text` with its {format} directive set to `version` (added before the first directive or music
    line if missing)."""
    directive = f"{{format: {label(version)}}}"
    lines = text.split("\n")
    info = detect(text)
    if info.line is not None:
        lines[info.line - 1] = directive
        return "\n".join(lines)
    for i, raw in enumerate(lines):
        line = raw.strip()
        if line and not line.startswith("#"):
            return "\n".join(lines[:i] + [directive] + lines[i:])
    return text + ("" if text.endswith("\n") or not text else "\n") + directive + "\n"


def upgrade(text: str) -> tuple[str, int, int]:
    """Rewrite a source in the current format; returns (new text, old format, new format).
    A file newer than CURRENT is returned unchanged."""
    info = detect(text)
    old = info.version
    if old > CURRENT:
        return text, old, old
    for n in range(old, CURRENT):
        text = UPGRADES[n](text)
    return set_format(text, CURRENT), old, CURRENT


def needs_upgrade(text: str) -> bool:
    """True if the file is in an older format than CURRENT or does not state its format."""
    info = detect(text)
    return info.version < CURRENT or not info.declared
