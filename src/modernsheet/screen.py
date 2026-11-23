"""Screen-space conversion shared by the on-screen backends (Flet, SVG).

Converts a DisplayList page (PDF points, origin bottom-left, text at baseline) into
screen operations (pixels, origin top-left, text boxes anchored at their top-left with
line height = 1 em), scaled by `scale`.
"""
from __future__ import annotations

from .display import DisplayList


def hex_color(rgb) -> str | None:
    if rgb is None:
        return None
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v * 255))) for v in rgb)


def screen_ops(dl: DisplayList, page_index: int, scale: float, metrics):
    """Yield screen operations for one page:
        ("line",   x1, y1, x2, y2, color, width, cap)
        ("rect",   x, y, w, h, radius, fill, stroke, width)          y = top edge
        ("circle", cx, cy, r, fill, stroke, width)
        ("path",   [("M",x,y)|("L",x,y)|("C",x1,y1,x2,y2,x,y)|("Z",)], fill, stroke, width)
        ("text",   x, top, string, font, size, color, outline, baseline)
    """
    H = dl.page_size[1]
    k = scale
    Y = lambda y: (H - y) * k
    for op in dl.pages[page_index]:
        kind = op[0]
        if kind == "line":
            _, x1, y1, x2, y2, rgb, w, cap = op
            yield ("line", x1 * k, Y(y1), x2 * k, Y(y2), hex_color(rgb), w * k, cap)
        elif kind == "rect":
            _, x, y, w, h, r, fill, stroke, lw = op
            yield ("rect", x * k, Y(y + h), w * k, h * k, r * k, hex_color(fill), hex_color(stroke), lw * k)
        elif kind == "circle":
            _, cx, cy, r, fill, stroke, lw = op
            yield ("circle", cx * k, Y(cy), r * k, hex_color(fill), hex_color(stroke), lw * k)
        elif kind == "path":
            _, segs, fill, stroke, lw = op
            out = []
            for s in segs:
                if s[0] in ("M", "L"):
                    out.append((s[0], s[1] * k, Y(s[2])))
                elif s[0] == "C":
                    out.append(("C", s[1] * k, Y(s[2]), s[3] * k, Y(s[4]), s[5] * k, Y(s[6])))
                else:
                    out.append(("Z",))
            yield ("path", out, hex_color(fill), hex_color(stroke), lw * k)
        elif kind == "text":
            _, x, y, s, font, size, rgb, outline = op
            ratio = metrics.faces[font].baseline_ratio
            base = Y(y)
            yield ("text", x * k, base - ratio * size * k, s, font, size * k, hex_color(rgb), outline * k, base)
