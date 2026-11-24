"""Regression tests — Guitar tablature. Run with `pytest` from the project folder."""
from modernsheet import layout, parse
from modernsheet import notes as notes_mod

from helpers import EX, notes_song


# ---- guitar tablature (tab.py; {notation: staff|both|tab})
from modernsheet import tab as tab_mod  # noqa: E402


def _fingered(body, capo=0):
    s = notes_song(body, key="C")
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
