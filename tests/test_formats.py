"""Regression tests — .chs format versions. Run with `pytest` from the project folder."""
import pytest

from modernsheet import parse
from modernsheet.importers import from_chordsheet_com

from helpers import SONGS, V1_SONG


# ---- .chs format versions
from modernsheet import formats  # noqa: E402


@pytest.mark.parametrize("path", SONGS, ids=lambda p: p.stem)
def test_examples_declare_the_current_format(path):
    info = formats.detect(path.read_text(encoding="utf-8"))
    assert info.declared and info.version == formats.CURRENT and info.problem is None


def test_format_detect():
    assert formats.detect(V1_SONG) == formats.FormatInfo(1, False)
    assert formats.detect("# c\n\n{format: v1}\n" + V1_SONG) == formats.FormatInfo(1, True, 3)
    assert formats.detect("{ FORMAT : V2 }").version == 2
    assert formats.detect("{format: 1}").version == 1               # number alone accepted
    late = formats.detect("{title: T}\n{format: v1}")
    assert late.version == 1 and late.line == 2 and "first directive" in late.problem
    bad = formats.detect("{format: banana}")
    assert bad.version == 1 and not bad.declared and "invalid format" in bad.problem


def test_format_parse_and_newer_files():
    song = parse("{format: v1}\n" + V1_SONG)
    assert song.format == 1 and song.warnings == [] and len(song.bars) == 2
    assert parse(V1_SONG).format == 1
    newer = parse("{format: v9}\n" + V1_SONG)
    assert newer.format == 9 and len(newer.bars) == 2                # read anyway, as the newest format
    assert "newer than this version" in newer.warnings[0] and newer.warnings[0].startswith("line 1:")


def test_set_format_and_upgrade_to_current():
    assert formats.set_format(V1_SONG, 1) == "{format: v1}\n" + V1_SONG
    assert formats.set_format("# c\n{title: T}\n", 1) == "# c\n{format: v1}\n{title: T}\n"
    assert formats.set_format("{format: 1}\n" + V1_SONG, 1) == "{format: v1}\n" + V1_SONG
    assert formats.set_format("", 1) == "{format: v1}\n"
    assert formats.upgrade(V1_SONG) == ("{format: v1}\n" + V1_SONG, 1, 1)
    assert formats.needs_upgrade(V1_SONG) and not formats.needs_upgrade("{format: v1}\n" + V1_SONG)
    assert formats.upgrade("{format: v9}\nx")[0] == "{format: v9}\nx"     # newer: never touched


def test_format_registry_with_a_breaking_v2(monkeypatch):
    """Simulate a future breaking change: in v2 a bar line is '/' instead of '|'."""
    def parse_v2(text, transpose=0, base_dir=None, files=None):
        return formats.v1.parse(text.replace("/", "|"), transpose=transpose, base_dir=base_dir, files=files)

    monkeypatch.setattr(formats, "CURRENT", 2)
    monkeypatch.setitem(formats.PARSERS, 2, parse_v2)
    monkeypatch.setitem(formats.UPGRADES, 1, lambda text: text.replace("|", "/"))
    v2 = "{format: v2}\n{start_of_verse: S}\n/ [C] / [G] /\n{end_of_verse}\n"
    assert len(parse(v2).bars) == 2 and parse(v2).warnings == []
    assert len(parse(V1_SONG).bars) == 2                              # old files keep their meaning
    new, old, to = formats.upgrade(V1_SONG)
    assert (old, to) == (1, 2) and new.startswith("{format: v2}\n") and "/ [C] / [G] /" in new
    assert [len(s.bars) for s in parse(new).sections] == [2]
    assert formats.needs_upgrade(V1_SONG)


def test_new_files_declare_the_format():
    from modernsheet import library
    assert formats.detect(library.new_song_text("X")).declared
    assert formats.detect(from_chordsheet_com("| C | G |").chs).declared
