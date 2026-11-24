"""Regression tests — Notes written in the .chs ({start_of_notes}). Run with `pytest` from the project
folder."""
import pytest

from modernsheet import parse

from helpers import EX, notes_song


# ---- notes written in the .chs ({start_of_notes}, SPEC §2.12b)
from modernsheet import notes as notes_mod  # noqa: E402


def _pitches(bar):
    return [("R" if n.step is None else n.step + {0: "", 1: "#", -1: "b", 2: "##", -2: "bb"}[n.alter]
             + str(n.octave)) for n in bar.notation.notes]


def test_notes_pitches_durations_octaves():
    s = notes_song("| [Gm7] G8 Bb D F [C7] A G E C | [Am7] C E G Bn [D7] C# A 3(F E D) |\n"
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
    s = notes_song("| C G G' G,, <C E G>2 |", key="C")
    assert _pitches(s.bars[0]) == ["C5", "G4", "G5", "G3", "C4", "E4", "G4"]
    stack = s.bars[0].notation.notes[4:]
    assert [n.chord for n in stack] == [False, True, True] and all(n.type == "half" for n in stack)
    rest = notes_song("| R* |").bars[0].notation.notes[0]
    assert rest.measure_rest and rest.dur == 4


def test_notes_lyrics():
    s = notes_song("| [F7] D2 Ab | [Bb7] C4 A- A F |\n"
                    "w: Blues, blues | del lu- ne-")
    a, b = s.bars[0].notation.notes, s.bars[1].notation.notes
    assert [n.lyric for n in a] == ["Blues,", "blues"]
    assert [n.lyric for n in b] == ["del", "lu-", "", "ne-"]          # tied continuation skipped
    s = notes_song("| C D E F |\nw: a _ c")
    assert [n.lyric for n in s.bars[0].notation.notes] == ["a", "", "c", ""]
    assert "more than the notes" in notes_song("| C2 D |\nw: a b c").warnings[0]


def test_notes_warnings():
    def warns(body, **kw):
        return " ".join(notes_song(body, **kw).warnings)
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
    s = notes_song("|: [F7] C1 | [Bb7] [F7] :| {volta: 2} [C7] C1 |", key="C")
    a, b, c = s.bars
    assert a.repeat_start and a.notation and b.notation is None and b.repeat_end == 2
    assert [e.chord for e in b.events] == ["Bb7", "F7"] and c.volta == "2."


def test_notes_transpose():
    s = notes_song("| [F7] F4 A C Eb |", transpose=2)
    assert _pitches(s.bars[0]) == ["G4", "B4", "D5", "F5"] and s.bars[0].events[0].chord == "G7"


def test_notes_beams():
    s = notes_song("| G8 A B C D E F G |", key="C")
    assert [n.beams.get(1) for n in s.bars[0].notation.notes] == ["begin", "continue", "continue", "end"] * 2
    s = notes_song("| G8 A B C D4 E |", key="C", time="3/4")         # 3/4: one beam per beat
    assert [n.beams.get(1) for n in s.bars[0].notation.notes] == ["begin", "end", "begin", "end", None, None]
    s = notes_song("| G8 A B C D E |", key="C", time="6/8")          # 6/8: per dotted quarter
    assert [n.beams.get(1) for n in s.bars[0].notation.notes] == ["begin", "continue", "end"] * 2
    s = notes_song("| G8 R A B C2 |", key="C")                       # a rest breaks the beam
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
