"""Regression tests — Engine: examples, layout, PDF and screen output, transposition, navigation and rhythm
marks, bar widths and row spacing. Run with `pytest` from the project folder."""
import pytest

from modernsheet import layout, parse
from modernsheet.fonts import registry
from modernsheet.pdf import pdf_bytes
from modernsheet.screen import screen_ops
from modernsheet.theory import transpose_chord

from helpers import EX, OPTIONS, SONGS, csm_song, load


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


def test_key_and_time_changes_in_a_song_without_header(tmp_path):
    """Once a bar exists, {key} and {time} are changes even if the song has no header (before 0.44.1
    the first one became the song's key or time, and the change was not drawn)."""
    s = parse("{start_of_verse: V}\n| [G7] || {key: Db} [Db] | [Gb] |\n| [Gm7] | {time: 2/4} [C7] | {time: 4/4} [F7] |\n"
              "{end_of_verse}\n")
    assert s.warnings == [] and (s.meta["key"], s.meta["time"]) == ("C", "4/4")
    assert [(b.key, b.key_change, b.prev_key) for b in s.bars[:2]] == [("C", False, None), ("Db", True, "C")]
    assert s.bars[0].double_after                                   # double bar before the new key
    assert [((b.num, b.den), b.time_change) for b in s.bars[4:]] == [((2, 4), True), ((4, 4), True)]
    # the header still works as before, also inside the first section before any bar
    s = parse("{start_of_verse: V}\n{key: F}\n{time: 3/4}\n| [F] |\n{end_of_verse}\n")
    assert (s.meta["key"], s.meta["time"]) == ("F", "3/4") and not s.bars[0].key_change and not s.bars[0].time_change
    # a MusicXML in another time after the first bars: a time change, too
    (tmp_path / "w.musicxml").write_text(
        '<score-partwise><part-list><score-part id="P1"><part-name>M</part-name></score-part></part-list>'
        '<part id="P1"><measure number="1"><attributes><divisions>1</divisions><key><fifths>0</fifths></key>'
        '<time><beats>3</beats><beat-type>4</beat-type></time></attributes><note><rest measure="yes"/>'
        '<duration>3</duration></note></measure></part></score-partwise>', encoding="utf-8")
    s = parse("{start_of_intro}\n| [C] |\n{musicxml: w.musicxml}\n{end_of_intro}\n", base_dir=tmp_path)
    assert s.warnings == [] and s.meta["time"] == "4/4" and ((s.bars[1].num, s.bars[1].den), s.bars[1].time_change) == ((3, 4), True)


def test_reference_shown_under_another_label():
    """{ref: Label = New label}: the copy shows the new label, keeps the original's colour (also a
    section_colors entry keyed by the original label), is transposed and repeated as usual."""
    s = parse("{key: G}\n{section_colors: Ritornello=#ff9900}\n{start_of_chorus: Ritornello}\n| [G] | [C] |\n"
              "{end_of_chorus}\n{key: A}\n{ref: Ritornello x2 = Ritornello finale | tutti insieme}\n{ref: chorus}\n"
              "{ref: Ritornello =}\n")
    assert s.warnings == []
    orig, renamed, by_kind, empty = s.sections
    assert (renamed.label, renamed.ref_label, renamed.times, renamed.note) == ("Ritornello finale", "Ritornello", 2,
                                                                                 "tutti insieme")
    assert [e.chord for b in renamed.bars for e in b.events] == ["A", "D", "A", "D"]
    assert by_kind.label == "Ritornello" and empty.label == "Ritornello"          # no new label: the original's
    from modernsheet.layout import Layout
    lay = Layout(s)
    assert {lay.label_color(sec) for sec in s.sections} == {(1.0, 0.6, 0.0)}
    assert "Strofa finale" in str(layout(load(EX / "amazing_grace.chs")).pages)   # the example shows it


def test_reference_straight_to_one_ending():
    """{ref: Label volta N}: one pass through the section straight to its ending N, without the repeat,
    the other endings or the brackets; repeats outside the endings stay; no such ending: a warning."""
    src = ("{start_of_chorus: Rit}\n|: [C] | [D] |\n{volta: 1} [E] :|\n{volta: 2} [F] | [G] ||\n| [A] |\n{end_of_chorus}\n"
           "{start_of_verse: V}\n|: [C] :|\n{end_of_verse}\n")
    s = parse(src + "{ref: Rit $volta 2 = Finale | dritti}\n{ref: Rit x2 $volta 1}\n{ref: V $volta 2}\n")
    rit, verse, fin, twice, whole = s.sections
    assert [[e.chord for e in b.events] for b in fin.bars] == [["C"], ["D"], ["F"], ["G"], ["A"]]
    assert (fin.label, fin.note) == ("Finale", "dritti")
    assert not any(b.repeat_start or b.repeat_end or b.volta or b.volta_end for b in fin.bars)
    assert [[e.chord for e in b.events] for b in twice.bars] == [["C"], ["D"], ["E"], ["A"]] * 2   # bars after the endings too
    assert s.warnings == ["line 12: ref: section 'V' has no ending 2: copied whole"]
    assert whole.bars[0].repeat_start and whole.bars[0].repeat_end == 2
    assert [b.volta for b in rit.bars if b.volta] == ["1.", "2."]          # the original is untouched
    ex = load(EX / "ripetizioni_e_volte.chs")
    assert ex.warnings == [] and any(sec.label == "Ultimo ritornello" for sec in ex.sections)


def test_reference_of_a_section_with_its_own_key():
    """A {key} inside a section, before its music, is the section's key: a {ref} later transposes from
    it (until 0.45.0 it transposed from the key before the section: A + 4 semitones gave Db, not B)."""
    s = parse("{key: G}\n{start_of_verse: V}\n| [G] | [D] |\n{end_of_verse}\n"
              "{start_of_chorus: Chorus}\n{key: A}\n| [A] | [E/G#] | [F#m] |\n{end_of_chorus}\n"
              "{key: B}\n{ref: Chorus}\n{ref: V}\n")
    assert s.warnings == []
    chorus, ref, verse = s.sections[1], s.sections[2], s.sections[3]
    assert chorus.key == "A"
    assert [e.chord for b in ref.bars for e in b.events] == ["B", "F#/A#", "G#m"]
    assert ref.bars[0].key == "B" and [e.chord for b in verse.bars for e in b.events] == ["B", "F#"]


def test_reference_once_without_repeats():
    """{ref: Label $once}: the section without repeats, each repeated part once; at a group of endings
    the last one (the way out), or ending N with `volta N`; combines with xN and = label."""
    src = ("{start_of_intro: I}\n|: [G] | [C] :| x3\n{end_of_intro}\n"
           "{start_of_chorus: Rit}\n|: [C] | [D] |\n{volta: 1} [E] :|\n{volta: 2} [F] ||\n| [A] |\n|: [B] :|\n"
           "{end_of_chorus}\n")
    s = parse(src + "{ref: I $once}\n{ref: Rit $once = Fine | piano}\n{ref: Rit $once $volta 1}\n{ref: Rit x2 $once}\n"
                    "{ref: Rit $volta 3 $once}\n")
    chords = lambda sec: [e.chord for b in sec.bars for e in b.events]
    intro, rit, i1, fin, v1, twice, missing = s.sections
    assert chords(i1) == ["G", "C"] and chords(fin) == ["C", "D", "F", "A", "B"]
    assert (fin.label, fin.note) == ("Fine", "piano")
    assert not any(b.repeat_start or b.repeat_end or b.volta or b.volta_end for sec in (i1, fin, v1, twice) for b in sec.bars)
    assert chords(v1) == ["C", "D", "E", "A", "B"] and chords(twice) == chords(fin) * 2
    assert chords(missing) == chords(fin)
    assert s.warnings == ["line 15: ref: section 'Rit' has no ending 3: the last ending of each repeat"]
    assert intro.bars[0].repeat_start and intro.bars[-1].repeat_end == 3      # the originals are untouched
    ex = load(EX / "ripetizioni_e_volte.chs")
    assert ex.warnings == [] and any(sec.label == "Chiusura" for sec in ex.sections)


def test_short_reference_is_just_the_box():
    """{ref: Label $short}: a section with no bars (only its box: label, xN, note); in another key the box
    says it, and the key change is drawn on the next bar written."""
    s = parse("{key: G}\n{start_of_chorus: Rit}\n|: [G] | [C] :|\n{end_of_chorus}\n"
              "{ref: Rit x2 $short | tutti}\n{key: A}\n{ref: Rit $short = Fine}\n{start_of_outro: O}\n| [A] |\n{end_of_outro}\n")
    assert s.warnings == []
    _, same, other, outro = s.sections
    assert (same.short, same.bars, same.times, same.note, same.ref_key) == (True, [], 2, "tutti", "")
    assert (other.label, other.ref_key, other.bars) == ("Fine", "A", [])
    assert outro.bars[0].key_change and outro.bars[0].prev_key == "G"
    texts = [op[3] for op in layout(s).pages[0] if op[0] == "text"]
    assert "Rit  x2" in texts and "reprise - tutti" in texts and "reprise - Key A" in texts
    ex = load(EX / "tempi_e_tonalita.chs")
    assert ex.warnings == [] and any(sec.short and sec.ref_key == "Eb" for sec in ex.sections)


def test_reference_options_with_dollar():
    """$volta N, $once, $short are the options of a {ref}; without the $ the words belong to the section's
    name, so a section called "Prima volta 2" (or "Coro once") is referenced by its name."""
    src = ("{start_of_chorus: Rit}\n|: [C] | [D] |\n{volta: 1} [E] :|\n{volta: 2} [F] ||\n{end_of_chorus}\n"
           "{start_of_verse: Prima volta 2}\n| [G] |\n{end_of_verse}\n")
    s = parse(src + "{ref: Rit $volta 2}\n{ref: Rit x2 $once = Fine | piano}\n{ref: Rit $short}\n"
                    "{ref: Prima volta 2}\n{ref: Prima volta 2 $short}\n{ref: Rit once}\n")
    chords = lambda sec: [e.chord for b in sec.bars for e in b.events]
    v2, once, short, named, named_short = s.sections[2:]
    assert chords(v2) == ["C", "D", "F"]
    assert chords(once) == ["C", "D", "F"] * 2 and (once.label, once.note) == ("Fine", "piano")
    assert short.short and short.bars == []
    assert named.label == "Prima volta 2" and chords(named) == ["G"]
    assert named_short.short and named_short.label == "Prima volta 2"
    assert s.warnings == ["line 14: ref: 'once' is an old syntax, now written with $: {ref: Rit $once}"]
    s = parse(src + "{ref: Rit x2 volta 2 short}\n{ref: Nessuna once}\n{ref: Rit once = Fine | piano}\n")
    assert s.warnings == ["line 9: ref: 'volta 2', 'short' is an old syntax, now written with $: "
                          "{ref: Rit x2 $volta 2 $short}",
                          "line 10: ref: section 'Nessuna once' not found (only earlier sections can be referenced)",
                          "line 11: ref: 'once' is an old syntax, now written with $: {ref: Rit $once = Fine | piano}"]


def test_text_and_option_ambiguities():
    """A {ref} whose whole text is a section's name refers to it even if the name looks like options
    ("Strofa x2", "Do = La", "A | B"); a line of text with no chord and no bar line gives a warning
    instead of disappearing."""
    s = parse("{start_of_verse: Strofa x2}\n| [C] |\n{end_of_verse}\n{start_of_bridge: Do = La}\n| [D] |\n"
              "{end_of_bridge}\n{start_of_chorus: A | B}\n| [E] |\n{end_of_chorus}\n"
              "{ref: Strofa x2}\n{ref: Do = La}\n{ref: A | B}\n{ref: Strofa x2 x2}\n")
    assert s.warnings == []
    refs = [sec for sec in s.sections if sec.is_ref]
    assert [(r.label, r.times, [e.chord for b in r.bars for e in b.events]) for r in refs] == [
        ("Strofa x2", 1, ["C"]), ("Do = La", 1, ["D"]), ("A | B", 1, ["E"]), ("Strofa x2", 2, ["C", "C"])]
    s = parse("{start_of_verse: V}\n| [C]Prima |\nsolo testo senza accordi\n{end_of_verse}\n")
    assert s.warnings == ["line 3: text without chords or bar lines: ignored (a line of text in the sheet: {text: …})"]


def test_repeat_end_glued_to_lyrics_is_text():
    """`:|` ends a repeat at the start of a line or after a space, a chord, a bar line or a directive;
    glued to a word the colon is lyrics ("Dico:|" = "Dico:" and a bar line)."""
    s = parse("{start_of_verse: V}\n| [C]Dico:| [G]sì |\n|: [C] | [G]:|\n|: [F] | [G] {fine}:|\n| [A] |\n:| x3\n"
              "{end_of_verse}\n")
    assert s.warnings == []
    b = s.bars
    assert (b[0].events[0].lyric, b[0].repeat_end, len(b)) == ("Dico:", 0, 7)
    assert b[3].repeat_end == 2                              # [G]:| right after a chord
    assert b[5].repeat_end == 2                              # right after a directive
    assert b[6].repeat_end == 3                              # at the start of a line
