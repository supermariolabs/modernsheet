"""Song library: a folder of .chs sources (with subfolders) for the app's browser and editor.

Standard library only, no Flet: the app builds its views on top of these helpers.
The header of every song (title, artist, key, time, tempo, tags, format) is kept in an index file,
so a folder is re-read only for the files that changed since the last scan (see Index).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import tempfile
import time
import unicodedata
import zipfile
from datetime import datetime
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .formats import FORMAT_LINE_RE, VALUE_RE
from .formats.v1 import add_tags, escape_line, format_stamp, parse_stamp, unescape
from .i18n import tr
from .parser import CURRENT, DIRECTIVE_LINE_RE, split_directive
from .theory import KEY_RE, PITCH

EXT = ".chs"
LINE_RE = re.compile(r"^line (\d+):")
INDEX_VERSION = 4                   # bump when the index layout or what is read from the songs changes
SORT_KEYS = ("title", "artist", "key", "tempo", "modified", "created")


@dataclass
class SongFile:
    path: Path
    title: str                      # {title: …} or, if missing, the file name
    artist: str = ""                # {artist: …} or {composer: …}
    key: str = ""                   # first {key: …}
    time: str = ""                  # first {time: …}
    tempo: str = ""                 # {tempo: …}
    tags: list[str] = field(default_factory=list)
    format: int = 1
    mtime: float = 0.0              # modification time of the file (seconds)
    ctime: float = 0.0              # creation time of the file (see file_created; seconds)
    created: str = ""               # {created: YYYY-MM-DD HH:MM}, written by the app
    modified: str = ""              # {modified: …}, written by the app at every save

    @property
    def modified_at(self) -> datetime | None:
        """Last save: {modified}, or the file's modification time for songs never saved by the app."""
        return parse_stamp(self.modified) or (datetime.fromtimestamp(self.mtime) if self.mtime else None)

    @property
    def created_at(self) -> datetime | None:
        """Creation: {created}, or the file's creation time for songs never saved by the app."""
        return parse_stamp(self.created) or (datetime.fromtimestamp(self.ctime) if self.ctime else None)

    @property
    def latest(self) -> datetime:
        """The most recent of creation and last save (to put the newest of same-title songs first)."""
        return max((d for d in (self.created_at, self.modified_at) if d), default=datetime.min)


@dataclass
class Folder:
    path: Path
    folders: list["Folder"] = field(default_factory=list)
    songs: list[SongFile] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.path.name

    def count(self) -> int:
        """Number of songs in this folder and all its subfolders."""
        return len(self.songs) + sum(f.count() for f in self.folders)

    def walk(self):
        """All songs, depth first."""
        yield from self.songs
        for f in self.folders:
            yield from f.walk()

    def find(self, path: Path) -> "Folder | None":
        """The folder (this one or a descendant) at `path`."""
        if self.path == path:
            return self
        for f in self.folders:
            if path.is_relative_to(f.path):
                return f.find(path)
        return None


def _key(s: str) -> str:
    return s.casefold()


def read_info(path: Path) -> SongFile:
    """Header of a song from its directives (no full parse): first title, artist (or composer), key,
    time and tempo; all the tags; the format. Without a title, the file name. Key and time count only
    before the first line of music, as for the parser: later ones are changes (a song without them
    in the header is in C, 4/4)."""
    info = SongFile(path, "")
    composer = ""
    music = False                         # a line of bars (or a MusicXML reference) has been seen
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        lines = []
    for line in lines:
        line = line.strip()
        f = FORMAT_LINE_RE.match(line)
        if f:
            v = VALUE_RE.fullmatch(f.group(1).strip())
            info.format = int(v.group(1)) if v and int(v.group(1)) >= 1 else 1
            continue
        m = DIRECTIVE_LINE_RE.match(escape_line(line))      # "\}" inside a value does not end it
        if not m:
            music = music or bool(line) and not line.startswith("#")
            continue
        name, value = split_directive(m.group(1))
        music = music or name == "musicxml"
        if name in ("key", "time") and music:
            continue
        if name == "tags":
            add_tags(info.tags, unescape(value))
        elif name == "composer" and not composer:
            composer = unescape(value)
        elif name in ("title", "artist", "key", "time", "tempo") and value and not getattr(info, name):
            setattr(info, name, unescape(value))                  # "\{demo\}" → "{demo}"
        elif name in ("created", "modified") and parse_stamp(value) and not getattr(info, name):
            setattr(info, name, value)
    info.artist = info.artist or composer
    info.title = info.title or path.stem.replace("_", " ")
    return info


def read_title(path: Path) -> str:
    """The song's {title: …}, or the file name."""
    return read_info(path).title


class Index:
    """Cache of the song headers of one library folder, in a JSON file (normally in the app's data
    folder, see index_path). An entry is valid while the file's modification time and size do not
    change. A missing, unreadable or outdated index is simply rebuilt."""

    def __init__(self, file: Path | None):
        self.file = file
        self.entries: dict[str, dict] = {}
        self.changed = False
        self.hits = self.misses = 0               # entries reused / files read in the last scan
        if file:
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                if data.get("version") == INDEX_VERSION and isinstance(data.get("files"), dict):
                    self.entries = data["files"]
            except (OSError, ValueError, AttributeError):
                pass

    def song(self, path: Path, rel: str) -> SongFile:
        try:
            st = path.stat()
        except OSError:
            return SongFile(path, path.stem.replace("_", " "))
        e = self.entries.get(rel)
        if e and e.get("mtime_ns") == st.st_mtime_ns and e.get("size") == st.st_size:
            try:
                self.hits += 1
                return SongFile(path=path, **e["info"])
            except TypeError:                      # entry from an incompatible layout
                pass
        self.misses += 1
        info = read_info(path)
        info.mtime = st.st_mtime
        info.ctime = _created_time(st)
        d = asdict(info)
        d.pop("path")
        self.entries[rel] = {"mtime_ns": st.st_mtime_ns, "size": st.st_size, "info": d}
        self.changed = True
        return info

    def keep_only(self, rels: set[str]) -> None:
        gone = set(self.entries) - rels
        for rel in gone:
            del self.entries[rel]
        self.changed |= bool(gone)

    def save(self) -> None:
        if not (self.file and self.changed):
            return
        try:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.file.with_suffix(".tmp")
            tmp.write_text(json.dumps({"version": INDEX_VERSION, "files": self.entries}, ensure_ascii=False),
                           encoding="utf-8")
            os.replace(tmp, self.file)
            self.changed = False
        except OSError:
            pass                                   # the index is only a cache


def index_path(data_dir: Path, root: Path) -> Path:
    """Index file for the library folder `root`, inside the app's data folder (one per library)."""
    digest = hashlib.sha1(str(Path(root).resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(data_dir) / "index" / f"{digest}.json"


def scan(root: Path, index: Index | None = None) -> Folder:
    """Scan `root` recursively for .chs files. Hidden files and folders are skipped; folders without
    songs are kept (a new folder is empty); entries are sorted case-insensitively, folders before songs.
    With an index, only new or changed files are read; the index is then saved."""
    root = Path(root)
    index = index or Index(None)
    index.hits = index.misses = 0
    seen: set[str] = set()
    folder = _scan(root, root, index, seen)
    index.keep_only(seen)
    index.save()
    return folder


def _scan(path: Path, root: Path, index: Index, seen: set[str]) -> Folder:
    folder = Folder(path)
    try:
        entries = sorted(path.iterdir(), key=lambda p: _key(p.name))
    except OSError:
        return folder
    for p in entries:
        if p.name.startswith("."):
            continue
        if p.is_dir():
            folder.folders.append(_scan(p, root, index, seen))
        elif p.suffix.lower() == EXT and p.is_file():
            rel = p.relative_to(root).as_posix()
            seen.add(rel)
            folder.songs.append(index.song(p, rel))
    return folder


def _fold(s: str) -> str:
    """Case- and accent-insensitive form for searching."""
    return "".join(c for c in unicodedata.normalize("NFD", s.casefold()) if not unicodedata.combining(c))


def _strip_ends(text: str) -> str:
    """Text from its first to its last letter or digit (quotes, brackets, punctuation around it ignored,
    as for the A–Z groups)."""
    return re.sub(r"^[^0-9a-z]+|[^0-9a-z]+$", "", text)


def _condition(cond: str):
    """One condition of a query → predicate on (folded title, folded haystack, folded tags):
    "abc*" title starts with abc, "*abc" title ends with abc, "*abc*" contains abc anywhere (title,
    artist, tags, path; spaces allowed); otherwise every word must occur (plain words) or be a tag (#word)."""
    lead, trail = cond.startswith("*"), cond.endswith("*")
    body = " ".join(cond.strip("*").split())
    if (lead or trail) and body:
        if lead and trail:
            return lambda title, hay, tags: body in hay
        part = _strip_ends(body) or body
        if trail:
            return lambda title, hay, tags: _strip_ends(title).startswith(part)
        return lambda title, hay, tags: _strip_ends(title).endswith(part)
    words = cond.split()
    tag_words = [w[1:] for w in words if w.startswith("#") and len(w) > 1]
    plain = [w for w in words if not w.startswith("#")]
    return lambda title, hay, tags: all(t in tags for t in tag_words) and all(w in hay for w in plain)


def parse_query(query: str) -> list[list]:
    """A search query → OR of ANDs of predicates: "a & b | c" = (a and b) or c ("&" binds tighter);
    spaces inside a plain condition also mean AND. Case and accents are ignored."""
    groups = []
    for alt in _fold(query).split("|"):
        conds = [_condition(c.strip()) for c in alt.split("&") if c.strip()]
        if conds:
            groups.append(conds)
    return groups


def search(folder: Folder, query: str) -> list[SongFile]:
    """Songs (in all subfolders) matching `query` (see parse_query and _condition); plain words look in
    the title, artist, tags and path relative to the folder, #word in the tags."""
    groups = parse_query(query)
    if not groups:
        return []
    out = []
    for s in folder.walk():
        title = _fold(s.title)
        tags = {_fold(t) for t in s.tags}
        hay = _fold(f"{s.title} {s.artist} {' '.join(s.tags)} {s.path.relative_to(folder.path).as_posix()}")
        if any(all(c(title, hay, tags) for c in conds) for conds in groups):
            out.append(s)
    return out


def _key_order(key: str) -> tuple:
    m = KEY_RE.match(key.strip())
    return (PITCH[m.group(1)], bool(m.group(2))) if m else (99, False)


def _tempo(t: str) -> int:
    m = re.match(r"\s*(\d+)", t)
    return int(m.group(1)) if m else -1


def sort_songs(songs: list[SongFile], by: str = "title", descending: bool = False) -> list[SongFile]:
    """Songs sorted by title, artist, key (C, C#/Db … B, major before minor), tempo (BPM), last save
    ({modified}, else the file time) or creation ({created}, else the file time). Songs without that
    information always come last; ties go by title and, for the same title, the most recently created or
    saved comes first (whatever the direction)."""
    if by not in SORT_KEYS:
        by = "title"
    value = {
        "title": lambda s: _fold(s.title),
        "artist": lambda s: _fold(s.artist),
        "key": lambda s: _key_order(s.key),
        "tempo": lambda s: _tempo(s.tempo),
        "modified": lambda s: s.modified_at,
        "created": lambda s: s.created_at,
    }[by]
    missing = {"artist": lambda s: not s.artist, "key": lambda s: _key_order(s.key)[0] == 99,
               "tempo": lambda s: _tempo(s.tempo) < 0, "modified": lambda s: s.modified_at is None,
               "created": lambda s: s.created_at is None}.get(by, lambda s: False)
    newest_first = sorted(songs, key=lambda s: s.latest, reverse=True)
    by_title = sorted(newest_first, key=lambda s: _fold(s.title))         # stable: same title → newest first
    present = sorted((s for s in by_title if not missing(s)), key=value, reverse=descending)
    return present + [s for s in by_title if missing(s)]


GROUPED_SORTS = {"title": "title", "artist": "artist"}   # sort key → field whose initial groups the songs


def index_letter(text: str) -> str:
    """Initial for the A–Z groups: the first letter A–Z of the text, case and accents ignored
    ("(Out here) on my own" → O, "È la luna" → E, "50 special" → S); "#" if it has none."""
    for ch in _fold(text).upper():
        if "A" <= ch <= "Z":
            return ch
    return "#"


def group_by_letter(songs: list[SongFile], field: str = "title", descending: bool = False) -> list[tuple[str, list[SongFile]]]:
    """Songs (already sorted) in A–Z groups by the initial of `field`; each group keeps the songs' order.
    Groups go A→Z (Z→A when descending), "#" (no letter, e.g. no artist) always last."""
    groups: dict[str, list[SongFile]] = {}
    for s in songs:
        groups.setdefault(index_letter(getattr(s, field) or ""), []).append(s)
    letters = sorted((k for k in groups if k != "#"), reverse=descending) + (["#"] if "#" in groups else [])
    return [(k, groups[k]) for k in letters]


def safe_filename(name: str) -> str:
    """A file name (without extension) from a song title: no path separators or control characters."""
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or tr("new_song")


def store_mode(platform: str, environ=None) -> bool:
    """True where the app is isolated in a sandbox (SPEC §8.6, "store mode"): iPad/iPhone, Android, and a
    Mac App Store build (macOS sets APP_SANDBOX_CONTAINER_ID in a sandboxed process). There a folder chosen
    by the user stays readable only while the app runs, so the library lives inside the app and files go
    in and out through the system dialogs (import, save, share) instead of folders kept in the settings."""
    environ = os.environ if environ is None else environ
    return platform in ("ios", "android", "android_tv") or (
        platform == "macos" and bool(environ.get("APP_SANDBOX_CONTAINER_ID")))


def move_library(old: Path, new: Path) -> bool:
    """Move a library folder to a new place when the new one does not exist yet (iOS: from the hidden app
    data to the Documents folder that the Files app shows); True if moved."""
    if not old.is_dir() or new.exists():
        return False
    new.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old), str(new))
    return True


def new_song_path(folder: Path, title: str) -> Path:
    """A path for a new song in `folder` that does not overwrite an existing file."""
    base = safe_filename(title)
    path = folder / f"{base}{EXT}"
    n = 2
    while path.exists():
        path = folder / f"{base} {n}{EXT}"
        n += 1
    return path


@dataclass
class DeletePlan:
    """What deleting a song removes: the .chs and the MusicXML files it references (`files`), except the
    referenced files that stay (`kept`: file → reason, "missing" / "outside" / the other songs using it)."""
    song: Path
    files: list[Path]
    kept: dict[Path, list[Path] | str] = field(default_factory=dict)


def _songs_under(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.lower().endswith(EXT) and not name.startswith("."):
                yield Path(dirpath) / name


def delete_plan(path: Path, root: Path | None = None) -> DeletePlan:
    """The files `delete_song` would remove. The references are read from the saved song. A referenced
    MusicXML stays if it does not exist, lies outside the library (`root`, or the song's folder without
    one), or another song of the library references it too."""
    if path.suffix.lower() != EXT:
        raise ValueError(f"not a {EXT} file: {path}")
    root = root if root and path.is_relative_to(root) else path.parent
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    plan = DeletePlan(path, [path])
    wanted: dict[Path, Path] = {}                         # resolved → as shown (song folder / ref)
    for ref in musicxml_refs(text):
        file = Path(os.path.normpath(path.parent / ref))
        if not file.is_file():
            plan.kept[file] = "missing"
        elif not file.resolve().is_relative_to(root.resolve()):
            plan.kept[file] = "outside"
        else:
            wanted.setdefault(file.resolve(), file)
    if wanted:
        for other in _songs_under(root):
            if other.resolve() == path.resolve():
                continue
            try:
                refs = musicxml_refs(other.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
            for ref in refs:
                shown = wanted.get((other.parent / ref).resolve())
                if shown is not None:
                    users = plan.kept.setdefault(shown, [])
                    if other not in users:
                        users.append(other)
    plan.files += [f for f in wanted.values() if f not in plan.kept]
    return plan


def merge_into(src: Path, dest: Path, keep=lambda rel: True) -> list[str]:
    """Copy the files of library `src` into library `dest` at the same relative paths, only those that
    `dest` does not have yet (and that `keep(rel)` accepts); returns the copied relative paths."""
    added = []
    for f in sorted(src.rglob("*")):
        rel = f.relative_to(src).as_posix()
        target = dest / rel
        if f.is_file() and keep(rel) and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            added.append(rel)
    return added


def delete_song(path: Path, root: Path | None = None, trash: Path | None = None,
                today: str | None = None) -> list[Path]:
    """Delete a song: the .chs and the MusicXML files only it references (see `delete_plan`).

    With `trash` (the sync trash of a synced library) every file is moved to `trash/<date>/<path in root>`,
    like the files the sync deletes, and those paths are returned; otherwise the files are deleted for
    good and [] is returned. The next sync carries the deletion to the remote, into its trash (SPEC §8.3b)."""
    plan = delete_plan(path, root)
    base = root if root and path.is_relative_to(root) else path.parent
    moved: list[Path] = []
    for file in plan.files:
        if trash is None:
            file.unlink()
            continue
        rel = file.relative_to(base) if file.is_relative_to(base) else Path(file.name)
        dest = trash / (today or time.strftime("%Y-%m-%d")) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        n = 2
        while dest.exists():
            dest = dest.with_name(f"{file.stem} {n}{file.suffix}")
            n += 1
        shutil.move(str(file), dest)
        moved.append(dest)
    return moved


def new_folder_path(parent: Path, name: str) -> Path:
    """A path for a new subfolder of `parent` that does not clash with an existing file or folder.
    The name is cleaned like a song file name and may not start with a dot (hidden folders are skipped)."""
    base = safe_filename(name).lstrip(".") if name.strip(" .") else ""
    base = base or tr("new_folder")
    path = parent / base
    n = 2
    while path.exists():
        path = parent / f"{base} {n}"
        n += 1
    return path


def clean_folder_name(name: str) -> str:
    """A folder name as typed → a valid one (cleaned like a song file name, not hidden); "" if blank."""
    return safe_filename(name).lstrip(".") if name.strip(" .") else ""


def outside_refs(root: Path, folder: Path) -> list[tuple[Path, str]]:
    """(song, reference) for the songs outside `folder` (anywhere under `root`) that cite a MusicXML
    file inside it: renaming or moving the folder would break them."""
    out = []
    folder = Path(os.path.normpath(folder))
    for song in _songs_under(root):
        if song.is_relative_to(folder):
            continue
        try:
            refs = musicxml_refs(song.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        out += [(song, ref) for ref in refs if Path(os.path.normpath(song.parent / ref)).is_relative_to(folder)]
    return out


@dataclass
class RenameResult:
    path: Path                      # the folder's new path
    updated: list[Path]             # songs elsewhere whose MusicXML references were rewritten


def rename_folder(folder: Path, new_name: str, root: Path) -> RenameResult:
    """Rename a subfolder of the library. The name is cleaned (clean_folder_name); a blank name, the
    library's main folder or a name already used next to it raise ValueError. A change of case only
    ("jazz" → "Jazz") goes through a temporary name, for case-insensitive disks. MusicXML references
    of songs in other folders that point inside it are rewritten to the new path."""
    folder, root = Path(os.path.normpath(folder)), Path(os.path.normpath(root))
    if folder == root or not folder.is_relative_to(root):
        raise ValueError("the main folder of the library cannot be renamed")
    name = clean_folder_name(new_name)
    if not name:
        raise ValueError("empty name")
    new = folder.parent / name
    if new == folder:
        return RenameResult(folder, [])
    same_folder = new.exists() and os.path.samefile(new, folder)     # a different case only
    if new.exists() and not same_folder:
        raise ValueError(f"'{name}' already exists")
    refs = outside_refs(root, folder)
    if same_folder:
        # only the case changes (jazz → Jazz): on macOS and Windows disks, which ignore case, a direct
        # rename may do nothing; going through a temporary (hidden) name always works
        tmp = folder.with_name(f".rename-{os.getpid()}-{name}")
        folder.rename(tmp)
        tmp.rename(new)
    else:
        folder.rename(new)
    by_song: dict[Path, dict[str, str]] = {}
    for song, ref in refs:
        target = new / Path(os.path.normpath(song.parent / ref)).relative_to(folder)
        by_song.setdefault(song, {})[ref] = Path(os.path.relpath(target, song.parent)).as_posix()
    updated = []
    for song, mapping in by_song.items():
        lines = song.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            m = DIRECTIVE_LINE_RE.match(line.strip())
            if not m:
                continue
            d_name, value = split_directive(m.group(1))
            file, bar, opts = value.partition("|")
            if d_name == "musicxml" and file.strip() in mapping:
                indent = line[:len(line) - len(line.lstrip())]
                lines[i] = f"{indent}{{musicxml: {mapping[file.strip()]}{' |' + opts if bar else ''}}}"
        song.write_text("\n".join(lines), encoding="utf-8")
        updated.append(song)
    return RenameResult(new, updated)


@dataclass
class ImportResult:
    path: Path                      # the imported song in the library
    copied: list[str]               # MusicXML files copied next to it
    missing: list[str]              # references that could not be copied (file not found / not available)


def import_song(dest: Path, name: str, text: str, src_dir: Path | None = None) -> ImportResult:
    """Import a .chs into the library folder `dest`, never overwriting: the song gets a free file name
    ("Name 2.chs"…) and the MusicXML files it cites (read from `src_dir`, the original's folder) are
    copied next to it; references are rewritten to the copies' names (a "../shared/x.musicxml" becomes
    "x.musicxml", so nothing lands outside the library). A file of the same name and content is reused;
    a different one gets a free name. Without `src_dir` (e.g. a file picked on a phone) references are
    kept as written and reported missing."""
    stem = Path(name).stem if name.lower().endswith(EXT) else name
    path = new_song_path(dest, stem)
    mapping, copied, missing = {}, [], []
    for ref in musicxml_refs(text):
        src = Path(os.path.normpath(src_dir / ref)) if src_dir else None
        if src is None or not src.is_file():
            missing.append(ref)
            continue
        data = src.read_bytes()
        target = dest / src.name
        n = 2
        while target.exists() and target.read_bytes() != data:
            target = dest / f"{src.stem} {n}{src.suffix}"
            n += 1
        if not target.exists():
            target.write_bytes(data)
            copied.append(target.name)
        mapping[ref] = target.name
    path.write_text(rewrite_musicxml_refs(text, mapping), encoding="utf-8")
    return ImportResult(path, copied, missing)


def rewrite_musicxml_refs(text: str, mapping: dict[str, str]) -> str:
    """The source with its {musicxml: …} references renamed as in `mapping` (bar ranges kept)."""
    if not mapping:
        return text
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = DIRECTIVE_LINE_RE.match(line.strip())
        if not m:
            continue
        d_name, value = split_directive(m.group(1))
        file, bar, opts = value.partition("|")
        if d_name == "musicxml" and file.strip() in mapping and mapping[file.strip()] != file.strip():
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f"{indent}{{musicxml: {mapping[file.strip()]}{' |' + opts if bar else ''}}}"
    return "\n".join(lines)


# ---- .zip archives (SPEC §8.6): a song with its MusicXML files, or the whole library, in one file that
# goes in and out of the app through the system dialogs (iPad/Android have no shared folders)
LIBRARY_EXTENSIONS = (".chs", ".musicxml", ".xml", ".mxl")     # files of a library (as synced, sync.py)
ZIP_MAX_FILES = 5000
ZIP_MAX_BYTES = 200 * 1024 * 1024          # uncompressed: a "zip bomb" is refused before anything is written


def song_zip(text: str, name: str, base_dir: Path | None) -> bytes:
    """A song as a .zip: the source (as `name`.chs) and the MusicXML files it cites, read from `base_dir`,
    side by side at the top of the archive (a "../shared/x.musicxml" is stored as "x.musicxml" and the
    reference rewritten, so the archive opens anywhere). Missing files are left out."""
    files: dict[str, bytes] = {}
    mapping: dict[str, str] = {}
    for ref in musicxml_refs(text):
        src = Path(os.path.normpath(base_dir / ref)) if base_dir else None
        if src is None or not src.is_file():
            continue
        data, target, n = src.read_bytes(), src.name, 2
        while target in files and files[target] != data:
            target = f"{src.stem} {n}{src.suffix}"
            n += 1
        files[target], mapping[ref] = data, target
    stem = Path(name).stem if name.lower().endswith(EXT) else name
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(safe_filename(stem) + EXT, rewrite_musicxml_refs(text, mapping).encode("utf-8"))
        for target, data in files.items():
            z.writestr(target, data)
    return buf.getvalue()


def library_files(root: Path) -> list[str]:
    """Paths (relative, with "/") of the library's songs and MusicXML files, hidden ones excluded."""
    out = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and rel.lower().endswith(LIBRARY_EXTENSIONS) and not any(
                part.startswith(".") for part in rel.split("/")):
            out.append(rel)
    return out


def library_zip(root: Path) -> bytes:
    """The whole library as a .zip (folders kept): a backup, or a way to move it to another device."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in library_files(root):
            z.write(root / rel, rel)
    return buf.getvalue()


@dataclass
class ZipImport:
    songs: list[Path]                # the songs written into the library
    folder: Path | None              # an archive of several songs: the new folder that holds them
    copied: list[str] = field(default_factory=list)    # one song: MusicXML files copied next to it
    missing: list[str] = field(default_factory=list)   # one song: references not found in the archive
    skipped: int = 0                 # entries left out (other file types, hidden, unsafe paths)


class BadZip(Exception):
    """Not a usable archive: unreadable, too big, or without songs."""


def _zip_members(z: zipfile.ZipFile) -> tuple[list[tuple[zipfile.ZipInfo, str]], int]:
    """The archive's library files with safe relative paths, and how many entries were skipped.
    Unsafe names (absolute, "..", drive letters), hidden files, macOS "__MACOSX" metadata and other
    file types are left out; a single folder around everything (as made by Finder) is removed."""
    keep, skipped = [], 0
    for info in z.infolist():
        if info.is_dir():
            continue
        parts = [p for p in info.filename.replace("\\", "/").split("/") if p not in ("", ".")]
        if (not parts or info.filename.startswith(("/", "\\")) or ":" in parts[0] or ".." in parts
                or parts[0] == "__MACOSX" or any(p.startswith(".") for p in parts)
                or not parts[-1].lower().endswith(LIBRARY_EXTENSIONS)):
            skipped += 1
            continue
        keep.append((info, "/".join(parts)))
    tops = {rel.split("/")[0] for _, rel in keep}
    if len(tops) == 1 and all("/" in rel for _, rel in keep):
        keep = [(info, rel.split("/", 1)[1]) for info, rel in keep]
    return keep, skipped


def import_zip(dest: Path, data: bytes, name: str = "") -> ZipImport:
    """Import a .zip into the library folder `dest`, never overwriting. One song: like import_song (free
    name, its MusicXML from the archive copied next to it). Several songs (e.g. an exported library): a
    new folder named after the archive, with the archive's folders inside. Raises BadZip."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as err:
        raise BadZip(str(err)) from err
    with z:
        members, skipped = _zip_members(z)
        if len(members) > ZIP_MAX_FILES or sum(i.file_size for i, _ in members) > ZIP_MAX_BYTES:
            raise BadZip("too big")
        songs = [rel for _, rel in members if rel.lower().endswith(EXT)]
        if not songs:
            raise BadZip("no songs")
        if len(songs) == 1:
            with tempfile.TemporaryDirectory() as tmp:
                for info, rel in members:
                    target = Path(tmp) / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(z.read(info))
                src = Path(tmp) / songs[0]
                text = src.read_text(encoding="utf-8", errors="replace")
                r = import_song(dest, src.name, text, src.parent)
            return ZipImport([r.path], None, r.copied, r.missing, skipped)
        folder = new_folder_path(dest, Path(name).stem if name else "")
        written = []
        for info, rel in members:
            target = folder / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))
            if rel.lower().endswith(EXT):
                written.append(target)
        return ZipImport(written, folder, skipped=skipped)


def file_created(path: Path) -> datetime | None:
    """Best guess of when a song without {created} was made: the file's creation time where the system
    keeps one (macOS, Windows), else its modification time; the earlier of the two."""
    try:
        return datetime.fromtimestamp(_created_time(path.stat()))
    except OSError:
        return None


def _created_time(st: os.stat_result) -> float:
    return min(getattr(st, "st_birthtime", st.st_mtime) or st.st_mtime, st.st_mtime)


HEADER_DIRECTIVES = {"format", "title", "subtitle", "artist", "composer", "key", "time", "tempo", "capo", "tags",
                     "bar_width", "label_colors", "section_colors", "bars_per_line", "created", "modified"}


def stamp(text: str, now: datetime, created: datetime | None = None, new_file: bool = False) -> str:
    """The source with {modified: now} and, if missing, {created: …} (`created`, else now). A new file
    (Save as) gets {created: now} even if the source had one. Existing lines are rewritten in place;
    missing ones go after the header directives at the top of the file (format, title, key…)."""
    lines = text.split("\n")
    want = {"created": format_stamp(now if new_file or created is None else created), "modified": format_stamp(now)}
    found: dict[str, int] = {}
    header_end = 0                        # lines [0, header_end) are the header directives
    in_header = True
    for i, line in enumerate(lines):
        m = DIRECTIVE_LINE_RE.match(line.strip())
        name = split_directive(m.group(1))[0] if m else None
        if in_header and name in HEADER_DIRECTIVES:
            header_end = i + 1
        elif in_header and (line.lstrip().startswith("#") or (not line.strip() and not header_end)):
            pass                          # comments, and blank lines before the first directive
        elif in_header:
            in_header = False
        if name in want and name not in found:
            found[name] = i
    if not header_end:                    # no header at the top: never before a {format} (first directive)
        fmt = next((i for i, line in enumerate(lines) if FORMAT_LINE_RE.match(line.strip())), None)
        header_end = fmt + 1 if fmt is not None else 0
    for name, i in found.items():
        if name == "modified" or new_file:
            lines[i] = f"{{{name}: {want[name]}}}"
    missing = [f"{{{n}: {want[n]}}}" for n in ("created", "modified") if n not in found]
    lines[header_end:header_end] = missing
    return "\n".join(lines)


def new_song_text(title: str, now: datetime | None = None) -> str:
    """Starting source for a new song."""
    when = format_stamp(now or datetime.now())
    return (f"{{format: v{CURRENT}}}\n{{title: {title}}}\n{{key: C}}\n{{time: 4/4}}\n"
            f"{{created: {when}}}\n{{modified: {when}}}\n\n"
            f"{{start_of_verse: {tr('section.verse')}}}\n| [C] | [F] | [G7] | [C] |\n{{end_of_verse}}\n")


def warning_line(warning: str) -> int | None:
    """Source line number of a parser warning ("line N: …"), if any."""
    m = LINE_RE.match(warning)
    return int(m.group(1)) if m else None


def line_offset(text: str, line: int) -> int:
    """Character offset of the start of 1-based `line` in `text` (clamped to the text)."""
    if line <= 1:
        return 0
    pos = 0
    for _ in range(line - 1):
        nl = text.find("\n", pos)
        if nl < 0:
            return len(text)
        pos = nl + 1
    return pos


def musicxml_refs(text: str) -> list[str]:
    """MusicXML files a .chs source refers to ({musicxml: file} or {musicxml: file | 3-4}), in order of
    first appearance, without duplicates; paths as written (relative to the .chs folder)."""
    out: list[str] = []
    for line in text.splitlines():
        m = DIRECTIVE_LINE_RE.match(line.strip())
        if not m:
            continue
        name, value = split_directive(m.group(1))
        file = value.partition("|")[0].strip()
        if name == "musicxml" and file and file not in out:
            out.append(file)
    return out


@dataclass
class Conversion:
    text: str                       # the source with the references converted
    count: int                      # references converted
    exact: bool                     # the song reads the same notes, chords and repeats as before


def _notated(song) -> list:
    """What a conversion must keep: per bar its notes, chords and repeat marks."""
    def sig(n):
        return (n.step, n.alter, n.octave, round(n.start, 6), round(n.dur, 6), n.type, n.dots, n.chord,
                n.tie_start, n.tie_stop, n.lyric, n.measure_rest, n.tuplet, n.tab_string)
    return [([sig(n) for n in b.notation.notes] if b.notation else None,
             [(e.chord, round(e.start, 6), round(e.dur, 6)) for e in b.events],
             (b.num, b.den, b.repeat_start, b.repeat_end, b.volta, b.volta_end)) for b in song.bars]


def convert_musicxml(text: str, ref: str, base_dir: Path, note: str = "") -> Conversion:
    """Write the bars of a MusicXML file as notes in the .chs (SPEC §2.12b): every `{musicxml: ref}`
    line (with or without a measure range) becomes a `{start_of_notes}` block (notes.to_notes_text,
    in the key in force at that line), with a `{time}` line where the file changes the time signature.
    The reference stays above the block as a comment (followed by `note`), as a trace; the MusicXML
    file is not touched. Raises OSError or SyntaxError if the file cannot be read."""
    from .formats.v1 import parse as parse_v1
    from .musicxml import measure_range, read_musicxml
    from .notes import to_notes_text
    measures, _ = read_musicxml((base_dir / ref).resolve())
    key, time_sig, out, count = "C", (4, 4), [], 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("#"):
            out.append(line)
            continue
        for k in re.findall(r"\{\s*key\s*:\s*([^}]*)\}", line):          # also inside a row of bars
            key = k.strip() if KEY_RE.match(k.strip()) else key
        for a, b in re.findall(r"\{\s*time\s*:\s*(\d+)\s*/\s*(\d+)\s*\}", line):
            time_sig = (int(a), int(b))
        m = DIRECTIVE_LINE_RE.match(line.strip())
        name, value = split_directive(m.group(1)) if m else ("", "")
        file, _, opts = value.partition("|")
        if name != "musicxml" or file.strip() != ref:
            out.append(line)
            continue
        count += 1
        part = measure_range(measures, opts)
        indent = line[:len(line) - len(line.lstrip())]
        out.append(f"{indent}# {line.strip()}" + (f"  ({note})" if note else "") + "\n")
        i = 0
        while i < len(part):                   # one block per run of measures in the same time signature
            sig = (part[i]["beats"], part[i]["beat_type"])
            j = i
            while j < len(part) and (part[j]["beats"], part[j]["beat_type"]) == sig:
                j += 1
            if sig != time_sig:
                out.append(f"{indent}{{time: {sig[0]}/{sig[1]}}}\n")
                time_sig = sig
            out.append(to_notes_text(part[i:j], key))
            i = j
    new = "".join(out)
    try:
        exact = _notated(parse_v1(text, base_dir=base_dir)) == _notated(parse_v1(new, base_dir=base_dir))
    except Exception:                       # noqa: BLE001  a source the engine cannot read: not checked
        exact = False
    return Conversion(new, count, exact)
