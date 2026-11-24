"""Command line: python -m modernsheet song.chs [options]"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import render_pdf
from .layout import THEMES
from .formats import CURRENT, detect, label, upgrade
from .parser import parse

def main(argv=None):
    """Command line: render .chs files to PDF, validate them (--check), or import chordsheet.com text
    (--from-chordsheet), show or upgrade the format version. Returns the exit status: 1 with --check
    if a file has warnings (so it can be used in scripts and CI), else 0."""
    ap = argparse.ArgumentParser(description="Render .chs chord sheets to PDF lead sheets.")
    ap.add_argument("files", nargs="+", help=".chs input files")
    ap.add_argument("-o", "--output", help="output PDF (single input) or folder")
    ap.add_argument("-t", "--transpose", type=int, default=0, help="semitones, e.g. 2 or -3")
    ap.add_argument("--bars-per-line", type=int, default=4, help="default bars per line (default 4)")
    ap.add_argument("--bar-width", choices=["uniform", "fit"], default="uniform",
                    help="uniform: same width for every bar (default); fit: each line fills the page")
    ap.add_argument("--row-spacing", default="normal", metavar="compact|normal|wide|extra|N%",
                    help="space between rows: a name or a percentage of the normal one (50%%-300%%)")
    ap.add_argument("--notation", choices=["staff", "both", "tab"], default="staff",
                    help="notated bars: staff (default), staff + guitar tablature, or tablature only")
    ap.add_argument("--paper", choices=["A4", "Letter"], default="A4")
    ap.add_argument("--theme", choices=list(THEMES), default="realbook",
                    help="realbook: handwritten jazz look (default); clean: plain sans-serif")
    ap.add_argument("--chord-symbols", choices=["text", "jazz"], default="text",
                    help="text: as written (Cmaj7, Cm7); jazz: CΔ7, C-7, Cø7, C°7")
    ap.add_argument("--label-colors", default="theme", metavar="theme|by_type|#RRGGBB",
                    help="section box colour: theme default, one colour per section type, or a fixed hex colour")
    ap.add_argument("--check", action="store_true", help="only parse and report warnings")
    fmt = ap.add_argument_group(".chs format versions")
    fmt.add_argument("--format-info", action="store_true",
                     help=f"print the format of each file (this version reads up to {label(CURRENT)})")
    fmt.add_argument("--upgrade", action="store_true",
                     help=f"rewrite the files in place in the current format ({label(CURRENT)})")
    imp = ap.add_argument_group("import from Chord Sheet Maker (chordsheet.com)")
    imp.add_argument("--from-chordsheet", action="store_true",
                     help="inputs are chordsheet.com texts: convert them to .chs (and render the PDF with --pdf)")
    imp.add_argument("--pdf", action="store_true", help="with --from-chordsheet: also render the converted song")
    for opt in ("title", "artist", "key", "tempo", "time"):
        imp.add_argument(f"--{opt}", default="", help=f"{opt} (chordsheet.com keeps it outside the chords text)")
    args = ap.parse_args(argv)

    status = 0
    if args.from_chordsheet:
        return import_chordsheet(args)
    if args.format_info or args.upgrade:
        return formats(args)
    for f in args.files:
        src = Path(f)
        song = parse(src.read_text(encoding="utf-8"), transpose=args.transpose, base_dir=src.parent)
        if args.check:
            print(f"{src}: {len(song.sections)} sections, {len(song.bars)} bars")
        else:
            out = output_path(args, src, ".pdf")
            render_pdf(song, str(out), bars_per_line=args.bars_per_line, bar_width=args.bar_width, row_spacing=args.row_spacing, notation=args.notation,
                       paper=args.paper, theme=args.theme, chord_symbols=args.chord_symbols,
                       label_colors=args.label_colors)
            print(f"{src} -> {out}")
        for w in song.warnings:
            print(f"  warning: {w}", file=sys.stderr)
            status = 1 if args.check else status
    return status




def formats(args) -> int:
    status = 0
    for f in args.files:
        src = Path(f)
        text = src.read_text(encoding="utf-8")
        info = detect(text)
        if args.format_info:
            state = "declared" if info.declared else "not declared, read as v1"
            newer = f" — newer than this version (up to {label(CURRENT)})" if info.version > CURRENT else ""
            print(f"{src}: format {label(info.version)} ({state}){newer}")
            if info.problem:
                print(f"  warning: {info.problem}", file=sys.stderr)
            continue
        new, old, to = upgrade(text)
        if old > CURRENT:
            print(f"{src}: format {label(old)} is newer than this version: not changed", file=sys.stderr)
            status = 1
        elif new == text:
            print(f"{src}: already {label(to)}")
        else:
            src.write_text(new, encoding="utf-8")
            print(f"{src}: {label(old)} -> {label(to)}")
    return status


def output_path(args, src: Path, suffix: str) -> Path:
    """-o can be a file or a folder (a folder if it exists, ends with '/', or there are several inputs).
    Missing folders are created."""
    if not args.output:
        return src.with_suffix(suffix)
    o = Path(args.output)
    if len(args.files) > 1 or o.is_dir() or args.output.endswith(("/", os.sep)) or not o.suffix:
        o.mkdir(parents=True, exist_ok=True)
        return o / (src.stem + suffix)
    o.parent.mkdir(parents=True, exist_ok=True)
    return o


def import_chordsheet(args) -> int:
    from .importers import from_chordsheet_com
    for f in args.files:
        src = Path(f)
        conv = from_chordsheet_com(src.read_text(encoding="utf-8"), title=args.title or "", artist=args.artist,
                                   key=args.key, tempo=args.tempo, time=args.time)
        out = output_path(args, src, ".chs")
        out.write_text(conv.chs, encoding="utf-8")
        print(f"{src} -> {out}")
        for n in conv.notes:
            print(f"  note: {n}", file=sys.stderr)
        song = parse(conv.chs, base_dir=out.parent)
        for w in song.warnings:
            print(f"  warning: {w}", file=sys.stderr)
        if args.pdf:
            pdf = out.with_suffix(".pdf")
            render_pdf(song, str(pdf), bars_per_line=args.bars_per_line, bar_width=args.bar_width, row_spacing=args.row_spacing, notation=args.notation,
                       paper=args.paper, theme=args.theme, chord_symbols=args.chord_symbols,
                       label_colors=args.label_colors)
            print(f"{out} -> {pdf}")
    return 0
