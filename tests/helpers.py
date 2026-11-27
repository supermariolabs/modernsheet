"""Shared by the regression tests: the bundled examples and how to read them."""
from pathlib import Path

from modernsheet import parse
from chordsheet_import import from_chordsheet_com

EX = Path(__file__).resolve().parents[1] / "src" / "examples"
SONGS = sorted(EX.glob("*.chs"))
OPTIONS = [dict(), dict(theme="clean", bar_width="fit"), dict(chord_symbols="jazz", label_colors="by_type")]


def load(path, transpose=0):
    return parse(path.read_text(encoding="utf-8"), transpose=transpose, base_dir=path.parent)


V1_SONG = "{start_of_verse: S}\n| [C] | [G] |\n{end_of_verse}\n"


def csm_song(text, **meta):
    conv = from_chordsheet_com(text, **meta)
    song = parse(conv.chs)
    assert song.warnings == [], conv.chs
    return conv, song


def notes_song(body, key="F", time="4/4", transpose=0):
    return parse(f"{{key: {key}}}\n{{time: {time}}}\n{{start_of_intro}}\n{{start_of_notes}}\n{body}\n"
                 f"{{end_of_notes}}\n{{end_of_intro}}\n", transpose=transpose)
