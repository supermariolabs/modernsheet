"""Regression tests for the engine: run with `pytest` from the project folder."""
from pathlib import Path

import pytest

from modernsheet import layout, parse
from modernsheet.fonts import registry
from modernsheet.pdf import pdf_bytes
from modernsheet.screen import screen_ops
from modernsheet.theory import transpose_chord

EX = Path(__file__).resolve().parents[1] / "src" / "examples"
SONGS = sorted(EX.glob("*.chs"))
OPTIONS = [dict(), dict(theme="clean", bar_width="fit"), dict(chord_symbols="jazz", label_colors="by_type")]


def load(path, transpose=0):
    return parse(path.read_text(encoding="utf-8"), transpose=transpose, base_dir=path.parent)


@pytest.mark.parametrize("path", SONGS, ids=lambda p: p.stem)
def test_examples_parse_without_warnings(path):
    song = load(path)
    assert song.sections and song.bars
    assert song.warnings == []


@pytest.mark.parametrize("opts", OPTIONS)
@pytest.mark.parametrize("path", SONGS, ids=lambda p: p.stem)
def test_layout_and_pdf(path, opts):
    dl = layout(load(path), **opts)
    assert dl.pages and all(dl.pages)
    assert pdf_bytes(dl).startswith(b"%PDF")


@pytest.mark.parametrize("path", SONGS, ids=lambda p: p.stem)
def test_screen_ops_stay_on_page(path):
    dl = layout(load(path))
    m = registry("realbook")
    w, h = dl.page_size
    for i in range(len(dl.pages)):
        for op in screen_ops(dl, i, 1.0, m):
            if op[0] == "line":
                assert -1 <= op[1] <= w + 1 and -1 <= op[2] <= h + 1


def test_flet_shapes_build():
    flet = pytest.importorskip("flet")  # noqa: F841
    from modernsheet.flet_view import page_shapes
    path = EX / "blues_con_melodia.chs"
    dl = layout(load(path))
    shapes = page_shapes(dl, 0, registry("realbook"), 1.5)
    assert len(shapes) > 100


def test_transpose_octave_is_identity():
    for ch in ["C7", "Bbmaj7", "F#m7b5", "Em7/D", "Ab13"]:
        assert transpose_chord(ch, 12, "C") == ch


def test_transposed_song_has_no_warnings():
    song = load(EX / "blues_con_melodia.chs", transpose=-2)
    assert song.warnings == []
    assert song.meta["key"] == "Eb"


# ---- import from Chord Sheet Maker (chordsheet.com)
from modernsheet.importers import from_chordsheet_com  # noqa: E402

CSM = Path(__file__).resolve().parent / "data" / "esempio_chordsheet_com.txt"


def csm_song(text, **meta):
    conv = from_chordsheet_com(text, **meta)
    song = parse(conv.chs)
    assert song.warnings == [], conv.chs
    return conv, song


def test_csm_example_converts_cleanly():
    conv, song = csm_song(CSM.read_text(encoding="utf-8"))
    assert song.meta["title"] == "Esempio da Chord Sheet Maker"
    assert song.meta["key"] == "G" and song.meta["tempo"] == "96"
    assert [s.kind for s in song.sections] == ["intro", "verse", "chorus", "bridge", "coda"]
    assert pdf_bytes(layout(song)).startswith(b"%PDF")


def test_csm_bars_glue_repeats_and_simile():
    _, song = csm_song("(C Am_D7 % G)x3\n|:F G:| C || %% *")
    bars = song.bars
    assert [e.chord for e in bars[1].events] == ["Am", "D7"]
    assert bars[0].repeat_start and bars[3].repeat_end == 3
    assert [e.chord for e in bars[2].events] == ["Am", "D7"]       # % of a 2-chord bar copies it
    assert bars[5].repeat_end == 2 and bars[6].double_after
    assert [e.chord for e in bars[7].events] == ["G"] and [e.chord for e in bars[8].events] == ["C"]


def test_csm_endings():
    _, song = csm_song("(A B 1. C D 2. E F)")
    b = song.bars
    assert b[2].volta == "1." and b[3].repeat_end == 2
    assert b[4].volta == "2." and b[5].volta_end and b[5].double_after


def test_csm_time_rests_and_nashville():
    _, song = csm_song("3:4 1 4 5 r1\n4:4 6m_2m 5/7", key="D")
    chords = [[e.chord for e in b.events] for b in song.bars]
    assert chords[:4] == [["D"], ["G"], ["A"], ["/"]]
    assert chords[4] == ["Bm", "Em"] and chords[5] == ["A/C#"]
    assert song.bars[0].num == 3 and song.bars[4].num == 4


# ---- song library (app browser and editor)
def test_library_scan_and_search(tmp_path):
    from modernsheet import library
    (tmp_path / "Jazz" / "Blues").mkdir(parents=True)
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "Empty").mkdir()
    (tmp_path / "Jazz" / "Blues" / "lunedi.chs").write_text("# c\n{title: Blues del lunedì}\n", encoding="utf-8")
    (tmp_path / "Jazz" / "notes.txt").write_text("not a song", encoding="utf-8")
    (tmp_path / "b_song.chs").write_text("{key: C}\n", encoding="utf-8")
    (tmp_path / "A song.CHS").write_text("{title: Alba}\n", encoding="utf-8")
    (tmp_path / ".hidden" / "x.chs").write_text("{title: X}\n", encoding="utf-8")

    tree = library.scan(tmp_path)
    assert [f.name for f in tree.folders] == ["Empty", "Jazz"]        # hidden folders skipped, empty ones kept
    assert tree.find(tmp_path / "Empty").count() == 0
    assert [s.title for s in tree.songs] == ["Alba", "b song"]        # sorted by name, title or file name
    assert tree.count() == 3
    blues = tree.find(tmp_path / "Jazz" / "Blues")
    assert blues and [s.path.name for s in blues.songs] == ["lunedi.chs"]
    assert tree.find(tmp_path / "Nope") is None

    assert [s.title for s in library.search(tree, "LUNEDI")] == ["Blues del lunedì"]   # case and accents
    assert [s.title for s in library.search(tree, "jazz blues")] == ["Blues del lunedì"]  # folder names too
    assert library.search(tree, "  ") == []


def test_library_new_song(tmp_path):
    from modernsheet import library
    assert library.safe_filename(' Il mio/brano: "uno" ') == "Il mio brano uno"
    assert library.safe_filename("..") == "Nuovo brano"
    p1 = library.new_song_path(tmp_path, "Brano")
    p1.write_text(library.new_song_text("Brano"), encoding="utf-8")
    assert p1.name == "Brano.chs"
    assert library.new_song_path(tmp_path, "Brano").name == "Brano 2.chs"
    song = parse(p1.read_text(encoding="utf-8"))                         # the template reads without warnings
    assert song.meta["title"] == "Brano" and song.bars and song.warnings == []


def test_library_warning_lines():
    from modernsheet import library
    text = "a\nbb\nccc"
    assert [library.line_offset(text, n) for n in (1, 2, 3, 9)] == [0, 2, 5, 8]   # clamped to the end
    song = parse("{start_of_verse: S}\n| [Xyz] |\n{end_of_verse}\n")
    assert [library.warning_line(w) for w in song.warnings] == [2]
    assert library.warning_line("no line") is None


# ---- app settings and editor support (pure Python parts of the app)
from modernsheet import syntax  # noqa: E402
from modernsheet.settings import Settings  # noqa: E402


def test_settings_roundtrip_and_validation():
    s = Settings(library_root="/x", pdf_dir="/y", theme="clean", bar_width="fit", row_spacing="wide",
                 notation="both", chord_symbols="jazz", label_colors="by_type")
    assert Settings.from_json(s.to_json()) == s
    assert s.layout_options() == dict(theme="clean", bar_width="fit", row_spacing="wide", notation="both",
                                      chord_symbols="jazz", label_colors="by_type")
    bad = Settings.from_json('{"theme": "neon", "row_spacing": "huge", "pdf_dir": 3, "library_root": "  ", "extra": 1}')
    assert bad == Settings()
    assert Settings.from_json(None) == Settings() == Settings.from_json("not json") == Settings.from_json("[1]")


@pytest.mark.parametrize("path", SONGS, ids=lambda p: p.stem)
def test_syntax_tokens_cover_the_source(path):
    text = path.read_text(encoding="utf-8")
    toks = syntax.tokens(text)
    assert "".join(s for _, s in toks) == text
    assert {k for k, _ in toks} <= {"text", "comment", "brace", "directive", "section", "value", "chord",
                                    "duration", "bar", "note", "rest"}


def test_syntax_token_kinds():
    toks = syntax.tokens("# c\n{start_of_verse: A}\n|: [C:2] la :| x3\n[G7 \n{titl")
    assert ("comment", "# c") in toks
    assert ("section", "start_of_verse:") in toks and ("value", " A") in toks
    assert ("chord", "[C") in toks and ("duration", ":2") in toks
    assert ("bar", "|:") in toks and ("bar", ":| x3") in toks
    assert ("chord", "[G7 ") in toks                  # unclosed chord: up to the end of the line
    assert toks[-2:] == [("brace", "{"), ("directive", "titl")]


def test_completion_context_and_suggestions():
    assert syntax.context("ab", 2) is None
    assert syntax.context("{ti", 3) == (1, "ti")
    assert syntax.context("{title: x", 9) is None                # past the name
    assert syntax.context("{\nx", 3) is None                     # other line
    names = [c.name for c in syntax.suggestions("{t", 2)]
    assert names[:3] == ["title", "time", "tempo"]
    assert "subtitle" in names                                   # contains "t" too, listed after
    inside = "{start_of_chorus: R}\n| [C] |\n{"
    names = [c.name for c in syntax.suggestions(inside, len(inside))]
    assert names[0] == "end_of_chorus" and not any(n.startswith("start_of_") for n in names if n != "start_of_notes")
    assert "start_of_notes" in names                             # a notes block goes inside a section


def test_completion_apply():
    by = {c.name: c for c in syntax.directives()}
    assert syntax.apply("x {ti", 5, by["title"]) == ("x {title: }", 10, 10)
    assert syntax.apply("{", 1, by["time"]) == ("{time: 4/4}", 7, 10)          # placeholder selected
    text, a, b = syntax.apply("{st", 3, by["start_of_verse"])
    assert text == "{start_of_verse: Strofa}\n\n{end_of_verse}" and text[a:b] == "Strofa"
    assert syntax.apply("{ti: X}", 3, by["title"]) == ("{title: X}", 6, 6)     # only the name is completed
    text = "{start_of_verse}\n{"
    end = syntax.suggestions(text, len(text))[0]
    assert syntax.apply(text, len(text), end)[0] == "{start_of_verse}\n{end_of_verse}"
    # every completed directive is understood by the parser
    for c in syntax.directives():
        src, _, _ = syntax.apply("{", 1, c)
        if c.name in ("ref", "musicxml", "key"):
            continue                                             # need a real value
        song = parse("{title: T}\n" + src + "\n{start_of_verse}\n| [C] |\n{end_of_verse}\n")
        assert not [w for w in song.warnings if "unknown directive" in w], c.name


def test_caret_row_col_wraps_between_words():
    f = syntax.caret_row_col
    assert f("", 0, 5) == (0, 0)
    assert f("ab cd", 4, 3) == (1, 1)                 # "cd" does not fit after "ab ": new row
    assert f("ab cd ef", 7, 5) == (1, 1)              # "ab cd" fits exactly, the space hangs
    assert f("abcdefgh", 7, 3) == (2, 1)              # a word longer than a row is split
    assert f("x\nab cd", 6, 3) == (2, 1)              # rows of previous lines count
    assert f("abc\n", 4, 10) == (1, 0)


# ---- .chs format versions
from modernsheet import formats  # noqa: E402

V1_SONG = "{start_of_verse: S}\n| [C] | [G] |\n{end_of_verse}\n"


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


# ---- tags, song index, card view helpers
def test_tags_directive():
    song = parse("{format: v1}\n{tags: Jazz,  Bossa   Nova , }\n{tags: jazz, ballad}\n" + V1_SONG)
    assert song.tags == ["jazz", "bossa nova", "ballad"] and song.warnings == []


def test_read_info_header(tmp_path):
    from modernsheet import library
    p = tmp_path / "x_y.chs"
    p.write_text("{format: v1}\n{composer: C}\n{key: Bb}\n{time: 3/4}\n{tempo: 96}\n{tags: a, B}\n"
                 "{start_of_verse}\n| [C] |\n{key: G}\n{tags: c}\n{end_of_verse}\n", encoding="utf-8")
    info = library.read_info(p)
    assert (info.title, info.artist, info.key, info.time, info.tempo) == ("x y", "C", "Bb", "3/4", "96")
    assert info.tags == ["a", "b", "c"] and info.format == 1


def test_library_index_reads_only_changed_files(tmp_path):
    from modernsheet import library
    root, data = tmp_path / "songs", tmp_path / "data"
    (root / "sub").mkdir(parents=True)
    (root / "a.chs").write_text("{title: A}\n{tags: x}\n", encoding="utf-8")
    (root / "sub" / "b.chs").write_text("{title: B}\n", encoding="utf-8")
    file = library.index_path(data, root)
    assert file.parent == data / "index" and file == library.index_path(data, root / "sub" / "..")

    idx = library.Index(file)
    tree = library.scan(root, idx)
    assert (idx.hits, idx.misses) == (0, 2) and file.exists()
    idx = library.Index(file)
    library.scan(root, idx)
    assert (idx.hits, idx.misses) == (0 + 2, 0)                     # nothing re-read

    import os
    (root / "a.chs").write_text("{title: A2}\n{tags: y, z}\n", encoding="utf-8")
    os.utime(root / "a.chs", ns=(1, 1))                              # changed mtime (and size)
    (root / "sub" / "b.chs").unlink()
    (root / "c.chs").write_text("{title: C}\n", encoding="utf-8")
    idx = library.Index(file)
    tree = library.scan(root, idx)
    assert (idx.hits, idx.misses) == (0, 2)
    assert {s.title: s.tags for s in tree.walk()} == {"A2": ["y", "z"], "C": []}
    assert set(library.Index(file).entries) == {"a.chs", "c.chs"}   # deleted files leave the index

    file.write_text("not json", encoding="utf-8")                    # a broken index is rebuilt
    idx = library.Index(file)
    assert [s.title for s in library.scan(root, idx).walk()] == ["A2", "C"] and idx.misses == 2


def test_library_search_artist_and_tags(tmp_path):
    from modernsheet import library
    (tmp_path / "one.chs").write_text("{title: Uno}\n{artist: Miles}\n{tags: jazz, ballad}\n", encoding="utf-8")
    (tmp_path / "two.chs").write_text("{title: Due}\n{tags: jazzy}\n", encoding="utf-8")
    tree = library.scan(tmp_path)
    names = lambda q: sorted(s.title for s in library.search(tree, q))   # noqa: E731
    assert names("miles") == ["Uno"]
    assert names("jazz") == ["Due", "Uno"]                           # plain words: substring
    assert names("#jazz") == ["Uno"]                                 # #tag: exact tag
    assert names("#jazz due") == [] and names("#BALLAD") == ["Uno"]


def test_sort_songs():
    from modernsheet.library import SongFile, sort_songs
    P = Path("x.chs")
    songs = [SongFile(P, "b", artist="Zed", key="G", tempo="120", mtime=3),
             SongFile(P, "a", key="Bbm", tempo="80", mtime=1),
             SongFile(P, "c", artist="Amy", key="Bb", mtime=2),
             SongFile(P, "D", key="C#")]
    title = lambda by, d=False: [s.title for s in sort_songs(songs, by, d)]   # noqa: E731
    assert title("title") == ["a", "b", "c", "D"] and title("title", True) == ["D", "c", "b", "a"]
    assert title("artist") == ["c", "b", "a", "D"]                  # no artist: last
    assert title("artist", True) == ["b", "c", "a", "D"]            # …also when descending
    assert title("key") == ["D", "b", "c", "a"]                     # C#, G, Bb, Bbm
    assert title("tempo") == ["a", "b", "c", "D"]
    assert title("modified", True) == ["b", "c", "a", "D"]
    assert title("bogus") == title("title")


def test_settings_library_view_and_sort():
    s = Settings.from_json('{"library_view": "list", "sort_by": "tempo", "sort_desc": true}')
    assert (s.library_view, s.sort_by, s.sort_desc) == ("list", "tempo", True)
    assert "sort_by" not in s.layout_options()
    assert Settings.from_json('{"library_view": "grid", "sort_desc": "yes"}') == Settings()


# ---- user interface languages
def test_i18n_catalog_is_complete():
    import string
    from modernsheet import i18n
    for key, entry in i18n.CATALOG.items():
        assert set(entry) == set(i18n.LANGUAGES), key
        fields = [{f for _, f, _, _ in string.Formatter().parse(entry[lang]) if f} for lang in i18n.LANGUAGES]
        assert all(f == fields[0] for f in fields), key           # same placeholders in every language


def test_i18n_every_key_used_by_the_app_exists():
    import re
    from modernsheet import i18n
    src = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
    used = set(re.findall(r'\btr\(\s*"([^"{]+)"', src)) | {f"{k}.{n}" for k in re.findall(r'tr_count\([^,]+,\s*"([^"]+)"', src)
                                                            for n in ("one", "many")}
    used |= {f"sort.{k}" for k in library_sort_keys()} | {f"hint.{c.name}" for c in syntax.directives()
                                                         if not c.name.startswith("start_of_")}
    assert used and not (used - set(i18n.CATALOG))


def library_sort_keys():
    from modernsheet import library
    return library.SORT_KEYS


def test_i18n_switch_language():
    from modernsheet import i18n, library
    try:
        assert i18n.tr("new_song", "en") == "New song" and i18n.tr_count(1, "songs", "en") == "1 song"
        assert i18n.tr("lib.results", "it", n=3, folder="x") == "3 risultati in x"
        assert i18n.tr("no.such.key") == "no.such.key"
        i18n.set_language("en")
        assert "{start_of_verse: Verse}" in library.new_song_text("T")
        verse = next(c for c in syntax.directives() if c.name == "start_of_verse")
        assert verse.hint == "Verse section" and "‹Verse›" in verse.snippet
        i18n.set_language("xx")                                        # unknown: default language
        assert i18n.language() == "it" and "{start_of_verse: Strofa}" in library.new_song_text("T")
    finally:
        i18n.set_language(i18n.DEFAULT)
    assert Settings.from_json('{"language": "en"}').language == "en"
    assert Settings.from_json('{"language": "fr"}').language == "it"


def test_library_new_folder(tmp_path):
    from modernsheet import library
    a = library.new_folder_path(tmp_path, "Jazz: standard/2")
    assert a == tmp_path / "Jazz standard 2"
    a.mkdir()
    assert library.new_folder_path(tmp_path, "Jazz standard 2") == tmp_path / "Jazz standard 2 2"
    assert library.new_folder_path(tmp_path, ".nascosta") == tmp_path / "nascosta"
    assert library.new_folder_path(tmp_path, "  ").name == "Nuova cartella"
    (tmp_path / "x.chs").write_text("{title: X}", encoding="utf-8")
    assert library.new_folder_path(tmp_path, "x.chs") == tmp_path / "x.chs 2"   # no clash with files either
    assert [f.name for f in library.scan(tmp_path).folders] == ["Jazz standard 2"]


# ---- editor tabs: MusicXML files of a song
from modernsheet import xml_syntax  # noqa: E402


def test_musicxml_refs_and_template(tmp_path):
    from modernsheet import library
    text = "{start_of_intro}\n{musicxml: a.musicxml}\n{musicxml: b.xml | 3-4}\n{musicxml: a.musicxml | 1}\n" \
           "| {musicxml: inline.musicxml} [C] |\n{end_of_intro}\n"
    assert library.musicxml_refs(text) == ["a.musicxml", "b.xml"]          # own line only, no duplicates
    (tmp_path / "a.musicxml").write_text(library.new_musicxml_text(3, 4, -1), encoding="utf-8")
    song = parse("{key: F}\n{time: 3/4}\n{start_of_intro}\n{musicxml: a.musicxml}\n{end_of_intro}\n",
                 base_dir=tmp_path)
    assert len(song.bars) == 1 and song.warnings == []


def test_parse_uses_unsaved_musicxml(tmp_path):
    from modernsheet import library
    f = tmp_path / "a.musicxml"
    f.write_text(library.new_musicxml_text(4, 4, 0), encoding="utf-8")
    src = "{start_of_intro}\n{musicxml: a.musicxml}\n{end_of_intro}\n"
    two = library.new_musicxml_text(4, 4, 0).replace("</measure>", '</measure>\n<measure number="2"><note>'
                                                     '<rest measure="yes"/><duration>4</duration></note></measure>')
    assert len(parse(src, base_dir=tmp_path).bars) == 1
    assert len(parse(src, base_dir=tmp_path, files={f: two}).bars) == 2     # the edited text wins
    assert "a.musicxml" in parse(src, base_dir=tmp_path, files={f: "<broken"}).warnings[0]   # warning, no crash


@pytest.mark.parametrize("path", sorted(EX.glob("*.musicxml")), ids=lambda p: p.stem)
def test_xml_tokens_cover_the_source(path):
    text = path.read_text(encoding="utf-8")
    toks = xml_syntax.tokens(text)
    assert "".join(s for _, s in toks) == text
    assert {k for k, _ in toks} <= {"text", "comment", "decl", "brace", "tag", "attr", "value", "entity"}


def test_xml_token_kinds():
    toks = xml_syntax.tokens('<?xml v="1"?>\n<!-- c -->\n<note a="1">&amp;<rest/></note>\n<mea')
    assert toks[0] == ("decl", '<?xml v="1"?>') and ("comment", "<!-- c -->") in toks
    assert ("tag", "note") in toks and ("attr", "a") in toks and ("value", '"1"') in toks
    assert ("entity", "&amp;") in toks and ("tag", "rest") in toks and ("brace", "/></") in toks
    assert toks[-2:] == [("brace", "<"), ("tag", "mea")]                   # unclosed tag while typing


def test_xml_completion():
    head = '<score-partwise>\n  <part id="P1">\n    <measure number="1">\n      <note>\n        '
    names = [c.name for c in xml_syntax.suggestions(head + "<", len(head) + 1)]
    assert names[:3] == ["pitch", "rest", "chord"]                         # children of <note> first
    assert [c.name for c in xml_syntax.suggestions(head + "<o", len(head) + 2)][0] == "octave"
    assert [c.name for c in xml_syntax.suggestions(head + "</", len(head) + 2)] == ["note"]
    assert xml_syntax.context("a < b", 3) is not None and xml_syntax.context("<x>", 3) is None
    by = {c.name: c for c in xml_syntax.suggestions(head + "<", len(head) + 1)}
    text, a, b = xml_syntax.apply(head + "<", len(head) + 1, by["pitch"])
    assert text.endswith("<pitch><step>C</step><octave>4</octave></pitch>") and text[a:b] == "C"
    text, a, b = xml_syntax.apply("  <", 3, by["note"] if "note" in by else xml_syntax.suggestions("<n", 2)[0])
    assert text.startswith("  <note>\n    <pitch>") and text.endswith("\n  </note>")   # indented like the line
    assert xml_syntax.apply("<no>", 3, xml_syntax.suggestions("<no", 3)[0])[0] == "<note>"  # name only
    end, _, _ = xml_syntax.apply(head + "</", len(head) + 2, xml_syntax.suggestions(head + "</", len(head) + 2)[0])
    assert end.endswith("</note>")
    assert xml_syntax.open_elements('<a><!-- <x> --><b/><c></c><d>', 30) == ["a", "d"]


def test_xml_completion_hints_exist():
    from modernsheet import i18n
    assert all(f"xml.{n}" in i18n.CATALOG for n in xml_syntax.ELEMENTS) and "xml.close" in i18n.CATALOG
    assert set(xml_syntax.CHILDREN) - {"score-partwise", "lyric"} <= set(xml_syntax.ELEMENTS) | {"score-partwise"}


# ---- library synchronisation (local-first)
from modernsheet import sync as S  # noqa: E402


class MemoryProvider:
    """In-memory remote for the tests; `offline` simulates no network."""

    def __init__(self):
        self.files: dict[str, tuple[bytes, int]] = {}
        self.n = 0
        self.offline = False

    def _rev(self, rel):
        return str(self.files[rel][1])

    def list(self):
        if self.offline:
            raise S.Offline("no network")
        return {rel: S.RemoteFile(self._rev(rel)) for rel in self.files}

    def download(self, rel):
        return self.files[rel][0]

    def upload(self, rel, data, expected_rev):
        if (self._rev(rel) if rel in self.files else None) != expected_rev:
            raise S.RemoteChanged(rel)
        self.n += 1
        self.files[rel] = (data, self.n)
        return self._rev(rel)

    def delete(self, rel, expected_rev):
        if self._rev(rel) != expected_rev:
            raise S.RemoteChanged(rel)
        del self.files[rel]

    def put(self, rel, data):                       # a change made by another device
        self.n += 1
        self.files[rel] = (data, self.n)


def device(tmp_path, name, provider):
    root = tmp_path / name
    root.mkdir()
    return root, S.Syncer(root, provider, S.Manifest(tmp_path / f"{name}.json"), trash=tmp_path / f"{name}-trash",
                          device=name, clock=lambda: 1_700_000_000)


def test_sync_copies_new_files_both_ways(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    (a / "Jazz").mkdir()
    (a / "Jazz" / "x.chs").write_text("x1", encoding="utf-8")
    (a / "x.musicxml").write_text("<x/>", encoding="utf-8")
    (a / "notes.txt").write_text("not synced", encoding="utf-8")
    (a / ".hidden.chs").write_text("not synced", encoding="utf-8")
    r = sa.sync()
    assert sorted(r.uploaded) == ["Jazz/x.chs", "x.musicxml"] and set(remote.files) == {"Jazz/x.chs", "x.musicxml"}
    b, sb = device(tmp_path, "B", remote)
    r = sb.sync()
    assert sorted(r.downloaded) == ["Jazz/x.chs", "x.musicxml"] and (b / "Jazz" / "x.chs").read_text() == "x1"
    assert sa.sync() == S.Report() or not sa.sync().changed_local      # nothing left to do


def test_sync_edits_deletes_and_offline(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    b, sb = device(tmp_path, "B", remote)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    sa.sync(); sb.sync()
    (b / "s.chs").write_text("v2 from B", encoding="utf-8")       # edit on B
    assert sb.sync().uploaded == ["s.chs"]
    assert sa.sync().downloaded == ["s.chs"] and (a / "s.chs").read_text() == "v2 from B"

    remote.offline = True                                          # A works offline…
    (a / "s.chs").write_text("v3 offline", encoding="utf-8")
    (a / "new.chs").write_text("n", encoding="utf-8")
    r = sa.sync()
    assert r.offline and not r.uploaded and remote.files["s.chs"][0] == b"v2 from B"
    remote.offline = False                                         # …and catches up later: no queue needed
    assert sorted(sa.sync().uploaded) == ["new.chs", "s.chs"]
    assert sorted(sb.sync().downloaded) == ["new.chs", "s.chs"]

    (a / "new.chs").unlink()                                       # delete on A
    assert sa.sync().deleted_remote == ["new.chs"]
    sb.sync()
    assert not (b / "new.chs").exists()                            # B deletes it too…
    assert list((tmp_path / "B-trash").rglob("new.chs"))            # …into its trash, not for good


def test_sync_conflict_keeps_both_versions(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    b, sb = device(tmp_path, "B", remote)
    (a / "s.chs").write_text("base", encoding="utf-8")
    sa.sync(); sb.sync()
    (a / "s.chs").write_text("A's edit", encoding="utf-8")
    (b / "s.chs").write_text("B's edit", encoding="utf-8")
    sb.sync()                                                       # B first: remote = B's edit
    r = sa.sync()
    assert len(r.conflicts) == 1 and r.conflicts[0].startswith("s (conflitto A ") and r.conflicts[0].endswith(".chs")
    assert (a / "s.chs").read_text() == "B's edit"                  # the remote keeps the name
    assert (a / r.conflicts[0]).read_text() == "A's edit"           # the local edit is not lost
    assert r.conflicts[0] in remote.files                           # and reaches the other devices
    sb.sync()
    assert (b / r.conflicts[0]).read_text() == "A's edit"
    # same content on both sides: no conflict copy
    (a / "s.chs").write_text("same", encoding="utf-8")
    remote.put("s.chs", b"same")
    assert sa.sync().conflicts == []


def test_sync_edit_wins_over_delete_and_busy_files(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    b, sb = device(tmp_path, "B", remote)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    sa.sync(); sb.sync()
    (a / "s.chs").write_text("edited on A", encoding="utf-8")
    (b / "s.chs").unlink()
    sb.sync()                                                       # B deletes the remote copy
    assert sa.sync().uploaded == ["s.chs"]                          # A's edit comes back
    assert sb.sync().downloaded == ["s.chs"] and (b / "s.chs").read_text() == "edited on A"
    remote.put("s.chs", b"remote edit")
    r = sa.sync(busy={"s.chs"})                                     # open with unsaved changes: later
    assert r.skipped == ["s.chs"] and (a / "s.chs").read_text() == "edited on A"


def test_folder_provider(tmp_path):
    cloud = tmp_path / "iCloud" / "Modern Sheet"
    a, sa = device(tmp_path, "A", S.FolderProvider(cloud))
    assert sa.sync().offline                                        # folder missing: offline, no damage
    cloud.mkdir(parents=True)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    assert sa.sync().uploaded == ["s.chs"] and (cloud / "s.chs").read_text() == "v1"
    (cloud / "Sub").mkdir()
    (cloud / "Sub" / "t.chs").write_text("t", encoding="utf-8")    # arrives from another device
    assert sa.sync().downloaded == ["Sub/t.chs"]
    import os
    (cloud / "s.chs").write_text("changed in the cloud", encoding="utf-8")
    os.utime(cloud / "s.chs", ns=(1, 1))
    assert sa.sync().downloaded == ["s.chs"] and (a / "s.chs").read_text() == "changed in the cloud"
    m = S.Manifest(tmp_path / "A.json")
    assert set(m.files) == {"s.chs", "Sub/t.chs"} and m.last_sync == 1_700_000_000
    assert S.state_dir(tmp_path, "folder:x") != S.state_dir(tmp_path, "folder:y")


def test_conflict_name():
    assert S.conflict_name("Jazz/Blues.chs", "iPad", 0).startswith("Jazz/Blues (conflitto iPad 19")
    assert S.conflict_name("x", "Mac", 0).startswith("x (conflitto Mac ")
    assert S.is_synced("a/b.musicxml") and not S.is_synced(".x/b.chs") and not S.is_synced("a.txt")


def test_unavailable_remote_file_is_never_a_deletion(tmp_path, monkeypatch):
    cloud = tmp_path / "iCloud"
    cloud.mkdir()
    monkeypatch.setattr(S.FolderProvider, "_request_download", staticmethod(lambda p: None))
    a, sa = device(tmp_path, "A", S.FolderProvider(cloud))
    (a / "s.chs").write_text("v1", encoding="utf-8")
    sa.sync()
    (cloud / "s.chs").rename(cloud / ".s.chs.icloud")              # evicted by iCloud
    r = sa.sync()
    assert (a / "s.chs").read_text() == "v1" and not r.deleted_local and not r.downloaded
    (a / "s.chs").write_text("v2", encoding="utf-8")                # edited while evicted: wait
    assert sa.sync().skipped == ["s.chs"] and (a / "s.chs").read_text() == "v2"
    (cloud / ".s.chs.icloud").rename(cloud / "s.chs")              # back on disk
    assert sa.sync().uploaded == ["s.chs"] and (cloud / "s.chs").read_text() == "v2"
    (cloud / ".t.chs.icloud").write_text("", encoding="utf-8")      # new, never downloaded: skipped
    assert sa.sync().skipped == ["t.chs"] and not (a / "t.chs").exists()


# ---- Google Drive provider, against an in-memory fake of the Drive API
import hashlib  # noqa: E402
import json as _json  # noqa: E402
import urllib.parse as _up  # noqa: E402

from modernsheet import gdrive as G  # noqa: E402


class FakeDrive:
    """Just the Drive v3 / OAuth endpoints the provider uses."""

    def __init__(self):
        self.items: dict[str, dict] = {}         # id -> {name, mimeType, parents, data, trashed, modifiedTime}
        self.n = 0
        self.access = "tok1"
        self.offline = False
        self.pending_polls = 1
        self.calls: list[str] = []

    def _id(self):
        self.n += 1
        return f"id{self.n}"

    def add(self, name, parent, data=None, mime=None):
        i = self._id()
        self.items[i] = {"name": name, "parents": [parent], "trashed": False, "modifiedTime": f"{self.n:06d}",
                         "mimeType": mime or ("application/octet-stream" if data is not None else G.FOLDER_MIME),
                         "data": data}
        return i

    def meta(self, i):
        it = self.items[i]
        d = {"id": i, "name": it["name"], "mimeType": it["mimeType"], "parents": it["parents"],
             "modifiedTime": it["modifiedTime"], "trashed": it["trashed"]}
        if it["data"] is not None:
            d["md5Checksum"] = hashlib.md5(it["data"]).hexdigest()
        return d

    def __call__(self, method, url, headers, body):
        if self.offline:
            raise S.Offline("no network")
        u = _up.urlparse(url)
        q = dict(_up.parse_qsl(u.query))
        self.calls.append(f"{method} {u.path}")
        ok = lambda d: G.Response(200, _json.dumps(d).encode())          # noqa: E731
        if url.startswith(G.DEVICE_URL):
            return ok({"device_code": "dev", "user_code": "ABCD-EFGH", "verification_url": "https://google.com/device",
                       "interval": 5, "expires_in": 1800})
        if url.startswith(G.TOKEN_URL):
            form = dict(_up.parse_qsl(body.decode()))
            if form["grant_type"] == "refresh_token":
                self.access = f"tok{self.n + 100}"
                return ok({"access_token": self.access, "expires_in": 3600})
            if self.pending_polls:
                self.pending_polls -= 1
                return G.Response(428, b'{"error": "authorization_pending"}')
            return ok({"access_token": self.access, "refresh_token": "refresh", "expires_in": 3600})
        if headers.get("Authorization") != f"Bearer {self.access}":
            return G.Response(401, b"{}")
        path = u.path.replace("/upload", "").removeprefix("/drive/v3")
        if path == "/about":
            return ok({"user": {"emailAddress": "mario@example.com", "displayName": "Mario"}})
        if path == "/files" and method == "GET":
            live = [i for i, it in self.items.items() if not it["trashed"]]
            if "name=" in q["q"]:                                          # the root folder query
                name = q["q"].split("name='")[1].split("'")[0]
                live = [i for i in live if self.items[i]["name"] == name and self.items[i]["parents"] == ["root"]]
            elif " in parents" in q["q"]:                                  # children of a folder
                pid = q["q"].split("'")[1]
                live = [i for i in live if pid in self.items[i]["parents"]]
            return ok({"files": [self.meta(i) for i in live]})
        if path == "/files" and method == "POST":
            if q.get("uploadType") == "multipart":
                boundary = headers["Content-Type"].split("boundary=")[1].encode()
                parts = body.split(b"--" + boundary)
                meta = _json.loads(parts[1].split(b"\r\n\r\n", 1)[1].rstrip(b"\r\n"))
                data = parts[2].split(b"\r\n\r\n", 1)[1][:-2]
                i = self.add(meta["name"], meta["parents"][0], data)
            else:
                meta = _json.loads(body)
                i = self.add(meta["name"], meta["parents"][0])
            return ok(self.meta(i))
        i = path.removeprefix("/files/")
        if i not in self.items:
            return G.Response(404, b"{}")
        if method == "GET":
            return G.Response(200, self.items[i]["data"]) if q.get("alt") == "media" else ok(self.meta(i))
        if method == "PATCH" and q.get("uploadType") == "media":
            self.n += 1
            self.items[i]["data"], self.items[i]["modifiedTime"] = body, f"{self.n:06d}"
            return ok(self.meta(i))
        if method == "PATCH":
            self.items[i].update(_json.loads(body))
            return ok(self.meta(i))
        return G.Response(400, b"{}")


def signed_in(tmp_path, fake, name="tok.json"):
    auth = G.GoogleAuth(G.ClientConfig("cid", "secret"), tmp_path / name, fake, clock=lambda: 1000)
    dc = auth.start()
    assert dc.user_code == "ABCD-EFGH" and auth.poll(dc) == "pending" and auth.poll(dc) == "ok"
    return auth


def test_google_device_flow_and_token_refresh(tmp_path):
    fake = FakeDrive()
    auth = signed_in(tmp_path, fake)
    assert auth.signed_in and (tmp_path / "tok.json").stat().st_mode & 0o077 == 0     # private file
    assert G.GoogleAuth(auth.client, tmp_path / "tok.json", fake).signed_in             # survives restarts
    drive = G.DriveProvider(auth, fake)
    assert drive.account()["emailAddress"] == "mario@example.com"
    fake.access = "rotated"                                     # the access token expired on the server
    fake.n += 1
    assert drive.account()["displayName"] == "Mario"            # 401 -> refreshed -> retried
    auth.sign_out()
    assert not auth.signed_in and not (tmp_path / "tok.json").exists()
    with pytest.raises(S.AuthRequired):
        drive.account()


def test_google_drive_sync_between_two_devices(tmp_path):
    fake = FakeDrive()
    remote_a = G.DriveProvider(signed_in(tmp_path, fake, "a.json"), fake)
    a, sa = device(tmp_path, "A", remote_a)
    (a / "Jazz").mkdir()
    (a / "Jazz" / "blues.chs").write_text("{title: Blues}", encoding="utf-8")
    (a / "Jazz" / "riff.musicxml").write_text("<score-partwise/>", encoding="utf-8")
    assert sorted(sa.sync().uploaded) == ["Jazz/blues.chs", "Jazz/riff.musicxml"]
    folders = [it for it in fake.items.values() if it["mimeType"] == G.FOLDER_MIME]
    assert sorted(f["name"] for f in folders) == ["Jazz", "Modern Sheet"]  # app folder + subfolder

    fake.pending_polls = 1
    remote_b = G.DriveProvider(signed_in(tmp_path, fake, "b.json"), fake)
    b, sb = device(tmp_path, "B", remote_b)
    assert sorted(sb.sync().downloaded) == ["Jazz/blues.chs", "Jazz/riff.musicxml"]
    assert sum(1 for it in fake.items.values() if it["name"] == "Modern Sheet") == 1   # root folder reused

    (b / "Jazz" / "blues.chs").write_text("{title: Blues 2}", encoding="utf-8")
    assert sb.sync().uploaded == ["Jazz/blues.chs"]
    assert sa.sync().downloaded == ["Jazz/blues.chs"] and (a / "Jazz" / "blues.chs").read_text() == "{title: Blues 2}"

    (a / "Jazz" / "blues.chs").write_text("A", encoding="utf-8")       # conflict through Drive
    (b / "Jazz" / "blues.chs").write_text("B", encoding="utf-8")
    sb.sync()
    r = sa.sync()
    assert len(r.conflicts) == 1 and (a / "Jazz" / "blues.chs").read_text() == "B"
    assert sb.sync().downloaded == r.conflicts

    (a / "Jazz" / "riff.musicxml").unlink()                             # delete = Drive trash
    assert sa.sync().deleted_remote == ["Jazz/riff.musicxml"]
    assert any(it["name"] == "riff.musicxml" and it["trashed"] for it in fake.items.values())
    sb.sync()
    assert not (b / "Jazz" / "riff.musicxml").exists()

    fake.offline = True                                                 # offline: nothing breaks
    (a / "new.chs").write_text("n", encoding="utf-8")
    assert sa.sync().offline
    fake.offline = False
    assert sa.sync().uploaded == ["new.chs"]


def test_google_drive_auth_revoked(tmp_path):
    fake = FakeDrive()
    auth = signed_in(tmp_path, fake)
    a, sa = device(tmp_path, "A", G.DriveProvider(auth, fake))
    auth.token["refresh_token"] = None                                 # revoked / signed out elsewhere
    r = sa.sync()
    assert r.auth_required and not r.offline


def test_google_client_config(tmp_path, monkeypatch):
    for prefix in ("MODERNSHEET", "CHORDSHEET"):
        monkeypatch.delenv(f"{prefix}_GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv(f"{prefix}_GOOGLE_CLIENT_SECRET", raising=False)
    f = tmp_path / "google_client.json"
    assert G.client_config(f) is None
    f.write_text('{"installed": {"client_id": "x.apps.googleusercontent.com", "client_secret": "s"}}')
    assert G.client_config(tmp_path / "missing.json", f) == G.ClientConfig("x.apps.googleusercontent.com", "s")
    monkeypatch.setenv("CHORDSHEET_GOOGLE_CLIENT_ID", "old-id")              # name used before 0.19
    monkeypatch.setenv("CHORDSHEET_GOOGLE_CLIENT_SECRET", "old-secret")
    assert G.client_config(f) == G.ClientConfig("old-id", "old-secret")
    monkeypatch.setenv("MODERNSHEET_GOOGLE_CLIENT_ID", "env-id")
    monkeypatch.setenv("MODERNSHEET_GOOGLE_CLIENT_SECRET", "env-secret")
    assert G.client_config(f) == G.ClientConfig("env-id", "env-secret")


def test_empty_or_recreated_remote_is_not_a_mass_deletion(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    (a / "t.chs").write_text("t", encoding="utf-8")
    sa.sync()
    remote.files.clear()                                         # the remote folder was emptied / replaced
    r = sa.sync()
    assert r.remote_reset and sorted(r.uploaded) == ["s.chs", "t.chs"] and not r.deleted_local
    assert (a / "s.chs").exists() and not (tmp_path / "A-trash").exists()
    assert not sa.sync().remote_reset                            # back to normal


def test_google_drive_folder_renamed_or_configurable(tmp_path):
    fake = FakeDrive()
    auth = signed_in(tmp_path, fake)
    drive = G.DriveProvider(auth, fake)
    a, sa = device(tmp_path, "A", drive)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    assert sa.sync().uploaded == ["s.chs"] and not sa.sync().remote_reset
    root = next(i for i, it in fake.items.items() if it["name"] == "Modern Sheet")
    fake.items[root]["name"] = "Old songs"                       # renamed on drive.google.com
    r = sa.sync()
    assert r.remote_reset and r.uploaded == ["s.chs"] and not r.deleted_local and (a / "s.chs").exists()
    assert sum(1 for it in fake.items.values() if it["name"] == "Modern Sheet") == 1   # a new app folder
    assert not sa.sync().remote_reset and not sa.sync().uploaded

    other = G.DriveProvider(auth, fake, root_name="Spartiti")    # another folder name: another library
    b, sb = device(tmp_path, "B", other)
    (b / "x.chs").write_text("x", encoding="utf-8")
    sb.sync()
    spartiti = next(i for i, it in fake.items.items() if it["name"] == "Spartiti")
    assert [it["name"] for it in fake.items.values() if it["parents"] == [spartiti]] == ["x.chs"]
    assert G.clean_folder_name("  Musica / Lead   sheet ") == "Musica Lead sheet"
    assert G.clean_folder_name("  ") == "Modern Sheet"


def test_web_manifest_names_the_app():
    """`flet run --ios/--android` serves src/assets/manifest.json instead of Flet's own."""
    import json
    assets = Path(__file__).resolve().parent.parent / "src" / "assets"
    manifest = json.loads((assets / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == manifest["short_name"] == "Modern Sheet"
    assert manifest["description"]
    for icon in manifest["icons"]:
        assert (assets / icon["src"]).is_file()
    for name in ("apple-touch-icon-192", "icon-192", "icon-512", "icon-maskable-192", "icon-maskable-512"):
        assert (assets / "icons" / f"{name}.png").is_file()   # replace Flet's own web icons


def test_delete_song_with_its_musicxml_into_the_sync_trash(tmp_path):
    from modernsheet import library as L
    root = tmp_path / "lib"
    (root / "Jazz").mkdir(parents=True)
    (root / "xml").mkdir()
    song = root / "Jazz" / "s.chs"
    song.write_text("{title: S}\n{musicxml: s.musicxml}\n{musicxml: ../xml/shared.musicxml | 1-2}\n"
                    "{musicxml: gone.musicxml}\n{musicxml: ../../out.musicxml}\n", encoding="utf-8")
    for f in (root / "Jazz" / "s.musicxml", root / "xml" / "shared.musicxml", tmp_path / "out.musicxml"):
        f.write_text("<x/>", encoding="utf-8")
    other = root / "o.chs"
    other.write_text("{musicxml: xml/shared.musicxml}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        L.delete_plan(root / "Jazz" / "s.musicxml")
    plan = L.delete_plan(song, root)
    assert plan.files == [song, root / "Jazz" / "s.musicxml"]
    assert plan.kept == {root / "xml" / "shared.musicxml": [other],          # another song uses it
                         root / "Jazz" / "gone.musicxml": "missing",
                         tmp_path / "out.musicxml": "outside"}                # never outside the library
    trash = tmp_path / "trash"
    moved = L.delete_song(song, root, trash, today="2026-11-23")
    assert moved == [trash / "2026-11-23" / "Jazz" / "s.chs", trash / "2026-11-23" / "Jazz" / "s.musicxml"]
    assert not song.exists() and not (root / "Jazz" / "s.musicxml").exists()
    assert (root / "xml" / "shared.musicxml").exists() and (tmp_path / "out.musicxml").exists()
    assert [s.path.name for s in L.scan(root).walk()] == ["o.chs"]
    song.write_text("again", encoding="utf-8")                        # same name, same day: no overwrite
    assert [m.name for m in L.delete_song(song, root, trash, today="2026-11-23")] == ["s 2.chs"]
    other.write_text("{musicxml: xml/shared.musicxml}\n", encoding="utf-8")
    assert L.delete_song(other, root) == [] and not other.exists()    # no sync: gone for good…
    assert not (root / "xml" / "shared.musicxml").exists()            # …with its now unshared MusicXML


def test_deleted_song_leaves_the_other_devices(tmp_path):
    from modernsheet import library as L
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    b, sb = device(tmp_path, "B", remote)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    (a / "other.chs").write_text("o", encoding="utf-8")   # an emptied remote is a reset, not a deletion (0.18)
    sa.sync(); sb.sync()
    L.delete_song(a / "s.chs", a, tmp_path / "A-trash")              # the app's delete button on A
    assert sa.sync().deleted_remote == ["s.chs"] and "s.chs" not in remote.files
    sb.sync()
    assert not (b / "s.chs").exists() and list((tmp_path / "B-trash").rglob("s.chs"))
    assert list((tmp_path / "A-trash").rglob("s.chs"))


def test_created_and_modified_dates():
    from datetime import datetime
    from modernsheet import i18n, library as L
    from modernsheet.formats.v1 import parse_stamp
    assert parse_stamp("2026-11-23 12:49") == datetime(2026, 11, 23, 12, 49)
    assert parse_stamp("2026-11-23") == datetime(2026, 11, 23) and parse_stamp("2026-11-23T12:49:05") == datetime(2026, 11, 23, 12, 49, 5)
    assert parse_stamp("23/11/2026") is None and parse_stamp("2026-02-30") is None
    ok = parse("{title: X}\n{created: 2026-11-20 10:00}\n{modified: 2026-11-23}\n"
               "{start_of_verse}\n| [C] |\n{end_of_verse}\n")
    assert not ok.warnings and ok.meta["created"] == "2026-11-20 10:00"
    assert any("invalid date" in w for w in parse("{modified: ieri}\n{start_of_verse}\n| [C] |\n{end_of_verse}\n").warnings)

    now, then = datetime(2026, 11, 23, 12, 49, 7), datetime(2026, 11, 1, 8, 5, 30)
    src = "# comment\n{format: v1}\n{title: X}\n{key: C}\n\n{start_of_verse}\n| [C] |\n{end_of_verse}\n"
    once = L.stamp(src, now, created=then)
    assert once.split("\n")[:6] == ["# comment", "{format: v1}", "{title: X}", "{key: C}",
                                     "{created: 2026-11-01 08:05:30}", "{modified: 2026-11-23 12:49:07}"]
    later = L.stamp(once, datetime(2026, 12, 1, 9, 0, 1), created=now)       # in place, created kept
    assert later.count("\n") == once.count("\n") and "{created: 2026-11-01 08:05:30}" in later
    assert "{modified: 2026-12-01 09:00:01}" in later
    copy = L.stamp(later, datetime(2026, 12, 2, 7, 30), new_file=True)     # Save as: a new file
    assert "{created: 2026-12-02 07:30:00}" in copy and "{modified: 2026-12-02 07:30:00}" in copy
    bare = L.stamp("| [C] |\n", now)                                       # no header: at the top
    assert bare.startswith("{created: 2026-11-23 12:49:07}\n{modified: 2026-11-23 12:49:07}\n| [C] |")
    late = L.stamp("| [C] |\n{format: v1}\n", now)                       # never before {format}
    assert late.split("\n")[:3] == ["| [C] |", "{format: v1}", "{created: 2026-11-23 12:49:07}"]
    assert not parse(L.new_song_text("Nuovo", now)).warnings and "{created: 2026-11-23 12:49:07}" in L.new_song_text("N", now)

    def song(name, text, mtime):
        p = Path(tmp) / name
        p.write_text(text, encoding="utf-8")
        os.utime(p, (mtime, mtime))
        return p
    import os, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        a = song("a.chs", "{title: A}\n{created: 2026-01-05 10:00}\n{modified: 2026-03-01 10:00}\n", 1_700_000_000)
        b = song("b.chs", "{title: B}\n{created: 2025-12-01 10:00}\n{modified: 2026-02-01 10:00}\n", 1_700_000_000)
        c = song("c.chs", "{title: C}\n", datetime(2026, 4, 1).timestamp())   # never saved by the app
        idx = L.Index(Path(tmp) / "idx" / "i.json")
        songs = list(L.scan(Path(tmp), idx).walk())
        assert {s.title: s.created for s in songs} == {"A": "2026-01-05 10:00", "B": "2025-12-01 10:00", "C": ""}
        by = lambda key, desc=False: [s.title for s in L.sort_songs(songs, key, desc)]
        assert by("created") == ["B", "A", "C"] and by("created", True) == ["C", "A", "B"]   # C: file time
        assert next(x for x in songs if x.title == "C").created_at is not None
        assert by("modified") == ["B", "A", "C"] and by("modified", True) == ["C", "A", "B"]  # file time
        idx.save()
        again = L.Index(Path(tmp) / "idx" / "i.json")
        assert [s.created for s in L.scan(Path(tmp), again).walk()] == [s.created for s in songs] and again.hits == 3
        assert L.file_created(a) is not None
        # same title: the most recently created or saved first, whatever the order and direction
        song("d.chs", "{title: A}\n{created: 2026-02-01 10:00:00}\n{modified: 2026-05-01 10:00:00}\n", 1_700_000_000)
        songs = list(L.scan(Path(tmp)).walk())
        names = lambda key, desc=False: [s.path.name for s in L.sort_songs(songs, key, desc) if s.title == "A"]
        assert names("title") == names("title", True) == names("artist") == ["d.chs", "a.chs"]
    assert i18n.tr_date(now, "it") == "23 nov 2026" and i18n.tr_date(now, "en") == "Nov 23, 2026"
    assert i18n.tr_datetime(now, "it") == "23 nov 2026 12:49:07"


def test_same_title_songs_are_told_apart():
    import main
    from modernsheet.library import SongFile
    a = SongFile(Path("a.chs"), "X", created="2026-11-20 10:00:00", modified="2026-11-23 13:05:12")
    b = SongFile(Path("b.chs"), "x", created="2026-11-20 10:00:00", modified="2026-11-23 13:05:13")
    c = SongFile(Path("c.chs"), "Other", modified="2026-11-23 13:05:12")
    assert main.tell_apart([a, b, c]) == {Path("a.chs"): "modified", Path("b.chs"): "modified"}
    b.modified, b.created = a.modified, "2026-11-21 09:00:00"              # same save time, other day
    assert main.tell_apart([a, b])[Path("b.chs")] == "created"
    b.created = a.created                                                    # only the file differs
    assert main.tell_apart([a, b])[Path("a.chs")] == "file"


# ---- navigation marks (segno, coda, D.C./D.S., Fine) and free text lines
NAV = """{title: N}
{start_of_verse: A}
{text: Prima volta piano}
{segno}
| [C] | [F] {to_coda} | [G] |
[Am] [Dm] {fine} [E7] {coda} [A]
| [C] | {ds: al Coda}
{text: Poi alla Coda}
{end_of_verse}
"""


def test_navigation_marks_go_on_the_right_bars():
    song = parse(NAV)
    assert song.warnings == []
    b = song.bars
    assert b[0].marks_start == ["segno"] and b[0].text_before == ["Prima volta piano"]
    assert b[1].marks_end == [("to_coda", "")]                       # written inside the bar
    assert b[4].marks_end == [("fine", "")] and b[4].double_after     # implicit line: after Dm; Fine = ||
    assert b[6].marks_start == ["coda"]                               # implicit line: before A
    assert b[7].marks_end == [("ds", "al Coda")]                      # right after a bar line: the bar before
    assert song.sections[0].text_after == ["Poi alla Coda"]
    # a {text} between rows starts a new row
    two = parse("{start_of_verse}\n| [C] | [F] |\n{text: x}\n| [G] |\n{end_of_verse}\n")
    assert two.bars[2].text_before == ["x"] and two.bars[2].break_before


def test_navigation_marks_warnings_and_references():
    song = parse("{fine}\n{text: fuori}\n{start_of_verse: A}\n| [C] |\n{segno}\n{end_of_verse}\n")
    assert any("before any bar" in w for w in song.warnings)
    assert any("outside a section" in w for w in song.warnings)
    assert any("no bar follows" in w for w in song.warnings)
    ref = parse("{start_of_verse: A}\n{text: t}\n{segno}\n| [C] {to_coda} |\n{end_of_verse}\n{ref: A}\n")
    copy = ref.sections[1].bars[0]                                    # signs and notes stay with the original
    assert not (copy.marks_start or copy.marks_end or copy.text_before)


@pytest.mark.parametrize("theme", ["realbook", "clean"])
def test_navigation_marks_and_text_are_drawn(theme):
    dl = layout(parse(NAV), theme=theme)
    texts = [op[3] for page in dl.pages for op in page if op[0] == "text"]
    for s in ("To Coda", "Fine", "D.S. al Coda", "Prima volta piano", "Poi alla Coda"):
        assert any(s in t for t in texts), s
    assert "" in texts and texts.count("") == 2          # segno; coda sign + To Coda ⊕
    plain = layout(parse(NAV.replace("{segno}\n", "").replace("{to_coda}", "").replace("{fine}", "")
                         .replace("{coda}", "").replace("{ds: al Coda}", "")), theme=theme)
    ys = lambda d: sorted(op[2] for op in d.pages[0] if op[0] == "text" and op[3] == "C")
    assert ys(dl)[0] < ys(plain)[0]                                   # the mark lane makes room


def test_csm_navigation_and_text_lines():
    conv, song = csm_song("= A\n- piano\n$ C D o E fine\n= B\nF G D.S. al coda con rep.\n= Coda\nO A B\n")
    b = song.bars
    assert b[0].marks_start == ["segno"] and b[1].marks_end == [("to_coda", "")]
    assert b[2].marks_end == [("fine", "")] and b[4].marks_end == [("ds", "al Coda con rep.")]
    assert b[5].marks_start == ["coda"] and b[0].text_before == ["piano"]
    assert "{segno}" in conv.chs and "{text: piano}" in conv.chs and not conv.notes


def test_signs_sit_lower_in_rows_without_lyrics():
    def gap(src):                     # segno baseline above the chord baseline of the same row
        dl = layout(parse("{start_of_verse}\n{segno}\n" + src + "\n{end_of_verse}\n"))
        ops = [op for op in dl.pages[0] if op[0] == "text"]
        segno = next(op for op in ops if op[3] == "")
        chord = next(op for op in ops if op[3] == "C")
        return segno[2] - chord[2]
    bare, sung, volta = gap("| [C] | [F] |"), gap("| [C]la la | [F]la |"), gap("| [C] | {volta: 1} [F] :|")
    assert bare < sung - 10 and bare < volta - 10        # lowered only when nothing else is above the staff
    assert bare > 8                                      # but still above the staff


# ---- rhythm marks and optional chords (inside the chord brackets)
def test_chord_marks_are_parsed_and_transposed():
    song = parse("{key: C}\n{start_of_verse}\n| [<C] [(F)] | [C~] | [C,,, fermata] | [<<(G7):3 diamond] [C?] |\n"
                 "[Am~] [(Dm7~)]\n| [C <>] [C tie] | [<(G7?)] |\n{end_of_verse}\n", transpose=2)
    assert song.warnings == []
    ev = [e for b in song.bars for e in b.events if e.chord]
    mk = lambda e: (e.chord, e.optional, e.push, e.tie, e.strokes, e.fermata, e.diamond)
    assert mk(ev[0]) == ("D", False, 1, False, 0, False, False)
    assert mk(ev[1]) == ("G", True, 0, False, 0, False, False)
    assert mk(ev[2]) == ("D", False, 0, True, 0, False, False)
    assert mk(ev[3]) == ("D", False, 0, False, 3, True, False)
    assert mk(ev[4]) == ("A7", True, 2, False, 0, False, True) and ev[4].dur == 3
    assert mk(ev[5]) == ("D", True, 0, False, 0, False, False)
    assert ev[6].tie and ev[7].tie and ev[7].optional and ev[7].chord == "Em7"     # implicit line, ~ inside ( )
    assert ev[8].diamond and ev[9].tie and mk(ev[10]) == ("A7", True, 1, False, 0, False, False)
    bad = parse("{start_of_verse}\n| [C foo] | [<<<C] |\n{end_of_verse}\n").warnings
    assert any("unknown chord mark 'foo'" in w for w in bad) and any("at most two" in w for w in bad)


@pytest.mark.parametrize("theme", ["realbook", "clean"])
def test_chord_marks_are_drawn(theme):
    src = ("{start_of_verse}\n| [<C] [(F)] | [G7,,,] | [C fermata] | [Am diamond] |\n"
           "| [Dm~] | [G7] | [C~] | [C~] |\n| [F] |\n{end_of_verse}\n")
    dl = layout(parse(src), theme=theme)
    texts = [op[3] for page in dl.pages for op in page if op[0] == "text"]
    assert "<" in texts and "(" in texts and ")" in texts
    assert texts.count("") == 3 and "" in texts and "" in texts      # slashes, fermata, diamond
    paths = sum(1 for page in dl.pages for op in page if op[0] == "path")
    plain = layout(parse(src.replace("~", "")), theme=theme)
    assert paths - sum(1 for page in plain.pages for op in page if op[0] == "path") == 4   # 2 ties + carried one twice


def test_csm_rhythm_marks_and_optional_chords():
    conv, song = csm_song("<C <<F_G,, Am^ Dm7fermata Em7<> A7? ^\nG6 [G_D+7] G6")
    ev = [e for b in song.bars for e in b.events if e.chord]
    assert ev[0].push == 1 and ev[1].push == 2 and ev[2].strokes == 2 and ev[3].tie
    assert ev[4].fermata and ev[5].diamond and ev[6].optional and ev[6].tie        # lone ^ ties the last chord
    assert [e.optional for e in ev[7:11]] == [False, True, True, False]            # [ … ] group
    assert not conv.notes


# ---- chord annotations [A "1°"] and the importer fixes found on real chordsheet.com songs
def test_chord_annotations():
    song = parse('{start_of_verse}\n| [A "1°"] [Bm:2 "ad  lib.." fermata] | [<(C)~ "opz"] | [% "again"] |\n'
                 '| [G "piano"]la la |\n{end_of_verse}\n')
    assert song.warnings == []
    ev = [e for b in song.bars for e in b.events]
    assert [e.note for e in ev[:3]] == ["1°", "ad lib..", "opz"] and ev[1].fermata and ev[2].tie and ev[2].optional
    assert ev[3].chord is None and ev[3].note == "again"
    dl = layout(song)
    texts = [op for op in dl.pages[0] if op[0] == "text"]
    y = {op[3]: op[2] for op in texts}
    assert {"ad lib..", "opz", "again", "piano"} <= set(y) and "1" in y    # "°" comes from the music font
    assert y["piano"] > y["la la"]                       # over the lyrics in a row that has them


def test_csm_annotations_beats_indents_and_counts():
    conv, song = csm_song('(E A E A"1°"_Bm_A/C#_A?"2°")\nG Em "a minor chord" Am7\n*_B_*_* E\n'
                          '( A B ) x4\n(C C 1.D\nX X 2.F_X_G)\nA %"ripeti" P1 B P0')
    ev = [e for b in song.bars for e in b.events]
    notes = [e.note for e in ev if e.note]
    assert notes == ["1°", "2°", "a minor chord", "ripeti"]
    b = song.bars
    starts = [(e.chord, e.start) for e in b[7].events]
    assert starts == [(None, 0.0), ("B", 1.0), (None, 2.0), (None, 3.0)]   # B on beat 2
    assert b[10].repeat_end == 4                                           # "( … ) x4"
    assert not conv.notes and "[X]" not in conv.chs and "P1" not in conv.chs


def test_library_groups_songs_by_letter():
    from modernsheet import library as L
    assert [L.index_letter(t) for t in ("(Out here) on my own", "È la luna", "50 special", "àbc", "123", "")] == \
        ["O", "E", "S", "A", "#", "#"]
    mk = lambda t, a="": L.SongFile(Path(t + ".chs"), t, artist=a)
    songs = L.sort_songs([mk("beta", "Zed"), mk("(Out here)"), mk("Alpha", "abba"), mk("123"), mk("avanti", "Zed")])
    groups = L.group_by_letter(songs)
    assert [(k, [s.title for s in g]) for k, g in groups] == \
        [("A", ["Alpha", "avanti"]), ("B", ["beta"]), ("O", ["(Out here)"]), ("#", ["123"])]
    assert [k for k, _ in L.group_by_letter(songs, descending=True)] == ["O", "B", "A", "#"]   # "#" always last
    by_artist = L.group_by_letter(L.sort_songs(songs, "artist"), "artist")
    assert [(k, len(g)) for k, g in by_artist] == [("A", 1), ("Z", 2), ("#", 2)]
    assert L.GROUPED_SORTS == {"title": "title", "artist": "artist"}


def test_library_search_patterns_and_or():
    from modernsheet import library as L
    root = Path("/lib")
    mk = lambda t, a="", tags=(), sub="": L.SongFile(root / sub / f"{t}.chs", t, artist=a, tags=list(tags))
    songs = [mk("Amazing Grace", "Traditional", ["gospel"]), mk("Àncora tu", "Battisti", ["pop"]),
             mk("(Out here) on my own", "N. Costa", ["pop"]), mk("Blues del lunedì", "Modern", ["blues", "jazz"]),
             mk("Hey Jude", "Beatles", ["pop"], sub="Beatles"), mk("Bossa", "Jobim", ["jazz"])]
    tree = L.Folder(root, songs=songs)
    q = lambda query: sorted(s.title for s in L.search(tree, query))
    assert q("a*") == ["Amazing Grace", "Àncora tu"]                       # title starts with, accents ignored
    assert q("o*") == ["(Out here) on my own"]                             # leading brackets ignored
    assert q("*own") == ["(Out here) on my own"] and q("*JUDE") == ["Hey Jude"]   # title ends with
    assert q("*tu") == ["Àncora tu"] and q("*grace") == ["Amazing Grace"]
    assert q("*ra*") == ["Amazing Grace", "Àncora tu"]                     # contains (title, artist…)
    assert q("*hey jude*") == ["Hey Jude"] and q("*BEATLES*") == ["Hey Jude"]
    assert q("b* & #jazz") == ["Blues del lunedì", "Bossa"]
    assert q("a* | b*") == ["Amazing Grace", "Blues del lunedì", "Bossa", "Àncora tu"]
    assert q("a* & #pop | #blues") == ["Blues del lunedì", "Àncora tu"]   # & binds tighter than |
    assert q("blues lunedi") == ["Blues del lunedì"] and q("#jazz") == ["Blues del lunedì", "Bossa"]
    assert q("") == [] and q(" | & ") == []


def test_later_ending_longer_than_the_first_keeps_its_staff():
    song = parse("{start_of_verse}\n|: [C] | [Em] | [Am] | [D] |\n{volta: 1} [D] | [C] :|\n"
                 "{volta: 2} [D] | [C] [D7] | [G] |\n{end_of_verse}\n")           # 2nd ending: 3 bars, 1st: 2
    dl = layout(song)
    lines = [op for op in dl.pages[0] if op[0] == "line" and op[2] == op[4]]          # horizontal staff lines
    bars = [op for op in dl.pages[0] if op[0] == "text" and op[3] == "G"]
    last_g = max(bars, key=lambda op: (-op[2], op[1]))                                # the 2nd ending's last G
    under = [l for l in lines if min(l[1], l[3]) <= last_g[1] + 5 <= max(l[1], l[3]) and abs(l[2] - last_g[2]) < 20]
    assert len(under) >= 5                                                            # all five staff lines


@pytest.mark.parametrize("theme", ["realbook", "clean"])
def test_key_change_is_spelled_under_the_staff(theme):
    src = "{key: C}\n{start_of_verse}\n| [C] | [G7] || {key: Db} [Db] | [Gb] |\n{key: F#m}\n| [F#m] | [C#7] |\n{end_of_verse}\n"
    labels = lambda text: [op for op in layout(parse(text), theme=theme).pages[0]
                           if op[0] == "text" and op[3].startswith("Key ")]
    keys = labels(src)
    assert [op[3][:5] for op in keys] == ["Key C", "Key D", "Key F"]   # header, mid-row change, change at a row start
    ops = [op for op in layout(parse(src), theme=theme).pages[0] if op[0] == "text"]
    db = next(op for op in ops if op[3] == "D" and op[2] < 700)          # the Db chord of the first row
    assert keys[1][2] < db[2] - 10                                       # under the staff
    plain = src.replace("{key: Db} ", "").replace("{key: F#m}\n", "")
    assert len(labels(plain)) == 1                                       # no change: only the header


def test_new_installation_library_and_merge(tmp_path):
    import main
    from modernsheet import library as L
    root = main.default_library(str(tmp_path / "data"))
    assert root.name == "Modern Sheet" and [p.name for p in root.iterdir()] == ["examples"]   # only the examples
    ex = sorted(p.name for p in (root / "examples").iterdir())
    assert ex == sorted(p.name for p in main.EXAMPLES.iterdir() if p.is_file())
    (root / "mine.chs").write_text("x", encoding="utf-8")
    assert main.default_library(str(tmp_path / "data")) == root and (root / "mine.chs").exists()  # made once
    # joining a synced library that already has examples/ (and other songs): only what it lacks is copied
    synced = tmp_path / "synced"
    (synced / "examples").mkdir(parents=True)
    (synced / "examples" / "demo.chs").write_text("remote version", encoding="utf-8")
    (synced / "import").mkdir()
    added = L.merge_into(root, synced, lambda rel: rel.endswith(".chs"))
    assert "examples/demo.chs" not in added and (synced / "examples" / "demo.chs").read_text() == "remote version"
    assert "mine.chs" in added and not [p for p in synced.glob("*.chs") if p.name != "mine.chs"]   # no strays
    assert L.merge_into(root, synced, lambda rel: rel.endswith(".chs")) == []                      # idempotent


def test_rename_folder(tmp_path):
    from modernsheet import library as L
    root = tmp_path / "lib"
    (root / "Jazz" / "Ballads").mkdir(parents=True)
    (root / "Pop").mkdir()
    (root / "Jazz" / "riff.musicxml").write_text("<x/>", encoding="utf-8")
    (root / "Jazz" / "Ballads" / "b.chs").write_text("{musicxml: ../riff.musicxml}\n", encoding="utf-8")
    (root / "Pop" / "p.chs").write_text("{title: P}\n{musicxml: ../Jazz/riff.musicxml | 1-2}\n", encoding="utf-8")
    (root / "top.chs").write_text("{musicxml: Jazz/riff.musicxml}\n", encoding="utf-8")
    assert sorted(s.name for s, _ in L.outside_refs(root, root / "Jazz")) == ["p.chs", "top.chs"]
    with pytest.raises(ValueError):
        L.rename_folder(root, "X", root)                                 # never the main folder
    with pytest.raises(ValueError):
        L.rename_folder(root / "Jazz", "Pop", root)                      # name in use
    with pytest.raises(ValueError):
        L.rename_folder(root / "Jazz", "  . ", root)                     # blank
    r = L.rename_folder(root / "Jazz", "Jazz: standard/2", root)        # cleaned name
    assert r.path == root / "Jazz standard 2" and not (root / "Jazz").exists()
    assert sorted(p.name for p in r.updated) == ["p.chs", "top.chs"]
    assert (root / "Pop" / "p.chs").read_text() == "{title: P}\n{musicxml: ../Jazz standard 2/riff.musicxml | 1-2}\n"
    assert (root / "top.chs").read_text() == "{musicxml: Jazz standard 2/riff.musicxml}\n"
    assert (r.path / "Ballads" / "b.chs").read_text() == "{musicxml: ../riff.musicxml}\n"   # inside: unchanged
    assert (root / "Pop" / "../Jazz standard 2/riff.musicxml").is_file()          # the new reference resolves
    r2 = L.rename_folder(r.path, "jazz STANDARD 2", root)               # case only
    assert r2.path.name == "jazz STANDARD 2" and [p.name for p in root.iterdir() if p.is_dir() and "azz" in p.name.lower()] == ["jazz STANDARD 2"]


def test_sync_removes_folders_it_emptied(tmp_path):
    remote_dir = tmp_path / "remote"
    remote_dir.mkdir()
    a, sa = device(tmp_path, "A", S.FolderProvider(remote_dir))
    b, sb = device(tmp_path, "B", S.FolderProvider(remote_dir))
    (a / "Old" / "Sub").mkdir(parents=True)
    (a / "Old" / "Sub" / "x.chs").write_text("x", encoding="utf-8")
    (a / "Old" / "y.chs").write_text("y", encoding="utf-8")
    (a / "Keep").mkdir()
    (a / "Keep" / "k.chs").write_text("k", encoding="utf-8")
    sa.sync(); sb.sync()
    (b / "Old" / ".DS_Store").write_text("finder", encoding="utf-8")
    (a / "Old").rename(a / "New")                                       # a folder renamed on A
    r = sa.sync()
    assert sorted(r.removed_folders) == ["Old", "Old/Sub"] and not (remote_dir / "Old").exists()
    rb = sb.sync()
    assert not (b / "Old").exists() and (b / "New" / "Sub" / "x.chs").read_text() == "x"   # .DS_Store ignored
    assert sorted(rb.removed_folders) == ["Old", "Old/Sub"] and (b / "Keep").exists()
    (b / "Keep" / "notes.txt").write_text("mine", encoding="utf-8")     # a file the app does not sync…
    (b / "Keep" / "k.chs").unlink()
    sb.sync(); sa.sync()
    assert (b / "Keep").exists() and not (a / "Keep").exists()          # …keeps that folder; elsewhere it goes


def test_drive_removes_folders_it_emptied(tmp_path):
    fake = FakeDrive()
    auth = signed_in(tmp_path, fake)
    a, sa = device(tmp_path, "A", G.DriveProvider(auth, fake))
    (a / "Old").mkdir()
    (a / "Old" / "x.chs").write_text("x", encoding="utf-8")
    (a / "Pdf").mkdir()
    (a / "Pdf" / "y.chs").write_text("y", encoding="utf-8")
    sa.sync()
    pdf_folder = next(i for i, it in fake.items.items() if it["name"] == "Pdf")
    fake.add("print.pdf", pdf_folder, b"%PDF")                         # put on Drive by hand
    (a / "Old").rename(a / "New")
    (a / "Pdf" / "y.chs").unlink()
    r = sa.sync()
    live = {it["name"] for it in fake.items.values() if not it["trashed"]}
    assert "Old" not in live and "New" in live and "Pdf" in live and "print.pdf" in live
    assert r.removed_folders == ["Old"]


def test_import_song_into_the_library(tmp_path):
    from modernsheet import library as L
    src = tmp_path / "outside" / "songs"
    (src.parent / "shared").mkdir(parents=True)
    src.mkdir()
    (src / "intro.musicxml").write_text("<a/>", encoding="utf-8")
    (src.parent / "shared" / "riff.musicxml").write_text("<b/>", encoding="utf-8")
    text = "{title: S}\n{musicxml: intro.musicxml}\n{musicxml: ../shared/riff.musicxml | 1-2}\n{musicxml: gone.musicxml}\n"
    lib = tmp_path / "lib" / "Jazz"
    lib.mkdir(parents=True)
    (lib / "intro.musicxml").write_text("<a/>", encoding="utf-8")         # same name and content: reused
    (lib / "riff.musicxml").write_text("<other/>", encoding="utf-8")      # same name, other content
    (lib / "Song.chs").write_text("x", encoding="utf-8")
    r = L.import_song(lib, "Song.chs", text, src)
    assert r.path == lib / "Song 2.chs" and (lib / "Song.chs").read_text() == "x"          # never overwrites
    assert r.copied == ["riff 2.musicxml"] and r.missing == ["gone.musicxml"]
    assert (lib / "riff 2.musicxml").read_text() == "<b/>" and (lib / "riff.musicxml").read_text() == "<other/>"
    assert r.path.read_text() == ("{title: S}\n{musicxml: intro.musicxml}\n{musicxml: riff 2.musicxml | 1-2}\n"
                                  "{musicxml: gone.musicxml}\n")
    phone = L.import_song(lib, "Phone", "{musicxml: a.musicxml}\n")                      # no folder: kept, missing
    assert phone.path.name == "Phone.chs" and phone.missing == ["a.musicxml"] and not phone.copied


# ---- import from a chordsheet.com account (fake site)
import html as _html  # noqa: E402
import re  # noqa: E402


class FakeChordsheet:
    """Just the pages the account importer reads: /login (Symfony form), /song/, /song/source/<id>."""
    LIST = ('<div class="row"><div class="card filter-me col-12"><div class="card-body">'
            '<h4 class="card-subtitle"><a href="/song/png/11/blue-night">Blue Night</a></h4>'
            '<h6 class="card-title">-</h6></div><div class="card-footer">'
            '<a href="/song/11/blue-night" title="PDF preview of Blue Night by -">x</a>'
            '<a href="/song/11/blue-night.pdf">pdf</a></div></div>'
            '<div class="card filter-me col-12"><div class="card-body">'
            '<h4 class="card-subtitle"><a href="/song/png/12/l-amore">L&#039;amore</a></h4>'
            '<h6 class="card-title">C. Baglioni</h6></div><div class="card-footer">'
            '<a href="/song/12/l-amore">x</a></div></div>'
            '<div class="card filter-me col-12"><div class="card-body">'
            '<h4 class="card-subtitle"><a href="/song/png/13/vuoto">Vuoto</a></h4><h6 class="card-title">-</h6>'
            '</div><div class="card-footer"><a href="/song/13/vuoto">x</a></div></div></div>')
    SOURCES = {"11": ("Blue Night · - · View Source", '= A\n(C F G"1°"_Am x)\nD.S. al coda'),
               "12": ("L'amore · C. Baglioni · View Source", "= Strofa\nC Am F G\n- piano"),
               "13": ("Vuoto · - · View Source", "")}

    def __init__(self):
        self.logged, self.posts, self.requests = False, [], []

    class _R:
        def __init__(self, url, body):
            self.url, self.body = url, body
        def geturl(self):
            return self.url
        def read(self):
            return self.body.encode()
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    def open(self, req, timeout=None):
        url = req.full_url
        path = url.split("chordsheet.test", 1)[1]
        self.requests.append(path)
        if path == "/login" and req.data is None:
            return self._R(url, '<form action="/login" method="post"><input name="_username"><input name="_password">'
                                '<input type="hidden" name="_csrf_token"\n   value="tok123"></form>')
        if path == "/login":
            form = dict(_up.parse_qsl(req.data.decode()))
            self.posts.append(form)
            if form == {"_username": "me@example.com", "_password": "secret", "_csrf_token": "tok123"}:
                self.logged = True
                return self._R("https://chordsheet.test/song/", self.LIST)
            return self._R("https://chordsheet.test/login", '<input name="_password">')
        if not self.logged:
            return self._R("https://chordsheet.test/login", '<input name="_password">')
        if path == "/song/":
            return self._R(url, self.LIST)
        m = re.match(r"/song/source/(\d+)\?slug=", path)
        title, src = self.SOURCES[m.group(1)]
        return self._R(url, f'<html><head><title>{_html.escape(title)}· Chord Sheet Maker</title></head>'
                            f'<pre class="fw-bold text-white p-3">{_html.escape(src)}</pre></html>')


def test_chordsheet_account_import():
    from modernsheet.importers import chordsheet_account as A
    site = FakeChordsheet()
    client = A.Client("https://chordsheet.test", site, pause=0.5, sleep=lambda s: None)
    with pytest.raises(A.LoginFailed):
        client.login("me@example.com", "wrong")
    client.login("me@example.com", "secret")
    songs = client.songs()
    assert [(s.id, s.title, s.artist) for s in songs] == [("11", "Blue Night", ""), ("12", "L'amore", "C. Baglioni"),
                                                         ("13", "Vuoto", "")]
    got = list(client.fetch_all(songs))
    assert [type(f).__name__ for _, f in got] == ["Fetched", "Fetched", "Fetched"]
    blue, amore, vuoto = (A.to_chs(f) for _, f in got)
    assert not amore.problems and "{tags: import_warn}" not in amore.text and "# chordsheet.com: /song/12/l-amore" in amore.text
    assert '[G "1°"]' in blue.text and "{ds: al Coda}" in blue.text
    assert vuoto.problems == ["empty"] and "{tags: import_warn}" in vuoto.text
    assert A.imported_ids([amore.text, vuoto.text, "x"]) == {"12", "13"}
    assert "secret" not in "".join(map(str, site.requests))      # the password only travels in the POST body


# ---- MusicXML editor: indentation and collapsed elements
XML_COMPACT = ('<?xml version="1.0"?>\n<score-partwise><part id="P1"><measure number="1"><note><pitch><step>C</step>'
               '<octave>4</octave></pitch><duration>1</duration></note><note><rest/></note></measure>'
               '<measure number="2"><note><pitch><step>D</step></pitch></note></measure></part></score-partwise>')


def _xml_canon(text):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(text.encode())
    for e in root.iter():
        e.text = e.text if e.text and e.text.strip() else None
        e.tail = e.tail if e.tail and e.tail.strip() else None
    return ET.tostring(root)


@pytest.mark.parametrize("path", sorted(EX.glob("*.musicxml")), ids=lambda p: p.stem)
def test_xml_indent_keeps_the_content(path):
    text = path.read_text(encoding="utf-8")
    for fmt in (xml_syntax.format_xml, xml_syntax.reindent_xml):
        out = fmt(text)
        assert _xml_canon(out) == _xml_canon(text)
        assert fmt(out) == out                                  # stable
    # reindent keeps the lines, only their leading whitespace changes
    out = xml_syntax.reindent_xml(text)
    assert [l.strip() for l in out.splitlines()] == [l.strip() for l in text.splitlines()]


def test_xml_format_one_element_per_line():
    out = xml_syntax.format_xml(XML_COMPACT)
    lines = out.splitlines()
    assert lines[2] == '  <part id="P1">'
    assert '          <step>C</step>' in lines                    # text-only elements stay on one line
    assert '        <rest/>' in lines and lines[-1] == "</score-partwise>"
    assert xml_syntax.xml_error(XML_COMPACT) is None
    assert xml_syntax.xml_error("<a>\n<b></a>")[0] == 2


def test_xml_folds_collapse_and_expand():
    text = xml_syntax.format_xml(XML_COMPACT)
    f = xml_syntax.Folds(text)
    assert f.fold_all("measure") == 2 and f.full() == text
    assert '    <measure number="1"> ⋯ </measure>' in f.view.splitlines()
    # expand measure 2, collapse a note inside it, then the whole part (nested), then back
    assert f.unfold_at(f.view.index('number="2"'))
    assert f.fold_at(f.view.index("<note>", f.view.index('number="2"')))
    assert "      <note> ⋯ </note>" in f.view.splitlines() and f.full() == text
    assert f.fold_at(f.view.index("<part"))
    assert f.view.count("\n") == 4 and f.full() == text
    assert f.unfold_at(f.view.index("<part")) and f.full() == text
    assert '    <measure number="1"> ⋯ </measure>' in f.view.splitlines()
    assert [f.view[i] for i in f.ellipses()] == ["⋯", "⋯"]
    # a single-line element cannot be collapsed; no fold on a line without one
    g = xml_syntax.Folds(text)
    assert not g.fold_at(g.view.index("<step>")) or "<pitch> ⋯ </pitch>" in g.view
    assert not xml_syntax.Folds("<a><b/></a>").fold_at(2)
    f.unfold_all()
    assert f.view == text and not f


def test_xml_folds_edits():
    text = xml_syntax.format_xml(XML_COMPACT)
    f = xml_syntax.Folds(text)
    f.fold_all("measure")
    v = f.view
    # typing before, between and after the collapsed measures is fine and lands in the full text
    at = v.index('<measure number="2">')
    assert f.edit(v[:at] + "<!-- x -->\n    " + v[at:])
    assert f.full() == text.replace('<measure number="2">', '<!-- x -->\n    <measure number="2">')
    v = f.view
    assert f.edit(v.replace("</part>", "</part><!-- y -->"))
    assert "</part><!-- y -->" in f.full() and f.full().count("<note>") == 3
    # an edit touching a marker is refused, nothing changes
    v = f.view
    k = v.index("⋯")
    assert not f.edit(v[:k] + v[k + 1:])
    assert not f.edit(v[:k - 3] + "Z" + v[k - 2:])
    assert f.view == v
    # the editor showing a collapsed line the folds do not know (drift): refused, the source is safe
    f.unfold_at(f.view.index('number="2"'))
    shown = f.view.replace(f.view[f.view.index('<measure number="2">'):f.view.index("</measure>", f.view.index(
        'number="2"')) + 10], '<measure number="2"> ⋯ </measure>')
    assert not f.edit(shown)
    assert f.full().count("<note>") == 3


# ---- notes written in the .chs ({start_of_notes}, SPEC §2.12b)
from modernsheet import notes as notes_mod  # noqa: E402


def _notes_song(body, key="F", time="4/4", transpose=0):
    return parse(f"{{key: {key}}}\n{{time: {time}}}\n{{start_of_intro}}\n{{start_of_notes}}\n{body}\n"
                 f"{{end_of_notes}}\n{{end_of_intro}}\n", transpose=transpose)


def _pitches(bar):
    return [("R" if n.step is None else n.step + {0: "", 1: "#", -1: "b", 2: "##", -2: "bb"}[n.alter]
             + str(n.octave)) for n in bar.notation.notes]


def test_notes_pitches_durations_octaves():
    s = _notes_song("| [Gm7] G8 Bb D F [C7] A G E C | [Am7] C E G Bn [D7] C# A 3(F E D) |\n"
                    "| [Gm7] D4. C8 [C7] E Eb D C | [F7] F2- F4 R4 |\n"
                    "| [F7] C@5/4 A F D | [Bb7] Bb@3/8 D F Ab C Bb Ab F |")
    assert s.warnings == []
    b = s.bars
    assert _pitches(b[0]) == ["G4", "Bb4", "D5", "F5", "A5", "G5", "E5", "C5"]   # first note near B4, then nearest
    assert [n.type for n in b[0].notation.notes] == ["eighth"] * 8                # the figure is kept
    assert [(e.chord, e.start, e.dur) for e in b[0].events] == [("Gm7", 0.0, 2.0), ("C7", 2.0, 2.0)]
    trip = [n for n in b[1].notation.notes if n.tuplet]
    assert len(trip) == 3 and trip[0].tuplet == (3, 2) and trip[0].tuplet_start and trip[-1].tuplet_stop
    assert abs(sum(n.dur for n in b[1].notation.notes) - 4) < 1e-9
    d = b[2].notation.notes[0]
    assert (d.type, d.dots, d.dur) == ("quarter", 1, 1.5)
    f1, f2, r = b[3].notation.notes
    assert f1.tie_start and f2.tie_stop and r.step is None
    assert _pitches(b[4]) == ["C5", "A4", "F4", "D4"]                              # @5 fixes the octave
    assert _pitches(b[5])[:3] == ["Bb3", "D4", "F4"] and b[5].notation.notes[0].type == "eighth"


def test_notes_relative_octave_marks_and_stacks():
    s = _notes_song("| C G G' G,, <C E G>2 |", key="C")
    assert _pitches(s.bars[0]) == ["C5", "G4", "G5", "G3", "C4", "E4", "G4"]
    stack = s.bars[0].notation.notes[4:]
    assert [n.chord for n in stack] == [False, True, True] and all(n.type == "half" for n in stack)
    rest = _notes_song("| R* |").bars[0].notation.notes[0]
    assert rest.measure_rest and rest.dur == 4


def test_notes_lyrics():
    s = _notes_song("| [F7] D2 Ab | [Bb7] C4 A- A F |\n"
                    "w: Blues, blues | del lu- ne-")
    a, b = s.bars[0].notation.notes, s.bars[1].notation.notes
    assert [n.lyric for n in a] == ["Blues,", "blues"]
    assert [n.lyric for n in b] == ["del", "lu-", "", "ne-"]          # tied continuation skipped
    s = _notes_song("| C D E F |\nw: a _ c")
    assert [n.lyric for n in s.bars[0].notation.notes] == ["a", "", "c", ""]
    assert "more than the notes" in _notes_song("| C2 D |\nw: a b c").warnings[0]


def test_notes_warnings():
    def warns(body, **kw):
        return " ".join(_notes_song(body, **kw).warnings)
    assert "key signature has Bb" in warns("| B1 |")                     # in F: B without accidental
    assert warns("| Bn1 |") == "" and warns("| Bb1 |") == ""
    assert "3 beats in 4/4" in warns("| C2 D4 |")
    assert "after @N" in warns("| C@54 D E F |")
    assert "same pitch" in warns("| C2- D2 |")
    assert "unrecognised note" in warns("| C H |")
    assert "not closed" in warns("| 3(C8 D E | F2. |")
    assert "no duration on chords" in warns("| [C:2] C1 |")
    s = parse("{start_of_verse}\n{start_of_notes}\n| C1 |\n{end_of_verse}\n")
    assert any("not closed" in w for w in s.warnings) and len(s.bars) == 1


def test_notes_chords_only_bar_and_repeats():
    s = _notes_song("|: [F7] C1 | [Bb7] [F7] :| {volta: 2} [C7] C1 |", key="C")
    a, b, c = s.bars
    assert a.repeat_start and a.notation and b.notation is None and b.repeat_end == 2
    assert [e.chord for e in b.events] == ["Bb7", "F7"] and c.volta == "2."


def test_notes_transpose():
    s = _notes_song("| [F7] F4 A C Eb |", transpose=2)
    assert _pitches(s.bars[0]) == ["G4", "B4", "D5", "F5"] and s.bars[0].events[0].chord == "G7"


def test_notes_beams():
    s = _notes_song("| G8 A B C D E F G |", key="C")
    assert [n.beams.get(1) for n in s.bars[0].notation.notes] == ["begin", "continue", "continue", "end"] * 2
    s = _notes_song("| G8 A B C D4 E |", key="C", time="3/4")         # 3/4: one beam per beat
    assert [n.beams.get(1) for n in s.bars[0].notation.notes] == ["begin", "end", "begin", "end", None, None]
    s = _notes_song("| G8 A B C D E |", key="C", time="6/8")          # 6/8: per dotted quarter
    assert [n.beams.get(1) for n in s.bars[0].notation.notes] == ["begin", "continue", "end"] * 2
    s = _notes_song("| G8 R A B C2 |", key="C")                       # a rest breaks the beam
    assert [n.beams.get(1) for n in s.bars[0].notation.notes] == [None, None, "begin", "end", None]


def _note_sig(n):
    return (n.step, n.alter, n.octave, round(n.start, 6), round(n.dur, 6), n.type, n.dots, n.chord, n.tie_start,
            n.tie_stop, n.lyric, n.measure_rest, n.tuplet, n.tuplet_start, n.tuplet_stop)


@pytest.mark.parametrize("path", sorted(EX.glob("*.musicxml")), ids=lambda p: p.stem)
def test_notes_from_musicxml_round_trip(path):
    from modernsheet.musicxml import read_musicxml
    measures, _ = read_musicxml(path)
    block = notes_mod.to_notes_text(measures, "F")
    a = parse(f"{{key: F}}\n{{start_of_intro}}\n{{musicxml: {path.name}}}\n{{end_of_intro}}\n", base_dir=EX)
    b = parse(f"{{key: F}}\n{{start_of_intro}}\n{block}{{end_of_intro}}\n")
    assert b.warnings == []
    assert [[_note_sig(n) for n in x.notation.notes] for x in a.bars] == \
           [[_note_sig(n) for n in x.notation.notes] for x in b.bars]
    assert [[(e.chord, round(e.start, 6), round(e.dur, 6)) for e in x.events] for x in a.bars] == \
           [[(e.chord, round(e.start, 6), round(e.dur, 6)) for e in x.events] for x in b.bars]
    assert [(x.repeat_start, x.repeat_end, x.volta, x.volta_end) for x in a.bars] == \
           [(x.repeat_start, x.repeat_end, x.volta, x.volta_end) for x in b.bars]


def test_notes_example_matches_musicxml_example():
    a = parse((EX / "blues_con_melodia.chs").read_text(encoding="utf-8"), base_dir=EX)
    b = parse((EX / "note_nel_chs.chs").read_text(encoding="utf-8"), base_dir=EX)
    assert a.warnings == b.warnings == []
    assert [[_note_sig(n) for n in x.notation.notes] if x.notation else None for x in a.bars] == \
           [[_note_sig(n) for n in x.notation.notes] if x.notation else None for x in b.bars]


def test_notes_editor_support():
    from modernsheet import syntax
    text = (EX / "note_nel_chs.chs").read_text(encoding="utf-8")
    toks = syntax.tokens(text)
    assert "".join(s for _, s in toks) == text
    kinds = {k for k, _ in toks}
    assert {"note", "rest", "duration"} <= kinds
    assert ("directive", "w:") in toks
    head = "{start_of_verse}\n{"
    assert "start_of_notes" in [c.name for c in syntax.suggestions(head, len(head))]
    head = "{start_of_verse}\n{start_of_notes}\n| C1 |\n{"
    assert syntax.suggestions(head, len(head))[0].name == "end_of_notes"
    assert syntax.open_section(head, len(head)) == "verse"


# ---- bar width per section ({bar_width} inside a section overrides the song's / the app's)
def _row_widths(song, **opts):
    from modernsheet.layout import Layout
    lay = Layout(song, **opts)
    lay.plan()
    out = {}
    for sec, rows, bpl in lay.layout:
        lay.bar_width = lay.section_mode(sec)
        x = lay.st.margin + (lay.max_prefix if lay.bar_width == "uniform" else lay.prefix_width(rows[0], False))
        out[sec.label] = (lay.bar_width, [lay.bar_widths(r, bpl, x) for r in rows])
    return out


def test_bar_width_per_section():
    src = ("{key: C}\n{start_of_verse: A}\n| [C] | [F] | [G] |\n{end_of_verse}\n"
           "{start_of_chorus: B}\n{bar_width: fit}\n| [C] | [F] | [G] | [C] |\n{end_of_chorus}\n"
           "{start_of_bridge: C}\n| [C] | [F] |\n{end_of_bridge}\n{ref: B}\n")
    s = parse(src)
    assert s.warnings == [] and "bar_width" not in s.meta
    assert [sec.bar_width for sec in s.sections] == [None, "fit", None, "fit"]     # the {ref} keeps it
    w = _row_widths(s)                                                            # app option: uniform
    mode_a, (a,) = w["A"][0], w["A"][1]
    assert mode_a == "uniform" and len({round(x, 3) for x in a}) == 1
    assert w["C"][0] == "uniform" and round(w["C"][1][0][0], 3) == round(a[0], 3)  # same grid as A
    mode_b, (b,) = w["B"][0], w["B"][1]
    assert mode_b == "fit" and sum(b) > 4 * a[0] + 10                             # a full row fills the width
    # the song header and the app option set the rest; a section still wins
    s = parse("{bar_width: fit}\n" + src.replace("{bar_width: fit}", "{bar_width: uniform}"))
    assert {k: v[0] for k, v in _row_widths(s, bar_width="uniform").items()} == {"A": "fit", "B": "uniform",
                                                                                   "C": "fit"}
    assert {k: v[0] for k, v in _row_widths(parse(src), bar_width="fit").items()} == {"A": "fit", "B": "fit",
                                                                                       "C": "fit"}
    assert "expected uniform or fit" in parse("{start_of_verse}\n{bar_width: wide}\n| [C] |\n{end_of_verse}\n").warnings[0]


def test_fit_rows_wrap_only_when_needed():
    """Fit mode: one crowded bar does not push the 4th bar to a new line when the others have room,
    a row closed for lack of room spans the whole width, no bar is narrower than it needs."""
    from modernsheet.layout import Layout
    src = ("{key: C}\n{start_of_verse: A}\n| [Bm7b5:1.5] [E7:2.5] | [Am] [%] [Am/G] | [F] [/] | |\n"
           "| [Cmaj7] [Am7] [Dm7] [G7] | [Em7] [A7] [Dm7] [G7] | [Cmaj7] [C7] [Fmaj7] [Fm6] | [Em7] [A7] [Dm7] [G7] |\n"
           "{end_of_verse}\n")
    for theme in ("realbook", "clean"):
        lay = Layout(parse(src), theme=theme, bar_width="fit")
        lay.plan()
        (sec, rows, bpl), = lay.layout
        assert len(rows[0]) == 4                                    # was 3 + 1 in the clean theme
        for i, r in enumerate(rows):
            x = lay.st.margin + lay.prefix_width(r, i == 0)
            w = lay.bar_widths(r, bpl, x)
            assert all(wi >= lay.bar_need(b, j == 0) - 0.5 for j, (b, wi) in enumerate(zip(r, w)))
            if i < len(rows) - 1:                                   # every row but the last reaches the margin
                assert abs(x + sum(w) - (lay.page_w - lay.st.margin)) < 0.5


# ---- space between rows: app option, a song's {row_spacing} wins
def test_row_spacing():
    from modernsheet.layout import Layout
    from modernsheet.model import row_spacing_factor
    assert [row_spacing_factor(v) for v in ("compact", "normal", "wide", "extra", "120%", "1,5", "0.4", "x")] == \
           [0.75, 1.0, 1.3, 1.6, 1.2, 1.5, None, None]
    body = "{start_of_verse}\n| [C] | [F] |\n| [G] | [C] |\n{end_of_verse}\n"

    def height(src, **opts):
        lay = Layout(parse(src), **opts)
        lay.plan()
        return lay.row_height(lay.layout[0][1][0])
    normal = height(body)
    gap = Layout(parse(body)).st.row_height - 20 - Layout(parse(body)).STAFF_H
    assert abs(height(body, row_spacing="wide") - (normal + 0.3 * gap)) < 1e-6         # the app option
    assert abs(height(body, row_spacing="compact") - (normal - 0.25 * gap)) < 1e-6
    assert abs(height("{row_spacing: 150%}\n" + body, row_spacing="compact") - (normal + 0.5 * gap)) < 1e-6
    assert height("{row_spacing: 120%}\n" + body) > normal
    s = parse("{row_spacing: huge}\n" + body)
    assert "row_spacing 'huge'" in s.warnings[0] and "row_spacing" not in s.meta
    # the page gets longer with more space: a long song needs more pages
    long = "{start_of_verse}\n" + "| [C] | [F] | [G] | [C] |\n" * 40 + "{end_of_verse}\n"
    assert len(layout(parse(long), row_spacing="extra").pages) > len(layout(parse(long), row_spacing="compact").pages)


# ---- guitar tablature (tab.py; {notation: staff|both|tab})
from modernsheet import tab as tab_mod  # noqa: E402


def _fingered(body, capo=0):
    s = _notes_song(body, key="C")
    warnings = tab_mod.assign([b.notation.notes for b in s.bars], capo)
    return [[(n.string, n.fret) if n.step else None for n in b.notation.notes] for b in s.bars], warnings


def test_tab_fingering():
    # C major scale from middle C (written): first position, open strings where they belong
    (scale,), w = _fingered("| C@4/8 D E F G A B C |")
    assert scale == [(1, 3), (2, 0), (2, 2), (2, 3), (3, 0), (3, 2), (4, 0), (4, 1)] and w == []
    # open chord shapes: one string per note, within reach
    (bar,), _ = _fingered("| <C@4 E G C>2 <G@3 B D>2 |")
    assert bar == [(1, 3), (2, 2), (3, 0), (4, 1), (0, 3), (1, 2), (2, 0)]
    # a tie keeps string and fret; a rest has none
    (bar,), _ = _fingered("| A@4/2- A4 R4 |")
    assert bar[0] == bar[1] and bar[2] is None
    # capo: frets from the capo; a note under it moves up an octave, with a warning
    (bar,), w = _fingered("| F#@3/4 G A E |", capo=2)
    assert bar[:3] == [(0, 0), (0, 1), (0, 3)] and "out of the instrument's range" in w[0]
    # notes no guitar can play together (E3 and G3 live on the low E string only): warned, not hidden
    (bar,), w = _fingered("| <E@3 G B>1 |")
    assert any("cannot play together" in x for x in w) and all(p is not None for p in bar)


def _texts(dl):
    return [op[3] for p in dl.pages for op in p if op[0] == "text"]


def test_tab_modes_render():
    src = ("{key: C}\n{capo: 0}\n{start_of_intro: Riff}\n{start_of_notes}\n"
           "| [C] C@4/8 E G C [G] B, G D2 | [Am] A@3/4 C E2 |\nw: la la la la la la la la la la\n"
           "{end_of_notes}\n| [F] | [G] |\n{end_of_intro}\n")
    staff = layout(parse(src))
    both = layout(parse(src), notation="both")
    tab = layout(parse(src), notation="tab")
    assert "T" not in _texts(staff) and {"T", "A", "B"} <= set(_texts(both)) and {"T", "A", "B"} <= set(_texts(tab))
    assert "3" in _texts(both) and "3" in _texts(tab)                           # fret of middle C
    # the option, the song and the section: the most specific wins
    s = parse("{notation: tab}\n" + src.replace("{start_of_notes}", "{notation: both}\n{start_of_notes}"))
    assert s.meta["notation"] == "tab" and s.sections[0].notation == "both"
    assert "notation 'piano'" in parse("{notation: piano}\n" + src).warnings[0]
    # the reader's switch over the sheet (notation_force) beats the song and its sections
    from modernsheet.layout import Layout as _L
    lay = _L(s, notation="staff", notation_force=True)
    assert [lay.section_notation(x) for x in s.sections] == ["staff"]
    lay = _L(parse("{notation: tab}\n" + src), notation="staff")
    assert lay.section_notation(lay.song.sections[0]) == "tab"
    # staff mode draws exactly what it drew before tablature existed: no strings assigned at all
    s = parse(src)
    layout(s)
    assert all(n.fret is None for b in s.bars if b.notation for n in b.notation.notes)

    from modernsheet.layout import Layout

    def height(**opts):
        lay = Layout(parse(src), **opts)
        lay.plan()
        lay.notation_mode = lay.section_notation(lay.song.sections[0])
        return lay.row_height(lay.layout[0][1][0])
    assert height(notation="both") > height(notation="tab") > height() - 1     # room for the six lines


def test_tab_example_has_no_warnings():
    s = parse((EX / "riff_per_chitarra.chs").read_text(encoding="utf-8"))
    for mode in ("staff", "both", "tab"):
        layout(s, notation=mode)
    assert s.warnings == []


def test_tab_phase2_hints_position_tuning():
    def fingered(body, key="C", head=""):
        s = parse(f"{head}{{key: {key}}}\n{{start_of_verse}}\n{{start_of_notes}}\n{body}\n{{end_of_notes}}\n{{end_of_verse}}\n")
        lay_warn = tab_mod.assign([b.notation.notes for b in s.bars], 0,
                                  tab_mod.parse_tuning(s.meta.get("tuning", "standard")))
        return [[(n.string, n.fret) for n in b.notation.notes if n.step] for b in s.bars], s.warnings + lay_warn
    # {tab_position: 5}: the scale moves up the neck
    (bar,), w = fingered("{tab_position: 5}\n| C@4/8 D E F G A B C |")
    assert w == [] and all(4 <= f <= 9 for _, f in bar)
    (bar,), _ = fingered("| C@4/8 D E F G A B C |")
    assert max(f for _, f in bar) <= 3                                   # without it: first position
    # ~N: the note on that string (guitar numbering, 1 = high E)
    (bar,), w = fingered("| E@4/4~5 G~4 B~3 E~2 |")
    assert bar == [(1, 7), (2, 5), (3, 4), (4, 5)] and w == []
    (bar,), w = fingered("| E@4/1~1 |")
    assert "cannot be played on string 1" in w[0]
    (bar,), _ = fingered("| <C@4~5 E~4 G~3>1 |")
    assert bar == [(1, 3), (2, 2), (3, 0)]
    # tunings: drop D reaches the low D without moving it; bass and ukulele have 4 strings
    (bar,), w = fingered("| D@3/4 A@3 D@4/2 |", head="{tuning: drop D}\n")
    assert bar[0] == (0, 0) and w == []
    (_,), w = fingered("| D@3/1 |")
    assert "out of the instrument's range" in w[0]
    assert tab_mod.parse_tuning("D A D G B E") == tab_mod.TUNINGS["drop d"]
    assert tab_mod.parse_tuning("DADGAD") == tab_mod.TUNINGS["dadgad"] and tab_mod.parse_tuning("x y") is None
    assert tab_mod.string_names(tab_mod.TUNINGS["half step down"]) == ["Eb", "Ab", "Db", "Gb", "Bb", "Eb"]
    assert "tuning 'banjo'" in parse("{tuning: banjo}\n").warnings[0]
    assert "tab_position 'x'" in parse("{start_of_verse}\n{tab_position: x}\n{end_of_verse}\n").warnings[0]


def test_tab_phase2_layout_and_musicxml(tmp_path):
    from modernsheet.layout import Layout
    src = "{key: C}\n{tuning: bass}\n{start_of_verse}\n{start_of_notes}\n| E@3/4 A D G |\n{end_of_notes}\n{end_of_verse}\n"
    lay = Layout(parse(src), notation="tab")
    assert lay.tab_n == 4 and abs(lay.TAB_H - 3 * lay.TAB_SP) < 1e-9
    texts = _texts(layout(parse(src.replace("bass", "drop D")), notation="both"))
    assert texts.count("D") >= 2 and "T" not in texts                    # string names instead of TAB
    # MusicXML guitar parts: string and fret from the file
    xml = (EX / "blues_tema.musicxml").read_text(encoding="utf-8")
    first = xml.index("<note>", xml.index('<measure number="1"'))
    end = xml.index("</note>", first)
    xml = xml[:end] + "<notations><technical><string>4</string><fret>12</fret></technical></notations>" + xml[end:]
    f = tmp_path / "g.musicxml"
    f.write_text(xml, encoding="utf-8")
    s = parse("{key: F}\n{start_of_verse}\n{musicxml: g.musicxml}\n{end_of_verse}\n", base_dir=tmp_path)
    n = s.bars[0].notation.notes[0]
    assert (n.tab_string, n.tab_fret) == (4, 12)
    tab_mod.assign([b.notation.notes for b in s.bars])
    assert (n.string, n.fret) == (2, 12)                                 # D5 on the D string, as the file says
    block = notes_mod.to_notes_text([dict(notes=[n], harmonies=[], length=4)], "F")
    assert "~4" in block
