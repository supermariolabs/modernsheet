"""SVG backend (screen-space): useful for previews, the web, and for checking the
conversion used by the Flet backend."""
from __future__ import annotations

from xml.sax.saxutils import escape

from .display import DisplayList
from .screen import screen_ops


def page_svg(dl: DisplayList, page_index: int, metrics, scale: float = 1.0) -> str:
    """One page as an SVG document, from the same screen operations as the Flet backend."""
    W, H = dl.page_size[0] * scale, dl.page_size[1] * scale
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}" height="{H:.1f}" viewBox="0 0 {W:.2f} {H:.2f}">',
           f'<rect width="{W:.2f}" height="{H:.2f}" fill="#ffffff"/>']
    caps = {0: "butt", 1: "round", 2: "square"}
    paint = lambda fill, stroke, w: (f'fill="{fill or "none"}"' + (f' stroke="{stroke}" stroke-width="{w:.2f}"' if stroke else ""))
    for op in screen_ops(dl, page_index, scale, metrics):
        k = op[0]
        if k == "line":
            _, x1, y1, x2, y2, c, w, cap = op
            out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{c}" '
                       f'stroke-width="{w:.2f}" stroke-linecap="{caps.get(cap, "butt")}"/>')
        elif k == "rect":
            _, x, y, w, h, r, fill, stroke, lw = op
            out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{r:.2f}" {paint(fill, stroke, lw)}/>')
        elif k == "circle":
            _, cx, cy, r, fill, stroke, lw = op
            out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" {paint(fill, stroke, lw)}/>')
        elif k == "path":
            _, segs, fill, stroke, lw = op
            d = " ".join(f"{s[0]}{' '.join(f'{v:.2f}' for v in s[1:])}" for s in segs)
            out.append(f'<path d="{d}" {paint(fill, stroke, lw)}/>')
        elif k == "text":
            _, x, top, s, font, size, c, outline, base = op
            face = metrics.faces[font]
            style = f'font-family:\'{face.family}\';font-size:{size:.2f}px'
            style += ";font-weight:bold" if face.bold else ""
            style += ";font-style:italic" if face.italic else ""
            stroke = f' stroke="{c}" stroke-width="{outline:.2f}" stroke-linejoin="round"' if outline else ""
            # anchored like Flutter: top of a 1-em line box + baseline ratio
            y = top + face.baseline_ratio * size
            out.append(f'<text x="{x:.2f}" y="{y:.2f}" fill="{c}"{stroke} style="{style}" xml:space="preserve">{escape(s)}</text>')
    out.append("</svg>")
    return "\n".join(out)
