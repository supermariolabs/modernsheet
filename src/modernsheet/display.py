"""Display list: the output of the layout layer.

A DisplayList is a list of pages; each page is a list of drawing operations in PDF
coordinates (points, origin bottom-left). Backends (pdf.py, flet_view.py, svg.py)
only replay these operations, so every backend shows exactly the same layout.

Operations (tuples, first item is the kind):
    ("line",   x1, y1, x2, y2, stroke_rgb, width, cap)          cap: 0 butt, 1 round, 2 square
    ("rect",   x, y, w, h, radius, fill_rgb|None, stroke_rgb|None, width)
    ("circle", cx, cy, r, fill_rgb|None, stroke_rgb|None, width)
    ("path",   [("M",x,y) | ("L",x,y) | ("C",x1,y1,x2,y2,x,y) | ("Z",)],
               fill_rgb|None, stroke_rgb|None, width)
    ("text",   x, y, string, font, size, fill_rgb, outline_width)   y = baseline;
               outline_width > 0 → also stroke the glyph outline (faux bold)

`Surface` records these operations behind the small subset of the reportlab canvas API
that the layout code uses, so the layout reads like ordinary drawing code.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DisplayList:
    page_size: tuple[float, float]
    pages: list[list[tuple]] = field(default_factory=list)
    title: str = ""
    author: str = ""
    fonts: dict[str, str] = field(default_factory=dict)       # font name → file path
    warnings: list[str] = field(default_factory=list)


class _Path:
    def __init__(self):
        self.ops: list[tuple] = []

    def moveTo(self, x, y):
        self.ops.append(("M", x, y))

    def lineTo(self, x, y):
        self.ops.append(("L", x, y))

    def curveTo(self, x1, y1, x2, y2, x, y):
        self.ops.append(("C", x1, y1, x2, y2, x, y))

    def close(self):
        self.ops.append(("Z",))


class _TextObject:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.font, self.size = None, None
        self.mode = 0
        self.chunks: list[str] = []

    def setFont(self, name, size):
        self.font, self.size = name, size

    def setTextRenderMode(self, mode):
        self.mode = mode

    def textOut(self, s):
        self.chunks.append(s)


class Surface:
    """Records drawing operations (reportlab-canvas-like API)."""

    def __init__(self, page_size, metrics):
        self.metrics = metrics
        self.dl = DisplayList(page_size=page_size, pages=[[]])
        self._state = dict(fill=(0, 0, 0), stroke=(0, 0, 0), width=1.0, cap=0, join=0, font=None, size=10)
        self._stack: list[dict] = []

    # -- state
    def saveState(self):
        self._stack.append(dict(self._state))

    def restoreState(self):
        self._state = self._stack.pop()

    def setFillColorRGB(self, r, g, b):
        self._state["fill"] = (r, g, b)

    def setStrokeColorRGB(self, r, g, b):
        self._state["stroke"] = (r, g, b)

    def setLineWidth(self, w):
        self._state["width"] = w

    def setLineCap(self, cap):
        self._state["cap"] = cap

    def setLineJoin(self, join):
        self._state["join"] = join

    def setFont(self, name, size):
        self._state["font"], self._state["size"] = name, size

    def setTitle(self, t):
        self.dl.title = t

    def setAuthor(self, a):
        self.dl.author = a

    # -- pages
    def _add(self, op):
        self.dl.pages[-1].append(op)

    def showPage(self):
        self.dl.pages.append([])

    def save(self):
        if self.dl.pages and not self.dl.pages[-1] and len(self.dl.pages) > 1:
            self.dl.pages.pop()

    # -- shapes
    def line(self, x1, y1, x2, y2):
        s = self._state
        self._add(("line", x1, y1, x2, y2, s["stroke"], s["width"], s["cap"]))

    def rect(self, x, y, w, h, stroke=1, fill=0):
        self.roundRect(x, y, w, h, 0, stroke=stroke, fill=fill)

    def roundRect(self, x, y, w, h, radius, stroke=1, fill=0):
        s = self._state
        self._add(("rect", x, y, w, h, radius, s["fill"] if fill else None, s["stroke"] if stroke else None, s["width"]))

    def circle(self, cx, cy, r, stroke=1, fill=0):
        s = self._state
        self._add(("circle", cx, cy, r, s["fill"] if fill else None, s["stroke"] if stroke else None, s["width"]))

    def beginPath(self):
        return _Path()

    def drawPath(self, path, stroke=1, fill=0):
        s = self._state
        self._add(("path", list(path.ops), s["fill"] if fill else None, s["stroke"] if stroke else None, s["width"]))

    # -- text
    def drawString(self, x, y, text):
        s = self._state
        self._add(("text", x, y, text, s["font"], s["size"], s["fill"], 0.0))

    def drawCentredString(self, x, y, text):
        s = self._state
        self.drawString(x - self.metrics.stringWidth(text, s["font"], s["size"]) / 2, y, text)

    def drawRightString(self, x, y, text):
        s = self._state
        self.drawString(x - self.metrics.stringWidth(text, s["font"], s["size"]), y, text)

    def beginText(self, x, y):
        return _TextObject(x, y)

    def drawText(self, t: _TextObject):
        s = self._state
        outline = s["width"] if t.mode == 2 else 0.0
        self._add(("text", t.x, t.y, "".join(t.chunks), t.font, t.size, s["fill"], outline))
