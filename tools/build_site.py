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
Static files (images, CSS) live in docs/assets/ and are not touched. docs/ also gets CNAME,
.nojekyll (plain HTML, no Jekyll), a language-detecting /index.html, 404.html and sitemap.xml.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site"
OUT = ROOT / "docs"
DOMAIN = "modernsheet.app"
REPO = "https://github.com/supermariolabs/modernsheet"
LANGS = {"it": "Italiano", "en": "English"}
UI = {
    "it": {"repo": "Codice su GitHub", "lang": "English", "menu": "Menu", "license": "Software libero, licenza GPL-3.0",
           "privacy": "Privacy", "skip": "Vai al contenuto", "beta": "Software in versione beta: può contenere errori", "notfound": "Pagina non trovata", "home": "Torna alla home"},
    "en": {"repo": "Code on GitHub", "lang": "Italiano", "menu": "Menu", "license": "Free software, GPL-3.0 license",
           "privacy": "Privacy", "skip": "Skip to content", "beta": "Beta software: it may contain bugs", "notfound": "Page not found", "home": "Back to home"},
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


def url(lang: str, slug: str) -> str:
    return f"/{lang}/{slug}/" if slug else f"/{lang}/"


def render(template: str, lang: str, meta: dict, body: str, nav: list[tuple[str, str, int]]) -> str:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "md_in_html", "toc", "sane_lists"],
                           extension_configs={"toc": {"permalink": "#", "permalink_title": "", "toc_depth": "2-3"}})
    content = md.convert(body.replace("{{repo}}", REPO))
    # "\|" keeps a pipe from splitting a table cell; inside <code> Markdown leaves the backslash: drop it
    content = re.sub(r"<code>(.*?)</code>", lambda m: "<code>" + m.group(1).replace("\\|", "|") + "</code>", content)
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
