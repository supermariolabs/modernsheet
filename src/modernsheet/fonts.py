"""Font registry and text metrics (pure Python, via fontTools).

The layout layer measures text here, so it does not depend on reportlab: the same
metrics drive the PDF backend and the on-screen (Flet) backend.
"""
from __future__ import annotations

import sys
from pathlib import Path

FONT_FILES = {
    # clean theme
    "Sym": "FreeSerif.ttf",
    "Sans": "DejaVuSans.ttf",
    "SansB": "DejaVuSans-Bold.ttf",
    "SansI": "DejaVuSans-Oblique.ttf",
    # realbook theme (Petaluma by Steinberg, SIL OFL)
    "Petaluma": "Petaluma.ttf",          # SMuFL music glyphs, handwritten
    "PScript": "PetalumaScript.ttf",     # handwritten text / chord symbols
}

_HERE = Path(__file__).resolve().parent
FONT_DIRS = [
    _HERE.parent / "assets" / "fonts",       # src/assets/fonts (shared with the Flet app)
    _HERE / "fonts",
    Path("/usr/share/fonts/truetype/freefont"),
    Path("/usr/share/fonts/truetype/dejavu"),
    Path.home() / "Library/Fonts",
    Path("/Library/Fonts"),
    Path("C:/Windows/Fonts"),
]


def fonts_for_theme(theme: str) -> set[str]:
    return {"Sans", "SansB", "Sym", "Petaluma"} | ({"SansI"} if theme == "clean" else {"PScript"})


class _Face:
    """Just what the layout needs from a font: character coverage, advances, ascent/descent."""

    def __init__(self, path: Path):
        from fontTools.ttLib import TTFont
        f = TTFont(str(path), lazy=True)
        self.path = path
        self.upm = f["head"].unitsPerEm
        cmap = f.getBestCmap()
        hmtx = f["hmtx"]
        scale = 1000.0 / self.upm
        # widths in 1/1000 em, rounded like reportlab does: PDF output stays identical
        self.charToGlyph = cmap
        self.widths = {cp: int(round(hmtx[g][0] * scale)) for cp, g in cmap.items()}
        notdef = f.getGlyphOrder()[0]
        self.missing_width = int(round(hmtx[notdef][0] * scale))
        hhea = f["hhea"]
        self.ascent = hhea.ascent / self.upm
        self.descent = hhea.descent / self.upm      # negative
        os2 = f["OS/2"] if "OS/2" in f else None
        if os2 is not None and os2.fsSelection & (1 << 7):    # USE_TYPO_METRICS
            asc, desc = os2.sTypoAscender, os2.sTypoDescender
        else:
            asc, desc = hhea.ascent, hhea.descent
        # where the baseline falls inside a line box of height 1 em (Flutter, height=1.0)
        self.baseline_ratio = asc / (asc - desc)
        self.family = f["name"].getDebugName(1)
        sub = (f["name"].getDebugName(2) or "").lower()
        self.bold = "bold" in sub
        self.italic = "italic" in sub or "oblique" in sub
        f.close()


class _FontRef:
    def __init__(self, face: _Face):
        self.face = face


class FontRegistry:
    """name → font file; string widths in points."""

    def __init__(self):
        self.faces: dict[str, _Face] = {}

    def load(self, names) -> "FontRegistry":
        for name in names:
            if name in self.faces:
                continue
            file = FONT_FILES[name]
            path = next((d / file for d in FONT_DIRS if (d / file).exists()), None)
            if path is None:
                sys.exit(f"Font {file} not found. Put it in {FONT_DIRS[0]} (see SPEC.md §7).")
            self.faces[name] = _Face(path)
        return self

    def paths(self) -> dict[str, str]:
        return {n: str(f.path) for n, f in self.faces.items()}

    # reportlab-compatible API used by the layout code
    def getFont(self, name: str) -> _FontRef:
        return _FontRef(self.faces[name])

    def stringWidth(self, text: str, name: str, size: float) -> float:
        face = self.faces[name]
        w = face.widths
        return sum(w.get(ord(ch), face.missing_width) for ch in text) * size * 0.001

    def ascent(self, name: str) -> float:
        return self.faces[name].ascent

    def descent(self, name: str) -> float:
        return self.faces[name].descent


_REGISTRY: FontRegistry | None = None


def registry(theme: str = "realbook") -> FontRegistry:
    """Shared registry with the fonts of a theme loaded."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = FontRegistry()
    return _REGISTRY.load(fonts_for_theme(theme))
