"""Build the website (modernsheet.app, GitHub Pages) from site/ into docs/.

    python tools/build_site.py

Sources: site/<lang>/<page>.md (lang = it, en) with a small header:

    ---
    title: Guida all'app
    slug: guida            # URL: /<lang>/<slug>/ ("" for the home page)
    nav: 2                 # position in the menu (omit to leave the page out of it)
    other: guide           # slug of the same page in the other language
    ---

Markdown (Python-Markdown: tables, fenced code, attributes, md_in_html) goes into site/template.html.

Rendered examples: a fenced block marked `{ .chs .render }` (optionally `bar_width=fit`) is a .chs
snippet that is also drawn by the engine itself (parse → layout → SVG) and shown next to the code, so the
picture can never disagree with the text. A snippet without sections is wrapped in an unlabeled section,
and one without {title} gets a hidden {key: C} {time: 4/4} header, as the fragment of a song it is; one
with {title} keeps its header. Snippets must read without warnings (the build stops otherwise). The SVG
is inlined and uses the app's own fonts, copied to docs/assets/fonts/ and declared in
docs/assets/style.css. Static files (images, CSS) live in docs/assets/ and are not touched. docs/ also
gets CNAME, .nojekyll (plain HTML, no Jekyll), a language-detecting /index.html, 404.html and
sitemap.xml.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from modernsheet import parse  # noqa: E402
from modernsheet.fonts import FONT_FILES, registry  # noqa: E402
from modernsheet.display import Surface  # noqa: E402
from modernsheet.layout import Layout  # noqa: E402
from modernsheet.screen import screen_ops  # noqa: E402
from modernsheet.svg import page_svg  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site"
OUT = ROOT / "docs"
DOMAIN = "modernsheet.app"
REPO = "https://github.com/supermariolabs/modernsheet"
LANGS = {"it": "Italiano", "en": "English"}
UI = {
    "it": {"repo": "Codice su GitHub", "lang": "English", "menu": "Menu", "license": "Software libero, licenza GPL-3.0",
           "privacy": "Privacy", "skip": "Vai al contenuto", "beta": "Software in versione beta: può contenere errori", "notfound": "Pagina non trovata", "home": "Torna alla home",
           "render": "Lo spartito disegnato da Modern Sheet per questo esempio"},
    "en": {"repo": "Code on GitHub", "lang": "Italiano", "menu": "Menu", "license": "Free software, GPL-3.0 license",
           "privacy": "Privacy", "skip": "Skip to content", "beta": "Beta software: it may contain bugs", "notfound": "Page not found", "home": "Back to home",
           "render": "The sheet Modern Sheet draws for this example"},
}


def read_page(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit(f"{path}: missing header")
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = re.sub(r"\s+#.*$", "", v).strip()
    return meta, text[m.end():]


# ---- rendered .chs examples
SNIPPET_LABEL = "\u2063"                 # label of the section wrapped around a bare snippet: not drawn
RENDER_RE = re.compile(r'<pre class="render"><code class="language-chs"(?: bar_width="(\w+)")?>(.*?)</code></pre>', re.S)
FONT_DIR = Path(__file__).resolve().parents[1] / "src" / "assets" / "fonts"
WEB_FONTS = {"Petaluma", "PScript", "Sans", "SansB", "Sym"}   # faces of the realbook theme
CSS_FAMILY = "ms-"                     # prefix: never confused with a font installed on the reader's computer
SNIPPET_PAGE_W = 440                   # points: narrower than A4, so the sheet stays legible next to the code
SNIPPET_SCALE = 1.08                   # pixels per point: one scale for every example (the column is ~400 px)


class SnippetLayout(Layout):
    """The engine's layout, minus what belongs to a page and not to a snippet: no footer, no page
    header unless the snippet has a {title}, no box for the section wrapped around a bare snippet.
    The page is narrower than A4 (SNIPPET_PAGE_W): shown at half the column width, a whole A4 row
    would be too small to read; rows are shorter, everything else is the engine's own layout."""

    def __init__(self, song, **opts):
        super().__init__(song, **opts)
        self.page_w = SNIPPET_PAGE_W
        self.c = Surface((self.page_w, self.page_h), self.metrics)

    def header(self):
        if "title" in self.song.meta:
            super().header()

    def footer(self):
        pass

    def section_header(self, sec):
        if sec.label != SNIPPET_LABEL:
            super().section_header(sec)


def snippet_svg(code: str, where: str, bar_width: str = "uniform") -> str:
    """The snippet drawn by the engine, as an inline SVG cropped to what is drawn. `bar_width`: the
    block's `bar_width=fit` attribute, for snippets whose bars of notes would leave half-empty rows
    on the narrow page with the uniform grid."""
    src = code if "{start_of_" in code else f"{{start_of_verse: {SNIPPET_LABEL}}}\n{code.rstrip()}\n{{end_of_verse}}\n"
    if "{title" not in code:
        # a fragment of a song: give it the header a real song has, or its first {key} / {time} would be
        # read as the song's key / time instead of a change (that happens only in a song without header)
        src = "{key: C}\n{time: 4/4}\n" + src
    song = parse(src)
    if song.warnings:
        sys.exit(f"{where}: rendered snippet with warnings: {song.warnings}")
    metrics = registry("realbook")
    dl = SnippetLayout(song, theme="realbook", bar_width=bar_width).run()
    if len(dl.pages) != 1:
        sys.exit(f"{where}: a rendered snippet must fit on one page")
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for op in screen_ops(dl, 0, 1.0, metrics):           # bounding box of everything drawn
        k = op[0]
        if k == "line":
            xs, ys = (op[1], op[3]), (op[2], op[4])
        elif k == "rect":
            xs, ys = (op[1], op[1] + op[3]), (op[2], op[2] + op[4])
        elif k == "circle":
            xs, ys = (op[1] - op[3], op[1] + op[3]), (op[2] - op[3], op[2] + op[3])
        elif k == "path":
            pts = [v for seg in op[1] for v in seg[1:]]
            xs, ys = pts[0::2] or [x0], pts[1::2] or [y0]
        else:                                               # text: its 1-em line box
            w = metrics.stringWidth(op[3], op[4], op[5]) if op[3] else 0
            xs, ys = (op[1], op[1] + w), (op[2], op[2] + op[5])
        x0, x1, y0, y1 = min(x0, *xs), max(x1, *xs), min(y0, *ys), max(y1, *ys)
    pad = 8
    x0, y0, w, h = x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    svg = page_svg(dl, 0, metrics)
    svg = re.sub(r'<svg [^>]*>', f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" '
                                 f'width="{w * SNIPPET_SCALE:.0f}" height="{h * SNIPPET_SCALE:.0f}" role="img">', svg, count=1)
    svg = re.sub(r'<rect width="[^"]*" height="[^"]*" fill="#ffffff"/>\n', "", svg, count=1)
    for face in metrics.faces.values():                    # the app's fonts, under their web names
        svg = svg.replace(f"font-family:'{face.family}'", f"font-family:'{CSS_FAMILY}{face.family}'")
    return svg


def render_snippets(content: str, where: str, caption: str) -> str:
    def one(m: re.Match) -> str:
        code = html.unescape(m.group(2))
        svg = snippet_svg(code, where, m.group(1) or "uniform")
        return (f'<div class="example"><pre><code class="language-chs">{m.group(2)}</code></pre>'
                f'<figure class="render" aria-label="{html.escape(caption)}">{svg}</figure></div>')
    return RENDER_RE.sub(one, content)


def copy_fonts() -> None:
    """The fonts the rendered examples use, next to the site's assets (SIL OFL / free licenses)."""
    dest = OUT / "assets" / "fonts"
    dest.mkdir(parents=True, exist_ok=True)
    for key in WEB_FONTS:
        src = FONT_DIR / FONT_FILES[key]
        if not (dest / src.name).exists() or (dest / src.name).read_bytes() != src.read_bytes():
            (dest / src.name).write_bytes(src.read_bytes())
    for lic in FONT_DIR.glob("LICENSE-*"):
        (dest / lic.name).write_bytes(lic.read_bytes())


def url(lang: str, slug: str) -> str:
    return f"/{lang}/{slug}/" if slug else f"/{lang}/"


def render(template: str, lang: str, meta: dict, body: str, nav: list[tuple[str, str, int]]) -> str:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "md_in_html", "toc", "sane_lists"],
                           extension_configs={"toc": {"permalink": "#", "permalink_title": "", "toc_depth": "2-3"}})
    content = md.convert(body.replace("{{repo}}", REPO))
    # "\|" keeps a pipe from splitting a table cell; inside <code> Markdown leaves the backslash: drop it
    content = re.sub(r"<code>(.*?)</code>", lambda m: "<code>" + m.group(1).replace("\\|", "|") + "</code>", content)
    content = render_snippets(content, f"{lang}/{meta.get('slug', '')}", UI[lang]["render"])
    slug = meta.get("slug", "")
    other = "en" if lang == "it" else "it"
    menu = "".join(
        '<a href="{}"{}>{}</a>'.format(url(lang, s), ' aria-current="page"' if s == slug else "", html.escape(t))
        for t, s, _ in nav)
    values = {
        "lang": lang, "title": html.escape(meta["title"]),
        "full_title": html.escape(meta["title"] if meta["title"] == "Modern Sheet" else f"{meta['title']} · Modern Sheet"), "description": html.escape(meta.get("description", "")),
        "content": content, "menu": menu, "home": url(lang, ""), "repo": REPO,
        "other_url": url(other, meta.get("other", slug)), "other_lang": other, "ui_lang": UI[lang]["lang"],
        "ui_repo": UI[lang]["repo"], "ui_license": UI[lang]["license"], "ui_menu": UI[lang]["menu"],
        "ui_skip": UI[lang]["skip"], "ui_beta": UI[lang]["beta"], "privacy": url(lang, "privacy"), "ui_privacy": UI[lang]["privacy"],
        "canonical": f"https://{DOMAIN}{url(lang, slug)}", "page_class": "home" if not slug else "doc",
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(values[m.group(1)]), template)


def main() -> None:
    template = (SRC / "template.html").read_text(encoding="utf-8")
    copy_fonts()
    urls = []
    for lang in LANGS:
        pages = [(p, *read_page(p)) for p in sorted((SRC / lang).glob("*.md"))]
        nav = sorted(((m["title"] if m.get("slug") else "Home", m.get("slug", ""), int(m["nav"]))
                      for _, m, _ in pages if m.get("nav")), key=lambda x: x[2])
        for path, meta, body in pages:
            dest = OUT / lang / meta.get("slug", "") / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(render(template, lang, meta, body, nav), encoding="utf-8")
            urls.append(f"https://{DOMAIN}{url(lang, meta.get('slug', ''))}")
            print(dest.relative_to(ROOT))
    # the root: Italian or English from the browser's language (links work without JavaScript too)
    (OUT / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Modern Sheet</title>'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<link rel="icon" href="/assets/img/favicon.png">'
        '<script>location.replace((navigator.language||"").toLowerCase().startsWith("it")?"/it/":"/en/")</script>'
        '</head><body><p><a href="/it/">Italiano</a> · <a href="/en/">English</a></p></body></html>\n',
        encoding="utf-8")
    nf = template
    (OUT / "404.html").write_text(render(nf, "en", {"title": "404", "slug": "404"},
                                         f"# 404\n\n{UI['en']['notfound']} · {UI['it']['notfound']}.\n\n"
                                         f"[English](/en/) · [Italiano](/it/)\n", []), encoding="utf-8")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: https://{DOMAIN}/sitemap.xml\n")
    (OUT / "CNAME").write_text(DOMAIN + "\n")
    (OUT / ".nojekyll").write_text("")


if __name__ == "__main__":
    main()
