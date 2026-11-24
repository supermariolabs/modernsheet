"""Flet backend: turns a DisplayList page into flet.canvas shapes.

Fonts must be registered in the Flet app under the same names used by the engine
(see FLET_FONTS and the app's page.fonts), so each text run uses exactly the font the
layout measured.
"""
from __future__ import annotations

from .display import DisplayList
from .fonts import FONT_FILES
from .screen import screen_ops

FLET_FONTS = {name: f"fonts/{file}" for name, file in FONT_FILES.items()}   # relative to the app's assets dir


def page_shapes(dl: DisplayList, page_index: int, metrics, scale: float = 1.0) -> list:
    """Canvas shapes for one page at `scale` pixels per point (screen_ops does the conversion).
    Filled and stroked shapes are two shapes, as Flet paints have one style each; flet is imported
    here so the engine stays importable without it (CLI, tests)."""
    import flet as ft
    import flet.canvas as cv

    caps = {0: ft.StrokeCap.BUTT, 1: ft.StrokeCap.ROUND, 2: ft.StrokeCap.SQUARE}

    def fill_paint(color):
        return ft.Paint(color=color, style=ft.PaintingStyle.FILL, anti_alias=True)

    def stroke_paint(color, width, cap=0):
        return ft.Paint(color=color, style=ft.PaintingStyle.STROKE, stroke_width=max(width, 0.01),
                        stroke_cap=caps.get(cap, ft.StrokeCap.BUTT), anti_alias=True)

    shapes = []
    for op in screen_ops(dl, page_index, scale, metrics):
        k = op[0]
        if k == "line":
            _, x1, y1, x2, y2, c, w, cap = op
            shapes.append(cv.Line(x1, y1, x2, y2, paint=stroke_paint(c, w, cap)))
        elif k == "rect":
            _, x, y, w, h, r, fill, stroke, lw = op
            if fill:
                shapes.append(cv.Rect(x, y, w, h, border_radius=r, paint=fill_paint(fill)))
            if stroke:
                shapes.append(cv.Rect(x, y, w, h, border_radius=r, paint=stroke_paint(stroke, lw)))
        elif k == "circle":
            _, cx, cy, r, fill, stroke, lw = op
            if fill:
                shapes.append(cv.Circle(cx, cy, r, paint=fill_paint(fill)))
            if stroke:
                shapes.append(cv.Circle(cx, cy, r, paint=stroke_paint(stroke, lw)))
        elif k == "path":
            _, segs, fill, stroke, lw = op
            els = []
            for s in segs:
                if s[0] == "M":
                    els.append(cv.Path.MoveTo(s[1], s[2]))
                elif s[0] == "L":
                    els.append(cv.Path.LineTo(s[1], s[2]))
                elif s[0] == "C":
                    els.append(cv.Path.CubicTo(*s[1:]))
                else:
                    els.append(cv.Path.Close())
            if fill:
                shapes.append(cv.Path(elements=els, paint=fill_paint(fill)))
            if stroke:
                shapes.append(cv.Path(elements=list(els), paint=stroke_paint(stroke, lw)))
        elif k == "text":
            _, x, top, s, font, size, c, outline, _base = op
            style = ft.TextStyle(font_family=font, size=size, height=1.0, color=c)
            shapes.append(cv.Text(x, top, s, style=style, alignment=ft.Alignment.TOP_LEFT))
            if outline:                               # faux bold: stroke the outline on top
                ostyle = ft.TextStyle(font_family=font, size=size, height=1.0,
                                      foreground=ft.Paint(color=c, style=ft.PaintingStyle.STROKE,
                                                          stroke_width=outline, stroke_join=ft.StrokeJoin.ROUND))
                shapes.append(cv.Text(x, top, s, style=ostyle, alignment=ft.Alignment.TOP_LEFT))
    return shapes
