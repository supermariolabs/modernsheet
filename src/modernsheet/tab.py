"""Guitar tablature: choose a string and a fret for every note of the notated bars (SPEC §4.8b).

A pitch can be played in several places; the fingering is chosen for the whole passage at once, as
the cheapest path through the possible positions (dynamic programming, Viterbi): the cost favours
staying in one hand position, low frets, few big shifts, and for notes on one stem one string each
within a playable stretch. Tied continuations repeat the string and fret of the note they continue.

Pitches are read as guitar notation: the written note is played as written (the guitar sounds an
octave lower), so the open strings are E3 A3 D4 G4 B4 E5 in written pitch. With a capo, frets are
counted from the capo. Notes out of reach move by octaves, with a warning.

Standard library only.
"""
from __future__ import annotations

import re
from itertools import product

STANDARD = (52, 57, 62, 67, 71, 76)     # written MIDI pitch of the open strings, 6th (low E) to 1st
# named tunings: written pitch of the open strings, from the string farthest from the floor's side (low E)
TUNINGS = {
    "standard": STANDARD,
    "drop d": (50, 57, 62, 67, 71, 76),
    "double drop d": (50, 57, 62, 67, 71, 74),
    "dadgad": (50, 57, 62, 67, 69, 74),
    "open g": (50, 55, 62, 67, 71, 74),
    "open d": (50, 57, 62, 66, 69, 74),
    "open e": (52, 59, 64, 68, 71, 76),
    "half step down": (51, 56, 61, 66, 70, 75),
    "bass": (40, 45, 50, 55),                 # written an octave over the sound, like the guitar
    "bass 5": (35, 40, 45, 50, 55),
    "ukulele": (67, 60, 64, 69),              # G C E A, re-entrant (the 4th string is a high G)
}
PITCH_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
_NAME_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def parse_tuning(value: str) -> tuple[int, ...] | None:
    """A tuning: a name (standard, drop D, DADGAD, open G, bass, ukulele…) or the open strings from
    the lowest, as note names ("D A D G B E", "DADGBE", with # or b); None if not valid. Written
    note names are placed from around the low E upwards, each string higher than the previous one."""
    v = " ".join(str(value).strip().lower().replace("-", " ").replace("_", " ").split())
    if v in TUNINGS:
        return TUNINGS[v]
    if v.replace(" ", "") in {k.replace(" ", ""): k for k in TUNINGS}:
        return TUNINGS[{k.replace(" ", ""): k for k in TUNINGS}[v.replace(" ", "")]]
    names = re.findall(r"([A-Ga-g])(#|b)?", str(value).replace(" ", ""))
    if not 4 <= len(names) <= 8 or "".join(a + b for a, b in names) != str(value).replace(" ", ""):
        return None
    out: list[int] = []
    for letter, acc in names:
        pc = (_NAME_PC[letter.upper()] + {"#": 1, "b": -1, "": 0}[acc]) % 12
        if not out:
            m = 48 + pc                          # the lowest string: between C3 and B3, near the low E
            m += 12 if m < 46 else 0
        else:
            m = out[-1] + (pc - out[-1]) % 12 or out[-1] + 12
        out.append(m)
    return tuple(out)


FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]


def string_names(tuning) -> list[str]:
    """Names of the open strings, lowest first (for the left of the tablature); flats if the tuning
    has an E flat, A flat or B flat (half step down), sharps otherwise."""
    names = FLAT_NAMES if {m % 12 for m in tuning} & {3, 8, 10} else PITCH_NAMES
    return [names[m % 12] for m in tuning]
MAX_FRET = 20
MAX_STRETCH = 4                         # frets between the lowest and highest fretted note of one stem

Place = tuple[int, int]                 # (string index 0 = low E … 5 = high E, fret)


def places(midi: int, capo: int = 0, tuning=STANDARD) -> list[Place]:
    out = []
    for s, open_ in enumerate(tuning):
        f = midi - open_ - capo
        if 0 <= f <= MAX_FRET - capo:
            out.append((s, f))
    return out


def in_range(midi: int, capo: int = 0, tuning=STANDARD) -> int:
    """The pitch moved by octaves into the playable range (unchanged if it is playable)."""
    low, high = min(tuning) + capo, max(tuning) + MAX_FRET
    while midi < low:
        midi += 12
    while midi > high:
        midi -= 12
    return midi


def _position(a: tuple[Place, ...]) -> float | None:
    fretted = [f for _, f in a if f > 0]
    return sum(fretted) / len(fretted) if fretted else None


def _static(a: tuple[Place, ...], pos: int | None = None) -> float:
    cost = 0.0
    for _, f in a:
        cost += 0.0 if f == 0 else 0.2 + 0.03 * f + 0.3 * max(0, f - 7)   # a fretted note takes a finger
        if pos is not None:                       # {tab_position: N}: the hand around fret N (N … N+4)
            if f == 0:
                cost += 1.2 if pos >= 5 else 0.0      # an open string from a high position
            elif f < pos - 1 or f > pos + 4:
                cost += 2.5 * (pos - 1 - f if f < pos - 1 else f - pos - 4)
    fretted = [f for _, f in a if f > 0]
    if len(fretted) > 1:
        span = max(fretted) - min(fretted)
        cost += 0.1 * span + (4.0 * (span - MAX_STRETCH) if span > MAX_STRETCH else 0)
    return cost


def _move(a: tuple[Place, ...], b: tuple[Place, ...], after_rest: bool, held: bool = False) -> float:
    """Cost of going from `a` to `b`; `held`: a hand position is asked, so moving inside it is cheap
    (leaving it is paid by _static)."""
    pa, pb = _position(a), _position(b)
    cost = 0.05 * abs(a[0][0] - b[0][0])                  # string changes
    if pa is not None and pb is not None:
        d = abs(pa - pb)
        cost += (0.35 * d + (1.5 if d > MAX_STRETCH else 0)) * (0.5 if after_rest else 1) * (0.2 if held else 1)
    return cost


def _options(midis: list[int], capo: int, tuning, wanted=None) -> list[tuple[Place, ...]]:
    """Ways to play notes sounding together: one string each, within a playable stretch.
    `wanted`: for each note None, or the places it is limited to (a string or a string and fret)."""
    per_note = [places(m, capo, tuning) for m in midis]
    for i, w in enumerate(wanted or []):
        if w:
            per_note[i] = [p for p in per_note[i] if p in w] or per_note[i]
    opts = []
    for combo in product(*per_note):
        strings = [s for s, _ in combo]
        if len(set(strings)) != len(strings):
            continue
        fretted = [f for _, f in combo if f > 0]
        if fretted and max(fretted) - min(fretted) > MAX_STRETCH + 2:
            continue
        opts.append(tuple(combo))
    if not opts and per_note:                  # cannot sound together: best effort, a free string where possible
        used, best = set(), []
        for p in per_note:
            pick = next((x for x in p if x[0] not in used), p[0] if p else (0, 0))
            used.add(pick[0])
            best.append(pick)
        opts = [tuple(best)]
    return opts


def fingering(events: list[list[int] | None], capo: int = 0, tuning=STANDARD, wanted=None,
              positions=None) -> list[tuple[Place, ...] | None]:
    """events: the MIDI pitches of each stem in order (None for a rest); returns a (string, fret)
    for every pitch of every stem (None for rests), the cheapest playable path. `wanted[i]`: per note
    of stem i, None or the allowed places; `positions[i]`: the hand position asked for stem i."""
    idx = [i for i, e in enumerate(events) if e]
    out: list[tuple[Place, ...] | None] = [None] * len(events)
    if not idx:
        return out
    wanted = wanted or [None] * len(events)
    positions = positions or [None] * len(events)
    layers = [_options(events[i], capo, tuning, wanted[i]) for i in idx]
    rest_before = [any(events[k] is None for k in range(idx[j - 1] + 1, i)) if j else False
                   for j, i in enumerate(idx)]
    cost = [_static(a, positions[idx[0]]) for a in layers[0]]
    back: list[list[int]] = []
    for j in range(1, len(layers)):
        new, ptr = [], []
        for b in layers[j]:
            best, arg = None, 0
            for k, a in enumerate(layers[j - 1]):
                c = cost[k] + _move(a, b, rest_before[j], positions[idx[j]] is not None)
                if best is None or c < best:
                    best, arg = c, k
            new.append(best + _static(b, positions[idx[j]]))
            ptr.append(arg)
        cost, back = new, back + [ptr]
    k = min(range(len(cost)), key=cost.__getitem__)
    for j in range(len(layers) - 1, -1, -1):
        out[idx[j]] = layers[j][k]
        if j:
            k = back[j - 1][k]
    return out


def assign(bars_notes: list[list], capo: int = 0, tuning=STANDARD) -> list[str]:
    """Set `string` and `fret` on the notes of consecutive notated bars (a list of each bar's notes,
    in order); tied continuations keep the string and fret of the note they continue. A note's
    `tab_string` (1 = highest string) limits it to that string, with `tab_fret` to that place;
    `tab_pos` keeps the hand around that fret. Returns warnings (octave moves, impossible requests)."""
    warnings: list[str] = []
    n_str = len(tuning)

    def label(n) -> str:
        return f"{n.step}{'#' * max(0, n.alter)}{'b' * max(0, -n.alter)}{n.octave}"
    stems: list[list] = []                 # each: the notes on one stem (rest: [rest])
    for notes in bars_notes:
        for n in notes:
            if n.chord and stems and stems[-1][0].step is not None:
                stems[-1].append(n)
            else:
                stems.append([n])
    events: list[list[int] | None] = []
    wanted: list[list | None] = []
    positions: list[int | None] = []
    playable: list[list] = []
    for st in stems:
        heads = [n for n in st if n.step is not None and not n.tie_stop]
        if not heads:
            events.append(None)
            wanted.append(None)
            positions.append(None)
            playable.append([])
            continue
        midis, want = [], []
        for n in heads:
            m = in_range(n.midi, capo, tuning)
            if m != n.midi:
                warnings.append(f"tab: {label(n)} out of the instrument's range, played "
                                f"{'up' if m > n.midi else 'down'} {abs(m - n.midi) // 12} octave(s)")
            midis.append(m)
            w = None
            if n.tab_string:
                if not 1 <= n.tab_string <= n_str:
                    warnings.append(f"tab: string {n.tab_string} for {label(n)}: there are {n_str} strings")
                else:
                    si = n_str - n.tab_string
                    w = [p for p in places(m, capo, tuning) if p[0] == si]
                    if n.tab_fret is not None:
                        w = [p for p in w if p[1] == n.tab_fret - capo] or w
                    if not w:
                        warnings.append(f"tab: {label(n)} cannot be played on string {n.tab_string}: "
                                        "string chosen by the app")
            want.append(w)
        events.append(midis)
        wanted.append(want)
        positions.append(heads[0].tab_pos)
        playable.append(heads)
    result = fingering(events, capo, tuning, wanted, positions)
    for ev, placed in zip(events, result):
        if ev and placed and len({st for st, _ in placed}) < len(placed):
            warnings.append("tab: notes on one stem that a guitar cannot play together (two on one string)")
    last: dict[int, Place] = {}            # pitch → place of the latest note, for ties
    for st, heads, placed in zip(stems, playable, result):
        for n, p in zip(heads, placed or ()):
            n.string, n.fret = p
            last[n.midi] = p
        for n in st:
            if n.step is not None and n.tie_stop:
                n.string, n.fret = last.get(n.midi, (None, None))
    return warnings
