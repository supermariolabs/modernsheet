"""Regression tests — Pure Python parts of the app: settings, editor support, languages, MusicXML tabs and
their conversion, XML indentation, changed parts and undo/redo. Run with `pytest` from the project folder."""
from pathlib import Path

import pytest

from modernsheet import parse

from helpers import EX, SONGS


# ---- app settings and editor support (pure Python parts of the app)
from modernsheet import syntax  # noqa: E402
from modernsheet.settings import Settings  # noqa: E402


def test_settings_roundtrip_and_validation():
    s = Settings(library_root="/x", pdf_dir="/y", theme="clean", bar_width="fit", row_spacing="wide",
                 notation="both", chord_symbols="jazz", label_colors="by_type")
    assert Settings.from_json(s.to_json()) == s
    assert s.layout_options() == dict(theme="clean", bar_width="fit", row_spacing="wide", notation="both",
                                      chord_symbols="jazz", note_names="letters", label_colors="by_type")
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


def _xml_one_measure(beats=4, beat_type=4, fifths=0):
    """A minimal MusicXML: one measure with a whole-bar rest."""
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<score-partwise version="4.0"><part-list><score-part id="P1">'
            f'<part-name>M</part-name></score-part></part-list><part id="P1"><measure number="1"><attributes>'
            f'<divisions>1</divisions><key><fifths>{fifths}</fifths></key><time><beats>{beats}</beats>'
            f'<beat-type>{beat_type}</beat-type></time></attributes><note><rest measure="yes"/>'
            f'<duration>{beats * 4 // beat_type}</duration></note></measure></part></score-partwise>\n')


def test_musicxml_refs(tmp_path):
    from modernsheet import library
    text = "{start_of_intro}\n{musicxml: a.musicxml}\n{musicxml: b.xml | 3-4}\n{musicxml: a.musicxml | 1}\n" \
           "| {musicxml: inline.musicxml} [C] |\n{end_of_intro}\n"
    assert library.musicxml_refs(text) == ["a.musicxml", "b.xml"]          # own line only, no duplicates
    (tmp_path / "a.musicxml").write_text(_xml_one_measure(3, 4, -1), encoding="utf-8")
    song = parse("{key: F}\n{time: 3/4}\n{start_of_intro}\n{musicxml: a.musicxml}\n{end_of_intro}\n",
                 base_dir=tmp_path)
    assert len(song.bars) == 1 and song.warnings == []


def test_parse_uses_unsaved_musicxml(tmp_path):
    f = tmp_path / "a.musicxml"
    f.write_text(_xml_one_measure(4, 4, 0), encoding="utf-8")
    src = "{start_of_intro}\n{musicxml: a.musicxml}\n{end_of_intro}\n"
    two = _xml_one_measure(4, 4, 0).replace("</measure>", '</measure>\n<measure number="2"><note>'
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


def test_convert_musicxml_examples():
    """Every MusicXML of the examples converts to notes that read back identical, references commented."""
    from modernsheet import library
    for chs in sorted(EX.glob("*.chs")):
        text = original = chs.read_text(encoding="utf-8")
        refs = library.musicxml_refs(text)
        for ref in refs:
            c = library.convert_musicxml(text, ref, EX, "converted")
            assert c.count >= 1 and c.exact, (chs.name, ref)
            assert f"# {{musicxml: {ref}" in c.text and "(converted)" in c.text
            text = c.text
        if refs:
            assert library.musicxml_refs(text) == []                 # commented: no tab, not read
            assert parse(text, base_dir=EX).warnings == []
            assert text.count("{start_of_notes}") >= sum(l.startswith("{musicxml:") for l in original.splitlines())


def test_convert_musicxml_range_time_and_key(tmp_path):
    from modernsheet import library
    xml = _xml_one_measure(3, 4, -1).replace("</measure>", '</measure><measure number="2"><note><pitch><step>B</step>'
                                             '<alter>-1</alter><octave>4</octave></pitch><duration>3</duration>'
                                             '<type>half</type><dot/></note></measure>')
    (tmp_path / "a.musicxml").write_text(xml, encoding="utf-8")
    src = ("{key: F}\n{time: 4/4}\n{start_of_intro}\n  {musicxml: a.musicxml | 2}\n{end_of_intro}\n"
           "{start_of_verse}\n| [F] | [C] |\n{end_of_verse}\n# {musicxml: a.musicxml}\n")
    c = library.convert_musicxml(src, "a.musicxml", tmp_path)
    assert c.count == 1 and c.exact                        # the commented reference is left alone
    assert "  # {musicxml: a.musicxml | 2}\n  {time: 3/4}\n{start_of_notes}\n| Bb2. |\n{end_of_notes}\n" in c.text
    assert c.text.endswith("# {musicxml: a.musicxml}\n")
    song = parse(c.text, base_dir=tmp_path)
    assert song.warnings == [] and (song.bars[1].num, song.bars[1].den) == (3, 4)
    with pytest.raises(OSError):
        library.convert_musicxml(src, "missing.musicxml", tmp_path)


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
    out = xml_syntax.format_xml(text)
    assert _xml_canon(out) == _xml_canon(text)
    assert xml_syntax.format_xml(out) == out                    # stable


def test_xml_format_one_element_per_line():
    out = xml_syntax.format_xml(XML_COMPACT)
    lines = out.splitlines()
    assert lines[2] == '  <part id="P1">'
    assert '          <step>C</step>' in lines                    # text-only elements stay on one line
    assert '        <rest/>' in lines and lines[-1] == "</score-partwise>"
    assert xml_syntax.xml_error(XML_COMPACT) is None
    assert xml_syntax.xml_error("<a>\n<b></a>")[0] == 2


# ---- editor: changed parts and undo / redo (edits.py)
from modernsheet import edits  # noqa: E402


def test_changes_since_saved():
    base = "{title: A}\n| [C] | [F] |\n{end}\n"
    assert edits.changes(base, base) == []
    text = "{title: AB}\n| [C] | [F] |\nnew line\n{end}\n"
    r = edits.changes(base, text)
    assert [(text[a:b], lvl) for a, b, lvl in r] == [("{title: A", 1), ("B", 2), ("}", 1), ("new line", 2)]
    assert edits.changes(base, base.replace("| [C] | [F] |\n", "")) == []     # a removed line: nothing to paint
    pieces = edits.mark([("x", text[:5]), ("y", text[5:])], r)
    assert "".join(s for _, s, _ in pieces) == text                         # nothing lost or repeated
    assert ("y", "B", 2) in pieces and pieces[0] == ("x", "{titl", 1)
    assert all(lvl == 0 for _, s, lvl in pieces if s.startswith("\n| [C]"))


def test_history_steps_and_grouping():
    h = edits.History()
    s, t = "", 0.0
    for ch in "ciao mondo":                       # typed one character at a time
        h.record(s, s + ch, t)
        s, t = s + ch, t + 0.1
    h.record(s, s + "\n", t)                       # a new line is a step of its own
    s += "\n"
    h.record(s, s + "x", t + 5)                    # after a pause: a new step
    s += "x"
    assert h.undo() == ("ciao mondo\n", 11)
    assert h.undo() == ("ciao mondo", 10)
    assert h.undo() == ("ciao", 4)                 # one word per step
    assert h.undo() == ("", 0) and h.undo() is None and not h.can_undo
    assert h.redo() == ("ciao", 4) and h.can_redo
    h.record("ciao", "ciao!", 100)                 # a new edit drops what could be redone
    assert not h.can_redo
    # backspaces in a row are one step; an edit elsewhere is another
    h = edits.History()
    h.record("abcdef", "abcde", 0)
    h.record("abcde", "abcd", 0.1)
    h.record("abcd", "Xabcd", 0.2)
    assert h.undo() == ("abcd", 0) and h.undo() == ("abcdef", 6)


def test_history_recognises_the_fields_own_undo():
    h = edits.History()
    h.record("a", "a b", 0)
    assert h.observe("a b", "a", 1) == "undo" and h.can_redo      # the text field undid our step
    assert h.observe("a", "a b", 2) == "redo" and not h.can_redo
    assert h.observe("a b", "a bc", 3) == "edit" and h.undo() == ("a b", 3)
