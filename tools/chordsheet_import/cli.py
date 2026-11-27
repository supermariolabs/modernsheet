"""Command line of the chordsheet.com import (SPEC §9):

  python chordsheet_cli.py convert song.txt … [-o DIR] [--title …] [--pdf]
  python chordsheet_cli.py account EMAIL [-o DIR] [--list] [--match TEXT] [--again]

`convert` reads the text of the "Chords" field saved in .txt files; `account` logs in (the password is
asked on the terminal and never stored), then downloads the account's songs not yet in the folder."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from modernsheet import parse, render_pdf
from modernsheet.library import new_song_path

from . import account as A
from .convert import convert


def main(argv=None, *, client=None, ask_password=getpass.getpass) -> int:
    ap = argparse.ArgumentParser(prog="chordsheet_cli.py",
                                 description="Import from Chord Sheet Maker (chordsheet.com) into Modern Sheet .chs files.")
    sub = ap.add_subparsers(dest="command", required=True)
    c = sub.add_parser("convert", help="convert chordsheet.com texts (.txt) into .chs")
    c.add_argument("files", nargs="+", help="text files with the content of the Chords field")
    c.add_argument("-o", "--output", help="output folder (default: next to each input)")
    for opt in ("title", "artist", "key", "tempo", "time"):
        c.add_argument(f"--{opt}", default="", help=f"{opt} (chordsheet.com keeps it outside the chords text)")
    c.add_argument("--pdf", action="store_true", help="also render each converted song as PDF")
    a = sub.add_parser("account", help="log in and download the songs of a chordsheet.com account")
    a.add_argument("email", help="the account's e-mail (the password is asked, never stored)")
    a.add_argument("-o", "--output", default=".", help="folder for the .chs files (default: current folder)")
    a.add_argument("--list", action="store_true", help="only list the songs (* = already in the folder)")
    a.add_argument("--match", default="", help="only songs whose title or artist contains this text")
    a.add_argument("--again", action="store_true", help="also songs already imported into the folder (as new files)")
    args = ap.parse_args(argv)
    return convert_files(args) if args.command == "convert" else import_account(args, client, ask_password)


def convert_files(args) -> int:
    for f in args.files:
        src = Path(f)
        conv = convert(src.read_text(encoding="utf-8"), title=args.title, artist=args.artist,
                       key=args.key, tempo=args.tempo, time=args.time)
        out = (Path(args.output) / src.with_suffix(".chs").name) if args.output else src.with_suffix(".chs")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(conv.chs, encoding="utf-8")
        print(f"{src} -> {out}")
        for n in conv.notes:
            print(f"  note: {n}", file=sys.stderr)
        song = parse(conv.chs, base_dir=out.parent)
        for w in song.warnings:
            print(f"  warning: {w}", file=sys.stderr)
        if args.pdf:
            render_pdf(song, str(out.with_suffix(".pdf")))
            print(f"{out} -> {out.with_suffix('.pdf')}")
    return 0


def import_account(args, client=None, ask_password=getpass.getpass) -> int:
    dest = Path(args.output)
    client = client or A.Client()
    try:
        client.login(args.email, ask_password(f"chordsheet.com password for {args.email}: "))
        songs = client.songs()
    except A.LoginFailed:
        print("login failed: wrong e-mail or password", file=sys.stderr)
        return 1
    except A.SiteError as err:
        print(f"chordsheet.com: {err}", file=sys.stderr)
        return 1
    done = A.imported_ids(p.read_text(encoding="utf-8", errors="replace") for p in dest.rglob("*.chs")) \
        if dest.is_dir() else set()
    q = args.match.casefold()
    songs = [s for s in songs if q in f"{s.title} {s.artist}".casefold()]
    if args.list:
        for s in songs:
            print(f"{'*' if s.id in done else ' '} {s.id:>8}  " + " — ".join(x for x in (s.title, s.artist) if x))
        print(f"{len(songs)} songs, {len(done & {s.id for s in songs})} already in {dest}")
        return 0
    todo = [s for s in songs if args.again or s.id not in done]
    if not todo:
        print(f"nothing new to import into {dest}")
        return 0
    dest.mkdir(parents=True, exist_ok=True)
    ok = warn = failed = 0
    for i, (s, got) in enumerate(client.fetch_all(todo), 1):
        if isinstance(got, Exception):
            failed += 1
            print(f"[{i}/{len(todo)}] {s.title}: error {got}", file=sys.stderr)
            continue
        conv = A.to_chs(got)
        path = new_song_path(dest, got.song.title)            # never overwrites
        path.write_text(conv.text, encoding="utf-8")
        ok += 1
        warn += bool(conv.problems)
        print(f"[{i}/{len(todo)}] {got.song.title} -> {path.name}" + ("  (to check: tag import_warn)" if conv.problems else ""))
    print(f"{ok} imported into {dest}" + (f", {warn} to check" if warn else "") + (f", {failed} failed" if failed else ""))
    return 1 if failed else 0
