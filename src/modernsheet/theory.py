"""Music theory: keys, signatures, transposition, chord spelling."""
from __future__ import annotations

import re

# =============================================================================
# Music theory
# =============================================================================

SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
NEUTRAL_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]  # for C / Am

PITCH = {n: i for i, n in enumerate(SHARP_NAMES)}
PITCH.update({n: i for i, n in enumerate(FLAT_NAMES)})
PITCH.update({"Cb": 11, "Fb": 4, "E#": 5, "B#": 0})

# number of sharps (+) or flats (-) for each major key
MAJOR_SIG = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
             "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6, "Cb": -7}

# staff positions (half-spaces above the bottom line, treble clef)
SHARP_STEPS = [8, 5, 9, 6, 3, 7, 4]   # F C G D A E B
FLAT_STEPS = [4, 7, 3, 6, 2, 5, 1]    # B E A D G C F

CHORD_RE = re.compile(r"^([A-G][#b]?)(.*?)(?:/([A-G][#b]?))?$")
KEY_RE = re.compile(r"^([A-G][#b]?)(m?)$")


def parse_key(key: str) -> tuple[int, bool]:
    m = KEY_RE.match(key.strip())
    if not m or m.group(1) not in PITCH:
        raise ValueError(f"invalid key '{key}'")
    return PITCH[m.group(1)], m.group(2) == "m"


def _major_name(major_pc: int, prefer_sharps: bool | None) -> str:
    names = [n for n in MAJOR_SIG if PITCH[n] == major_pc]
    if prefer_sharps is not None and len(names) > 1:
        names.sort(key=lambda n: (MAJOR_SIG[n] > 0) != prefer_sharps)
        return names[0]
    return min(names, key=lambda n: (abs(MAJOR_SIG[n]), MAJOR_SIG[n] > 0))


def key_signature(key: str) -> int:
    """+n sharps / -n flats for a major or minor key name (e.g. 'Bb', 'F#m')."""
    pc, minor = parse_key(key)
    root = key.strip().rstrip("m")
    if not minor and root in MAJOR_SIG:
        return MAJOR_SIG[root]
    prefer = True if "#" in root else False if "b" in root else None
    return MAJOR_SIG[_major_name((pc + 3) % 12 if minor else pc, prefer)]


def transpose_key(key: str, semis: int) -> str:
    if semis % 12 == 0:
        return key
    pc, minor = parse_key(key)
    new_pc = (pc + semis) % 12
    major = _major_name((new_pc + 3) % 12 if minor else new_pc, None)
    return spelling_for(major)[new_pc] + "m" if minor else major


def spelling_for(key: str) -> list[str]:
    sig = key_signature(key)
    return FLAT_NAMES if sig < 0 else SHARP_NAMES if sig > 0 else NEUTRAL_NAMES


def transpose_chord(chord: str | None, semis: int, key: str) -> str | None:
    if not chord or chord == "/" or semis % 12 == 0:
        return chord
    m = CHORD_RE.match(chord)
    if not m:
        return chord
    root, quality, bass = m.groups()
    names = spelling_for(key)
    out = names[(PITCH[root] + semis) % 12] + quality
    if bass:
        out += "/" + names[(PITCH[bass] + semis) % 12]
    return out


def semitones_between(from_key: str, to_key: str) -> int:
    d = (parse_key(to_key)[0] - parse_key(from_key)[0]) % 12
    return d - 12 if d > 6 else d


# Equivalent spellings of a chord quality (SPEC §2.4, §9b point 7): written freely in the file, shown in
# one way. Only the start of the quality is rewritten; what follows (7, 9, add9, sus4, #11…) stays.
_QUALITY_FORMS = [
    (r"^(?:ø7?|m7b5|-7b5|min7b5|mi7b5)", "m7b5"),    # half-diminished
    (r"^Δ(?=\d)", "maj"), (r"^Δ", "maj7"),          # Δ alone is a major seventh
    (r"^(?:maj|Maj|MAJ|ma(?=\d)|Ma(?=\d))", "maj"),     # ma7 = maj7, but madd9 is m + add9
    (r"^M(?=\d)", "maj"), (r"^M$", ""),              # CM7 = Cmaj7, CM = C
    (r"^(?:°|o(?=\d|$)|dim)", "dim"),
    (r"^(?:\+|aug)", "aug"),
    (r"^(?:min|mi|-)", "m"),                          # minor
]


def normalize_quality(quality: str) -> str:
    """The standard spelling of a chord quality: Maj7/M7/ma7/Δ → maj7, -/min/mi → m, ø → m7b5,
    °/o → dim, + → aug (the rest of the quality is kept as written)."""
    for pat, rep in _QUALITY_FORMS:
        new = re.sub(pat, rep, quality)
        if new != quality:
            return new
    return quality


# Italian (solfège) note names, a display option (note_names = italian): the source keeps the letters.
ITALIAN_NAMES = {"C": "Do", "D": "Re", "E": "Mi", "F": "Fa", "G": "Sol", "A": "La", "B": "Si"}


def note_name(letter: str, names: str = "letters") -> str:
    """The name of a note letter (A-G) in the chosen naming: C → C (letters) or Do (italian)."""
    return ITALIAN_NAMES.get(letter, letter) if names == "italian" else letter


def pretty_chord(text: str) -> str:
    """Typographic accidentals: Bb7b9 -> B♭7♭9, F#m -> F♯m."""
    text = re.sub(r"(?<=[A-G])b", "♭", text)
    text = re.sub(r"b(?=\d)", "♭", text)
    return text.replace("#", "♯")

