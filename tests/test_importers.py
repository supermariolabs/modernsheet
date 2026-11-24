"""Regression tests — Importers: chordsheet.com text, the fixes found on real songs, the account import
against a fake site. Run with `pytest` from the project folder."""
from pathlib import Path

import urllib.parse as _up

import pytest

from modernsheet import layout
from modernsheet.pdf import pdf_bytes

from helpers import csm_song


# ---- import from Chord Sheet Maker (chordsheet.com)

CSM = Path(__file__).resolve().parent / "data" / "esempio_chordsheet_com.txt"


def test_csm_example_converts_cleanly():
    conv, song = csm_song(CSM.read_text(encoding="utf-8"))
    assert song.meta["title"] == "Esempio da Chord Sheet Maker"
    assert song.meta["key"] == "G" and song.meta["tempo"] == "96"
    assert [s.kind for s in song.sections] == ["intro", "verse", "chorus", "bridge", "coda"]
    assert pdf_bytes(layout(song)).startswith(b"%PDF")


def test_csm_bars_glue_repeats_and_simile():
    _, song = csm_song("(C Am_D7 % G)x3\n|:F G:| C || %% *")
    bars = song.bars
    assert [e.chord for e in bars[1].events] == ["Am", "D7"]
    assert bars[0].repeat_start and bars[3].repeat_end == 3
    assert [e.chord for e in bars[2].events] == ["Am", "D7"]       # % of a 2-chord bar copies it
    assert bars[5].repeat_end == 2 and bars[6].double_after
    assert [e.chord for e in bars[7].events] == ["G"] and [e.chord for e in bars[8].events] == ["C"]


def test_csm_endings():
    _, song = csm_song("(A B 1. C D 2. E F)")
    b = song.bars
    assert b[2].volta == "1." and b[3].repeat_end == 2
    assert b[4].volta == "2." and b[5].volta_end and b[5].double_after


def test_csm_time_rests_and_nashville():
    _, song = csm_song("3:4 1 4 5 r1\n4:4 6m_2m 5/7", key="D")
    chords = [[e.chord for e in b.events] for b in song.bars]
    assert chords[:4] == [["D"], ["G"], ["A"], ["/"]]
    assert chords[4] == ["Bm", "Em"] and chords[5] == ["A/C#"]
    assert song.bars[0].num == 3 and song.bars[4].num == 4


# ---- chord annotations [A "1°"] and the importer fixes found on real chordsheet.com songs
def test_csm_annotations_beats_indents_and_counts():
    conv, song = csm_song('(E A E A"1°"_Bm_A/C#_A?"2°")\nG Em "a minor chord" Am7\n*_B_*_* E\n'
                          '( A B ) x4\n(C C 1.D\nX X 2.F_X_G)\nA %"ripeti" P1 B P0')
    ev = [e for b in song.bars for e in b.events]
    notes = [e.note for e in ev if e.note]
    assert notes == ["1°", "2°", "a minor chord", "ripeti"]
    b = song.bars
    starts = [(e.chord, e.start) for e in b[7].events]
    assert starts == [(None, 0.0), ("B", 1.0), (None, 2.0), (None, 3.0)]   # B on beat 2
    assert b[10].repeat_end == 4                                           # "( … ) x4"
    assert not conv.notes and "[X]" not in conv.chs and "P1" not in conv.chs


# ---- import from a chordsheet.com account (fake site)
import html as _html  # noqa: E402
import re  # noqa: E402


class FakeChordsheet:
    """Just the pages the account importer reads: /login (Symfony form), /song/, /song/source/<id>."""
    LIST = ('<div class="row"><div class="card filter-me col-12"><div class="card-body">'
            '<h4 class="card-subtitle"><a href="/song/png/11/blue-night">Blue Night</a></h4>'
            '<h6 class="card-title">-</h6></div><div class="card-footer">'
            '<a href="/song/11/blue-night" title="PDF preview of Blue Night by -">x</a>'
            '<a href="/song/11/blue-night.pdf">pdf</a></div></div>'
            '<div class="card filter-me col-12"><div class="card-body">'
            '<h4 class="card-subtitle"><a href="/song/png/12/l-amore">L&#039;amore</a></h4>'
            '<h6 class="card-title">C. Baglioni</h6></div><div class="card-footer">'
            '<a href="/song/12/l-amore">x</a></div></div>'
            '<div class="card filter-me col-12"><div class="card-body">'
            '<h4 class="card-subtitle"><a href="/song/png/13/vuoto">Vuoto</a></h4><h6 class="card-title">-</h6>'
            '</div><div class="card-footer"><a href="/song/13/vuoto">x</a></div></div></div>')
    SOURCES = {"11": ("Blue Night · - · View Source", '= A\n(C F G"1°"_Am x)\nD.S. al coda'),
               "12": ("L'amore · C. Baglioni · View Source", "= Strofa\nC Am F G\n- piano"),
               "13": ("Vuoto · - · View Source", "")}

    def __init__(self):
        self.logged, self.posts, self.requests = False, [], []

    class _R:
        def __init__(self, url, body):
            self.url, self.body = url, body
        def geturl(self):
            return self.url
        def read(self):
            return self.body.encode()
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    def open(self, req, timeout=None):
        url = req.full_url
        path = url.split("chordsheet.test", 1)[1]
        self.requests.append(path)
        if path == "/login" and req.data is None:
            return self._R(url, '<form action="/login" method="post"><input name="_username"><input name="_password">'
                                '<input type="hidden" name="_csrf_token"\n   value="tok123"></form>')
        if path == "/login":
            form = dict(_up.parse_qsl(req.data.decode()))
            self.posts.append(form)
            if form == {"_username": "me@example.com", "_password": "secret", "_csrf_token": "tok123"}:
                self.logged = True
                return self._R("https://chordsheet.test/song/", self.LIST)
            return self._R("https://chordsheet.test/login", '<input name="_password">')
        if not self.logged:
            return self._R("https://chordsheet.test/login", '<input name="_password">')
        if path == "/song/":
            return self._R(url, self.LIST)
        m = re.match(r"/song/source/(\d+)\?slug=", path)
        title, src = self.SOURCES[m.group(1)]
        return self._R(url, f'<html><head><title>{_html.escape(title)}· Chord Sheet Maker</title></head>'
                            f'<pre class="fw-bold text-white p-3">{_html.escape(src)}</pre></html>')


def test_chordsheet_account_import():
    from modernsheet.importers import chordsheet_account as A
    site = FakeChordsheet()
    client = A.Client("https://chordsheet.test", site, pause=0.5, sleep=lambda s: None)
    with pytest.raises(A.LoginFailed):
        client.login("me@example.com", "wrong")
    client.login("me@example.com", "secret")
    songs = client.songs()
    assert [(s.id, s.title, s.artist) for s in songs] == [("11", "Blue Night", ""), ("12", "L'amore", "C. Baglioni"),
                                                         ("13", "Vuoto", "")]
    got = list(client.fetch_all(songs))
    assert [type(f).__name__ for _, f in got] == ["Fetched", "Fetched", "Fetched"]
    blue, amore, vuoto = (A.to_chs(f) for _, f in got)
    assert not amore.problems and "{tags: import_warn}" not in amore.text and "# chordsheet.com: /song/12/l-amore" in amore.text
    assert '[G "1°"]' in blue.text and "{ds: al Coda}" in blue.text
    assert vuoto.problems == ["empty"] and "{tags: import_warn}" in vuoto.text
    assert A.imported_ids([amore.text, vuoto.text, "x"]) == {"12", "13"}
    assert "secret" not in "".join(map(str, site.requests))      # the password only travels in the POST body
