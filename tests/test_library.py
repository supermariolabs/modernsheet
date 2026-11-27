"""Regression tests — Song library: folders, index, tags, search, sorting. Run with `pytest` from the project
folder."""
from pathlib import Path

import pytest

from modernsheet import parse
from modernsheet.settings import Settings

from helpers import V1_SONG


# ---- song library (app browser and editor)
def test_library_scan_and_search(tmp_path):
    from modernsheet import library
    (tmp_path / "Jazz" / "Blues").mkdir(parents=True)
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "Empty").mkdir()
    (tmp_path / "Jazz" / "Blues" / "lunedi.chs").write_text("# c\n{title: Blues del lunedì}\n", encoding="utf-8")
    (tmp_path / "Jazz" / "notes.txt").write_text("not a song", encoding="utf-8")
    (tmp_path / "b_song.chs").write_text("{key: C}\n", encoding="utf-8")
    (tmp_path / "A song.CHS").write_text("{title: Alba}\n", encoding="utf-8")
    (tmp_path / ".hidden" / "x.chs").write_text("{title: X}\n", encoding="utf-8")

    tree = library.scan(tmp_path)
    assert [f.name for f in tree.folders] == ["Empty", "Jazz"]        # hidden folders skipped, empty ones kept
    assert tree.find(tmp_path / "Empty").count() == 0
    assert [s.title for s in tree.songs] == ["Alba", "b song"]        # sorted by name, title or file name
    assert tree.count() == 3
    blues = tree.find(tmp_path / "Jazz" / "Blues")
    assert blues and [s.path.name for s in blues.songs] == ["lunedi.chs"]
    assert tree.find(tmp_path / "Nope") is None

    assert [s.title for s in library.search(tree, "LUNEDI")] == ["Blues del lunedì"]   # case and accents
    assert [s.title for s in library.search(tree, "jazz blues")] == ["Blues del lunedì"]  # folder names too
    assert library.search(tree, "  ") == []


def test_library_new_song(tmp_path):
    from modernsheet import library
    assert library.safe_filename(' Il mio/brano: "uno" ') == "Il mio brano uno"
    assert library.safe_filename("..") == "Nuovo brano"
    p1 = library.new_song_path(tmp_path, "Brano")
    p1.write_text(library.new_song_text("Brano"), encoding="utf-8")
    assert p1.name == "Brano.chs"
    assert library.new_song_path(tmp_path, "Brano").name == "Brano 2.chs"
    song = parse(p1.read_text(encoding="utf-8"))                         # the template reads without warnings
    assert song.meta["title"] == "Brano" and song.bars and song.warnings == []


def test_library_warning_lines():
    from modernsheet import library
    text = "a\nbb\nccc"
    assert [library.line_offset(text, n) for n in (1, 2, 3, 9)] == [0, 2, 5, 8]   # clamped to the end
    song = parse("{start_of_verse: S}\n| [Xyz] |\n{end_of_verse}\n")
    assert [library.warning_line(w) for w in song.warnings] == [2]
    assert library.warning_line("no line") is None


# ---- tags, song index, card view helpers
def test_tags_directive():
    song = parse("{format: v1}\n{tags: Jazz,  Bossa   Nova , }\n{tags: jazz, ballad}\n" + V1_SONG)
    assert song.tags == ["jazz", "bossa nova", "ballad"] and song.warnings == []


def test_read_info_header(tmp_path):
    from modernsheet import library
    p = tmp_path / "x_y.chs"
    p.write_text("{format: v1}\n{composer: C}\n{key: Bb}\n{time: 3/4}\n{tempo: 96}\n{tags: a, B}\n"
                 "{start_of_verse}\n| [C] |\n{key: G}\n{tags: c}\n{end_of_verse}\n", encoding="utf-8")
    info = library.read_info(p)
    assert (info.title, info.artist, info.key, info.time, info.tempo) == ("x y", "C", "Bb", "3/4", "96")
    assert info.tags == ["a", "b", "c"] and info.format == 1


def test_library_index_reads_only_changed_files(tmp_path):
    from modernsheet import library
    root, data = tmp_path / "songs", tmp_path / "data"
    (root / "sub").mkdir(parents=True)
    (root / "a.chs").write_text("{title: A}\n{tags: x}\n", encoding="utf-8")
    (root / "sub" / "b.chs").write_text("{title: B}\n", encoding="utf-8")
    file = library.index_path(data, root)
    assert file.parent == data / "index" and file == library.index_path(data, root / "sub" / "..")

    idx = library.Index(file)
    tree = library.scan(root, idx)
    assert (idx.hits, idx.misses) == (0, 2) and file.exists()
    idx = library.Index(file)
    library.scan(root, idx)
    assert (idx.hits, idx.misses) == (0 + 2, 0)                     # nothing re-read

    import os
    (root / "a.chs").write_text("{title: A2}\n{tags: y, z}\n", encoding="utf-8")
    os.utime(root / "a.chs", ns=(1, 1))                              # changed mtime (and size)
    (root / "sub" / "b.chs").unlink()
    (root / "c.chs").write_text("{title: C}\n", encoding="utf-8")
    idx = library.Index(file)
    tree = library.scan(root, idx)
    assert (idx.hits, idx.misses) == (0, 2)
    assert {s.title: s.tags for s in tree.walk()} == {"A2": ["y", "z"], "C": []}
    assert set(library.Index(file).entries) == {"a.chs", "c.chs"}   # deleted files leave the index

    file.write_text("not json", encoding="utf-8")                    # a broken index is rebuilt
    idx = library.Index(file)
    assert [s.title for s in library.scan(root, idx).walk()] == ["A2", "C"] and idx.misses == 2


def test_library_search_artist_and_tags(tmp_path):
    from modernsheet import library
    (tmp_path / "one.chs").write_text("{title: Uno}\n{artist: Miles}\n{tags: jazz, ballad}\n", encoding="utf-8")
    (tmp_path / "two.chs").write_text("{title: Due}\n{tags: jazzy}\n", encoding="utf-8")
    tree = library.scan(tmp_path)
    names = lambda q: sorted(s.title for s in library.search(tree, q))   # noqa: E731
    assert names("miles") == ["Uno"]
    assert names("jazz") == ["Due", "Uno"]                           # plain words: substring
    assert names("#jazz") == ["Uno"]                                 # #tag: exact tag
    assert names("#jazz due") == [] and names("#BALLAD") == ["Uno"]


def test_sort_songs():
    from modernsheet.library import SongFile, sort_songs
    P = Path("x.chs")
    songs = [SongFile(P, "b", artist="Zed", key="G", tempo="120", mtime=3),
             SongFile(P, "a", key="Bbm", tempo="80", mtime=1),
             SongFile(P, "c", artist="Amy", key="Bb", mtime=2),
             SongFile(P, "D", key="C#")]
    title = lambda by, d=False: [s.title for s in sort_songs(songs, by, d)]   # noqa: E731
    assert title("title") == ["a", "b", "c", "D"] and title("title", True) == ["D", "c", "b", "a"]
    assert title("artist") == ["c", "b", "a", "D"]                  # no artist: last
    assert title("artist", True) == ["b", "c", "a", "D"]            # …also when descending
    assert title("key") == ["D", "b", "c", "a"]                     # C#, G, Bb, Bbm
    assert title("tempo") == ["a", "b", "c", "D"]
    assert title("modified", True) == ["b", "c", "a", "D"]
    assert title("bogus") == title("title")


def test_settings_library_view_and_sort():
    s = Settings.from_json('{"library_view": "list", "sort_by": "tempo", "sort_desc": true}')
    assert (s.library_view, s.sort_by, s.sort_desc) == ("list", "tempo", True)
    assert "sort_by" not in s.layout_options()
    assert Settings.from_json('{"library_view": "grid", "sort_desc": "yes"}') == Settings()


def test_library_groups_songs_by_letter():
    from modernsheet import library as L
    assert [L.index_letter(t) for t in ("(Out here) on my own", "È la luna", "50 special", "àbc", "123", "")] == \
        ["O", "E", "S", "A", "#", "#"]
    mk = lambda t, a="": L.SongFile(Path(t + ".chs"), t, artist=a)
    songs = L.sort_songs([mk("beta", "Zed"), mk("(Out here)"), mk("Alpha", "abba"), mk("123"), mk("avanti", "Zed")])
    groups = L.group_by_letter(songs)
    assert [(k, [s.title for s in g]) for k, g in groups] == \
        [("A", ["Alpha", "avanti"]), ("B", ["beta"]), ("O", ["(Out here)"]), ("#", ["123"])]
    assert [k for k, _ in L.group_by_letter(songs, descending=True)] == ["O", "B", "A", "#"]   # "#" always last
    by_artist = L.group_by_letter(L.sort_songs(songs, "artist"), "artist")
    assert [(k, len(g)) for k, g in by_artist] == [("A", 1), ("Z", 2), ("#", 2)]
    assert L.GROUPED_SORTS == {"title": "title", "artist": "artist"}


def test_library_search_patterns_and_or():
    from modernsheet import library as L
    root = Path("/lib")
    mk = lambda t, a="", tags=(), sub="": L.SongFile(root / sub / f"{t}.chs", t, artist=a, tags=list(tags))
    songs = [mk("Amazing Grace", "Traditional", ["gospel"]), mk("Àncora tu", "Battisti", ["pop"]),
             mk("(Out here) on my own", "N. Costa", ["pop"]), mk("Blues del lunedì", "Modern", ["blues", "jazz"]),
             mk("Hey Jude", "Beatles", ["pop"], sub="Beatles"), mk("Bossa", "Jobim", ["jazz"])]
    tree = L.Folder(root, songs=songs)
    q = lambda query: sorted(s.title for s in L.search(tree, query))
    assert q("a*") == ["Amazing Grace", "Àncora tu"]                       # title starts with, accents ignored
    assert q("o*") == ["(Out here) on my own"]                             # leading brackets ignored
    assert q("*own") == ["(Out here) on my own"] and q("*JUDE") == ["Hey Jude"]   # title ends with
    assert q("*tu") == ["Àncora tu"] and q("*grace") == ["Amazing Grace"]
    assert q("*ra*") == ["Amazing Grace", "Àncora tu"]                     # contains (title, artist…)
    assert q("*hey jude*") == ["Hey Jude"] and q("*BEATLES*") == ["Hey Jude"]
    assert q("b* & #jazz") == ["Blues del lunedì", "Bossa"]
    assert q("a* | b*") == ["Amazing Grace", "Blues del lunedì", "Bossa", "Àncora tu"]
    assert q("a* & #pop | #blues") == ["Blues del lunedì", "Àncora tu"]   # & binds tighter than |
    assert q("blues lunedi") == ["Blues del lunedì"] and q("#jazz") == ["Blues del lunedì", "Bossa"]
    assert q("") == [] and q(" | & ") == []


def test_new_installation_library_and_merge(tmp_path):
    import main
    from modernsheet import library as L
    root = main.default_library(str(tmp_path / "data"))
    assert root.name == "Modern Sheet" and [p.name for p in root.iterdir()] == ["examples"]   # only the examples
    ex = sorted(p.name for p in (root / "examples").iterdir())
    assert ex == sorted(p.name for p in main.EXAMPLES.iterdir() if p.is_file())
    (root / "mine.chs").write_text("x", encoding="utf-8")
    assert main.default_library(str(tmp_path / "data")) == root and (root / "mine.chs").exists()  # made once
    # joining a synced library that already has examples/ (and other songs): only what it lacks is copied
    synced = tmp_path / "synced"
    (synced / "examples").mkdir(parents=True)
    (synced / "examples" / "demo.chs").write_text("remote version", encoding="utf-8")
    (synced / "import").mkdir()
    added = L.merge_into(root, synced, lambda rel: rel.endswith(".chs"))
    assert "examples/demo.chs" not in added and (synced / "examples" / "demo.chs").read_text() == "remote version"
    assert "mine.chs" in added and not [p for p in synced.glob("*.chs") if p.name != "mine.chs"]   # no strays
    assert L.merge_into(root, synced, lambda rel: rel.endswith(".chs")) == []                      # idempotent


def test_rename_folder(tmp_path):
    from modernsheet import library as L
    root = tmp_path / "lib"
    (root / "Jazz" / "Ballads").mkdir(parents=True)
    (root / "Pop").mkdir()
    (root / "Jazz" / "riff.musicxml").write_text("<x/>", encoding="utf-8")
    (root / "Jazz" / "Ballads" / "b.chs").write_text("{musicxml: ../riff.musicxml}\n", encoding="utf-8")
    (root / "Pop" / "p.chs").write_text("{title: P}\n{musicxml: ../Jazz/riff.musicxml | 1-2}\n", encoding="utf-8")
    (root / "top.chs").write_text("{musicxml: Jazz/riff.musicxml}\n", encoding="utf-8")
    assert sorted(s.name for s, _ in L.outside_refs(root, root / "Jazz")) == ["p.chs", "top.chs"]
    with pytest.raises(ValueError):
        L.rename_folder(root, "X", root)                                 # never the main folder
    with pytest.raises(ValueError):
        L.rename_folder(root / "Jazz", "Pop", root)                      # name in use
    with pytest.raises(ValueError):
        L.rename_folder(root / "Jazz", "  . ", root)                     # blank
    r = L.rename_folder(root / "Jazz", "Jazz: standard/2", root)        # cleaned name
    assert r.path == root / "Jazz standard 2" and not (root / "Jazz").exists()
    assert sorted(p.name for p in r.updated) == ["p.chs", "top.chs"]
    assert (root / "Pop" / "p.chs").read_text() == "{title: P}\n{musicxml: ../Jazz standard 2/riff.musicxml | 1-2}\n"
    assert (root / "top.chs").read_text() == "{musicxml: Jazz standard 2/riff.musicxml}\n"
    assert (r.path / "Ballads" / "b.chs").read_text() == "{musicxml: ../riff.musicxml}\n"   # inside: unchanged
    assert (root / "Pop" / "../Jazz standard 2/riff.musicxml").is_file()          # the new reference resolves
    r2 = L.rename_folder(r.path, "jazz STANDARD 2", root)               # case only
    assert r2.path.name == "jazz STANDARD 2" and [p.name for p in root.iterdir() if p.is_dir() and "azz" in p.name.lower()] == ["jazz STANDARD 2"]


def test_import_song_into_the_library(tmp_path):
    from modernsheet import library as L
    src = tmp_path / "outside" / "songs"
    (src.parent / "shared").mkdir(parents=True)
    src.mkdir()
    (src / "intro.musicxml").write_text("<a/>", encoding="utf-8")
    (src.parent / "shared" / "riff.musicxml").write_text("<b/>", encoding="utf-8")
    text = "{title: S}\n{musicxml: intro.musicxml}\n{musicxml: ../shared/riff.musicxml | 1-2}\n{musicxml: gone.musicxml}\n"
    lib = tmp_path / "lib" / "Jazz"
    lib.mkdir(parents=True)
    (lib / "intro.musicxml").write_text("<a/>", encoding="utf-8")         # same name and content: reused
    (lib / "riff.musicxml").write_text("<other/>", encoding="utf-8")      # same name, other content
    (lib / "Song.chs").write_text("x", encoding="utf-8")
    r = L.import_song(lib, "Song.chs", text, src)
    assert r.path == lib / "Song 2.chs" and (lib / "Song.chs").read_text() == "x"          # never overwrites
    assert r.copied == ["riff 2.musicxml"] and r.missing == ["gone.musicxml"]
    assert (lib / "riff 2.musicxml").read_text() == "<b/>" and (lib / "riff.musicxml").read_text() == "<other/>"
    assert r.path.read_text() == ("{title: S}\n{musicxml: intro.musicxml}\n{musicxml: riff 2.musicxml | 1-2}\n"
                                  "{musicxml: gone.musicxml}\n")
    phone = L.import_song(lib, "Phone", "{musicxml: a.musicxml}\n")                      # no folder: kept, missing
    assert phone.path.name == "Phone.chs" and phone.missing == ["a.musicxml"] and not phone.copied


def test_song_card_key_and_time_only_from_the_header(tmp_path):
    from modernsheet import library
    (tmp_path / "a.chs").write_text("{title: A}\n{start_of_verse}\n| [C] | {key: Db} [Db] |\n{key: E}\n{time: 3/4}\n"
                                    "| [E] |\n{end_of_verse}\n", encoding="utf-8")
    (tmp_path / "b.chs").write_text("{title: B}\n{key: G}\n{time: 3/4}\n{start_of_verse}\n| [G] |\n{key: A}\n"
                                    "{end_of_verse}\n", encoding="utf-8")
    a, b = library.read_info(tmp_path / "a.chs"), library.read_info(tmp_path / "b.chs")
    assert (a.key, a.time) == ("", "")              # only changes, after the music: no key on the card
    assert (b.key, b.time) == ("G", "3/4")


def test_store_mode_keeps_the_library_inside_the_app(tmp_path, monkeypatch):
    """Store mode (iPad/iPhone, Android, Mac App Store sandbox, SPEC §8.6): a folder chosen in the settings
    and folder sync are ignored, the library is the app's own (on iOS in Documents, moved there once)."""
    import main
    from modernsheet import library as L
    from modernsheet.settings import Settings
    assert L.store_mode("ios") and L.store_mode("android") and not L.store_mode("macos", {})
    assert L.store_mode("macos", {"APP_SANDBOX_CONTAINER_ID": "app.modernsheet"})
    assert not L.store_mode("windows", {"APP_SANDBOX_CONTAINER_ID": "x"}) and not L.store_mode("linux", {})
    data, docs = tmp_path / "data", tmp_path / "Documents"
    old = main.default_library(str(data))
    (old / "mine.chs").write_text("x", encoding="utf-8")
    assert L.move_library(old, docs / "Modern Sheet") and (docs / "Modern Sheet" / "mine.chs").exists()
    assert not old.exists() and not L.move_library(old, docs / "Modern Sheet")         # once only
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(data))
    monkeypatch.delenv("MODERNSHEET_LIBRARY", raising=False)
    monkeypatch.delenv("CHORDSHEET_LIBRARY", raising=False)
    elsewhere = tmp_path / "chosen"
    elsewhere.mkdir()
    app = object.__new__(main.App)
    app.settings = Settings(library_root=str(elsewhere), sync_mode="folder", sync_folder=str(tmp_path / "remote"))
    app.home, app.store = str(docs), True
    assert app.sync_state() is None                                    # no folder sync in store mode
    assert app.library_root() == docs / "Modern Sheet"                 # not the folder chosen earlier
    app.store = False                                                  # desktop: as before
    assert app.sync_state() is not None and app.library_root().name == "library"   # the synced local copy
    app.settings.sync_mode = "none"
    assert app.library_root() == elsewhere


def test_song_and_library_zip_roundtrip(tmp_path):
    """A song goes out as a .zip with its MusicXML (references made local), the library as a .zip with
    its folders; importing never overwrites, and unsafe or foreign entries are left out (SPEC §8.6)."""
    import io
    import zipfile
    from modernsheet import library as L
    lib, shared = tmp_path / "lib", tmp_path / "lib" / "shared"
    (lib / "Jazz").mkdir(parents=True)
    shared.mkdir()
    (shared / "x.musicxml").write_text("<x/>", encoding="utf-8")
    src = "{title: A}\n{start_of_verse: V}\n  {musicxml: ../shared/x.musicxml | 1-2}\n{end_of_verse}\n"
    (lib / "Jazz" / "A.chs").write_text(src, encoding="utf-8")
    (lib / "Jazz" / "B.chs").write_text("{title: B}\n", encoding="utf-8")
    (lib / ".trash").mkdir()
    (lib / ".trash" / "old.chs").write_text("x", encoding="utf-8")
    (lib / "notes.txt").write_text("x", encoding="utf-8")
    z = zipfile.ZipFile(io.BytesIO(L.song_zip(src, "A.chs", lib / "Jazz")))
    assert sorted(z.namelist()) == ["A.chs", "x.musicxml"]
    assert "  {musicxml: x.musicxml | 1-2}" in z.read("A.chs").decode()
    dest = tmp_path / "phone"
    dest.mkdir()
    (dest / "A.chs").write_text("mine", encoding="utf-8")
    r = L.import_zip(dest, L.song_zip(src, "A", lib / "Jazz"), "A.zip")
    assert r.songs == [dest / "A 2.chs"] and r.copied == ["x.musicxml"] and r.missing == [] and r.folder is None
    assert (dest / "A.chs").read_text() == "mine"
    assert L.library_files(lib) == ["Jazz/A.chs", "Jazz/B.chs", "shared/x.musicxml"]
    r = L.import_zip(dest, L.library_zip(lib), "Modern Sheet.zip")
    assert r.folder == dest / "Modern Sheet" and sorted(p.relative_to(r.folder).as_posix() for p in r.songs) == [
        "Jazz/A.chs", "Jazz/B.chs"]
    assert (r.folder / "shared" / "x.musicxml").exists()                       # references still work
    assert L.import_zip(dest, L.library_zip(lib), "Modern Sheet.zip").folder == dest / "Modern Sheet 2"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as w:
        for name in ("../evil.chs", "/abs.chs", "C:/win.chs", "__MACOSX/._a.chs", "Song/.hidden.chs", "Song/run.sh"):
            w.writestr(name, "x")
        w.writestr("Song/a.chs", "{title: a}")
        w.writestr("Song/b.chs", "{title: b}")
    r = L.import_zip(dest, buf.getvalue(), "evil.zip")
    assert r.skipped == 6 and sorted(p.name for p in r.songs) == ["a.chs", "b.chs"]
    assert not (tmp_path / "evil.chs").exists() and all(p.is_relative_to(dest) for p in tmp_path.rglob("*.chs")
                                                         if "lib" not in p.parts)
    with pytest.raises(L.BadZip):
        L.import_zip(dest, b"not a zip")
    empty = io.BytesIO()
    with zipfile.ZipFile(empty, "w") as w:
        w.writestr("readme.txt", "x")
    with pytest.raises(L.BadZip):
        L.import_zip(dest, empty.getvalue())


def test_drive_copy_is_visible_on_ios(tmp_path, monkeypatch):
    """With Google Drive on iPad/iPhone the local copy of the library lives in the app's Documents (shown
    by the Files app), one folder per Drive folder and account; an older copy in the app data moves there."""
    import main
    from modernsheet.settings import Settings
    data, docs = tmp_path / "data", tmp_path / "Documents"
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(data))
    monkeypatch.delenv("MODERNSHEET_LIBRARY", raising=False)
    monkeypatch.delenv("CHORDSHEET_LIBRARY", raising=False)
    app = object.__new__(main.App)
    app.settings = Settings(sync_mode="gdrive", sync_account="me@example.com")
    app.home, app.store = None, True                                     # Android: in the app data
    hidden = app.library_root()
    assert hidden == app.sync_state() / "library"
    (hidden / "old.chs").write_text("x", encoding="utf-8")
    app.home = str(docs)                                                 # iPad/iPhone
    visible = app.library_root()
    assert visible == docs / "Modern Sheet (Google Drive · me@example.com)" and (visible / "old.chs").exists()
    assert not hidden.exists() and app.local_copy(app.sync_state()) == visible
    app.root = visible
    assert app.home_label() == "Google Drive"
    app.settings.sync_account = "other@example.com"                      # another account: its own copy
    assert app.library_root() == docs / "Modern Sheet (Google Drive · other@example.com)"
