"""Library synchronisation: a local folder (always used by the app, works offline) kept in step with
a remote copy through a Provider. Standard library only.

Local-first: the app reads and writes only the local folder. `sync()` compares, file by file,
    L  the local content now (hash),
    R  the remote revision now,
    B  the state of the last successful sync (manifest: hash and remote revision),
and copies whatever changed on one side only. When both sides changed, nothing is lost: the
remote version takes the file's name and the local one is kept next to it as a conflict copy
("Song (conflitto Mac 2026-11-23 10-15).chs"), which is then uploaded like any new file.
Files deleted on the other side are moved to a trash folder, not destroyed. Work done offline
needs no queue: at the next sync it is simply "changed since B".

Providers implement list / download / upload / delete on paths relative to the library root
("Jazz/Blues.chs", always with "/"). FolderProvider syncs with another folder (e.g. one inside
iCloud Drive or Google Drive for desktop); a Google Drive API provider will follow.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .i18n import tr

MANIFEST_VERSION = 1
SYNCED_EXTENSIONS = (".chs", ".musicxml", ".xml", ".mxl")


class RemoteChanged(Exception):
    """The remote file changed after it was listed: the next sync will handle it."""


class Offline(Exception):
    """The remote copy cannot be reached right now."""


class AuthRequired(Exception):
    """The remote needs the user to sign in again (e.g. revoked or expired account access)."""


@dataclass
class RemoteFile:
    rev: str                       # changes whenever the content changes
    available: bool = True         # False: exists but cannot be read now (e.g. iCloud placeholder)


class Provider(Protocol):
    def list(self) -> dict[str, RemoteFile]: ...
    def download(self, rel: str) -> bytes: ...
    def upload(self, rel: str, data: bytes, expected_rev: str | None) -> str: ...   # returns the new rev
    def delete(self, rel: str, expected_rev: str | None) -> None: ...


@dataclass
class Report:
    uploaded: list[str] = field(default_factory=list)
    downloaded: list[str] = field(default_factory=list)
    deleted_local: list[str] = field(default_factory=list)
    deleted_remote: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)      # names of the conflict copies made
    skipped: list[str] = field(default_factory=list)        # left for the next sync (busy or raced)
    errors: list[str] = field(default_factory=list)
    offline: bool = False
    auth_required: bool = False
    remote_reset: bool = False      # the remote was new or empty although files were synced before
    removed_folders: list[str] = field(default_factory=list)   # folders emptied by this sync and removed

    @property
    def changed_local(self) -> bool:
        return bool(self.downloaded or self.deleted_local or self.conflicts)


def is_synced(rel: str) -> bool:
    """Library files that are synced: songs and MusicXML, not hidden files or folders."""
    parts = rel.split("/")
    return not any(p.startswith(".") for p in parts) and rel.lower().endswith(SYNCED_EXTENSIONS)


def _hash(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def conflict_name(rel: str, device: str, when: float | None = None) -> str:
    """'Jazz/Blues.chs' -> 'Jazz/Blues (conflitto Mac 2026-11-23 10-15).chs'."""
    folder, _, name = rel.rpartition("/")
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    stamp = time.strftime("%Y-%m-%d %H-%M", time.localtime(when))
    new = f"{stem} ({tr('sync.conflict', device=device, when=stamp)})" + (f".{ext}" if ext else "")
    return f"{folder}/{new}" if folder else new


class Manifest:
    """State of the last successful sync, per file: content hash, remote revision, and the local
    modification time and size (to avoid re-hashing unchanged files). Saved as JSON."""

    def __init__(self, file: Path | None):
        self.file = file
        self.files: dict[str, dict] = {}
        self.last_sync: float | None = None
        if file:
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                if data.get("version") == MANIFEST_VERSION:
                    self.files = dict(data.get("files", {}))
                    self.last_sync = data.get("last_sync")
            except (OSError, ValueError, AttributeError):
                pass

    def save(self) -> None:
        if not self.file:
            return
        data = {"version": MANIFEST_VERSION, "last_sync": self.last_sync, "files": self.files}
        _write_atomic(self.file, json.dumps(data, ensure_ascii=False).encode("utf-8"))


class Syncer:
    def __init__(self, local: Path, provider: Provider, manifest: Manifest, trash: Path | None = None,
                 device: str = "", clock=time.time):
        self.local = Path(local)
        self.provider = provider
        self.manifest = manifest
        self.trash = trash
        self.device = device or tr("sync.this_device")
        self.clock = clock

    # ---- local side
    def local_files(self) -> dict[str, str]:
        """rel -> content hash of the synced local files (hash reused while mtime and size match)."""
        out: dict[str, str] = {}
        for dirpath, dirnames, filenames in os.walk(self.local):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                path = Path(dirpath) / name
                rel = path.relative_to(self.local).as_posix()
                if not is_synced(rel):
                    continue
                try:
                    st = path.stat()
                    e = self.manifest.files.get(rel)
                    if e and e.get("mtime_ns") == st.st_mtime_ns and e.get("size") == st.st_size:
                        out[rel] = e["hash"]
                    else:
                        out[rel] = _hash(path.read_bytes())
                except OSError:
                    continue
        return out

    def _record(self, rel: str, digest: str, rev: str) -> None:
        st = (self.local / rel).stat()
        self.manifest.files[rel] = {"hash": digest, "rev": rev, "mtime_ns": st.st_mtime_ns, "size": st.st_size}

    def _to_trash(self, rel: str) -> None:
        src = self.local / rel
        if self.trash:
            dest = self.trash / time.strftime("%Y-%m-%d", time.localtime(self.clock())) / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                dest = dest.with_name(f"{dest.stem} {int(self.clock())}{dest.suffix}")
            shutil.move(str(src), dest)
        else:
            src.unlink()

    # ---- one file
    def _download(self, rel: str, rev: str, report: Report) -> None:
        data = self.provider.download(rel)
        _write_atomic(self.local / rel, data)
        self._record(rel, _hash(data), rev)
        report.downloaded.append(rel)

    def _upload(self, rel: str, expected: str | None, report: Report) -> None:
        data = (self.local / rel).read_bytes()
        rev = self.provider.upload(rel, data, expected)
        self._record(rel, _hash(data), rev)
        report.uploaded.append(rel)

    def _conflict(self, rel: str, remote: RemoteFile, report: Report) -> None:
        """Both sides changed: if the contents differ, the local version moves to a conflict copy
        (uploaded as a new file) and the remote one takes the name."""
        data = self.provider.download(rel)
        local = (self.local / rel).read_bytes()
        if _hash(data) == _hash(local):
            self._record(rel, _hash(data), remote.rev)
            return
        copy = conflict_name(rel, self.device, self.clock())
        _write_atomic(self.local / copy, local)
        _write_atomic(self.local / rel, data)
        self._record(rel, _hash(data), remote.rev)
        report.conflicts.append(copy)
        self._upload(copy, None, report)

    def _one(self, rel: str, L: str | None, R: RemoteFile | None, report: Report) -> None:
        """Decide one file by three-way comparison: L = local content hash, R = remote file (revision),
        B = both as they were at the last sync (manifest). Only the side that changed since B wins;
        a deletion is just a change to "nothing".

        Safety rules, all from real failure cases of sync tools:
        - a file that is listed remotely but cannot be downloaded now (an iCloud placeholder not yet
          on the disk, a Drive file being processed) is never taken as deleted;
        - when both sides changed, nothing is lost: an edit beats a deletion on either side, and two
          different edits keep both versions (the remote one under a "conflict" name);
        - local deletions decided here go to the app's trash, not away (_to_trash)."""
        B = self.manifest.files.get(rel)
        if R is not None and not R.available:
            # present remotely but not downloadable now: never a deletion; unchanged if we know it
            if B is None or L != B["hash"]:
                report.skipped.append(rel)               # decide when the content can be read
                return
            R = RemoteFile(B["rev"])
        if B is None:
            if L and R:
                self._conflict(rel, R, report)           # new on both sides
            elif L:
                self._upload(rel, None, report)
            elif R:
                self._download(rel, R.rev, report)
            return
        local_changed = L != B["hash"]
        remote_changed = (R.rev if R else None) != B["rev"]
        if not local_changed and not remote_changed:
            if L is None and R is None:
                self.manifest.files.pop(rel, None)
            return
        if local_changed and not remote_changed:
            if L is None:
                if R:
                    self.provider.delete(rel, R.rev)
                    report.deleted_remote.append(rel)
                self.manifest.files.pop(rel, None)
            else:
                self._upload(rel, R.rev if R else None, report)
        elif remote_changed and not local_changed:
            if R is None:
                if L:
                    self._to_trash(rel)
                    report.deleted_local.append(rel)
                self.manifest.files.pop(rel, None)
            else:
                self._download(rel, R.rev, report)
        else:                                             # both changed
            if L is None and R is None:
                self.manifest.files.pop(rel, None)
            elif L is None:
                self._download(rel, R.rev, report)        # deleted here, edited there: keep the edit
            elif R is None:
                self._upload(rel, None, report)           # edited here, deleted there: keep the edit
            else:
                self._conflict(rel, R, report)

    # ---- whole library
    def sync(self, busy: set[str] = frozenset()) -> Report:
        """One synchronisation. `busy`: files not to touch now (e.g. open with unsaved changes in
        the editor); they are handled by a later sync. Offline: nothing changes, report.offline."""
        report = Report()
        try:
            remote = self.provider.list()
        except AuthRequired as err:
            report.auth_required = True
            report.errors.append(str(err))
            return report
        except (Offline, OSError) as err:
            report.offline = True
            report.errors.append(str(err))
            return report
        fresh = getattr(self.provider, "fresh", False)
        if fresh:
            self.provider.fresh = False                  # a signal for this sync only
        if self.manifest.files and (fresh or not remote):
            # The remote copy is new (e.g. its folder was renamed or deleted and created again) or
            # empty, but files were synced with it: that is not "delete everything here". Start over
            # as with a new remote, so the local files are uploaded again and nothing goes to the trash.
            self.manifest.files = {}
            report.remote_reset = True
        local = self.local_files()
        for rel in sorted(set(local) | set(remote) | set(self.manifest.files)):
            if not is_synced(rel):
                continue
            if rel in busy:
                report.skipped.append(rel)
                continue
            try:
                self._one(rel, local.get(rel), remote.get(rel), report)
            except RemoteChanged:
                # uploads and deletions say which remote revision they expect: another device changed
                # the file after our listing, so we must not overwrite it; the next sync decides again
                report.skipped.append(rel)
            except AuthRequired as err:
                report.auth_required = True
                report.errors.append(str(err))
                break
            except (Offline, ConnectionError) as err:
                report.offline = True
                report.errors.append(str(err))
                break
            except OSError as err:
                report.errors.append(f"{rel}: {err}")
        if not report.offline:
            self.manifest.last_sync = self.clock()
            self._remove_emptied(report)
        self.manifest.save()
        return report

    def _remove_emptied(self, report: Report) -> None:
        """Folders that this sync emptied (e.g. a folder renamed or emptied on one device) go away on
        both sides instead of lingering empty: here for files deleted from the remote, there for files
        deleted here. Only really empty folders (a Finder .DS_Store aside), deepest first."""
        for rel in _parent_folders(report.deleted_local):
            if remove_empty_dir(self.local / rel):
                report.removed_folders.append(rel)
        remove = getattr(self.provider, "remove_empty_folder", None)
        if remove:
            for rel in _parent_folders(report.deleted_remote):
                try:
                    if remove(rel):
                        report.removed_folders.append(rel)
                except (RemoteChanged, OSError, ConnectionError) as err:
                    report.errors.append(f"{rel}/: {err}")


def _parent_folders(rels: list[str]) -> list[str]:
    """Every folder containing one of the files (and their parents), deepest first; never the root."""
    out: set[str] = set()
    for rel in rels:
        parts = rel.split("/")[:-1]
        for i in range(len(parts), 0, -1):
            out.add("/".join(parts[:i]))
    return sorted(out, key=lambda r: (-r.count("/"), r))


def remove_empty_dir(path: Path) -> bool:
    """Remove `path` if it holds nothing but a Finder .DS_Store; anything else (a song, an iCloud
    placeholder, a file the app does not sync) keeps it."""
    try:
        entries = list(path.iterdir())
    except OSError:
        return False
    if any(e.name != ".DS_Store" for e in entries):
        return False
    try:
        for e in entries:
            e.unlink()
        path.rmdir()
    except OSError:
        return False
    return True


ICLOUD_PLACEHOLDER = re.compile(r"^\.(.+)\.icloud$")


class FolderProvider:
    """The remote copy is another folder: typically one synced by iCloud Drive, Google Drive for
    desktop or Dropbox, which then carry the files to the other devices. Revisions are the file's
    modification time and size. A missing folder (e.g. an unmounted drive) counts as offline.
    iCloud on older macOS replaces files evicted from the disk with hidden placeholders
    ".Name.chs.icloud": they are listed as unavailable (never as deleted) and their download is
    requested, so a later sync can read them."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def _rev(self, path: Path) -> str:
        st = path.stat()
        return f"{st.st_mtime_ns}-{st.st_size}"

    def list(self) -> dict[str, RemoteFile]:
        if not self.root.is_dir():
            raise Offline(tr("sync.folder_missing", path=self.root))
        out = {}
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                path = Path(dirpath) / name
                m = ICLOUD_PLACEHOLDER.match(name)
                if m:
                    rel = (path.parent / m.group(1)).relative_to(self.root).as_posix()
                    if is_synced(rel) and rel not in out:
                        out[rel] = RemoteFile("", available=False)
                        self._request_download(path)
                    continue
                rel = path.relative_to(self.root).as_posix()
                if is_synced(rel):
                    try:
                        out[rel] = RemoteFile(self._rev(path))
                    except OSError:
                        pass
        return out

    @staticmethod
    def _request_download(placeholder: Path) -> None:
        """Ask iCloud to bring an evicted file back (macOS `brctl`); harmless if not available."""
        import subprocess
        try:
            subprocess.Popen(["brctl", "download", str(placeholder)], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except OSError:
            pass

    def download(self, rel: str) -> bytes:
        return (self.root / rel).read_bytes()

    def _check(self, rel: str, expected: str | None) -> None:
        path = self.root / rel
        current = self._rev(path) if path.exists() else None
        if current != expected:
            raise RemoteChanged(rel)

    def upload(self, rel: str, data: bytes, expected_rev: str | None) -> str:
        self._check(rel, expected_rev)
        _write_atomic(self.root / rel, data)
        return self._rev(self.root / rel)

    def delete(self, rel: str, expected_rev: str | None) -> None:
        self._check(rel, expected_rev)
        (self.root / rel).unlink()

    def remove_empty_folder(self, rel: str) -> bool:
        return bool(rel) and remove_empty_dir(self.root / rel)


def state_dir(data_dir: Path, remote_id: str) -> Path:
    """Folder of the app's data that holds, for one remote: the local copy (library/), the manifest
    and the trash. One per remote, so switching remotes never mixes files."""
    digest = hashlib.sha1(remote_id.encode("utf-8")).hexdigest()[:16]
    return Path(data_dir) / "sync" / digest
