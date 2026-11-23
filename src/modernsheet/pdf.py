"""PDF backend: replays a DisplayList on a reportlab canvas."""
from __future__ import annotations

import io

from .display import DisplayList


def write_pdf(dl: DisplayList, target) -> None:
    """target: file path or binary file-like object."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    for name, path in dl.fonts.items():
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, path))
    c = canvas.Canvas(target, pagesize=dl.page_size)
    c.setTitle(dl.title)
    c.setAuthor(dl.author)
    for i, page in enumerate(dl.pages):
        if i:
            c.showPage()
        for op in page:
            _replay(c, op)
    c.save()


def pdf_bytes(dl: DisplayList) -> bytes:
    buf = io.BytesIO()
    write_pdf(dl, buf)
    return buf.getvalue()


def _replay(c, op):
    kind = op[0]
    if kind == "line":
        _, x1, y1, x2, y2, rgb, w, cap = op
        c.setStrokeColorRGB(*rgb)
        c.setLineWidth(w)
        c.setLineCap(cap)
        c.line(x1, y1, x2, y2)
        c.setLineCap(0)
    elif kind == "rect":
        _, x, y, w, h, r, fill, stroke, lw = op
        _paint(c, fill, stroke, lw)
        if r:
            c.roundRect(x, y, w, h, r, stroke=int(stroke is not None), fill=int(fill is not None))
        else:
            c.rect(x, y, w, h, stroke=int(stroke is not None), fill=int(fill is not None))
    elif kind == "circle":
        _, cx, cy, r, fill, stroke, lw = op
        _paint(c, fill, stroke, lw)
        c.circle(cx, cy, r, stroke=int(stroke is not None), fill=int(fill is not None))
    elif kind == "path":
        _, segs, fill, stroke, lw = op
        _paint(c, fill, stroke, lw)
        p = c.beginPath()
        for s in segs:
            if s[0] == "M":
                p.moveTo(s[1], s[2])
            elif s[0] == "L":
                p.lineTo(s[1], s[2])
            elif s[0] == "C":
                p.curveTo(*s[1:])
            else:
                p.close()
        c.drawPath(p, stroke=int(stroke is not None), fill=int(fill is not None))
    elif kind == "text":
        _, x, y, s, font, size, rgb, outline = op
        c.setFillColorRGB(*rgb)
        if outline:
            c.saveState()
            c.setStrokeColorRGB(*rgb)
            c.setLineWidth(outline)
            c.setLineJoin(1)
            t = c.beginText(x, y)
            t.setFont(font, size)
            t.setTextRenderMode(2)
            t.textOut(s)
            c.drawText(t)
            c.restoreState()
        else:
            c.setFont(font, size)
            c.drawString(x, y, s)


def _paint(c, fill, stroke, lw):
    if fill is not None:
        c.setFillColorRGB(*fill)
    if stroke is not None:
        c.setStrokeColorRGB(*stroke)
    c.setLineWidth(lw)
