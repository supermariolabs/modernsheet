"""Import from a chordsheet.com account: log in, list the user's chord sheets, read their sources.

chordsheet.com has no API: this reads the same pages a browser does (standard library only, so it
also works on iPad and Android). The password is used for the login and never stored; the session
cookies live in memory only. Sources are read one at a time with a short pause, to be gentle with
the site. The conversion itself is chordsheet_com.convert (SPEC §9).
"""
from __future__ import annotations

import html
import http.cookiejar
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from ..formats import parse
from .chordsheet_com import convert

BASE = "https://www.chordsheet.com"
USER_AGENT = "ModernSheet/1.0 (chordsheet.com import)"
PAUSE = 0.25                         # seconds between two song pages


class LoginFailed(Exception):
    """Wrong email or password (the site shows the login form again)."""


class SiteError(Exception):
    """The site could not be reached or answered something unexpected."""


@dataclass
class RemoteSong:
    id: str
    slug: str
    title: str
    artist: str = ""

    @property
    def url(self) -> str:
        return f"/song/{self.id}/{self.slug}"


@dataclass
class Fetched:
    song: RemoteSong
    source: str                      # the chord sheet's source text ("" for an empty sheet)


@dataclass
class Converted:
    text: str                        # the .chs file
    problems: list[str]              # conversion notes and parser warnings ("empty" for an empty sheet)


def _text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def parse_song_list(page: str) -> list[RemoteSong]:
    """The user's songs from "My Chord Sheets" (/song/): one card per song, with the title in an <h4>,
    the artist in an <h6> ("-" if none) and links to /song/<id>/<slug>. Without that markup, the
    links alone (title from the link's title attribute or the slug)."""
    songs: dict[str, RemoteSong] = {}
    for card in re.split(r'<div class="card[ "]', page)[1:]:
        m = re.search(r'href="/song/(?:png/)?(\d+)/([^"/.?#]+)"', card)
        if not m:
            continue
        sid, slug = m.groups()
        h4 = re.search(r"<h4[^>]*>(.*?)</h4>", card, re.S)
        h6 = re.search(r"<h6[^>]*>(.*?)</h6>", card, re.S)
        title = _text(h4.group(1)) if h4 else ""
        artist = _text(h6.group(1)) if h6 else ""
        songs.setdefault(sid, RemoteSong(sid, slug, title or slug.replace("-", " "), "" if artist == "-" else artist))
    if not songs:
        for m in re.finditer(r'<a [^>]*href="/song/(\d+)/([^"/.?#]+)"[^>]*>', page):
            sid, slug = m.groups()
            t = re.search(r'title="PDF preview of (.*?)(?: by (.*?))?"', m.group(0))
            title = html.unescape(t.group(1)) if t else slug.replace("-", " ")
            artist = html.unescape(t.group(2) or "") if t else ""
            songs.setdefault(sid, RemoteSong(sid, slug, title, "" if artist == "-" else artist))
    return list(songs.values())


def parse_source_page(page: str) -> tuple[str, str, str]:
    """(source, title, artist) from a song's "view source" page: the source is the first <pre>, title
    and artist come from the page title "Title · Artist · View Source· …"."""
    pre = re.search(r"<pre[^>]*>(.*?)</pre>", page, re.S)
    if pre is None:
        raise SiteError("no source on the page")
    source = html.unescape(pre.group(1))
    t = re.search(r"<title>(.*?)</title>", page, re.S)
    parts = [p.strip() for p in html.unescape(t.group(1)).split("·")] if t else []
    title = parts[0] if parts else ""
    artist = parts[1] if len(parts) > 2 and parts[1] != "-" else ""
    return source.strip("\n"), title, artist


def to_chs(fetched: Fetched) -> Converted:
    """The .chs file for a song: converted, with a comment pointing to the original, and the tag
    import_warn when the conversion left notes or warnings (or the sheet is empty)."""
    s = fetched.song
    conv = convert(fetched.source, title=s.title, artist=s.artist)
    problems = list(conv.notes) + parse(conv.chs).warnings
    lines = conv.chs.split("\n")
    at = next(i for i, line in enumerate(lines) if line.startswith("{time:")) + 1
    extra = [f"# chordsheet.com: {s.url}"]
    if not fetched.source.strip():
        extra.append("# Sorgente vuoto su chordsheet.com: nessun accordo da importare.")
        problems.append("empty")
    if problems:
        extra.insert(0, "{tags: import_warn}")
    lines[at:at] = extra
    return Converted("\n".join(lines), problems)


def imported_ids(texts) -> set[str]:
    """chordsheet.com song ids already imported, from the "# chordsheet.com: /song/<id>/…" comments."""
    return {m.group(1) for t in texts for m in re.finditer(r"^# chordsheet\.com: /song/(\d+)/", t, re.M)}


class Client:
    """A logged-in session with chordsheet.com. `opener` (urllib-like, for the tests) defaults to a
    real one with an in-memory cookie jar; `pause` is the wait between two song pages."""

    def __init__(self, base: str = BASE, opener=None, pause: float = PAUSE, sleep=time.sleep):
        self.base = base.rstrip("/")
        self.opener = opener or urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.pause, self.sleep = pause, sleep

    def _get(self, path: str, data: dict | None = None) -> tuple[str, str]:
        """(final URL, page) of a GET, or of a form POST when `data` is given."""
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        req = urllib.request.Request(self.base + path, data=body, headers={"User-Agent": USER_AGENT})
        try:
            with self.opener.open(req, timeout=20) as r:
                return r.geturl(), r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as err:
            raise SiteError(f"HTTP {err.code}") from err
        except (urllib.error.URLError, OSError) as err:
            raise SiteError(str(getattr(err, "reason", err))) from err

    def login(self, email: str, password: str) -> None:
        _, page = self._get("/login")
        token = re.search(r'name="_csrf_token"\s+value="([^"]+)"', page)
        if not token:
            raise SiteError("login form not found")
        url, page = self._get("/login", {"_username": email, "_password": password,
                                          "_csrf_token": token.group(1)})
        if urllib.parse.urlparse(url).path.rstrip("/") == "/login" or 'name="_password"' in page:
            raise LoginFailed(email)

    def songs(self) -> list[RemoteSong]:
        url, page = self._get("/song/")
        if urllib.parse.urlparse(url).path.rstrip("/") == "/login":
            raise LoginFailed("")
        return parse_song_list(page)

    def fetch(self, song: RemoteSong) -> Fetched:
        _, page = self._get(f"/song/source/{song.id}?slug={urllib.parse.quote(song.slug)}")
        source, title, artist = parse_source_page(page)
        return Fetched(RemoteSong(song.id, song.slug, title or song.title, artist or song.artist), source)

    def fetch_all(self, songs: list[RemoteSong], progress=None):
        """Fetch the songs one at a time (a short pause between them); yields (song, Fetched | error)."""
        for i, s in enumerate(songs):
            if i:
                self.sleep(self.pause)
            try:
                yield s, self.fetch(s)
            except SiteError as err:
                yield s, err
            if progress:
                progress(i + 1, len(songs))
