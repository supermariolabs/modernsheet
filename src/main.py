"""Modern Sheet — app (Flet: iPad, Android, macOS, Windows, Linux).

Three screens:
    library   a folder of .chs sources (with subfolders): browse, search, create songs
              (default: the bundled examples folder)
    editor    source editor on the left (dark, syntax highlighting, directive completion after "{"),
              live preview on the right (the editor can be hidden)
    settings  library folder, PDF folder, default display options

Uses the same engine as the command line:
    parse (.chs)  →  layout (DisplayList)  →  Flet canvas on screen  /  PDF export

Run on the desktop:   flet run            (from the project folder)
Build for devices:    flet build ipa | apk | macos | windows | linux
"""
from __future__ import annotations

import asyncio
import math
import os
import platform
import shutil
import time
from datetime import datetime
from pathlib import Path

import flet as ft
import flet.canvas as cv

from dataclasses import dataclass, field

from modernsheet import edits, formats, gdrive, layout, library, parse, sync, syntax, xml_syntax
from modernsheet.flet_view import FLET_FONTS, page_shapes
from modernsheet.fonts import registry
from modernsheet.pdf import pdf_bytes
from modernsheet.i18n import LANGUAGES, set_language, tr, tr_count, tr_date, tr_datetime
from modernsheet.settings import Settings, env
from modernsheet.theory import pretty_chord

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE / "examples"                 # bundled examples: the default library folder
PAGE_GAP = 18
MAX_SCALE = 2.2
PREVIEW_DELAY = 0.35            # seconds of typing pause before the preview is redrawn
SYNC_EVERY = 300                # seconds between automatic syncs while the app is open
PREF_SETTINGS = "modernsheet.settings"
PREF_LEGACY_SETTINGS = "chordsheet.settings"   # 0.10–0.18, when the app was called Chord Sheet
PREF_ROOT = "chordsheet.library_root"          # before 0.10: only the library folder was stored
DESKTOP = (ft.PagePlatform.MACOS, ft.PagePlatform.WINDOWS, ft.PagePlatform.LINUX)

# ---- source editor: a transparent TextField over a Text with coloured spans, same font and metrics.
# Flet's TextField cannot colour parts of its text, so the field's own text is transparent (it keeps
# caret, selection, keyboard, IME and copy/paste) and a Text with coloured spans is drawn exactly
# under it. That only works if both lay out the text identically: same bundled monospace font, a
# forced line height (strut), no extra letter spacing, the same wrapping width. The constants below
# are measured values that make the two coincide; change them together or the colours drift.
CODE_FONT = "ChsMono"                         # DejaVu Sans Mono, bundled: identical metrics everywhere
CODE_SIZE = 13
CODE_LINE = 1.4                               # line height, in font sizes
CODE_ADVANCE = 0.602                          # DejaVu Sans Mono advance width, in em
CODE_PAD = 12
CURSOR_W = 2
HIGHLIGHT_SHIFT = 4                           # the field draws its lines this much higher than a Text (measured)
EDITOR_BG = "#1E1F24"
EDITOR_FG = "#D8DEE9"
SYNTAX_COLORS = {
    "text": EDITOR_FG,
    "comment": "#7F8C98",
    "brace": "#8A93A6",
    "directive": "#C792EA",
    "section": "#5CC8FF",
    "value": "#F0A974",
    "chord": "#FFD866",
    "duration": "#A9DC76",
    "bar": "#78A6FF",
    "note": "#7FDBCA",               # notes written in the source ({start_of_notes})
    "rest": "#9AA3B5",
}
XML_COLORS = {                                # MusicXML token kind -> colour of SYNTAX_COLORS
    "text": "text", "comment": "comment", "decl": "comment", "brace": "brace",
    "tag": "section", "attr": "directive", "value": "value", "entity": "bar",
}
TAB_BG = "#16171B"
CHANGE_BG = {edits.LINE: "#262F26", edits.CHARS: "#35512F"}   # changed line / text written, until saved
POPUP_ROWS = 8
POPUP_ROW_H = 30
POPUP_W = 330


def code_style(color: str | None = EDITOR_FG, **kw) -> ft.TextStyle:
    # letter_spacing=0: the Material theme adds 0.5 to text fields, which would break the overlay
    return ft.TextStyle(font_family=CODE_FONT, size=CODE_SIZE, height=CODE_LINE, letter_spacing=0,
                        color=color, **kw)


DEFAULT_LIBRARY = "Modern Sheet"             # the library of a new installation, in the app's data folder


def default_library(data: str | None = None) -> Path:
    """The library of a new installation: a "Modern Sheet" folder in the app's data (on iPad/iPhone in
    its Documents folder, `data` given by the app, so that the Files app shows it) with the bundled
    examples in its "examples" subfolder, made on first start (the user's own songs and folders go
    next to it; the examples can be edited). Without a data folder: the bundled examples themselves."""
    data = data or os.environ.get("FLET_APP_STORAGE_DATA")
    if not data:
        return EXAMPLES
    root = Path(data) / DEFAULT_LIBRARY
    if not root.exists():
        try:
            root.mkdir(parents=True)
            shutil.copytree(EXAMPLES, root / "examples")
        except OSError:
            return EXAMPLES
    return root


CARD_MAX_W = 300
CARD_H = 236                  # fixed card height: the grid ratio follows the actual card width (draw_library)
CARD_GAP = 10
FOLDER_H = 112
SAVE_COLOR = ft.Colors.GREEN_600               # the Save button when there is something to save                # folder cards: lower than song cards
CARD_TITLE_BG = "#0066CC"     # same blue as the section boxes of the sheet


@dataclass
class Doc:
    """A file open in the editor: the song (.chs, always the first tab) or a MusicXML it references
    (read only: shown indented, it can only be converted into notes of the song)."""
    kind: str                       # "chs" | "xml"
    name: str                       # tab label
    path: Path | None
    text: str = ""
    saved: str = ""
    missing: bool = False           # referenced but not on disk (yet)
    note: str | None = None         # why it cannot be shown (compressed, unreadable)
    scroll: float = 0.0
    base: str = ""                  # the text as opened or last saved: what differs from it is painted
    history: edits.History = field(default_factory=edits.History)   # undo / redo

    def __post_init__(self):
        self.base = self.text

    @property
    def dirty(self) -> bool:
        return self.text != self.saved


SAME_TITLE_COLOR = ft.Colors.ORANGE_800        # the detail that tells same-title songs apart
DATE_COLOR = ft.Colors.BLUE_GREY_400


def song_dates(s: library.SongFile) -> dict[str, str]:
    """{"created": "Created 20 Nov 2026", "modified": "Modified 23 Nov 2026 13:05:12"} (known parts)."""
    out = {}
    if s.created_at:
        out["created"] = tr("card.created", date=tr_date(s.created_at))
    if s.modified_at:
        out["modified"] = tr("card.modified", date=tr_datetime(s.modified_at))
    return out


def tell_apart(songs: list[library.SongFile]) -> dict[Path, str]:
    """For songs shown with the same title: the detail that distinguishes them ("modified", else
    "created", else "file"), to be shown in another colour."""
    groups: dict[str, list[library.SongFile]] = {}
    for s in songs:
        groups.setdefault(s.title.casefold(), []).append(s)
    out: dict[Path, str] = {}
    for group in groups.values():
        if len(group) < 2:
            continue
        dates = [song_dates(s) for s in group]
        field = next((f for f in ("modified", "created") if len({d.get(f) for d in dates}) == len(group)), "file")
        out.update({s.path: field for s in group})
    return out


def song_meta(s: library.SongFile) -> str:
    return " · ".join(x for x in (pretty_chord(s.key) if s.key else "", s.time,
                                  f"♩ = {s.tempo}" if s.tempo else "") if x)


def meta_item(icon, text: str) -> ft.Control:
    return ft.Row(tight=True, spacing=3, controls=[
        ft.Icon(icon, size=14, color=ft.Colors.BLUE_GREY_400), ft.Text(text, size=13)])


def edit_caret(old: str, new: str) -> int:
    """Caret offset right after an edit that turned `old` into `new` (end of the changed span)."""
    p = 0
    n = min(len(old), len(new))
    while p < n and old[p] == new[p]:
        p += 1
    s = 0
    while s < n - p and old[-1 - s] == new[-1 - s]:
        s += 1
    return len(new) - s


def theme_selector(on_change) -> ft.SegmentedButton:
    return ft.SegmentedButton(
        selected=["realbook"], show_selected_icon=False,
        # the "realbook" theme is shown as "Fake Book" (a generic name): "The Real Book" is a trademark (SPEC §8.6)
        segments=[ft.Segment(value="realbook", label=ft.Text("Fake Book")),
                  ft.Segment(value="clean", label=ft.Text("Clean"))],
        on_change=lambda e: on_change(e.control.selected[0]))


def notation_selector(on_change) -> ft.SegmentedButton:
    """Notated bars: staff, staff + guitar tablature, tablature only."""
    return ft.SegmentedButton(
        selected=["staff"], show_selected_icon=False,
        segments=[ft.Segment(value=v, label=ft.Text(tr(f"opt.notation.{v}")), tooltip=tr(f"opt.notation.{v}_tip"))
                  for v in ("staff", "both", "tab")],
        on_change=lambda e: on_change(e.control.selected[0]))


def bar_width_selector(on_change) -> ft.SegmentedButton:
    return ft.SegmentedButton(
        selected=["uniform"], show_selected_icon=False,
        segments=[ft.Segment(value="uniform", label=ft.Text(tr("opt.grid"))),
                  ft.Segment(value="fit", label=ft.Text(tr("opt.fill")))],
        on_change=lambda e: on_change(e.control.selected[0]))


class App:
    """The whole app: three screens (library, settings, editor with preview) on one Flet page.

    The engine does the music (parse → layout → DisplayList); this class only shows it, edits the
    source, and manages files, settings and sync. Long work (parsing and layout, PDF, sync, Drive)
    runs in threads (asyncio.to_thread) so typing never waits for it."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.picker = ft.FilePicker()
        self.last_selection: ft.TextSelection | None = None
        self.tell_apart: dict[Path, str] = {}
        self.prefs = ft.SharedPreferences()
        self.launcher = ft.UrlLauncher()
        self.clipboard = ft.Clipboard()
        self.share = ft.Share()
        self.paths = ft.StoragePaths()
        page.services.extend([self.picker, self.prefs, self.launcher, self.clipboard, self.share, self.paths])
        # store mode (iPad/iPhone, Android, Mac App Store): the library lives inside the app, no folders in
        # the settings, files in and out through the system dialogs (SPEC §8.6, library.store_mode)
        self.store = library.store_mode(page.platform.value if page.platform else "")
        self.home: str | None = None              # iOS: the app's Documents folder (default_library)
        self._drive: gdrive.DriveProvider | None = None

        self.settings = Settings()

        # library
        self.root: Path | None = None
        self.tree: library.Folder | None = None
        self.cwd: Path | None = None             # folder shown in the browser
        self.query = ""
        self._syncing = False
        self._sync_again = False
        self.sync_report: sync.Report | None = None

        # open document
        self.path: Path | None = None            # None: example, import or not yet saved
        self.name = "Modern Sheet"                # file name (without extension) or import name
        self.song_title: str | None = None       # {title: …} of the last successful preview
        self.docs: list[Doc] = [Doc("chs", "", None)]    # tabs: the song, then its MusicXML files
        self.doc_index = 0
        self.base_dir: Path | None = None
        self.notes: list[str] = []               # conversion notes of an imported song
        self.opts = self.settings.layout_options()
        self.transpose = 0
        self.dl = None
        self.error: str | None = None
        self.scale = 1.0
        self.current_page = 0
        self.show_editor = False             # songs open in view mode (sheet only)
        self.fullscreen = False
        self.editor_focused = False
        self.screen = "library"
        self._typing = 0                          # debounce counter for the live preview

        # directive completion popup
        self.ac_items: list[syntax.Completion] = []
        self.ac_index = 0
        self.ac_caret = 0                         # caret offset the suggestions were computed for
        self._nav_until = 0.0                     # ignore caret moves caused by popup navigation keys
        self._undo_key: tuple[str, float] | None = None   # ⌘Z / ⌘⇧Z just pressed: (action, when)

        self.build_library()
        self.build_editor()
        self.build_settings()
        page.on_resize = self.on_resize
        page.on_keyboard_event = self.on_key
        if page.platform in DESKTOP:
            page.window.prevent_close = True
            page.window.on_event = self.on_window_event
        self.show_library()

    # the song source is always the first document
    @property
    def text(self) -> str:
        return self.docs[0].text

    @text.setter
    def text(self, value: str):
        self.docs[0].text = value

    @property
    def saved_text(self) -> str:
        return self.docs[0].saved

    @saved_text.setter
    def saved_text(self, value: str):
        self.docs[0].saved = self.docs[0].base = value      # saved: the changed parts are no longer painted

    @property
    def doc(self) -> Doc:
        return self.docs[self.doc_index]

    async def start(self):
        raw = await self.prefs.get(PREF_SETTINGS) or await self.prefs.get(PREF_LEGACY_SETTINGS)
        self.settings = Settings.from_json(raw)
        if not self.settings.library_root:
            self.settings.library_root = await self.prefs.get(PREF_ROOT)      # older versions
        self.opts = self.settings.layout_options()
        await self.find_home()
        self.apply_language()
        self.set_root(self.library_root())
        self.run(self.sync_now())
        self.run(self.sync_loop())

    async def find_home(self):
        """iPad/iPhone: the library goes in the app's Documents folder, which the Files app shows ("On My
        iPad › Modern Sheet", Info.plist UIFileSharingEnabled); a library made by an earlier version in the
        hidden app data is moved there. Elsewhere the app data folder stays (Android shows no app folder:
        files go in and out by import, export and Google Drive)."""
        if self.page.platform != ft.PagePlatform.IOS or env("LIBRARY"):
            return
        try:
            self.home = await self.paths.get_application_documents_directory()
        except Exception:                         # noqa: BLE001 — without it the data folder still works
            return
        data = os.environ.get("FLET_APP_STORAGE_DATA")
        if data and self.home:
            try:
                library.move_library(Path(data) / DEFAULT_LIBRARY, Path(self.home) / DEFAULT_LIBRARY)
            except OSError:
                pass

    def apply_language(self):
        """Use the language of the settings: texts are read when the screens are built, so they are
        built again (only from the library or settings screens: no document is open there)."""
        set_language(self.settings.language)
        self.page.locale_configuration = ft.LocaleConfiguration(
            supported_locales=[ft.Locale(code) for code in LANGUAGES],
            current_locale=ft.Locale(self.settings.language))
        self.build_library()
        self.build_editor()
        self.build_settings()
        self.search.value = self.query
        if self.screen == "library":              # put the new controls on the page
            self.page.appbar = self.lib_appbar
            self.page.controls = [ft.SafeArea(expand=True, content=self.lib_body)]

    def set_language(self, lang: str):
        if lang == self.settings.language:
            return
        self.settings.language = lang
        self.run(self.save_settings())
        self.apply_language()
        self.show_settings()

    def library_root(self) -> Path:
        """Library folder: MODERNSHEET_LIBRARY (development), the local copy of a synced library,
        the chosen folder, or the examples."""
        if not env("LIBRARY") and self.sync_state():
            local = self.local_copy(self.sync_state())
            local.mkdir(parents=True, exist_ok=True)
            return local
        # in store mode a folder chosen earlier is not readable after a restart: always the app's library
        for root in (env("LIBRARY"), None if self.store else self.settings.library_root):
            if root and Path(root).is_dir():
                return Path(root)
        return default_library(self.home)

    async def save_settings(self):
        await self.prefs.set(PREF_SETTINGS, self.settings.to_json())

    # ================================================================ library sync (local-first)
    def sync_state(self) -> Path | None:
        """App-data folder of the current remote (local copy, manifest, trash); None if not syncing."""
        data = os.environ.get("FLET_APP_STORAGE_DATA")
        st = self.settings
        if not data:
            return None
        if st.sync_mode == "folder" and st.sync_folder and not self.store:      # store mode: Drive only
            return sync.state_dir(Path(data), f"folder:{Path(st.sync_folder).resolve()}")
        if st.sync_mode == "gdrive" and st.sync_account:
            folder = gdrive.clean_folder_name(st.sync_drive_folder)
            # one local copy per account and Drive folder ("Chord Sheet", the default of 0.17–0.18, keeps its key)
            key = f"gdrive:{st.sync_account}" + ("" if folder == gdrive.LEGACY_ROOT_NAME else f":{folder}")
            return sync.state_dir(Path(data), key)
        return None

    def local_copy(self, state: Path) -> Path:
        """The local copy of a synced library: "library" in the remote's app-data folder (with the manifest
        and the trash), or on iPad/iPhone a folder of the app's Documents, which the Files app shows, named
        after what it is a copy of ("Modern Sheet (Google Drive · account)": one per Drive folder and
        account, as the state folders). A copy made by an earlier version in the app data is moved there."""
        st = self.settings
        if not self.home or st.sync_mode != "gdrive":
            return state / "library"
        name = library.safe_filename(f"{gdrive.clean_folder_name(st.sync_drive_folder)} (Google Drive · {st.sync_account})")
        visible = Path(self.home) / name
        try:
            library.move_library(state / "library", visible)
        except OSError:
            pass
        return visible

    # ---- Google Drive
    def google_client(self) -> gdrive.ClientConfig | None:
        """The app's OAuth client: env vars, src/google_client.json (not in git) or the app's data folder."""
        data = os.environ.get("FLET_APP_STORAGE_DATA")
        return gdrive.client_config(HERE / "google_client.json", *([Path(data) / "google_client.json"] if data else []))

    def google_auth(self) -> gdrive.GoogleAuth | None:
        data, cfg = os.environ.get("FLET_APP_STORAGE_DATA"), self.google_client()
        return gdrive.GoogleAuth(cfg, Path(data) / "google" / "token.json") if data and cfg else None

    def drive(self) -> gdrive.DriveProvider | None:
        """One provider for the session (it remembers the Drive folder ids between syncs)."""
        if self._drive is None:
            auth = self.google_auth()
            self._drive = gdrive.DriveProvider(auth, root_name=gdrive.clean_folder_name(
                self.settings.sync_drive_folder)) if auth and auth.signed_in else None
        return self._drive

    def syncer(self) -> sync.Syncer | None:
        state = self.sync_state()
        if not state or env("LIBRARY"):
            return None
        if self.settings.sync_mode == "gdrive":
            provider = self.drive()
            if provider is None:
                return None
        else:
            provider = sync.FolderProvider(Path(self.settings.sync_folder))
        return sync.Syncer(self.local_copy(state), provider, sync.Manifest(state / "manifest.json"), trash=state / "trash",
                           device=platform.node().split(".")[0] or str(self.page.platform.value))

    async def sync_now(self, e=None):
        """One sync in the background. Files open with unsaved changes wait for the next one; files
        open in the editor without changes are reloaded if a newer version arrives."""
        if self._syncing or getattr(self, "_renaming", False):
            self._sync_again = True              # asked while one is running: run again right after
            return
        syncer = self.syncer()
        if not syncer:
            return
        self._syncing = True
        self._sync_again = False
        self.draw_sync_status()
        root = syncer.local
        busy = {d.path.resolve().relative_to(root.resolve()).as_posix() for d in self.docs
                if d.path and d.dirty and d.path.resolve().is_relative_to(root.resolve())}
        try:
            report = await asyncio.to_thread(syncer.sync, busy)
        finally:
            self._syncing = False
        self.sync_report = report
        if report.changed_local:
            await self.reload_after_sync(root, report)
        if report.auth_required:
            self.toast(tr("gd.auth_required"))
        elif report.remote_reset:
            self.toast(tr("sync.remote_reset"))
        elif report.conflicts:
            self.toast(tr("sync.conflicts", n=len(report.conflicts), first=report.conflicts[0]))
        elif report.errors and not report.offline:
            self.toast(tr("sync.errors", n=len(report.errors), first=report.errors[0]))
        self.draw_sync_status()
        if self._sync_again:                     # settings or files changed during the sync
            await self.sync_now()

    async def reload_after_sync(self, root: Path, report: sync.Report):
        if self.screen == "library":
            self.rescan()
        elif self.screen == "editor":
            changed = {(root / rel).resolve() for rel in report.downloaded}
            reloaded = []
            for d in self.docs:
                if d.path and not d.dirty and d.path.resolve() in changed:
                    try:
                        d.text = d.saved = d.base = d.path.read_text(encoding="utf-8")
                        d.history.clear()                 # another device's version: a fresh start
                        d.missing = False
                        reloaded.append(d)
                    except (OSError, UnicodeDecodeError):
                        continue
            if not reloaded:
                return
            if self.doc in reloaded:
                self.show_doc()
            self.update_chrome()
            await self.render()

    async def sync_loop(self):
        while True:
            await asyncio.sleep(SYNC_EVERY)
            await self.sync_now()

    def sync_status_text(self) -> str:
        if self._syncing:
            return tr("sync.running")
        r = self.sync_report
        if r and r.auth_required:
            return tr("gd.auth_required")
        if r and r.offline:
            return tr("sync.offline")
        state = self.sync_state()
        last = sync.Manifest(state / "manifest.json").last_sync if state else None
        text = tr("sync.last", when=time.strftime("%H:%M", time.localtime(last))) if last else tr("sync.never")
        if r and r.conflicts:
            text += " · " + tr("sync.conflicts", n=len(r.conflicts), first=r.conflicts[0])
        return text

    def draw_sync_status(self):
        on = self.syncer() is not None
        self.sync_btn.visible = on
        if on:
            r = self.sync_report
            self.sync_btn.icon = (ft.Icons.CLOUD_SYNC if self._syncing else ft.Icons.CLOUD_OFF if r and r.offline
                                  else ft.Icons.SYNC_PROBLEM if r and (r.conflicts or r.errors or r.auth_required)
                                  else ft.Icons.CLOUD_DONE)
            self.sync_btn.tooltip = self.sync_status_text() + "\n" + tr("sync.now")
        if self.screen == "settings":
            self.draw_settings()
        else:
            self.page.update()

    async def pick_sync_folder(self, e=None):
        if not os.environ.get("FLET_APP_STORAGE_DATA"):
            self.toast(tr("sync.unavailable"))
            return
        path = await self.picker.get_directory_path(dialog_title=tr("sync.choose"),
                                                    initial_directory=self.settings.sync_folder)
        if not path:
            return
        await self.activate_sync("folder", folder=path)

    async def activate_sync(self, mode: str, folder: str | None = None, account: str | None = None):
        """Switch the library to the local copy of a remote; the current songs can join it."""
        old_root = self.root
        choice = None
        if old_root and any(old_root.rglob("*.chs")):
            choice = await self.ask(tr("sync.merge_title"), ft.Text(tr("sync.merge_text", name=old_root.name)),
                                    [(tr("cancel"), None), (tr("sync.merge_no"), "no"), (tr("sync.merge_yes"), "yes")])
            if choice is None:
                return
        self.settings.sync_mode, self.settings.sync_folder, self.settings.sync_account = mode, folder, account
        await self.save_settings()
        local = self.library_root()
        self.sync_report = None
        self.set_root(local)
        self.draw_settings()
        await self.sync_now()                     # first what the remote already has (e.g. its examples/)…
        if choice == "yes" and old_root and old_root.resolve() != local.resolve():
            # …then only the songs it lacks, at the same paths: no duplicates, no conflict copies
            if library.merge_into(old_root, local, sync.is_synced):
                self.rescan()
                await self.sync_now()

    async def stop_sync(self, e=None):
        """The local copy stays in the app's data (and is used again if the same folder is chosen)."""
        self.settings.sync_mode, self.settings.sync_folder, self.settings.sync_account = "none", None, None
        await self.save_settings()
        self.sync_report = None
        self.set_root(self.library_root())
        self.draw_sync_status()

    async def connect_google(self, e=None):
        """Device-flow sign-in: show the code, wait for the user to confirm it on any device."""
        if not os.environ.get("FLET_APP_STORAGE_DATA"):
            self.toast(tr("sync.unavailable"))
            return
        auth = self.google_auth()
        if auth is None:
            self.toast(tr("gd.no_client"))
            return
        try:
            dc = await asyncio.to_thread(auth.start)
        except (sync.Offline, OSError) as err:
            self.toast(tr("gd.failed", err=err))
            return
        state = {"cancelled": False}
        status = ft.Text(tr("gd.waiting"), size=12, color=ft.Colors.BLUE_GREY_600)

        def cancel(e=None):
            state["cancelled"] = True
            self.page.pop_dialog()

        dialog = ft.AlertDialog(
            modal=True, title=ft.Text(tr("gd.code_title")),
            content=ft.Column(tight=True, spacing=12, controls=[
                ft.Text(tr("gd.code_text", url=dc.verification_url)),
                ft.Text(dc.user_code, size=32, weight=ft.FontWeight.W_700, selectable=True,
                        font_family=CODE_FONT, text_align=ft.TextAlign.CENTER),
                ft.Row(wrap=True, spacing=8, controls=[
                    ft.FilledTonalButton(tr("gd.open"), icon=ft.Icons.OPEN_IN_BROWSER,
                                         on_click=lambda e: self.run(self.launcher.launch_url(dc.verification_url))),
                    ft.OutlinedButton(tr("gd.copy"), icon=ft.Icons.COPY,
                                      on_click=lambda e: self.run(self.clipboard.set(dc.user_code)))]),
                ft.Row(spacing=8, controls=[ft.ProgressRing(width=16, height=16, stroke_width=2), status])]),
            actions=[ft.TextButton(tr("cancel"), on_click=cancel)])
        self.page.show_dialog(dialog)
        interval, result = dc.interval, "pending"
        while not state["cancelled"]:
            await asyncio.sleep(interval)
            if state["cancelled"]:
                return
            try:
                result = await asyncio.to_thread(auth.poll, dc)
            except (sync.Offline, OSError):
                continue                                  # network hiccup: keep waiting
            if result == "slow_down":
                interval += 5
            elif result != "pending":
                break
        if state["cancelled"]:
            return
        if result != "ok":
            status.value = tr("gd.denied") if result == "denied" else tr("gd.expired")
            self.page.update()
            return
        self.page.pop_dialog()
        self._drive = None
        try:
            account = (await asyncio.to_thread(self.drive().account)).get("emailAddress") or "google"
        except (sync.Offline, sync.AuthRequired, OSError) as err:
            self.toast(tr("gd.failed", err=err))
            return
        await self.activate_sync("gdrive", account=account)

    async def set_drive_folder(self, e=None):
        """New name of the app's folder in Drive: while connected, the library moves to that folder
        (a different local copy); the old one stays as it is, in Drive and locally."""
        name = gdrive.clean_folder_name(self.gd_folder.value or "")
        old = gdrive.clean_folder_name(self.settings.sync_drive_folder)
        self.gd_folder.value = name
        if name == old:
            self.draw_settings()
            return
        connected = self.settings.sync_mode == "gdrive" and self.settings.sync_account
        if connected and await self.ask(tr("gd.folder_title"), ft.Text(tr("gd.folder_text", name=name, old=old)),
                                        [(tr("cancel"), None), (tr("gd.folder_ok", name=name), "ok")]) != "ok":
            self.gd_folder.value = old
            self.draw_settings()
            return
        self.settings.sync_drive_folder = name
        self._drive = None
        if connected:
            await self.activate_sync("gdrive", account=self.settings.sync_account)
        else:
            await self.save_settings()
            self.draw_settings()

    async def disconnect_google(self, e=None):
        auth = self.google_auth()
        if auth:
            auth.sign_out()
        self._drive = None
        if self.settings.sync_mode == "gdrive":
            await self.stop_sync()
        self.draw_settings()

    # ================================================================ library screen
    def build_library(self):
        """Controls of the library screen, built once: app bar (sync state, refresh, import, settings),
        search with sorting and view switch, the breadcrumbs and the body that draw_library fills."""
        self.sync_btn = ft.IconButton(ft.Icons.CLOUD_DONE, visible=False, on_click=self.sync_now)
        self.lib_appbar = ft.AppBar(
            title=ft.Text(tr("library"), size=18, weight=ft.FontWeight.W_600),
            actions=[
                self.sync_btn,
                ft.IconButton(ft.Icons.REFRESH, tooltip=tr("lib.refresh"), on_click=lambda e: self.rescan()),
                ft.IconButton(ft.Icons.NOTE_ADD_OUTLINED, tooltip=tr("lib.open_file"), on_click=self.pick_file),
                ft.IconButton(ft.Icons.SETTINGS_OUTLINED, tooltip=tr("settings"), on_click=self.show_settings),
            ])
        self.search = ft.TextField(
            hint_text=tr("lib.search_hint"), tooltip=tr("lib.search_help"),
            prefix_icon=ft.Icons.SEARCH, dense=True, border_radius=24, filled=True, expand=True,
            on_change=self.on_search)
        self.clear_btn = ft.IconButton(ft.Icons.CLOSE, icon_size=18, tooltip=tr("lib.clear_search"),
                                       on_click=self.clear_search)
        self.sort_menu = ft.PopupMenuButton(
            icon=ft.Icons.SORT, tooltip=tr("lib.sort"),
            items=[ft.PopupMenuItem(content=ft.Text(tr(f"sort.{key}")), data=key, on_click=self.on_sort)
                   for key in library.SORT_KEYS])
        self.sort_dir = ft.IconButton(ft.Icons.ARROW_UPWARD, on_click=self.toggle_sort_dir)
        self.sort_label = ft.Text("", size=12, color=ft.Colors.BLUE_GREY_600)
        self.view_btn = ft.IconButton(ft.Icons.VIEW_LIST_OUTLINED, on_click=self.toggle_view)
        self.lib_tools = ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            self.search, ft.Container(width=8), self.sort_label, self.sort_menu, self.sort_dir, self.view_btn])
        self.crumbs = ft.Row(spacing=0, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        self.items = ft.ListView(expand=True, spacing=0, padding=ft.Padding.only(bottom=80))
        # cards: rows of fixed-size cards, with full-width A–Z headers between them (built lazily by the list)
        self.cards = ft.ListView(expand=True, spacing=CARD_GAP, padding=ft.Padding.only(top=4, bottom=80))
        # bottom-right actions (two buttons: a page has a single floating action button)
        big = ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=20, vertical=18),
                             shape=ft.RoundedRectangleBorder(radius=16), elevation=3)
        self.lib_actions = ft.Row(tight=True, spacing=12, controls=[
            ft.FilledTonalButton(tr("new_folder"), icon=ft.Icons.CREATE_NEW_FOLDER_OUTLINED, style=big,
                                 on_click=self.new_folder),
            ft.FilledButton(tr("new_song"), icon=ft.Icons.ADD, style=big, on_click=self.new_song),
        ])
        self.lib_body = ft.Container(expand=True, padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                                     bgcolor=ft.Colors.WHITE)
        # built once: redrawing only swaps the results, so the search field keeps its focus while typing
        self.lib_results = ft.Container(expand=True)
        self.lib_main = ft.Stack(expand=True, controls=[
            ft.Column(expand=True, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                      controls=[self.lib_tools, self.crumbs, ft.Divider(height=1), self.lib_results]),
            ft.Container(self.lib_actions, right=8, bottom=8)])
        self.card_layout: tuple[int, int] | None = None      # (columns, card width) the cards were built for

    def set_root(self, root: Path):
        self.root, self.cwd, self.query = root, root, ""
        self.search.value = ""
        self.rescan()

    def rescan(self):
        if not self.root:
            return
        data = os.environ.get("FLET_APP_STORAGE_DATA")
        index = library.Index(library.index_path(Path(data), self.root) if data else None)
        self.tree = library.scan(self.root, index)
        if self.cwd is None or self.tree.find(self.cwd) is None:
            self.cwd = self.root
        self.draw_library()

    def on_resize(self, e=None):
        if self.screen == "editor":
            self.draw()
        elif self.screen == "library" and self.settings.library_view == "cards":
            self._resize_ticket = getattr(self, "_resize_ticket", 0) + 1
            self.run(self.relayout_cards(self._resize_ticket))

    async def relayout_cards(self, ticket: int):
        """Card rows depend on the window width: rebuild them once resizing pauses, and only if the
        columns changed (not for height changes, e.g. the on-screen keyboard)."""
        await asyncio.sleep(0.15)
        if ticket != self._resize_ticket or self.screen != "library":
            return
        n, w = self.fit_cards()
        if self.card_layout != (n, round(w)):
            self.draw_library()

    def fit_cards(self) -> tuple[int, float]:
        """Columns and card width for the current window: as many columns as fit cards at most
        CARD_MAX_W wide, sharing the width (every card is CARD_H tall)."""
        width = (self.page.width or 1000) - 2 * 12 - 4                 # lib_body padding, scrollbar slack
        n = max(1, math.ceil(width / (CARD_MAX_W + CARD_GAP)))
        return n, (width - CARD_GAP * (n - 1)) / n

    def card_rows(self, cards: list[ft.Control], height: float = CARD_H) -> list[ft.Control]:
        n, w = self.fit_cards()
        return [ft.Row(spacing=CARD_GAP, controls=[ft.Container(width=w, height=height, content=c)
                                                   for c in cards[i:i + n]])
                for i in range(0, len(cards), n)]

    def letter_header(self, letter: str) -> ft.Control:
        """ "A ─────────" between the groups of songs."""
        return ft.Container(
            padding=ft.Padding.only(left=2, right=4, top=10, bottom=2),
            content=ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text(letter, size=20, weight=ft.FontWeight.W_700, color=CARD_TITLE_BG),
                ft.Container(expand=True, height=1.5, bgcolor=ft.Colors.BLUE_GREY_200)]))

    def show_library(self):
        if self.fullscreen:
            self.set_fullscreen(False, redraw=False)
        self.screen = "library"
        self.page.appbar = self.lib_appbar
        self.page.floating_action_button = None
        self.page.controls = [ft.SafeArea(expand=True, content=self.lib_body)]
        if self.root:
            self.rescan()             # titles or files may have changed meanwhile
        else:
            self.draw_library()
        self.draw_sync_status()
        self.run(self.sync_now())

    def draw_library(self):
        """Redraw the library: breadcrumbs, then folders and songs of the open folder (or the search
        results) as cards or as a list, grouped A–Z when sorted by title or artist."""
        if self.screen != "library":
            return
        self.page.floating_action_button = None
        if not self.tree:
            self.lib_body.content = ft.Column(
                expand=True, alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14,
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.BLUE_GREY_300),
                    ft.Text(tr("lib.choose_title"), size=18),
                    ft.Text(tr("lib.choose_help"),
                            color=ft.Colors.BLUE_GREY_600),
                    ft.FilledButton(tr("lib.choose_button"), icon=ft.Icons.FOLDER_OPEN, on_click=self.pick_root),
                ])
            self.page.update()
            return

        st = self.settings
        cards = st.library_view == "cards"
        self.view_btn.icon = ft.Icons.VIEW_LIST_OUTLINED if cards else ft.Icons.GRID_VIEW
        self.view_btn.tooltip = tr("lib.view_list") if cards else tr("lib.view_cards")
        self.sort_dir.icon = ft.Icons.ARROW_DOWNWARD if st.sort_desc else ft.Icons.ARROW_UPWARD
        self.sort_dir.tooltip = tr("lib.descending") if st.sort_desc else tr("lib.ascending")
        self.sort_label.value = tr(f"sort.{st.sort_by}")
        folder = self.tree.find(self.cwd) or self.tree
        searching = bool(self.query.strip())
        self.search.suffix_icon = self.clear_btn if self.query else None
        if searching:
            songs = library.sort_songs(library.search(self.tree, self.query), st.sort_by, st.sort_desc)
            self.crumbs.controls = [ft.Text(tr("lib.results", n=len(songs), folder=self.tree.name),
                                            color=ft.Colors.BLUE_GREY_700)]
            folders = []
        else:
            songs = library.sort_songs(folder.songs, st.sort_by, st.sort_desc)
            self.crumbs.controls = self.breadcrumbs(folder)
            folders = folder.folders
        self.tell_apart = tell_apart(songs)
        # A–Z groups when sorted by title or artist (by that field's initial); folders always first
        field = library.GROUPED_SORTS.get(st.sort_by)
        groups = library.group_by_letter(songs, field, st.sort_desc) if field else [(None, songs)]
        if cards:
            items = self.card_rows([self.folder_card(f.name, f.count(), f.path) for f in folders], FOLDER_H)
            for letter, group in groups:
                if letter:
                    items.append(self.letter_header(letter))
                items += self.card_rows([self.song_card(s, show_folder=searching) for s in group])
        else:
            items = [self.folder_tile(f) for f in folders]
            for letter, group in groups:
                if letter:
                    items.append(self.letter_header(letter))
                items += [self.song_tile(s, show_folder=searching) for s in group]
        if not items:
            view: ft.Control = ft.Container(ft.Text(tr("lib.no_songs") if searching else tr("lib.empty_folder"),
                                                    color=ft.Colors.BLUE_GREY_600), padding=ft.Padding.all(16))
        elif cards:
            self.cards.controls = items
            view = self.cards
        else:
            self.items.controls = items
            view = self.items
        self.lib_results.content = view
        if self.lib_body.content is not self.lib_main:
            self.lib_body.content = self.lib_main
        n, w = self.fit_cards()
        self.card_layout = (n, round(w))
        self.page.update()

    def home_label(self) -> str:
        """Name of the main folder as the user knows it: for a synced library its local copy (a folder
        called "library" in the app data) is shown as what it is a copy of."""
        state = self.sync_state()
        if state is not None and self.root and self.root == self.local_copy(state):
            st = self.settings
            return Path(st.sync_folder).name if st.sync_mode == "folder" else tr("gd.title")
        return self.root.name or str(self.root)

    def place_label(self, folder: Path) -> str:
        """`folder` for dialogs: "Google Drive › Jazz › Ballads" (main folder label, then the subfolders)."""
        rel = folder.relative_to(self.root).parts if self.root and folder.is_relative_to(self.root) else None
        if rel is None:
            return str(folder)
        return " › ".join([self.home_label(), *rel])

    def breadcrumbs(self, folder: library.Folder) -> list[ft.Control]:
        """⬆ (parent folder) · 🏠 main folder › sub › sub: every part but the last opens that folder."""
        rel = folder.path.relative_to(self.root).parts
        parts = [self.root.joinpath(*rel[:i]) for i in range(len(rel) + 1)]
        at_root = folder.path == self.root
        out: list[ft.Control] = [
            ft.IconButton(ft.Icons.ARROW_UPWARD, tooltip=tr("lib.up"), disabled=at_root,
                          on_click=lambda e: self.go(folder.path.parent)),
            ft.VerticalDivider(width=12),
        ]
        for i, p in enumerate(parts):
            if i:
                out.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=ft.Colors.BLUE_GREY_400))
            label = self.home_label() if i == 0 else p.name
            current = p == folder.path
            if i == 0:
                home = ft.Row(tight=True, spacing=6, controls=[
                    ft.Icon(ft.Icons.HOME_OUTLINED, size=18,
                            color=None if current else ft.Colors.BLUE_700), ft.Text(label)])
                out.append(ft.Container(home, padding=ft.Padding.symmetric(horizontal=8, vertical=6))
                           if current else ft.TextButton(content=home, on_click=lambda e: self.go(self.root),
                                                         tooltip=tr("lib.home", name=label)))
            elif current:
                out.append(ft.Text(label, weight=ft.FontWeight.W_600))
            else:
                out.append(ft.TextButton(label, on_click=lambda e, p=p: self.go(p)))
        return out

    def song_tile(self, s: library.SongFile, show_folder: bool = False) -> ft.ListTile:
        where = s.path.relative_to(self.root).as_posix() if show_folder else s.path.name
        mark = self.tell_apart.get(s.path)
        parts = [(x, None) for x in (s.artist, song_meta(s)) if x] + [(where, "file")] + \
                [(text, field) for field, text in song_dates(s).items()]
        spans: list[ft.TextSpan] = []
        for i, (text, field) in enumerate(parts):
            if i:
                spans.append(ft.TextSpan(" · "))
            spans.append(ft.TextSpan(text, ft.TextStyle(color=SAME_TITLE_COLOR, weight=ft.FontWeight.W_600)
                                     if field and field == mark else None))
        return ft.ListTile(
            leading=ft.Icon(ft.Icons.MUSIC_NOTE_OUTLINED, color=ft.Colors.BLUE_700),
            title=ft.Text(s.title), subtitle=ft.Text(spans=spans, color=ft.Colors.BLUE_GREY_500),
            trailing=ft.Row(tight=True, spacing=4, controls=[self.tag_chip(t) for t in s.tags[:4]]) if s.tags else None,
            on_click=lambda e, p=s.path: self.open_song(p))

    def folder_tile(self, f: library.Folder) -> ft.ListTile:
        n = f.count()
        return ft.ListTile(
            leading=ft.Icon(ft.Icons.FOLDER, color=ft.Colors.AMBER_700),
            title=ft.Text(f.name), subtitle=ft.Text(tr_count(n, "songs")),
            trailing=ft.Row(tight=True, spacing=0, controls=[self.folder_menu(f.path), ft.Icon(ft.Icons.CHEVRON_RIGHT)]),
            on_click=lambda e, p=f.path: self.go(p))

    def folder_menu(self, path: Path) -> ft.Control:
        """⋮ on a folder: its actions (rename)."""
        return ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT, icon_size=20, tooltip=tr("lib.folder_actions"),
            items=[ft.PopupMenuItem(content=ft.Text(tr("lib.rename")),
                                    on_click=lambda e, p=path: self.run(self.rename_folder(p)))])

    async def rename_folder(self, path: Path):
        """Rename a folder of the library (library.rename_folder): never during a sync, and the
        references of other songs to its MusicXML files follow it."""
        name = ft.TextField(label=tr("lib.folder_name"), value=path.name, autofocus=True)
        info = [ft.Text(tr_count(sum(1 for _ in path.rglob("*.chs")), "songs"), size=12,
                        color=ft.Colors.BLUE_GREY_600)]
        refs = library.outside_refs(self.root, path)
        if refs:
            info.append(ft.Text(tr("lib.rename_refs", n=len({s for s, _ in refs})), size=12))
        if self.sync_state() is not None:
            info.append(ft.Text(tr("lib.rename_synced"), size=12, color=ft.Colors.BLUE_GREY_600))
        choice = await self.ask(tr("lib.rename_title", name=path.name),
                                ft.Column(tight=True, spacing=8, controls=[name, *info]),
                                [(tr("cancel"), None), (tr("lib.rename"), "ok")])
        if choice != "ok":
            return
        self._renaming = True                       # no sync starts while files move
        try:
            for _ in range(300):                     # wait for a running sync (at most ~1 minute)
                if not self._syncing:
                    break
                await asyncio.sleep(0.2)
            else:
                self.toast(tr("lib.rename_busy"))
                return
            try:
                result = library.rename_folder(path, name.value or "", self.root)
            except ValueError:                        # blank name, or already used next to it
                self.toast(tr("lib.rename_invalid"))
                return
            except OSError as err:
                self.toast(tr("lib.rename_failed", err=err))
                return
        finally:
            self._renaming = False
        if self.cwd and self.cwd.is_relative_to(path):
            self.cwd = result.path / self.cwd.relative_to(path)
        self.rescan()
        self.toast(tr("lib.renamed", old=path.name, new=result.path.name) +
                   (tr("lib.renamed_refs", n=len(result.updated)) if result.updated else ""))
        self.run(self.sync_now())

    def song_card(self, s: library.SongFile, show_folder: bool = False) -> ft.Control:
        """Title in a blue band, then artist, key · time · tempo, tags, file and dates, one line each;
        every card has the same height (CARD_H), the file and the dates sit at the bottom."""
        meta = []
        if s.key:
            meta.append(meta_item(ft.Icons.MUSIC_NOTE, pretty_chord(s.key)))
        if s.time:
            meta.append(meta_item(ft.Icons.TIMER_OUTLINED, s.time))
        if s.tempo:
            meta.append(ft.Text(f"♩ = {s.tempo}", size=13))
        one_line = dict(max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        rows: list[ft.Control] = [
            ft.Text(s.artist or " ", size=13, color=ft.Colors.BLUE_GREY_600, **one_line),
            ft.Row(spacing=12, scroll=ft.ScrollMode.HIDDEN, controls=meta),
        ]
        if s.tags:
            rows.append(ft.Row(spacing=4, scroll=ft.ScrollMode.HIDDEN, controls=[self.tag_chip(t) for t in s.tags]))
        rows.append(ft.Container(expand=True))                # file and dates at the bottom
        # the file (what Save as and Delete act on; tells copies with the same title apart), in its folder
        # while searching
        where = s.path.name
        if show_folder:
            where = self.place_label(s.path.parent) + " › " + where
        mark = self.tell_apart.get(s.path)
        rows.append(ft.Text(where, size=11, color=SAME_TITLE_COLOR if mark == "file" else DATE_COLOR,
                            weight=ft.FontWeight.W_600 if mark == "file" else None, **one_line))
        for field, text in song_dates(s).items():           # one line each: created, modified
            hit = field == mark
            rows.append(ft.Text(text, size=11, color=SAME_TITLE_COLOR if hit else DATE_COLOR,
                                weight=ft.FontWeight.W_600 if hit else None, **one_line))
        title = ft.Container(
            bgcolor=CARD_TITLE_BG, height=60, alignment=ft.Alignment.CENTER_LEFT,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            content=ft.Text(s.title, size=16, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS))
        return ft.Card(
            elevation=1, margin=0, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Container(
                ink=True, tooltip=s.path.name, on_click=lambda e, p=s.path: self.open_song(p),
                content=ft.Column(spacing=0, controls=[
                    title,
                    ft.Container(expand=True, padding=ft.Padding.only(left=14, right=14, top=10, bottom=12),
                                 content=ft.Column(spacing=5, controls=rows))])))

    def folder_card(self, name: str, count: int, path: Path) -> ft.Control:
        sub = tr_count(count, "songs")
        return ft.Card(
            elevation=0, margin=0, bgcolor=ft.Colors.AMBER_50, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Container(
                padding=ft.Padding.all(14), ink=True, on_click=lambda e: self.go(path),
                content=ft.Column(spacing=6, controls=[
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Icon(ft.Icons.FOLDER, color=ft.Colors.AMBER_700, size=32), self.folder_menu(path)]),
                    ft.Text(name, size=16, weight=ft.FontWeight.W_600, max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(sub, size=12, color=ft.Colors.BLUE_GREY_600)])))

    def tag_chip(self, tag: str) -> ft.Control:
        return ft.Container(
            ft.Text(f"#{tag}", size=11, color=ft.Colors.BLUE_800), bgcolor=ft.Colors.BLUE_50, border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2), tooltip=tr("lib.tag_tooltip", tag=tag),
            on_click=lambda e: self.set_query(f"#{tag}"))

    def go(self, path: Path):
        self.cwd = path
        self.draw_library()

    def on_search(self, e):
        """Filter as you type, once typing pauses briefly (the field itself is never rebuilt)."""
        self.query = e.control.value or ""
        self._search_ticket = getattr(self, "_search_ticket", 0) + 1
        self.run(self.search_after_pause(self._search_ticket))

    async def search_after_pause(self, ticket: int):
        await asyncio.sleep(0.12)
        if ticket == self._search_ticket and self.screen == "library":
            self.draw_library()

    async def clear_search(self, e=None):
        self.set_query("")
        await self.search.focus()

    def set_query(self, query: str):
        self.search.value = self.query = query
        self.draw_library()

    def on_sort(self, e):
        self.settings.sort_by = e.control.data
        self.run(self.save_settings())
        self.draw_library()

    def toggle_sort_dir(self, e=None):
        self.settings.sort_desc = not self.settings.sort_desc
        self.run(self.save_settings())
        self.draw_library()

    def toggle_view(self, e=None):
        self.settings.library_view = "list" if self.settings.library_view == "cards" else "cards"
        self.run(self.save_settings())
        self.draw_library()

    async def pick_root(self, e=None):
        path = await self.picker.get_directory_path(dialog_title=tr("set.library_folder"),
                                                    initial_directory=str(self.root) if self.root else None)
        if not path:
            return
        self.settings.library_root = path
        await self.save_settings()
        self.set_root(Path(path))
        self.draw_settings()

    async def new_folder(self, e=None):
        """Create a subfolder of the open folder (of the main folder during a search) and open it."""
        name = ft.TextField(label=tr("lib.folder_name"), autofocus=True, value="")
        where = self.cwd if self.cwd and not self.query.strip() else self.root
        choice = await self.ask(tr("new_folder"), ft.Column(tight=True, controls=[
            name, ft.Text(tr("lib.new_in", folder=self.place_label(where)), size=12, color=ft.Colors.BLUE_GREY_600)]),
            [(tr("cancel"), None), (tr("lib.create"), "ok")])
        if choice != "ok":
            return
        path = library.new_folder_path(where, (name.value or "").strip())
        try:
            path.mkdir()
        except OSError as err:
            self.toast(tr("lib.folder_failed", err=err))
            return
        self.set_query("")
        self.cwd = path
        self.rescan()

    async def new_song(self, e):
        title = ft.TextField(label=tr("lib.new_title"), autofocus=True, value="")
        where = self.cwd if self.cwd and not self.query.strip() else self.root
        choice = await self.ask(tr("new_song"), ft.Column(tight=True, controls=[
            title, ft.Text(tr("lib.new_in", folder=self.place_label(where)),
                           size=12, color=ft.Colors.BLUE_GREY_600)]), [(tr("cancel"), None), (tr("lib.create"), "ok")])
        if choice != "ok":
            return
        name = (title.value or "").strip() or tr("new_song")
        path = library.new_song_path(where, name)
        try:
            path.write_text(library.new_song_text(name), encoding="utf-8")
        except OSError as err:
            self.toast(tr("lib.create_failed", err=err))
            return
        self.open_song(path, edit=True)

    # ================================================================ settings screen
    def build_settings(self):
        """Controls of the settings screen, built once (draw_settings fills in the current values):
        folders, sync (folder or Google Drive), display defaults, language."""
        self.set_appbar = ft.AppBar(
            leading=ft.IconButton(ft.Icons.ARROW_BACK, tooltip=tr("library"), on_click=lambda e: self.show_library()),
            title=ft.Text(tr("settings"), size=18, weight=ft.FontWeight.W_600))
        self.root_tile = ft.ListTile(
            leading=ft.Icon(ft.Icons.LIBRARY_MUSIC_OUTLINED), title=ft.Text(tr("set.library_folder")),
            trailing=ft.Row(tight=True, spacing=0, controls=[
                ft.IconButton(ft.Icons.FOLDER_OPEN, tooltip=tr("choose"), on_click=self.pick_root),
                ft.IconButton(ft.Icons.RESTART_ALT, tooltip=tr("set.reset_examples"), on_click=self.reset_root)]))
        self.sync_tile = ft.ListTile(
            leading=ft.Icon(ft.Icons.CLOUD_SYNC_OUTLINED), title=ft.Text(tr("sync.folder")),
            trailing=ft.Row(tight=True, spacing=0, controls=[
                ft.IconButton(ft.Icons.FOLDER_OPEN, tooltip=tr("sync.choose"), on_click=self.pick_sync_folder),
                ft.IconButton(ft.Icons.CLOUD_OFF, tooltip=tr("sync.stop"), on_click=self.stop_sync)]))
        self.gd_tile = ft.ListTile(
            leading=ft.Icon(ft.Icons.ADD_TO_DRIVE), title=ft.Text(tr("gd.title")),
            trailing=ft.Row(tight=True, spacing=0, controls=[
                ft.IconButton(ft.Icons.LOGIN, tooltip=tr("gd.connect"), on_click=self.connect_google),
                ft.IconButton(ft.Icons.LOGOUT, tooltip=tr("gd.disconnect"), on_click=self.disconnect_google)]))
        self.gd_folder = ft.TextField(label=tr("gd.folder"), helper=tr("gd.folder_help"), dense=True,
                                      value=self.settings.sync_drive_folder, prefix_icon=ft.Icons.FOLDER_OUTLINED,
                                      on_submit=self.set_drive_folder, on_blur=self.set_drive_folder)
        self.sync_folder_help = ft.Container(ft.Text(tr("sync.folder_help"), size=12, color=ft.Colors.BLUE_GREY_600),
                                             padding=ft.Padding.only(left=16, right=16, bottom=4))
        self.sync_info = ft.Text("", size=12, color=ft.Colors.BLUE_GREY_600)
        self.sync_now_btn = ft.OutlinedButton(tr("sync.now"), icon=ft.Icons.SYNC, on_click=self.sync_now)
        self.pdf_tile = ft.ListTile(
            leading=ft.Icon(ft.Icons.PICTURE_AS_PDF_OUTLINED), title=ft.Text(tr("set.pdf_folder")),
            trailing=ft.Row(tight=True, spacing=0, controls=[
                ft.IconButton(ft.Icons.FOLDER_OPEN, tooltip=tr("choose"), on_click=self.pick_pdf_dir),
                ft.IconButton(ft.Icons.CLEAR, tooltip=tr("set.no_pdf_folder"), on_click=self.reset_pdf_dir)]))
        self.set_theme = theme_selector(lambda v: self.set_default("theme", v))
        self.set_width = bar_width_selector(lambda v: self.set_default("bar_width", v))
        self.set_notation = notation_selector(lambda v: self.set_default("notation", v))
        self.set_spacing = ft.SegmentedButton(
            selected=["normal"], show_selected_icon=False,
            segments=[ft.Segment(value=v, label=ft.Text(tr(f"opt.spacing.{v}")))
                      for v in ("compact", "normal", "wide", "extra")],
            on_change=lambda e: self.set_default("row_spacing", e.control.selected[0]))
        self.set_chords = ft.SegmentedButton(
            selected=["text"], show_selected_icon=False,
            segments=[ft.Segment(value="text", label=ft.Text(tr("opt.standard"))),
                      ft.Segment(value="jazz", label=ft.Text(tr("opt.jazz")))],
            on_change=lambda e: self.set_default("chord_symbols", e.control.selected[0]))
        self.set_names = ft.SegmentedButton(
            selected=["letters"], show_selected_icon=False,
            segments=[ft.Segment(value="letters", label=ft.Text(tr("opt.letters"))),
                      ft.Segment(value="italian", label=ft.Text(tr("opt.italian")))],
            on_change=lambda e: self.set_default("note_names", e.control.selected[0]))
        self.set_lang = ft.SegmentedButton(
            selected=[self.settings.language], show_selected_icon=False,
            segments=[ft.Segment(value=code, label=ft.Text(name)) for code, name in LANGUAGES.items()],
            on_change=lambda e: self.set_language(e.control.selected[0]))
        self.set_colors = ft.Switch(value=False, on_change=lambda e: self.set_default(
            "label_colors", "by_type" if e.control.value else "theme"))

        def option(title: str, subtitle: str, control: ft.Control) -> ft.Control:
            return ft.ListTile(title=ft.Text(title), subtitle=ft.Text(subtitle, color=ft.Colors.BLUE_GREY_600),
                               trailing=control)

        def heading(text: str) -> ft.Control:
            return ft.Container(ft.Text(text, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_700),
                                padding=ft.Padding.only(left=16, top=16, bottom=4))

        self.set_body = ft.Container(
            expand=True, bgcolor=ft.Colors.WHITE,
            content=ft.ListView(expand=True, padding=ft.Padding.symmetric(horizontal=8, vertical=8), controls=[
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Container(
                    expand=True, max_width=760,
                    content=ft.Column(spacing=0, controls=[
                    heading(tr("set.general")),
                    option(tr("set.language"), tr("set.language_help"), self.set_lang),
                    ft.Divider(height=24),
                    heading(tr("set.folders")),
                    self.root_tile,
                    self.pdf_tile,
                    ft.ListTile(leading=ft.Icon(ft.Icons.ARCHIVE_OUTLINED), title=ft.Text(tr("set.export_library")),
                                subtitle=ft.Text(tr("set.export_library_help"), color=ft.Colors.BLUE_GREY_600),
                                trailing=ft.IconButton(ft.Icons.DOWNLOAD, tooltip=tr("set.export_library"),
                                                       on_click=self.export_library_zip)),
                    ft.Divider(height=24),
                    heading(tr("sync.section")),
                    self.sync_folder_help,
                    self.sync_tile,
                    ft.Container(ft.Text(tr("gd.help"), size=12, color=ft.Colors.BLUE_GREY_600),
                                 padding=ft.Padding.only(left=16, right=16, top=8)),
                    self.gd_tile,
                    ft.Container(self.gd_folder, padding=ft.Padding.only(left=72, right=16, bottom=8)),
                    ft.Container(ft.Row(wrap=True, spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[self.sync_now_btn, self.sync_info]),
                                 padding=ft.Padding.only(left=16, bottom=8)),
                    ft.Divider(height=24),
                    heading(tr("set.display")),
                    ft.Container(ft.Text(tr("set.display_help"), size=12, color=ft.Colors.BLUE_GREY_600),
                                 padding=ft.Padding.only(left=16, bottom=4)),
                    option(tr("set.theme"), tr("set.theme_help"), self.set_theme),
                    option(tr("set.bar_width"), tr("set.bar_width_help"),
                           self.set_width),
                    option(tr("set.row_spacing"), tr("set.row_spacing_help"), self.set_spacing),
                    option(tr("set.notation"), tr("set.notation_help"), self.set_notation),
                    option(tr("set.chords"), tr("set.chords_help"),
                           self.set_chords),
                    option(tr("set.note_names"), tr("set.note_names_help"), self.set_names),
                    option(tr("set.colors"), tr("set.colors_help"), self.set_colors),
                    ]))])]))

    def show_settings(self, e=None):
        self.screen = "settings"
        self.page.appbar = self.set_appbar
        self.page.floating_action_button = None
        self.page.controls = [ft.SafeArea(expand=True, content=self.set_body)]
        self.draw_settings()

    def draw_settings(self):
        """Fill the settings screen with the current values (folders, sync state, Drive account)."""
        if self.screen != "settings":
            return
        st = self.settings
        default = default_library(self.home)
        syncing = self.syncer() is not None
        if env("LIBRARY"):
            root = tr("set.from_env", path=self.root)
        elif syncing:
            root = tr("sync.local_copy", path=self.root)
        elif self.store:
            root = tr("set.in_app_ios", folder=self.root.name) if self.page.platform == ft.PagePlatform.IOS \
                else tr("set.in_app")
        elif self.root == default:
            root = tr("set.examples", path=default)
        else:
            root = str(self.root)
        self.root_tile.subtitle = ft.Text(root, color=ft.Colors.BLUE_GREY_600)
        for b in self.root_tile.trailing.controls:
            b.disabled = syncing                  # a synced library lives in its local copy
        # store mode: no folders kept in the settings (the library is the app's, PDFs go through the
        # system dialog every time) and no folder sync (Google Drive only)
        self.root_tile.trailing.visible = not self.store
        self.pdf_tile.visible = self.sync_tile.visible = self.sync_folder_help.visible = not self.store
        self.sync_tile.subtitle = ft.Text(st.sync_folder if st.sync_mode == "folder" and st.sync_folder
                                          else tr("sync.folder_none"), color=ft.Colors.BLUE_GREY_600)
        self.sync_tile.trailing.controls[1].disabled = st.sync_mode != "folder"
        auth = self.google_auth()
        signed_in = bool(auth and auth.signed_in)
        if not self.google_client():
            gd_sub = tr("gd.no_client")
        elif st.sync_mode == "gdrive" and st.sync_account and signed_in:
            gd_sub = tr("gd.connected", account=st.sync_account)
        else:
            gd_sub = tr("gd.not_connected")
        self.gd_tile.subtitle = ft.Text(gd_sub, color=ft.Colors.BLUE_GREY_600)
        self.gd_tile.trailing.controls[0].disabled = not self.google_client()
        # (gd_folder.value is not refreshed here: a background sync would overwrite what is being typed)
        self.gd_tile.trailing.controls[1].disabled = not signed_in
        self.sync_now_btn.visible = self.sync_info.visible = syncing
        self.sync_now_btn.disabled = self._syncing
        self.sync_info.value = self.sync_status_text() if syncing else ""
        self.pdf_tile.subtitle = ft.Text(st.pdf_dir or tr("set.pdf_ask"),
                                         color=ft.Colors.BLUE_GREY_600)
        self.set_theme.selected = [st.theme]
        self.set_width.selected = [st.bar_width]
        self.set_spacing.selected = [st.row_spacing]
        self.set_notation.selected = [st.notation]
        self.set_chords.selected = [st.chord_symbols]
        self.set_names.selected = [st.note_names]
        self.set_colors.value = st.label_colors == "by_type"
        self.set_lang.selected = [st.language]
        self.page.update()

    def set_default(self, key: str, value: str):
        setattr(self.settings, key, value)
        self.run(self.save_settings())
        self.draw_settings()

    async def reset_root(self, e=None):
        self.settings.library_root = None
        await self.save_settings()
        self.set_root(self.library_root())
        self.draw_settings()

    async def pick_pdf_dir(self, e=None):
        path = await self.picker.get_directory_path(dialog_title=tr("set.pdf_folder"),
                                                    initial_directory=self.settings.pdf_dir)
        if path:
            self.settings.pdf_dir = path
            await self.save_settings()
            self.draw_settings()

    async def reset_pdf_dir(self, e=None):
        self.settings.pdf_dir = None
        await self.save_settings()
        self.draw_settings()

    # ================================================================ editor screen
    def build_editor(self):
        """Controls of the editor screen, built once: app bar, preview toolbar, the source editor
        (tabs, MusicXML bar, coloured text under a transparent field, completion popup, warnings,
        status) and the preview pages."""
        self.title = ft.Text("", size=18, weight=ft.FontWeight.W_600, no_wrap=True,
                             overflow=ft.TextOverflow.ELLIPSIS)
        # view ⇄ edit: the pencil opens the editor, the reader icon goes back to the sheet alone
        self.toggle_btn = ft.IconButton(ft.Icons.EDIT_OUTLINED, selected_icon=ft.Icons.CHROME_READER_MODE_OUTLINED,
                                        on_click=self.toggle_editor)
        self.fullscreen_btn = ft.IconButton(ft.Icons.FULLSCREEN, tooltip=tr("ed.fullscreen"),
                                            on_click=lambda e: self.set_fullscreen(True))
        self.save_btn = ft.IconButton(ft.Icons.SAVE_OUTLINED, tooltip=tr("ed.save"), on_click=self.save)
        self.undo_btn = ft.IconButton(ft.Icons.UNDO, tooltip=tr("ed.undo"),
                                      on_click=lambda e: self.run(self.undo_redo("undo")))
        self.redo_btn = ft.IconButton(ft.Icons.REDO, tooltip=tr("ed.redo"),
                                      on_click=lambda e: self.run(self.undo_redo("redo")))
        self.delete_btn = ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR, tooltip=tr("ed.delete"),
                                        on_click=self.delete_song)
        self.ed_appbar = ft.AppBar(
            leading=ft.IconButton(ft.Icons.ARROW_BACK, tooltip=tr("library"), on_click=self.back),
            title=self.title,
            actions=[
                self.undo_btn,
                self.redo_btn,
                self.fullscreen_btn,
                self.toggle_btn,
                self.save_btn,
                ft.IconButton(ft.Icons.SAVE_AS_OUTLINED, tooltip=tr("ed.save_as"), on_click=self.save_as_clicked),
                ft.IconButton(ft.Icons.PICTURE_AS_PDF_OUTLINED, tooltip=tr("ed.export_pdf"), on_click=self.export_pdf),
                # share sheet (Mail, Files, AirDrop…) on iPad/iPhone and Android, where files leave the app this
                # way; the song with its MusicXML as .zip everywhere (shared on mobile, saved on desktop)
                ft.PopupMenuButton(icon=ft.Icons.IOS_SHARE if self.page.platform == ft.PagePlatform.IOS
                                   else ft.Icons.SHARE, tooltip=tr("ed.share"),
                                   items=([ft.PopupMenuItem(content=ft.Text(tr("ed.share_pdf")), on_click=self.share_pdf),
                                           ft.PopupMenuItem(content=ft.Text(tr("ed.share_chs")), on_click=self.share_chs)]
                                          if self.page.platform in (ft.PagePlatform.IOS, ft.PagePlatform.ANDROID) else [])
                                   + [ft.PopupMenuItem(content=ft.Text(tr("ed.export_zip")), on_click=self.export_song_zip)]),
                self.delete_btn,
            ])
        self.theme_seg = theme_selector(lambda v: self.set_opt("theme", v))
        self.width_seg = bar_width_selector(lambda v: self.set_opt("bar_width", v))
        self.notation_seg = notation_selector(self.choose_notation)
        self.jazz_sw = ft.Switch(value=False, on_change=lambda e: self.set_opt(
            "chord_symbols", "jazz" if e.control.value else "text"))
        self.names_sw = ft.Switch(value=False, on_change=lambda e: self.set_opt(
            "note_names", "italian" if e.control.value else "letters"))
        self.colors_sw = ft.Switch(value=False, on_change=lambda e: self.set_opt(
            "label_colors", "by_type" if e.control.value else "theme"))
        self.tr_label = ft.Text("0", width=34, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_600)
        toolbar = ft.Row(
            wrap=True, spacing=14, run_spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(spacing=0, controls=[
                    ft.Text(tr("ed.transpose")),
                    ft.IconButton(ft.Icons.REMOVE, tooltip=tr("ed.semitone_down"), on_click=lambda e: self.set_transpose(-1)),
                    self.tr_label,
                    ft.IconButton(ft.Icons.ADD, tooltip=tr("ed.semitone_up"), on_click=lambda e: self.set_transpose(+1)),
                ]),
                self.theme_seg,
                self.width_seg,
                self.notation_seg,
                # the switches stay together on one line (the toolbar wraps between groups)
                ft.Row(spacing=16, tight=True, controls=[
                    ft.Row(spacing=4, tight=True, controls=[self.jazz_sw, ft.Text(tr("ed.jazz"))]),
                    ft.Row(spacing=4, tight=True, controls=[self.names_sw, ft.Text(tr("ed.italian"))]),
                    ft.Row(spacing=4, tight=True, controls=[self.colors_sw, ft.Text(tr("ed.colors"))])]),
            ])

        # source editor: the TextField's own text is transparent, the coloured Text below shows it;
        # both grow with the text and scroll together in the outer column
        self.highlight = ft.Text(spans=[], style=code_style())
        self.editor = ft.TextField(
            multiline=True, min_lines=1, max_lines=None, text_style=code_style(ft.Colors.TRANSPARENT),
            strut_style=ft.StrutStyle(font_family=CODE_FONT, size=CODE_SIZE, height=CODE_LINE,
                                      force_strut_height=True),
            border=ft.InputBorder.NONE, content_padding=ft.Padding.all(CODE_PAD), left=0, right=0, top=0,
            cursor_color="#FFCC00", cursor_width=CURSOR_W, selection_color=ft.Colors.with_opacity(0.35, "#5C8DFF"),
            autocorrect=False, enable_suggestions=False,
            # iPad/iOS keyboards would turn " into “ ” and -- into —, breaking annotations and lyrics
            smart_dashes_type=False, smart_quotes_type=False, capitalization=ft.TextCapitalization.NONE,
            keyboard_type=ft.KeyboardType.MULTILINE,
            on_change=self.on_edit, on_selection_change=self.on_caret,
            on_focus=lambda e: self.set_focus(True), on_blur=lambda e: self.set_focus(False))
        self.ac_list = ft.Column(spacing=0, tight=True, scroll=ft.ScrollMode.AUTO)
        self.ac_popup = ft.Container(
            visible=False, width=POPUP_W, left=0, top=0, bgcolor="#2B2F38", border_radius=6,
            border=ft.Border.all(1, "#454B57"), padding=ft.Padding.symmetric(vertical=4),
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK)),
            content=self.ac_list)
        code = ft.Stack(controls=[
            # the field keeps cursor width + 1 px free at the right edge: wrap the copy at the same width
            ft.Container(self.highlight, alignment=ft.Alignment.TOP_LEFT,
                         padding=ft.Padding.only(left=CODE_PAD, top=CODE_PAD - HIGHLIGHT_SHIFT, bottom=CODE_PAD,
                                                 right=CODE_PAD + CURSOR_W + 1)),
            self.editor,
            self.ac_popup,
        ])
        self.code_view = ft.Column(
            expand=True, spacing=0, scroll=ft.ScrollMode.AUTO, on_scroll=self.on_code_scroll,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[code,
                      # room below the last line (and for the popup): a tap there puts the caret at the end
                      ft.Container(height=POPUP_ROWS * POPUP_ROW_H + 40, on_click=self.focus_end)])
        self.status = ft.Text("", size=12, color="#8A93A6")
        self.upgrade_btn = ft.TextButton(tr("ed.upgrade", v=formats.label(formats.CURRENT)), visible=False,
                                         icon=ft.Icons.UPGRADE, on_click=self.upgrade_format,
                                         style=ft.ButtonStyle(color="#78A6FF"))
        self.warn_list = ft.ListView(spacing=0, height=0)
        self.tabs = ft.Row(spacing=0, scroll=ft.ScrollMode.AUTO)
        self.tab_banner = ft.Container(visible=False, bgcolor="#2A2D35",
                                       padding=ft.Padding.symmetric(horizontal=12, vertical=8))
        # MusicXML tabs are read only: a bar says so and offers the conversion into notes of the song
        self.xml_bar = ft.Container(
            visible=False, bgcolor="#262A31", padding=ft.Padding.symmetric(horizontal=12, vertical=4),
            width=float("inf"),                     # the bar spans the whole editor
            content=ft.Row(spacing=12, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Row(tight=True, spacing=6, controls=[
                    ft.Icon(ft.Icons.VISIBILITY_OUTLINED, size=16, color="#8A93A6"),
                    ft.Text(tr("xml.read_only"), size=12, color="#8A93A6")]),
                ft.FilledTonalButton(tr("xml.convert"), icon=ft.Icons.AUTO_FIX_HIGH, tooltip=tr("xml.convert_tip"),
                                     on_click=lambda e: self.run(self.convert_xml())),
            ]))
        self.editor_panel = ft.Container(
            expand=1, bgcolor=EDITOR_BG,
            content=ft.Column(expand=True, spacing=0, controls=[
                ft.Container(self.tabs, bgcolor=TAB_BG), self.tab_banner, self.xml_bar,
                self.code_view, ft.Divider(height=1, color="#3A3F4B"), self.warn_list,
                ft.Container(ft.Row([ft.Container(self.status, expand=True), self.upgrade_btn],
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
                             padding=ft.Padding.symmetric(horizontal=12, vertical=4))]))
        self.pages = ft.ListView(expand=True, spacing=PAGE_GAP, padding=ft.Padding.all(16))
        self.error_box = ft.Container(visible=False, bgcolor=ft.Colors.RED_50,
                                      padding=ft.Padding.symmetric(horizontal=12, vertical=6))
        self.toolbar_box = ft.Container(toolbar, padding=ft.Padding.only(left=12, right=12, top=6))
        self.preview_panel = ft.Column(expand=1, spacing=6, controls=[self.toolbar_box, self.error_box, self.pages])
        self.divider = ft.VerticalDivider(width=1)
        self.ed_body = ft.Row(expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                              controls=[self.editor_panel, self.divider, self.preview_panel])
        # full screen: only the pages, plus an always visible way out (also Esc)
        self.exit_fullscreen_btn = ft.Container(
            right=16, top=12,
            content=ft.FilledTonalButton(
                tr("ed.exit_fullscreen"), icon=ft.Icons.FULLSCREEN_EXIT, tooltip=tr("ed.exit_fullscreen_tip"),
                on_click=lambda e: self.set_fullscreen(False),
                style=ft.ButtonStyle(bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.BLUE_GREY_50),
                                     elevation=3)))

    def open_song(self, path: Path, edit: bool = False):
        """Open a song in view mode (the sheet alone); `edit` opens the editor too (new songs)."""
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            self.toast(tr("ed.open_failed", name=path.name, err=err))
            return
        self.run(self.open_text(text, path.stem, path.parent, path, edit=edit))

    async def open_text(self, text: str, name: str, base_dir: Path | None, path: Path | None,
                        notes: list[str] | None = None, saved: bool = True, edit: bool = False):
        if not await self.confirm_discard():
            return
        self.name, self.base_dir, self.path = name, base_dir, path
        self.docs = [Doc("chs", path.name if path else name, path, text, text if saved else "")]
        self.doc_index = 0
        self.load_musicxml_docs()
        self.notes = list(notes or [])
        self.transpose, self.current_page, self.dl, self.error, self.song_title = 0, 0, None, None, None
        self.opts = self.settings.layout_options()          # every song starts from the defaults
        self.show_editor = edit                             # view mode unless asked (new or imported song)
        self.fullscreen = False
        self.sync_option_controls()
        self.show_doc()
        self.show_editor_screen()
        await self.render()

    def show_editor_screen(self):
        self.screen = "editor"
        self.page.appbar = self.ed_appbar
        self.page.floating_action_button = None
        self.page.controls = [ft.SafeArea(expand=True, content=self.ed_body)]
        self.update_chrome()
        self.page.update()

    def dirty(self) -> bool:
        return self.screen == "editor" and any(d.dirty for d in self.docs)

    # ---- tabs: the song and the MusicXML files it references
    def load_musicxml_docs(self) -> list[str]:
        """Add a tab for every MusicXML file the song references and has no tab yet (in order of
        reference); tabs of files no longer referenced go away unless they have unsaved changes.
        Returns the names of the new tabs. Needs the song's folder (base_dir). The files are read only:
        shown with one element per line (xml_syntax.format_xml), never written."""
        refs = library.musicxml_refs(self.text) if self.base_dir else []
        keep = {d.name: d for d in self.docs[1:] if d.name in refs}
        added: list[str] = []
        docs = [self.docs[0]]
        for ref in refs:
            if ref in keep:
                docs.append(keep.pop(ref))
                continue
            path = self.base_dir / ref
            d = Doc("xml", ref, path)
            if not path.is_file():
                d.missing = True
            elif path.suffix.lower() == ".mxl":
                d.note = tr("tab.compressed", name=ref)       # cannot be shown, but can be converted
            else:
                try:
                    raw = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as err:
                    d.note = tr("tab.read_failed", name=ref, err=err)
                else:
                    d.text = d.saved = d.base = raw if xml_syntax.xml_error(raw) else xml_syntax.format_xml(raw)
            docs.append(d)
            added.append(ref)
        current = self.doc
        self.docs = docs
        self.doc_index = docs.index(current) if current in docs else 0
        return added

    def draw_tabs(self):
        tabs = []
        for i, d in enumerate(self.docs):
            active = i == self.doc_index
            label = tr("tab.missing", name=d.name) if d.missing else d.name
            tabs.append(ft.Container(
                padding=ft.Padding.only(left=12, right=12, top=8, bottom=6), tooltip=str(d.path or d.name),
                bgcolor=EDITOR_BG if active else None, on_click=lambda e, i=i: self.run(self.switch_tab(i)),
                border=ft.Border.only(bottom=ft.BorderSide(2, "#FFCC00" if active else TAB_BG)),
                content=ft.Row(tight=True, spacing=6, controls=[
                    ft.Icon(ft.Icons.MUSIC_NOTE if d.kind == "chs" else ft.Icons.QUEUE_MUSIC, size=14,
                            color=EDITOR_FG if active else "#8A93A6"),
                    ft.Text(("● " if d.dirty else "") + label, size=12, no_wrap=True,
                            color=EDITOR_FG if active else "#8A93A6",
                            italic=d.missing)])))
        self.tabs.controls = tabs
        d = self.doc
        if d.note:
            self.tab_banner.content = ft.Text(d.note, size=12, color="#F0A974")
        elif d.missing and not d.text:
            self.tab_banner.content = ft.Text(tr("tab.missing_text", name=d.name), size=12, color="#F0A974")
        self.tab_banner.visible = bool(d.note or d.missing)
        self.editor.read_only = d.kind == "xml"
        self.xml_bar.visible = d.kind == "xml" and not d.missing and d.path is not None

    def show_doc(self):
        """Put the active document in the editor."""
        self.editor.value = self.doc.text
        self.hide_completions()
        self.paint_source()
        self.draw_tabs()

    async def switch_tab(self, index: int):
        if index == self.doc_index or index >= len(self.docs):
            return
        self.doc_index = index
        self.show_doc()
        self.update_chrome()
        self.page.update()
        await self.code_view.scroll_to(offset=self.doc.scroll, duration=0)

    def on_code_scroll(self, e):
        self.doc.scroll = e.pixels

    async def convert_xml(self):
        """Write the bars of the open MusicXML tab as notes in the song (library.convert_musicxml): its
        references become {start_of_notes} blocks, kept above them as comments; the file is not touched.
        The song is changed in the editor, to be saved (or discarded) as any other edit."""
        d = self.doc
        if d.kind != "xml" or not d.path or not self.base_dir:
            return
        if await self.ask(tr("xml.convert_title", name=d.name), ft.Text(tr("xml.convert_text", name=d.name)),
                          [(tr("cancel"), None), (tr("xml.convert_ok"), "ok")]) != "ok":
            return
        try:
            result = await asyncio.to_thread(library.convert_musicxml, self.text, d.name, self.base_dir,
                                             tr("xml.converted_note"))
        except Exception as err:                    # noqa: BLE001  unreadable or broken file
            self.toast(tr("xml.convert_failed", name=d.name, err=err))
            return
        if not result.count:
            return
        self.docs[0].history.record(self.text, result.text, time.monotonic(), group=False)
        self.text = result.text
        self.load_musicxml_docs()                   # the file is no longer referenced: its tab goes away
        self.doc_index = 0
        self.show_doc()
        at = self.text.find(f"# {{musicxml: {d.name}")
        if at >= 0:
            self.editor.selection = ft.TextSelection(base_offset=at, extent_offset=at)
        self.update_chrome()
        self.page.update()
        self.toast(tr("xml.converted" if result.exact else "xml.converted_check", name=d.name, n=result.count))
        await self.render()

    def update_chrome(self):
        """Refresh everything around the source after a change: title with ●, Save, Undo/Redo, the
        editor/preview visibility, tabs and the status line (file, lines, format version)."""
        dirty = self.dirty()
        self.title.value = ("● " if dirty else "") + (self.song_title or self.name)
        # Save: disabled until something changes (song or a MusicXML tab), then enabled and green
        self.save_btn.disabled = not dirty
        self.save_btn.icon = ft.Icons.SAVE if dirty else ft.Icons.SAVE_OUTLINED
        self.save_btn.icon_color = SAVE_COLOR if dirty else None
        self.title.tooltip = str(self.path) if self.path else tr("ed.not_saved_tooltip")
        self.editor_panel.visible = self.divider.visible = self.show_editor
        # undo / redo of the song source, while it is being edited
        self.undo_btn.visible = self.redo_btn.visible = self.show_editor and not self.fullscreen
        self.undo_btn.disabled = not self.docs[0].history.can_undo
        self.redo_btn.disabled = not self.docs[0].history.can_redo
        self.toggle_btn.selected = not self.show_editor
        self.delete_btn.visible = self.path is not None        # a song never saved has no file to delete
        self.toggle_btn.tooltip = tr("ed.hide_editor") if self.show_editor else tr("ed.show_editor")
        if self.fullscreen:
            self.editor_panel.visible = self.divider.visible = False
        where = self.path.relative_to(self.root).as_posix() if self.path and self.root and \
            self.path.is_relative_to(self.root) else (str(self.path) if self.path else tr("ed.not_saved"))
        self.draw_tabs()
        if self.doc.kind == "xml":
            lines = self.doc.text.count("\n") + 1
            self.status.value = tr("ed.status_xml", where=self.doc.name, lines=lines)
            self.upgrade_btn.visible = False
            return
        lines = self.text.count("\n") + 1
        fmt = formats.detect(self.text)
        version = formats.label(fmt.version) + ("" if fmt.declared else tr("ed.format_undeclared"))
        if fmt.version > formats.CURRENT:
            version += tr("ed.format_newer", v=formats.label(formats.CURRENT))
        self.status.value = tr("ed.status", where=where, lines=lines, version=version) + \
            (tr("ed.unsaved") if self.docs[0].dirty else "")
        self.upgrade_btn.visible = formats.needs_upgrade(self.text)

    def set_focus(self, focused: bool):
        self.editor_focused = focused
        if not focused and self.ac_popup.visible:
            self.run(self.hide_after_blur())

    async def hide_after_blur(self):
        """A tap on the popup or Tab takes the focus away before the choice arrives: wait for it."""
        await asyncio.sleep(0.4)
        if not self.editor_focused and self.ac_popup.visible:
            self.hide_completions()
            self.page.update()

    def set_fullscreen(self, on: bool, redraw: bool = True):
        """Full screen: no app bar, toolbar, editor or status, just the pages (window full screen on
        desktop); the "Exit full screen" button stays in the corner, Esc does the same."""
        if on == self.fullscreen and redraw:
            return
        self.fullscreen = on
        self.toolbar_box.visible = not on
        if self.page.platform in DESKTOP:
            self.page.window.full_screen = on
        if self.screen == "editor" and redraw:
            self.page.appbar = None if on else self.ed_appbar
            body = ft.SafeArea(expand=True, content=self.ed_body)
            self.page.controls = [ft.Stack(expand=True, controls=[body, self.exit_fullscreen_btn])] if on else [body]
            self.update_chrome()
            self.draw()

    def toggle_editor(self, e=None):
        self.show_editor = not self.show_editor
        self.update_chrome()
        self.draw()

    async def back(self, e=None):
        if not await self.confirm_discard():
            return
        self.docs, self.doc_index = [Doc("chs", "", None)], 0
        self.show_library()

    # ---- source editor: highlighting and directive completion
    def paint_source(self):
        """Coloured copy of the source under the (transparent) text field."""
        text = self.editor.value or ""
        lang, colors = (xml_syntax, XML_COLORS) if self.doc.kind == "xml" else (syntax, {})
        # what differs from the text as opened or last saved gets a green background
        pieces = edits.mark(lang.tokens(text), edits.changes(self.doc.base, text))
        self.highlight.spans = [ft.TextSpan(s, code_style(SYNTAX_COLORS[colors.get(k, k)], italic=(k == "comment"),
                                                          bgcolor=CHANGE_BG.get(level)))
                                for k, s, level in pieces]
        # a trailing newline needs a character after it, or the Text is one line shorter than the field
        if text.endswith("\n") or not text:
            self.highlight.spans.append(ft.TextSpan(" ", code_style()))

    async def focus_end(self, e=None):
        n = len(self.editor.value or "")
        self.editor.selection = ft.TextSelection(base_offset=n, extent_offset=n)
        self.page.update()
        await self.editor.focus()

    async def on_edit(self, e):
        """Every change of the source text (typing, paste, the field's own undo): update the document,
        the undo history, the colours and the completion popup, then redraw the preview after a
        short pause (schedule_render), not at every keystroke."""
        if self.doc.kind != "chs":               # MusicXML tabs are read only
            return
        old, new = self.doc.text, self.editor.value or ""
        if self._undo_key and time.monotonic() - self._undo_key[1] < 0.5:
            # ⌘Z / Ctrl+Z also reached the text field, which undid on its own: use the app's history instead
            action, self._undo_key = self._undo_key[0], None
            self.editor.value = old
            await self.undo_redo(action)
            return
        caret = edit_caret(old, new)
        if self.ac_popup.visible and new in (old[:self.ac_caret] + ch + old[self.ac_caret:] for ch in "\n\t"):
            # Enter (or Tab) while the popup is open: accept the highlighted completion instead.
            # The key cannot be intercepted before the field handles it, so the newline (or tab) has
            # already been inserted when we hear about it: put the old text back, then complete
            self.editor.value = old
            await self.accept_completion(self.ac_index, caret=self.ac_caret)
            return
        self.doc.text = new
        self.doc.history.observe(old, new, time.monotonic())   # also the text field's own undo / redo
        self.paint_source()
        if len(new) >= len(old) and syntax.context(new, caret):
            self.show_completions(caret)
        else:
            self.hide_completions()
        self.update_chrome()
        self.page.update()
        await self.schedule_render()

    async def schedule_render(self):
        self._typing += 1
        ticket = self._typing
        await asyncio.sleep(PREVIEW_DELAY)
        if ticket == self._typing:
            await self.render()

    async def on_caret(self, e: ft.TextSelectionChangeEvent):
        """Close the popup when the caret leaves the directive name (clicks, arrows outside the popup)."""
        self.last_selection = e.selection
        caret = e.selection.extent_offset
        if e.cause is None:                   # set by the app (completion accepted, popup navigation)
            return
        await asyncio.sleep(0.05)             # the text change of the same keystroke may come later
        if not self.ac_popup.visible or time.monotonic() < self._nav_until:
            return
        if caret != self.ac_caret and not syntax.context(self.editor.value or "", caret):
            self.hide_completions()
            self.page.update()

    def show_completions(self, caret: int):
        items = syntax.suggestions(self.editor.value or "", caret)
        if not items:
            self.hide_completions()
            return
        self.ac_items, self.ac_caret = items, caret
        self.ac_index = 0
        self.ac_popup.visible = True
        self.draw_completions()
        row, col = self.caret_row_col(caret)
        line_h = CODE_SIZE * CODE_LINE
        cw = CODE_SIZE * CODE_ADVANCE
        self.ac_popup.top = CODE_PAD + (row + 1) * line_h + 2
        self.ac_popup.left = max(4, min(CODE_PAD + col * cw - 16, self.editor_width() - POPUP_W - 4))
        self.ac_list.height = min(len(items), POPUP_ROWS) * POPUP_ROW_H

    def draw_completions(self):
        rows = []
        for i, c in enumerate(self.ac_items):
            sel = i == self.ac_index
            rows.append(ft.Container(
                height=POPUP_ROW_H, padding=ft.Padding.symmetric(horizontal=10),
                bgcolor="#3D5A99" if sel else None, on_click=lambda e, i=i: self.run(self.accept_completion(i)),
                content=ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(c.name, style=code_style(SYNTAX_COLORS[
                        "section" if c.name.startswith(("start_of_", "end_of_")) and "notes" not in c.name
                        else "directive"])),
                    ft.Text(c.hint, size=11, color="#9AA3B5", expand=True, no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS)])))
        self.ac_list.controls = rows

    def hide_completions(self):
        self.ac_popup.visible = False
        self.ac_items = []

    async def accept_completion(self, index: int, caret: int | None = None):
        if not self.ac_items:
            return
        text = self.editor.value or ""
        new, a, b = syntax.apply(text, self.ac_caret if caret is None else caret, self.ac_items[index])
        self.hide_completions()
        self.doc.history.record(self.doc.text, new, time.monotonic(), group=False)
        self.doc.text = new
        self.editor.value = new
        self.paint_source()
        self.editor.selection = ft.TextSelection(base_offset=a, extent_offset=b)
        self.update_chrome()
        self.page.update()
        await self.editor.focus()
        await self.schedule_render()

    # ---- undo / redo of the song source
    async def undo_redo(self, action: str):
        """Undo ("undo") or redo ("redo") one step of the song source (edits.History), on its tab."""
        d = self.docs[0]
        step = d.history.undo() if action == "undo" else d.history.redo()
        if step is None:
            return
        text, caret = step
        d.text = text
        self.doc_index = 0
        self.show_doc()
        caret = min(caret, len(text))
        self.editor.selection = ft.TextSelection(base_offset=caret, extent_offset=caret)
        self.update_chrome()
        self.page.update()
        await self.schedule_render()

    def caret_row_col(self, caret: int) -> tuple[int, int]:
        """Visual row and column of the caret (lines wrap between words at the editor width)."""
        columns = int((self.editor_width() - 2 * CODE_PAD - CURSOR_W - 1) // (CODE_SIZE * CODE_ADVANCE))
        # one column less: if anything, wrap too early, so the popup never covers the caret's line
        return syntax.caret_row_col(self.editor.value or "", caret, columns - 1)

    def editor_width(self) -> float:
        return ((self.page.width or 1000) - 1) / 2

    async def completion_key(self, key: str) -> bool:
        """Keys for the open popup: ↑/↓ choose, Tab accepts (Enter is handled in on_edit), Esc closes."""
        if not self.ac_popup.visible:
            return False
        if key == "Tab":
            await self.accept_completion(self.ac_index)
            return True
        if key in ("Arrow Down", "Arrow Up"):
            n = len(self.ac_items)
            self.ac_index = (self.ac_index + (1 if key == "Arrow Down" else -1)) % n
            self._nav_until = time.monotonic() + 0.4
            self.draw_completions()
            # the field moved the caret as well: put it back
            self.editor.selection = ft.TextSelection(base_offset=self.ac_caret, extent_offset=self.ac_caret)
            self.page.update()
            await self.ac_list.scroll_to(offset=max(0, (self.ac_index - POPUP_ROWS + 1) * POPUP_ROW_H),
                                         duration=0)
            return True
        if key == "Escape":
            self.hide_completions()
            self.page.update()
            return True
        return False

    # ---- live preview
    async def render(self):
        """Parse and lay out the current text (off the UI thread) and redraw the preview.
        On an engine error the last good preview stays and the error is shown above it."""
        text, semis, opts, base = self.text, self.transpose, dict(self.opts), self.base_dir
        try:
            dl, title, song_notation = await asyncio.to_thread(self.build, text, semis, opts, base)
        except Exception as err:          # keep typing even if the engine chokes on a half-written line
            self.error = f"{type(err).__name__}: {err}"
        else:
            if text != self.text or semis != self.transpose or opts != self.opts:
                return                    # stale: a newer render is on its way
            self.dl, self.error, self.song_title = dl, None, title
            if not opts.get("notation_force"):      # until the reader switches: show the song's own choice
                self.notation_seg.selected = [song_notation or opts["notation"]]
        self.draw()

    @staticmethod
    def build(text, transpose, opts, base_dir):
        song = parse(text, transpose=transpose, base_dir=base_dir)
        return layout(song, **opts), song.meta.get("title"), song.meta.get("notation")

    def draw(self):
        """Redraw the preview from the last DisplayList: one canvas per page, scaled to the panel
        width (up to MAX_SCALE), with the engine error and the warnings around it."""
        if self.screen != "editor":
            return
        self.tr_label.value = f"{self.transpose:+d}" if self.transpose else "0"
        self.error_box.visible = bool(self.error)
        if self.error:
            self.error_box.content = ft.Text(tr("ed.engine_error", err=self.error),
                                             size=12, color=ft.Colors.RED_900)
        self.draw_warnings()
        self.update_chrome()
        if self.dl:
            pw, ph = self.dl.page_size
            width = self.page.width or 1000
            if self.show_editor and not self.fullscreen:
                width = (width - 1) / 2
            self.scale = max(0.3, min(MAX_SCALE, (width - 2 * 16 - 8) / pw))
            # the same metrics the layout measured with: page_shapes positions text by them
            metrics = registry(self.opts["theme"])
            self.pages.controls = [
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[
                    ft.Container(
                        key=ft.ScrollKey(f"p{i}"),
                        width=pw * self.scale, height=ph * self.scale, bgcolor=ft.Colors.WHITE,
                        shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK)),
                        content=cv.Canvas(shapes=page_shapes(self.dl, i, metrics, self.scale),
                                          width=pw * self.scale, height=ph * self.scale))])
                for i in range(len(self.dl.pages))]
        self.page.update()

    def draw_warnings(self):
        items = [ft.Text(f"ℹ {n}", size=12, color=ft.Colors.BLUE_GREY_700) for n in self.notes]
        for w in (self.dl.warnings if self.dl else []):
            line = library.warning_line(w)
            items.append(ft.Container(
                ft.Text(f"⚠ {w}", size=12, color=ft.Colors.AMBER_900),
                tooltip=tr("ed.goto_line") if line else None,
                on_click=(lambda e, n=line: self.goto_line(n)) if line else None))
        self.warn_list.controls = [ft.Container(c, padding=ft.Padding.symmetric(horizontal=12, vertical=2))
                                   for c in items]
        self.warn_list.height = min(len(items), 5) * 20 + (8 if items else 0)

    async def goto_line(self, line: int):
        if self.fullscreen:
            self.set_fullscreen(False)
        if not self.show_editor:
            self.toggle_editor()
        await self.switch_tab(0)                # warnings refer to the song source
        start = library.line_offset(self.text, line)
        end = self.text.find("\n", start)
        self.editor.selection = ft.TextSelection(base_offset=start, extent_offset=len(self.text) if end < 0 else end)
        self.page.update()
        await self.editor.focus()

    # ---- options
    def sync_option_controls(self):
        self.theme_seg.selected = [self.opts["theme"]]
        self.width_seg.selected = [self.opts["bar_width"]]
        self.notation_seg.selected = [self.opts["notation"]]
        self.jazz_sw.value = self.opts["chord_symbols"] == "jazz"
        self.names_sw.value = self.opts["note_names"] == "italian"
        self.colors_sw.value = self.opts["label_colors"] == "by_type"

    def set_transpose(self, d: int):
        self.transpose += d
        self.run(self.render())

    def set_opt(self, key, value):
        self.opts[key] = value
        self.run(self.render())

    def choose_notation(self, value):
        """The switch over the sheet is the reader's choice: it beats the song's {notation} and its sections'."""
        self.opts["notation"] = value
        self.opts["notation_force"] = True
        self.run(self.render())

    # ---- saving
    async def upgrade_format(self, e=None):
        """Rewrite the source in the current format (the user then saves as usual)."""
        new, old, to = formats.upgrade(self.text)
        if new == self.text:
            return
        self.docs[0].history.record(self.text, new, time.monotonic(), group=False)
        self.text = new
        await self.switch_tab(0)
        self.show_doc()
        self.toast(tr("ed.upgraded", old=formats.label(old), new=formats.label(to)))
        await self.render()

    async def confirm_newer_format(self) -> bool:
        """A file in a newer format was read only in part: saving it from here may lose information."""
        fmt = formats.detect(self.text)
        if fmt.version <= formats.CURRENT:
            return True
        return await self.ask(
            tr("ed.newer_title"),
            ft.Text(tr("ed.newer_text", v=formats.label(fmt.version), current=formats.label(formats.CURRENT))),
            [(tr("cancel"), None), (tr("ed.save_anyway"), "ok")]) == "ok"

    async def save(self, e=None):
        """Save every open file with changes: the song and its MusicXML tabs (nothing if none changed)."""
        if self.screen != "editor" or (self.path and not self.dirty()):
            return
        if not self.path:
            if await self.save_as():
                await self.refresh_tabs([self.path.name if self.path else self.name])
            return
        if not await self.confirm_newer_format():
            return
        if self.docs[0].dirty:
            self.stamp(created=library.file_created(self.path))
        try:
            self.path.write_text(self.text, encoding="utf-8")
        except OSError as err:
            self.toast(tr("ed.save_failed", err=err))
            return
        self.saved_text = self.text
        await self.refresh_tabs([self.path.name])

    async def refresh_tabs(self, saved: list[str]):
        """After saving the song: look for the MusicXML files it references now (the tabs are read
        only, there is nothing of theirs to write); each new reference gets its tab (opened right away
        if it is the first one). The song's changes are no longer painted: it is the saved text now."""
        if self.doc_index == 0:
            self.paint_source()
        had_xml = len(self.docs) > 1
        added = self.load_musicxml_docs()
        msg = tr("ed.saved", name=", ".join(saved))
        if added:
            msg += " · " + tr("tab.new_tabs", names=", ".join(added))
            if not had_xml and self.doc_index == 0:
                await self.switch_tab(1)              # the first MusicXML of the song: show it
        self.draw()
        self.toast(msg)
        self.run(self.sync_now())

    async def save_as_clicked(self, e=None):
        if await self.save_as():
            await self.refresh_tabs([self.path.name if self.path else self.name])

    def stamp(self, created: datetime | None = None, new_file: bool = False):
        """Write {created}/{modified} into the song source (library.stamp), keeping the caret where it was."""
        old = self.text
        new = library.stamp(old, datetime.now(), created, new_file)
        if new == old:
            return
        self.text = new
        if self.doc_index == 0:
            sel = self.last_selection
            p = next((i for i, (a, b) in enumerate(zip(old, new)) if a != b), min(len(old), len(new)))
            shift = len(new) - len(old)

            def moved(x: int) -> int:
                return x + shift if x > p else x
            self.show_doc()
            if sel is not None:
                self.editor.selection = ft.TextSelection(base_offset=moved(sel.base_offset),
                                                         extent_offset=moved(sel.extent_offset))

    async def save_as(self, e=None) -> bool:
        """Save under a new name. Inside the library: a name dialog, saved next to the song (or in the open
        folder), so the new file is in the library and keeps the song's relative MusicXML references; the
        system dialog is a button away (*Other location…*), and the only way for files outside the library."""
        if not await self.confirm_newer_format():
            return False
        folder = self.path.parent if self.path else (self.cwd or self.root)
        if self.root and folder and folder.is_relative_to(self.root):
            name = ft.TextField(label=tr("ed.file_name"), autofocus=True, suffix=ft.Text(library.EXT),
                                value=self.path.stem if self.path else (self.song_title or self.name))
            choice = await self.ask(tr("ed.save_as"), ft.Column(tight=True, controls=[
                name, ft.Text(tr("lib.new_in", folder=self.place_label(folder)), size=12,
                              color=ft.Colors.BLUE_GREY_600)]),
                [(tr("cancel"), None), (tr("ed.other_place"), "other"), (tr("save"), "ok")])
            if choice is None:
                return False
            if choice == "ok":
                stem = (name.value or "").strip()
                if stem.lower().endswith(library.EXT):
                    stem = stem[:-len(library.EXT)]
                path = library.new_song_path(folder, stem or self.song_title or self.name)   # never overwrites
                self.stamp(new_file=True)                 # a new file: created now
                try:
                    path.write_text(self.text, encoding="utf-8")
                except OSError as err:
                    self.toast(tr("ed.save_failed", err=err))
                    return False
                self.path, self.base_dir, self.name = path, path.parent, path.stem
                self.docs[0].name, self.docs[0].path = path.name, path
                self.saved_text = self.text
                self.draw()
                self.toast(tr("ed.saved", name=path.name))
                return True
        return await self.save_as_elsewhere()

    async def save_as_elsewhere(self) -> bool:
        """Save under a new name with the system dialog (anywhere)."""
        old = self.text
        self.stamp(new_file=True)
        data = self.text.encode("utf-8")
        start = self.path.parent if self.path else (self.cwd or self.root)
        path = await self.picker.save_file(dialog_title=tr("ed.save_source"),
                                           file_name=f"{library.safe_filename(self.song_title or self.name)}.chs",
                                           initial_directory=str(start) if start else None,
                                           allowed_extensions=["chs"], src_bytes=data)
        if not path:
            self.text = old                       # cancelled: no stamp
            if self.doc_index == 0:
                self.show_doc()
            return False
        path = Path(path)
        if self.page.platform in DESKTOP:
            if path.suffix.lower() != library.EXT:
                path = path.with_suffix(library.EXT)
            try:
                path.write_bytes(data)          # desktop: the dialog only returns the path
            except OSError as err:
                self.toast(tr("ed.save_failed", err=err))
                return False
            self.path, self.base_dir = path, path.parent
        self.name = path.stem
        self.docs[0].name = path.name
        self.saved_text = self.text
        self.draw()
        self.toast(tr("ed.saved", name=path.name))
        return True

    async def delete_song(self, e=None):
        """Delete the open song after confirmation, then go back to the library."""
        if self.screen != "editor" or not self.path:
            return
        path = self.path
        synced = self.sync_state() is not None and self.root is not None and path.is_relative_to(self.root)
        try:
            plan = library.delete_plan(path, self.root)
        except ValueError as err:
            self.toast(tr("ed.delete_failed", err=err))
            return
        here = path.parent

        def shown(p: Path) -> str:
            return p.relative_to(here).as_posix() if p.is_relative_to(here) else str(p)

        def bullet(text: str, **kw) -> ft.Control:
            return ft.Text(f"•  {text}", **kw)

        lines: list[ft.Control] = [ft.Text(tr("ed.delete_text", title=self.song_title or self.name))]
        lines += [bullet(shown(f), weight=ft.FontWeight.W_600) for f in plan.files]
        if plan.kept:
            lines.append(ft.Text(tr("ed.delete_kept")))
            for f, why in plan.kept.items():
                if isinstance(why, list):
                    text = tr("ed.kept_shared", file=shown(f), songs=", ".join(shown(s) for s in why))
                else:
                    text = tr(f"ed.kept_{why}", file=shown(f))
                lines.append(bullet(text, color=ft.Colors.ON_SURFACE_VARIANT))
        lines.append(ft.Text(tr("ed.delete_synced") if synced else tr("ed.delete_final")))
        if self.dirty():
            lines.append(ft.Text(tr("ed.delete_unsaved")))
        choice = await self.ask(tr("ed.delete_title"), ft.Column(lines, tight=True, spacing=6, scroll=ft.ScrollMode.AUTO),
                                [(tr("cancel"), None), (tr("ed.delete_confirm"), "delete")], danger=True)
        if choice != "delete":
            return
        try:
            library.delete_song(path, self.root, self.sync_state() / "trash" if synced else None)
        except (OSError, ValueError) as err:
            self.toast(tr("ed.delete_failed", err=err))
            return
        self.docs, self.doc_index = [Doc("chs", "", None)], 0
        self.path = None
        self.show_library()                   # rescans and syncs: the deletion reaches the remote
        self.toast(tr("ed.deleted", name=path.name))

    async def confirm_discard(self) -> bool:
        """True if the open document can be closed: no changes, or the user saved or discarded them."""
        if not self.dirty():
            return True
        choice = await self.ask(tr("ed.unsaved_title"),
                                ft.Text(tr("ed.unsaved_text", name=self.song_title or self.name)),
                                [(tr("cancel"), None), (tr("ed.dont_save"), "discard"), (tr("save"), "save")])
        if choice == "discard":
            return True
        if choice == "save":
            await self.save()
            return not self.dirty()
        return False

    async def on_window_event(self, e):
        """Desktop: the window's close button is intercepted (prevent_close) to ask about unsaved
        changes first; the window is destroyed only once that is settled."""
        if e.type == ft.WindowEventType.CLOSE:
            if await self.confirm_discard():
                await self.page.window.destroy()

    # ---- opening and importing single files
    async def pick_file(self, e):
        """Import a .chs file into the library (the open folder; the main one during a search), with the
        MusicXML files it cites, never overwriting (library.import_song); then open the copy."""
        if not self.root:
            return
        files = await self.picker.pick_files(dialog_title=tr("ed.open_song"), allowed_extensions=["chs", "zip"],
                                             with_data=True)
        if not files:
            return
        f = files[0]
        src = Path(f.path) if f.path and Path(f.path).exists() else None
        if f.name.lower().endswith(".zip"):
            await self.import_zip_file(f, src)
            return
        try:
            text = src.read_text(encoding="utf-8") if src else (f.bytes or b"").decode("utf-8")
        except (OSError, UnicodeDecodeError) as err:
            self.toast(tr("ed.open_failed", name=f.name, err=err))
            return
        dest = self.cwd if self.cwd and not self.query.strip() else self.root
        try:
            # on a phone or the web the file comes without its folder: its MusicXML cannot be copied
            result = library.import_song(dest, f.name, text, src.parent if src else None)
        except OSError as err:
            self.toast(tr("lib.import_chs_failed", err=err))
            return
        msg = tr("lib.imported_chs", name=result.path.name, folder=self.place_label(dest))
        if result.copied:
            msg += tr("lib.imported_xml", n=len(result.copied))
        if result.missing:
            msg += tr("lib.imported_missing", names=", ".join(result.missing))
        self.rescan()
        self.open_song(result.path)
        self.toast(msg)
        self.run(self.sync_now())

    async def import_zip_file(self, f, src: Path | None):
        """A .zip into the open folder (library.import_zip): one song with its MusicXML (then opened), or
        several songs, e.g. an exported library, in a new folder named after the archive."""
        dest = self.cwd if self.cwd and not self.query.strip() else self.root
        try:
            data = src.read_bytes() if src else (f.bytes or b"")
            result = await asyncio.to_thread(library.import_zip, dest, data, f.name)
        except library.BadZip as err:
            self.toast(tr("lib.zip_bad", name=f.name, err=err))
            return
        except OSError as err:
            self.toast(tr("lib.import_chs_failed", err=err))
            return
        self.rescan()
        if result.folder is None:
            msg = tr("lib.imported_chs", name=result.songs[0].name, folder=self.place_label(dest))
            if result.copied:
                msg += tr("lib.imported_xml", n=len(result.copied))
            if result.missing:
                msg += tr("lib.imported_missing", names=", ".join(result.missing))
            self.open_song(result.songs[0])
        else:
            msg = tr("lib.zip_imported", n=len(result.songs), folder=self.place_label(result.folder))
        self.toast(msg)
        self.run(self.sync_now())

    async def export_song_zip(self, e=None):
        """The song with its MusicXML files as a .zip: shared on iPad/iPhone and Android, saved elsewhere."""
        data = await asyncio.to_thread(library.song_zip, self.text, self.song_title or self.name, self.base_dir)
        name = self.export_name(".zip")
        if self.page.platform in (ft.PagePlatform.IOS, ft.PagePlatform.ANDROID):
            await self.share_file(ft.ShareFile.from_bytes(data, mime_type="application/zip", name=name))
            return
        await self.save_bytes(data, name, "zip", tr("ed.export_zip"))

    async def export_library_zip(self, e=None):
        """The whole library as a .zip (backup, or moving it to another device), through the save dialog."""
        if not self.root:
            return
        data = await asyncio.to_thread(library.library_zip, self.root)
        name = f"Modern Sheet {datetime.now():%Y-%m-%d}.zip"
        await self.save_bytes(data, name, "zip", tr("set.export_library"))

    async def save_bytes(self, data: bytes, name: str, ext: str, title: str):
        """Save a file through the system dialog (on desktop it only returns the path: we write it)."""
        path = await self.picker.save_file(dialog_title=title, file_name=name, allowed_extensions=[ext],
                                           src_bytes=data)
        if not path:
            return
        if self.page.platform in DESKTOP:
            try:
                Path(path).write_bytes(data)
            except OSError as err:
                self.toast(tr("ed.save_failed", err=err))
                return
        self.toast(tr("ed.file_saved", name=Path(path).name))

    # ---- keyboard: ⌘S / Ctrl+S, page turning (keyboard and Bluetooth pedals send arrow / page keys)
    async def on_key(self, e: ft.KeyboardEvent):
        if self.screen != "editor":
            return
        if await self.completion_key(e.key):
            return
        if e.key == "Escape" and self.fullscreen:
            self.set_fullscreen(False)
            return
        if e.key.upper() == "S" and (e.meta or e.ctrl):
            await self.save()
            return
        if (e.meta or e.ctrl) and (e.key.upper() == "Z" or (e.key.upper() == "Y" and e.ctrl)):
            if self.show_editor and self.doc.kind == "chs":
                action = "redo" if e.shift or e.key.upper() == "Y" else "undo"
                # the text field may undo by itself as well (on_edit then takes over): wait for it
                self._undo_key = (action, time.monotonic())
                await asyncio.sleep(0.15)
                if self._undo_key and self._undo_key[0] == action:
                    self._undo_key = None
                    await self.undo_redo(action)
            return
        if self.editor_focused or not self.dl:
            return                         # arrows and space belong to the editor while typing
        if e.key in ("Page Down", "Arrow Right", "Arrow Down", " "):
            self.current_page = min(self.current_page + 1, len(self.dl.pages) - 1)
        elif e.key in ("Page Up", "Arrow Left", "Arrow Up"):
            self.current_page = max(self.current_page - 1, 0)
        else:
            return
        await self.pages.scroll_to(scroll_key=f"p{self.current_page}", duration=250)

    # ---- PDF export (same DisplayList as on screen)
    async def export_pdf(self, e):
        if not self.dl:
            return
        data = await asyncio.to_thread(pdf_bytes, self.dl)
        name = self.export_name(".pdf")
        folder = self.settings.pdf_dir if not self.store and self.settings.pdf_dir and Path(self.settings.pdf_dir).is_dir() \
            else None
        path = await self.picker.save_file(dialog_title=tr("ed.export_pdf"), file_name=name, initial_directory=folder,
                                           allowed_extensions=["pdf"], src_bytes=data)
        if path and self.page.platform in DESKTOP:
            Path(path).write_bytes(data)          # desktop: the dialog only returns the path
        if path:
            self.toast(tr("ed.pdf_saved", name=Path(path).name))

    def export_name(self, ext: str) -> str:
        """File name for an exported song: the title (transposition added for a PDF)."""
        tr_part = f"_{self.transpose:+d}" if self.transpose and ext == ".pdf" else ""
        return f"{library.safe_filename(self.song_title or self.name)}{tr_part}{ext}"

    async def share_pdf(self, e=None):
        """The sheet as PDF through the system share sheet (as shown: transposition and options included)."""
        if not self.dl:
            return
        data = await asyncio.to_thread(pdf_bytes, self.dl)
        await self.share_file(ft.ShareFile.from_bytes(data, mime_type="application/pdf", name=self.export_name(".pdf")))

    async def share_chs(self, e=None):
        """The .chs source (as in the editor, saved or not) through the system share sheet."""
        await self.share_file(ft.ShareFile.from_bytes(self.text.encode("utf-8"), mime_type="text/plain",
                                                      name=self.export_name(".chs")))

    async def share_file(self, f: ft.ShareFile):
        # on iPad the share sheet is a popover and needs a point to come from (else it fails): the share
        # button, top right
        origin = ft.Offset((self.page.width or 800) - 120, 56)
        try:
            await self.share.share_files([f], share_position_origin=origin)
        except Exception as err:                  # noqa: BLE001 — report, never crash the editor
            self.toast(tr("ed.share_failed", err=err))

    # ---- helpers
    def run(self, coro):
        async def task():
            await coro
        self.page.run_task(task)

    def toast(self, msg: str):
        self.page.show_dialog(ft.SnackBar(ft.Text(msg)))

    async def ask(self, title: str, content: ft.Control, buttons: list[tuple[str, str | None]],
                  danger: bool = False):
        """Modal dialog; returns the value of the pressed button (None for cancel).
        The last button is the main one, red if `danger`."""
        fut = asyncio.get_running_loop().create_future()

        def done(value):
            self.page.pop_dialog()
            if not fut.done():
                fut.set_result(value)

        actions = [(ft.FilledButton if i == len(buttons) - 1 else ft.TextButton)(label, on_click=lambda e, v=v: done(v))
                   for i, (label, v) in enumerate(buttons)]
        if danger:
            actions[-1].style = ft.ButtonStyle(bgcolor=ft.Colors.ERROR, color=ft.Colors.ON_ERROR)
        self.page.show_dialog(ft.AlertDialog(modal=True, title=ft.Text(title), content=content, actions=actions))
        return await fut


async def main(page: ft.Page):
    page.title = "Modern Sheet"
    if page.platform == ft.PagePlatform.WINDOWS:          # window icon while developing (flet run)
        page.window.icon = str(HERE / "assets" / "icon.ico")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.GREY_200
    page.fonts = dict(FLET_FONTS)        # same font files the engine measures with
    page.fonts[CODE_FONT] = "fonts/DejaVuSansMono.ttf"
    app = App(page)
    await app.start()


if __name__ == "__main__":
    if not os.environ.get("FLET_APP_STORAGE_DATA") and (HERE.parent / "pyproject.toml").exists():
        # started with `python src/main.py` (e.g. the VS Code debugger): use the data folder of `flet run`,
        # so settings, index and the synced library are the same and sync is not silently off
        os.environ["FLET_APP_STORAGE_DATA"] = str(HERE.parent / ".flet" / "storage" / "data")
    ft.run(main)
