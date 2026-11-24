"""Regression tests — Library synchronisation: engine with an in-memory remote, Google Drive against a fake
API. Run with `pytest` from the project folder."""
from pathlib import Path

import pytest

from modernsheet import parse


# ---- library synchronisation (local-first)
from modernsheet import sync as S  # noqa: E402


class MemoryProvider:
    """In-memory remote for the tests; `offline` simulates no network."""

    def __init__(self):
        self.files: dict[str, tuple[bytes, int]] = {}
        self.n = 0
        self.offline = False

    def _rev(self, rel):
        return str(self.files[rel][1])

    def list(self):
        if self.offline:
            raise S.Offline("no network")
        return {rel: S.RemoteFile(self._rev(rel)) for rel in self.files}

    def download(self, rel):
        return self.files[rel][0]

    def upload(self, rel, data, expected_rev):
        if (self._rev(rel) if rel in self.files else None) != expected_rev:
            raise S.RemoteChanged(rel)
        self.n += 1
        self.files[rel] = (data, self.n)
        return self._rev(rel)

    def delete(self, rel, expected_rev):
        if self._rev(rel) != expected_rev:
            raise S.RemoteChanged(rel)
        del self.files[rel]

    def put(self, rel, data):                       # a change made by another device
        self.n += 1
        self.files[rel] = (data, self.n)


def device(tmp_path, name, provider):
    root = tmp_path / name
    root.mkdir()
    return root, S.Syncer(root, provider, S.Manifest(tmp_path / f"{name}.json"), trash=tmp_path / f"{name}-trash",
                          device=name, clock=lambda: 1_700_000_000)


def test_sync_copies_new_files_both_ways(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    (a / "Jazz").mkdir()
    (a / "Jazz" / "x.chs").write_text("x1", encoding="utf-8")
    (a / "x.musicxml").write_text("<x/>", encoding="utf-8")
    (a / "notes.txt").write_text("not synced", encoding="utf-8")
    (a / ".hidden.chs").write_text("not synced", encoding="utf-8")
    r = sa.sync()
    assert sorted(r.uploaded) == ["Jazz/x.chs", "x.musicxml"] and set(remote.files) == {"Jazz/x.chs", "x.musicxml"}
    b, sb = device(tmp_path, "B", remote)
    r = sb.sync()
    assert sorted(r.downloaded) == ["Jazz/x.chs", "x.musicxml"] and (b / "Jazz" / "x.chs").read_text() == "x1"
    assert sa.sync() == S.Report() or not sa.sync().changed_local      # nothing left to do


def test_sync_edits_deletes_and_offline(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    b, sb = device(tmp_path, "B", remote)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    sa.sync(); sb.sync()
    (b / "s.chs").write_text("v2 from B", encoding="utf-8")       # edit on B
    assert sb.sync().uploaded == ["s.chs"]
    assert sa.sync().downloaded == ["s.chs"] and (a / "s.chs").read_text() == "v2 from B"

    remote.offline = True                                          # A works offline…
    (a / "s.chs").write_text("v3 offline", encoding="utf-8")
    (a / "new.chs").write_text("n", encoding="utf-8")
    r = sa.sync()
    assert r.offline and not r.uploaded and remote.files["s.chs"][0] == b"v2 from B"
    remote.offline = False                                         # …and catches up later: no queue needed
    assert sorted(sa.sync().uploaded) == ["new.chs", "s.chs"]
    assert sorted(sb.sync().downloaded) == ["new.chs", "s.chs"]

    (a / "new.chs").unlink()                                       # delete on A
    assert sa.sync().deleted_remote == ["new.chs"]
    sb.sync()
    assert not (b / "new.chs").exists()                            # B deletes it too…
    assert list((tmp_path / "B-trash").rglob("new.chs"))            # …into its trash, not for good


def test_sync_conflict_keeps_both_versions(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    b, sb = device(tmp_path, "B", remote)
    (a / "s.chs").write_text("base", encoding="utf-8")
    sa.sync(); sb.sync()
    (a / "s.chs").write_text("A's edit", encoding="utf-8")
    (b / "s.chs").write_text("B's edit", encoding="utf-8")
    sb.sync()                                                       # B first: remote = B's edit
    r = sa.sync()
    assert len(r.conflicts) == 1 and r.conflicts[0].startswith("s (conflitto A ") and r.conflicts[0].endswith(".chs")
    assert (a / "s.chs").read_text() == "B's edit"                  # the remote keeps the name
    assert (a / r.conflicts[0]).read_text() == "A's edit"           # the local edit is not lost
    assert r.conflicts[0] in remote.files                           # and reaches the other devices
    sb.sync()
    assert (b / r.conflicts[0]).read_text() == "A's edit"
    # same content on both sides: no conflict copy
    (a / "s.chs").write_text("same", encoding="utf-8")
    remote.put("s.chs", b"same")
    assert sa.sync().conflicts == []


def test_sync_edit_wins_over_delete_and_busy_files(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    b, sb = device(tmp_path, "B", remote)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    sa.sync(); sb.sync()
    (a / "s.chs").write_text("edited on A", encoding="utf-8")
    (b / "s.chs").unlink()
    sb.sync()                                                       # B deletes the remote copy
    assert sa.sync().uploaded == ["s.chs"]                          # A's edit comes back
    assert sb.sync().downloaded == ["s.chs"] and (b / "s.chs").read_text() == "edited on A"
    remote.put("s.chs", b"remote edit")
    r = sa.sync(busy={"s.chs"})                                     # open with unsaved changes: later
    assert r.skipped == ["s.chs"] and (a / "s.chs").read_text() == "edited on A"


def test_folder_provider(tmp_path):
    cloud = tmp_path / "iCloud" / "Modern Sheet"
    a, sa = device(tmp_path, "A", S.FolderProvider(cloud))
    assert sa.sync().offline                                        # folder missing: offline, no damage
    cloud.mkdir(parents=True)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    assert sa.sync().uploaded == ["s.chs"] and (cloud / "s.chs").read_text() == "v1"
    (cloud / "Sub").mkdir()
    (cloud / "Sub" / "t.chs").write_text("t", encoding="utf-8")    # arrives from another device
    assert sa.sync().downloaded == ["Sub/t.chs"]
    import os
    (cloud / "s.chs").write_text("changed in the cloud", encoding="utf-8")
    os.utime(cloud / "s.chs", ns=(1, 1))
    assert sa.sync().downloaded == ["s.chs"] and (a / "s.chs").read_text() == "changed in the cloud"
    m = S.Manifest(tmp_path / "A.json")
    assert set(m.files) == {"s.chs", "Sub/t.chs"} and m.last_sync == 1_700_000_000
    assert S.state_dir(tmp_path, "folder:x") != S.state_dir(tmp_path, "folder:y")


def test_conflict_name():
    assert S.conflict_name("Jazz/Blues.chs", "iPad", 0).startswith("Jazz/Blues (conflitto iPad 19")
    assert S.conflict_name("x", "Mac", 0).startswith("x (conflitto Mac ")
    assert S.is_synced("a/b.musicxml") and not S.is_synced(".x/b.chs") and not S.is_synced("a.txt")


def test_unavailable_remote_file_is_never_a_deletion(tmp_path, monkeypatch):
    cloud = tmp_path / "iCloud"
    cloud.mkdir()
    monkeypatch.setattr(S.FolderProvider, "_request_download", staticmethod(lambda p: None))
    a, sa = device(tmp_path, "A", S.FolderProvider(cloud))
    (a / "s.chs").write_text("v1", encoding="utf-8")
    sa.sync()
    (cloud / "s.chs").rename(cloud / ".s.chs.icloud")              # evicted by iCloud
    r = sa.sync()
    assert (a / "s.chs").read_text() == "v1" and not r.deleted_local and not r.downloaded
    (a / "s.chs").write_text("v2", encoding="utf-8")                # edited while evicted: wait
    assert sa.sync().skipped == ["s.chs"] and (a / "s.chs").read_text() == "v2"
    (cloud / ".s.chs.icloud").rename(cloud / "s.chs")              # back on disk
    assert sa.sync().uploaded == ["s.chs"] and (cloud / "s.chs").read_text() == "v2"
    (cloud / ".t.chs.icloud").write_text("", encoding="utf-8")      # new, never downloaded: skipped
    assert sa.sync().skipped == ["t.chs"] and not (a / "t.chs").exists()


# ---- Google Drive provider, against an in-memory fake of the Drive API
import hashlib  # noqa: E402
import json as _json  # noqa: E402
import urllib.parse as _up  # noqa: E402

from modernsheet import gdrive as G  # noqa: E402


class FakeDrive:
    """Just the Drive v3 / OAuth endpoints the provider uses."""

    def __init__(self):
        self.items: dict[str, dict] = {}         # id -> {name, mimeType, parents, data, trashed, modifiedTime}
        self.n = 0
        self.access = "tok1"
        self.offline = False
        self.pending_polls = 1
        self.calls: list[str] = []

    def _id(self):
        self.n += 1
        return f"id{self.n}"

    def add(self, name, parent, data=None, mime=None):
        i = self._id()
        self.items[i] = {"name": name, "parents": [parent], "trashed": False, "modifiedTime": f"{self.n:06d}",
                         "mimeType": mime or ("application/octet-stream" if data is not None else G.FOLDER_MIME),
                         "data": data}
        return i

    def meta(self, i):
        it = self.items[i]
        d = {"id": i, "name": it["name"], "mimeType": it["mimeType"], "parents": it["parents"],
             "modifiedTime": it["modifiedTime"], "trashed": it["trashed"]}
        if it["data"] is not None:
            d["md5Checksum"] = hashlib.md5(it["data"]).hexdigest()
        return d

    def __call__(self, method, url, headers, body):
        if self.offline:
            raise S.Offline("no network")
        u = _up.urlparse(url)
        q = dict(_up.parse_qsl(u.query))
        self.calls.append(f"{method} {u.path}")
        ok = lambda d: G.Response(200, _json.dumps(d).encode())          # noqa: E731
        if url.startswith(G.DEVICE_URL):
            return ok({"device_code": "dev", "user_code": "ABCD-EFGH", "verification_url": "https://google.com/device",
                       "interval": 5, "expires_in": 1800})
        if url.startswith(G.TOKEN_URL):
            form = dict(_up.parse_qsl(body.decode()))
            if form["grant_type"] == "refresh_token":
                self.access = f"tok{self.n + 100}"
                return ok({"access_token": self.access, "expires_in": 3600})
            if self.pending_polls:
                self.pending_polls -= 1
                return G.Response(428, b'{"error": "authorization_pending"}')
            return ok({"access_token": self.access, "refresh_token": "refresh", "expires_in": 3600})
        if headers.get("Authorization") != f"Bearer {self.access}":
            return G.Response(401, b"{}")
        path = u.path.replace("/upload", "").removeprefix("/drive/v3")
        if path == "/about":
            return ok({"user": {"emailAddress": "mario@example.com", "displayName": "Mario"}})
        if path == "/files" and method == "GET":
            live = [i for i, it in self.items.items() if not it["trashed"]]
            if "name=" in q["q"]:                                          # the root folder query
                name = q["q"].split("name='")[1].split("'")[0]
                live = [i for i in live if self.items[i]["name"] == name and self.items[i]["parents"] == ["root"]]
            elif " in parents" in q["q"]:                                  # children of a folder
                pid = q["q"].split("'")[1]
                live = [i for i in live if pid in self.items[i]["parents"]]
            return ok({"files": [self.meta(i) for i in live]})
        if path == "/files" and method == "POST":
            if q.get("uploadType") == "multipart":
                boundary = headers["Content-Type"].split("boundary=")[1].encode()
                parts = body.split(b"--" + boundary)
                meta = _json.loads(parts[1].split(b"\r\n\r\n", 1)[1].rstrip(b"\r\n"))
                data = parts[2].split(b"\r\n\r\n", 1)[1][:-2]
                i = self.add(meta["name"], meta["parents"][0], data)
            else:
                meta = _json.loads(body)
                i = self.add(meta["name"], meta["parents"][0])
            return ok(self.meta(i))
        i = path.removeprefix("/files/")
        if i not in self.items:
            return G.Response(404, b"{}")
        if method == "GET":
            return G.Response(200, self.items[i]["data"]) if q.get("alt") == "media" else ok(self.meta(i))
        if method == "PATCH" and q.get("uploadType") == "media":
            self.n += 1
            self.items[i]["data"], self.items[i]["modifiedTime"] = body, f"{self.n:06d}"
            return ok(self.meta(i))
        if method == "PATCH":
            self.items[i].update(_json.loads(body))
            return ok(self.meta(i))
        return G.Response(400, b"{}")


def signed_in(tmp_path, fake, name="tok.json"):
    auth = G.GoogleAuth(G.ClientConfig("cid", "secret"), tmp_path / name, fake, clock=lambda: 1000)
    dc = auth.start()
    assert dc.user_code == "ABCD-EFGH" and auth.poll(dc) == "pending" and auth.poll(dc) == "ok"
    return auth


def test_google_device_flow_and_token_refresh(tmp_path):
    fake = FakeDrive()
    auth = signed_in(tmp_path, fake)
    assert auth.signed_in and (tmp_path / "tok.json").stat().st_mode & 0o077 == 0     # private file
    assert G.GoogleAuth(auth.client, tmp_path / "tok.json", fake).signed_in             # survives restarts
    drive = G.DriveProvider(auth, fake)
    assert drive.account()["emailAddress"] == "mario@example.com"
    fake.access = "rotated"                                     # the access token expired on the server
    fake.n += 1
    assert drive.account()["displayName"] == "Mario"            # 401 -> refreshed -> retried
    auth.sign_out()
    assert not auth.signed_in and not (tmp_path / "tok.json").exists()
    with pytest.raises(S.AuthRequired):
        drive.account()


def test_google_drive_sync_between_two_devices(tmp_path):
    fake = FakeDrive()
    remote_a = G.DriveProvider(signed_in(tmp_path, fake, "a.json"), fake)
    a, sa = device(tmp_path, "A", remote_a)
    (a / "Jazz").mkdir()
    (a / "Jazz" / "blues.chs").write_text("{title: Blues}", encoding="utf-8")
    (a / "Jazz" / "riff.musicxml").write_text("<score-partwise/>", encoding="utf-8")
    assert sorted(sa.sync().uploaded) == ["Jazz/blues.chs", "Jazz/riff.musicxml"]
    folders = [it for it in fake.items.values() if it["mimeType"] == G.FOLDER_MIME]
    assert sorted(f["name"] for f in folders) == ["Jazz", "Modern Sheet"]  # app folder + subfolder

    fake.pending_polls = 1
    remote_b = G.DriveProvider(signed_in(tmp_path, fake, "b.json"), fake)
    b, sb = device(tmp_path, "B", remote_b)
    assert sorted(sb.sync().downloaded) == ["Jazz/blues.chs", "Jazz/riff.musicxml"]
    assert sum(1 for it in fake.items.values() if it["name"] == "Modern Sheet") == 1   # root folder reused

    (b / "Jazz" / "blues.chs").write_text("{title: Blues 2}", encoding="utf-8")
    assert sb.sync().uploaded == ["Jazz/blues.chs"]
    assert sa.sync().downloaded == ["Jazz/blues.chs"] and (a / "Jazz" / "blues.chs").read_text() == "{title: Blues 2}"

    (a / "Jazz" / "blues.chs").write_text("A", encoding="utf-8")       # conflict through Drive
    (b / "Jazz" / "blues.chs").write_text("B", encoding="utf-8")
    sb.sync()
    r = sa.sync()
    assert len(r.conflicts) == 1 and (a / "Jazz" / "blues.chs").read_text() == "B"
    assert sb.sync().downloaded == r.conflicts

    (a / "Jazz" / "riff.musicxml").unlink()                             # delete = Drive trash
    assert sa.sync().deleted_remote == ["Jazz/riff.musicxml"]
    assert any(it["name"] == "riff.musicxml" and it["trashed"] for it in fake.items.values())
    sb.sync()
    assert not (b / "Jazz" / "riff.musicxml").exists()

    fake.offline = True                                                 # offline: nothing breaks
    (a / "new.chs").write_text("n", encoding="utf-8")
    assert sa.sync().offline
    fake.offline = False
    assert sa.sync().uploaded == ["new.chs"]


def test_google_drive_auth_revoked(tmp_path):
    fake = FakeDrive()
    auth = signed_in(tmp_path, fake)
    a, sa = device(tmp_path, "A", G.DriveProvider(auth, fake))
    auth.token["refresh_token"] = None                                 # revoked / signed out elsewhere
    r = sa.sync()
    assert r.auth_required and not r.offline


def test_google_client_config(tmp_path, monkeypatch):
    for prefix in ("MODERNSHEET", "CHORDSHEET"):
        monkeypatch.delenv(f"{prefix}_GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv(f"{prefix}_GOOGLE_CLIENT_SECRET", raising=False)
    f = tmp_path / "google_client.json"
    assert G.client_config(f) is None
    f.write_text('{"installed": {"client_id": "x.apps.googleusercontent.com", "client_secret": "s"}}')
    assert G.client_config(tmp_path / "missing.json", f) == G.ClientConfig("x.apps.googleusercontent.com", "s")
    monkeypatch.setenv("CHORDSHEET_GOOGLE_CLIENT_ID", "old-id")              # name used before 0.19
    monkeypatch.setenv("CHORDSHEET_GOOGLE_CLIENT_SECRET", "old-secret")
    assert G.client_config(f) == G.ClientConfig("old-id", "old-secret")
    monkeypatch.setenv("MODERNSHEET_GOOGLE_CLIENT_ID", "env-id")
    monkeypatch.setenv("MODERNSHEET_GOOGLE_CLIENT_SECRET", "env-secret")
    assert G.client_config(f) == G.ClientConfig("env-id", "env-secret")


def test_empty_or_recreated_remote_is_not_a_mass_deletion(tmp_path):
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    (a / "t.chs").write_text("t", encoding="utf-8")
    sa.sync()
    remote.files.clear()                                         # the remote folder was emptied / replaced
    r = sa.sync()
    assert r.remote_reset and sorted(r.uploaded) == ["s.chs", "t.chs"] and not r.deleted_local
    assert (a / "s.chs").exists() and not (tmp_path / "A-trash").exists()
    assert not sa.sync().remote_reset                            # back to normal


def test_google_drive_folder_renamed_or_configurable(tmp_path):
    fake = FakeDrive()
    auth = signed_in(tmp_path, fake)
    drive = G.DriveProvider(auth, fake)
    a, sa = device(tmp_path, "A", drive)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    assert sa.sync().uploaded == ["s.chs"] and not sa.sync().remote_reset
    root = next(i for i, it in fake.items.items() if it["name"] == "Modern Sheet")
    fake.items[root]["name"] = "Old songs"                       # renamed on drive.google.com
    r = sa.sync()
    assert r.remote_reset and r.uploaded == ["s.chs"] and not r.deleted_local and (a / "s.chs").exists()
    assert sum(1 for it in fake.items.values() if it["name"] == "Modern Sheet") == 1   # a new app folder
    assert not sa.sync().remote_reset and not sa.sync().uploaded

    other = G.DriveProvider(auth, fake, root_name="Spartiti")    # another folder name: another library
    b, sb = device(tmp_path, "B", other)
    (b / "x.chs").write_text("x", encoding="utf-8")
    sb.sync()
    spartiti = next(i for i, it in fake.items.items() if it["name"] == "Spartiti")
    assert [it["name"] for it in fake.items.values() if it["parents"] == [spartiti]] == ["x.chs"]
    assert G.clean_folder_name("  Musica / Lead   sheet ") == "Musica Lead sheet"
    assert G.clean_folder_name("  ") == "Modern Sheet"


def test_web_manifest_names_the_app():
    """`flet run --ios/--android` serves src/assets/manifest.json instead of Flet's own."""
    import json
    assets = Path(__file__).resolve().parent.parent / "src" / "assets"
    manifest = json.loads((assets / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == manifest["short_name"] == "Modern Sheet"
    assert manifest["description"]
    for icon in manifest["icons"]:
        assert (assets / icon["src"]).is_file()
    for name in ("apple-touch-icon-192", "icon-192", "icon-512", "icon-maskable-192", "icon-maskable-512"):
        assert (assets / "icons" / f"{name}.png").is_file()   # replace Flet's own web icons


def test_delete_song_with_its_musicxml_into_the_sync_trash(tmp_path):
    from modernsheet import library as L
    root = tmp_path / "lib"
    (root / "Jazz").mkdir(parents=True)
    (root / "xml").mkdir()
    song = root / "Jazz" / "s.chs"
    song.write_text("{title: S}\n{musicxml: s.musicxml}\n{musicxml: ../xml/shared.musicxml | 1-2}\n"
                    "{musicxml: gone.musicxml}\n{musicxml: ../../out.musicxml}\n", encoding="utf-8")
    for f in (root / "Jazz" / "s.musicxml", root / "xml" / "shared.musicxml", tmp_path / "out.musicxml"):
        f.write_text("<x/>", encoding="utf-8")
    other = root / "o.chs"
    other.write_text("{musicxml: xml/shared.musicxml}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        L.delete_plan(root / "Jazz" / "s.musicxml")
    plan = L.delete_plan(song, root)
    assert plan.files == [song, root / "Jazz" / "s.musicxml"]
    assert plan.kept == {root / "xml" / "shared.musicxml": [other],          # another song uses it
                         root / "Jazz" / "gone.musicxml": "missing",
                         tmp_path / "out.musicxml": "outside"}                # never outside the library
    trash = tmp_path / "trash"
    moved = L.delete_song(song, root, trash, today="2026-11-23")
    assert moved == [trash / "2026-11-23" / "Jazz" / "s.chs", trash / "2026-11-23" / "Jazz" / "s.musicxml"]
    assert not song.exists() and not (root / "Jazz" / "s.musicxml").exists()
    assert (root / "xml" / "shared.musicxml").exists() and (tmp_path / "out.musicxml").exists()
    assert [s.path.name for s in L.scan(root).walk()] == ["o.chs"]
    song.write_text("again", encoding="utf-8")                        # same name, same day: no overwrite
    assert [m.name for m in L.delete_song(song, root, trash, today="2026-11-23")] == ["s 2.chs"]
    other.write_text("{musicxml: xml/shared.musicxml}\n", encoding="utf-8")
    assert L.delete_song(other, root) == [] and not other.exists()    # no sync: gone for good…
    assert not (root / "xml" / "shared.musicxml").exists()            # …with its now unshared MusicXML


def test_deleted_song_leaves_the_other_devices(tmp_path):
    from modernsheet import library as L
    remote = MemoryProvider()
    a, sa = device(tmp_path, "A", remote)
    b, sb = device(tmp_path, "B", remote)
    (a / "s.chs").write_text("v1", encoding="utf-8")
    (a / "other.chs").write_text("o", encoding="utf-8")   # an emptied remote is a reset, not a deletion (0.18)
    sa.sync(); sb.sync()
    L.delete_song(a / "s.chs", a, tmp_path / "A-trash")              # the app's delete button on A
    assert sa.sync().deleted_remote == ["s.chs"] and "s.chs" not in remote.files
    sb.sync()
    assert not (b / "s.chs").exists() and list((tmp_path / "B-trash").rglob("s.chs"))
    assert list((tmp_path / "A-trash").rglob("s.chs"))


def test_created_and_modified_dates():
    from datetime import datetime
    from modernsheet import i18n, library as L
    from modernsheet.formats.v1 import parse_stamp
    assert parse_stamp("2026-11-23 12:49") == datetime(2026, 11, 23, 12, 49)
    assert parse_stamp("2026-11-23") == datetime(2026, 11, 23) and parse_stamp("2026-11-23T12:49:05") == datetime(2026, 11, 23, 12, 49, 5)
    assert parse_stamp("23/11/2026") is None and parse_stamp("2026-02-30") is None
    ok = parse("{title: X}\n{created: 2026-11-20 10:00}\n{modified: 2026-11-23}\n"
               "{start_of_verse}\n| [C] |\n{end_of_verse}\n")
    assert not ok.warnings and ok.meta["created"] == "2026-11-20 10:00"
    assert any("invalid date" in w for w in parse("{modified: ieri}\n{start_of_verse}\n| [C] |\n{end_of_verse}\n").warnings)

    now, then = datetime(2026, 11, 23, 12, 49, 7), datetime(2026, 11, 1, 8, 5, 30)
    src = "# comment\n{format: v1}\n{title: X}\n{key: C}\n\n{start_of_verse}\n| [C] |\n{end_of_verse}\n"
    once = L.stamp(src, now, created=then)
    assert once.split("\n")[:6] == ["# comment", "{format: v1}", "{title: X}", "{key: C}",
                                     "{created: 2026-11-01 08:05:30}", "{modified: 2026-11-23 12:49:07}"]
    later = L.stamp(once, datetime(2026, 12, 1, 9, 0, 1), created=now)       # in place, created kept
    assert later.count("\n") == once.count("\n") and "{created: 2026-11-01 08:05:30}" in later
    assert "{modified: 2026-12-01 09:00:01}" in later
    copy = L.stamp(later, datetime(2026, 12, 2, 7, 30), new_file=True)     # Save as: a new file
    assert "{created: 2026-12-02 07:30:00}" in copy and "{modified: 2026-12-02 07:30:00}" in copy
    bare = L.stamp("| [C] |\n", now)                                       # no header: at the top
    assert bare.startswith("{created: 2026-11-23 12:49:07}\n{modified: 2026-11-23 12:49:07}\n| [C] |")
    late = L.stamp("| [C] |\n{format: v1}\n", now)                       # never before {format}
    assert late.split("\n")[:3] == ["| [C] |", "{format: v1}", "{created: 2026-11-23 12:49:07}"]
    assert not parse(L.new_song_text("Nuovo", now)).warnings and "{created: 2026-11-23 12:49:07}" in L.new_song_text("N", now)

    def song(name, text, mtime):
        p = Path(tmp) / name
        p.write_text(text, encoding="utf-8")
        os.utime(p, (mtime, mtime))
        return p
    import os, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        a = song("a.chs", "{title: A}\n{created: 2026-01-05 10:00}\n{modified: 2026-03-01 10:00}\n", 1_700_000_000)
        b = song("b.chs", "{title: B}\n{created: 2025-12-01 10:00}\n{modified: 2026-02-01 10:00}\n", 1_700_000_000)
        c = song("c.chs", "{title: C}\n", datetime(2026, 4, 1).timestamp())   # never saved by the app
        idx = L.Index(Path(tmp) / "idx" / "i.json")
        songs = list(L.scan(Path(tmp), idx).walk())
        assert {s.title: s.created for s in songs} == {"A": "2026-01-05 10:00", "B": "2025-12-01 10:00", "C": ""}
        by = lambda key, desc=False: [s.title for s in L.sort_songs(songs, key, desc)]
        assert by("created") == ["B", "A", "C"] and by("created", True) == ["C", "A", "B"]   # C: file time
        assert next(x for x in songs if x.title == "C").created_at is not None
        assert by("modified") == ["B", "A", "C"] and by("modified", True) == ["C", "A", "B"]  # file time
        idx.save()
        again = L.Index(Path(tmp) / "idx" / "i.json")
        assert [s.created for s in L.scan(Path(tmp), again).walk()] == [s.created for s in songs] and again.hits == 3
        assert L.file_created(a) is not None
        # same title: the most recently created or saved first, whatever the order and direction
        song("d.chs", "{title: A}\n{created: 2026-02-01 10:00:00}\n{modified: 2026-05-01 10:00:00}\n", 1_700_000_000)
        songs = list(L.scan(Path(tmp)).walk())
        names = lambda key, desc=False: [s.path.name for s in L.sort_songs(songs, key, desc) if s.title == "A"]
        assert names("title") == names("title", True) == names("artist") == ["d.chs", "a.chs"]
    assert i18n.tr_date(now, "it") == "23 nov 2026" and i18n.tr_date(now, "en") == "Nov 23, 2026"
    assert i18n.tr_datetime(now, "it") == "23 nov 2026 12:49:07"


def test_same_title_songs_are_told_apart():
    import main
    from modernsheet.library import SongFile
    a = SongFile(Path("a.chs"), "X", created="2026-11-20 10:00:00", modified="2026-11-23 13:05:12")
    b = SongFile(Path("b.chs"), "x", created="2026-11-20 10:00:00", modified="2026-11-23 13:05:13")
    c = SongFile(Path("c.chs"), "Other", modified="2026-11-23 13:05:12")
    assert main.tell_apart([a, b, c]) == {Path("a.chs"): "modified", Path("b.chs"): "modified"}
    b.modified, b.created = a.modified, "2026-11-21 09:00:00"              # same save time, other day
    assert main.tell_apart([a, b])[Path("b.chs")] == "created"
    b.created = a.created                                                    # only the file differs
    assert main.tell_apart([a, b])[Path("a.chs")] == "file"


def test_sync_removes_folders_it_emptied(tmp_path):
    remote_dir = tmp_path / "remote"
    remote_dir.mkdir()
    a, sa = device(tmp_path, "A", S.FolderProvider(remote_dir))
    b, sb = device(tmp_path, "B", S.FolderProvider(remote_dir))
    (a / "Old" / "Sub").mkdir(parents=True)
    (a / "Old" / "Sub" / "x.chs").write_text("x", encoding="utf-8")
    (a / "Old" / "y.chs").write_text("y", encoding="utf-8")
    (a / "Keep").mkdir()
    (a / "Keep" / "k.chs").write_text("k", encoding="utf-8")
    sa.sync(); sb.sync()
    (b / "Old" / ".DS_Store").write_text("finder", encoding="utf-8")
    (a / "Old").rename(a / "New")                                       # a folder renamed on A
    r = sa.sync()
    assert sorted(r.removed_folders) == ["Old", "Old/Sub"] and not (remote_dir / "Old").exists()
    rb = sb.sync()
    assert not (b / "Old").exists() and (b / "New" / "Sub" / "x.chs").read_text() == "x"   # .DS_Store ignored
    assert sorted(rb.removed_folders) == ["Old", "Old/Sub"] and (b / "Keep").exists()
    (b / "Keep" / "notes.txt").write_text("mine", encoding="utf-8")     # a file the app does not sync…
    (b / "Keep" / "k.chs").unlink()
    sb.sync(); sa.sync()
    assert (b / "Keep").exists() and not (a / "Keep").exists()          # …keeps that folder; elsewhere it goes


def test_drive_removes_folders_it_emptied(tmp_path):
    fake = FakeDrive()
    auth = signed_in(tmp_path, fake)
    a, sa = device(tmp_path, "A", G.DriveProvider(auth, fake))
    (a / "Old").mkdir()
    (a / "Old" / "x.chs").write_text("x", encoding="utf-8")
    (a / "Pdf").mkdir()
    (a / "Pdf" / "y.chs").write_text("y", encoding="utf-8")
    sa.sync()
    pdf_folder = next(i for i, it in fake.items.items() if it["name"] == "Pdf")
    fake.add("print.pdf", pdf_folder, b"%PDF")                         # put on Drive by hand
    (a / "Old").rename(a / "New")
    (a / "Pdf" / "y.chs").unlink()
    r = sa.sync()
    live = {it["name"] for it in fake.items.values() if not it["trashed"]}
    assert "Old" not in live and "New" in live and "Pdf" in live and "print.pdf" in live
    assert r.removed_folders == ["Old"]
