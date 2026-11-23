"""Google Drive provider for the library sync (see sync.py). Standard library only (urllib).

Sign-in: OAuth 2.0 *device flow* ("TVs and Limited Input devices" client): the app shows a short
code, the user enters it at google.com/device on any device. It needs no redirect, browser
integration or native SDK, so it works the same on macOS, Windows, Linux, iPad and Android.

Scope: drive.file — the app sees only the files it created (its "Modern Sheet" folder in the user's
Drive). This scope needs no Google security review; files added to that folder by hand through the
Drive web site are not visible to the app.

The app's OAuth client (client id and secret, from the user's own Google Cloud project) is read
from the environment (MODERNSHEET_GOOGLE_CLIENT_ID / MODERNSHEET_GOOGLE_CLIENT_SECRET; the CHORDSHEET_ names
of earlier versions also work) or from a
JSON file kept out of version control (see client_config). The refresh token is stored in the
app's data folder (file readable by the user only).

The client secret is NOT confidential: the device flow requires it, so it ships inside every built app
(desktop packages, APK) and can be extracted. Google treats installed-app secrets this way. Whoever
extracts it can only pose as this app and use its quota; user data still needs each user's consent,
drive.file limits access to the app's own files and tokens stay on the device. On abuse: rotate the
secret in the Cloud Console and release a new build (SPEC.md §8.3b).

All HTTP goes through a `Transport` (callable), replaced by a fake Drive in the tests.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .settings import env
from .sync import AuthRequired, Offline, RemoteChanged, RemoteFile, is_synced

SCOPE = "https://www.googleapis.com/auth/drive.file"
DEVICE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3"
FOLDER_MIME = "application/vnd.google-apps.folder"
ROOT_NAME = "Modern Sheet"                # default name of the app's folder in the Drive root
LEGACY_ROOT_NAME = "Chord Sheet"          # default before 0.19 (the app was called Chord Sheet)


def clean_folder_name(name: str) -> str:
    """A folder name for the Drive root: trimmed, no slashes; empty -> the default."""
    return " ".join(name.replace("/", " ").replace("\\", " ").split()) or ROOT_NAME


class DriveError(OSError):
    """An API call failed (the sync reports it and retries next time)."""


class AuthError(AuthRequired):
    """Not signed in, or the sign-in was revoked: the user must connect the account again."""


@dataclass
class Response:
    status: int
    body: bytes

    def json(self) -> dict:
        return json.loads(self.body or b"{}")


Transport = Callable[[str, str, dict, bytes | None], Response]


def urllib_transport(method: str, url: str, headers: dict, body: bytes | None) -> Response:
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return Response(r.status, r.read())
    except urllib.error.HTTPError as e:
        return Response(e.code, e.read())
    except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
        raise Offline(str(getattr(e, "reason", e))) from e


@dataclass
class ClientConfig:
    client_id: str
    client_secret: str


def client_config(*files: Path) -> ClientConfig | None:
    """The app's OAuth client: environment variables first, then the first readable JSON file among
    `files`, either {"client_id": …, "client_secret": …} or Google's download format {"installed": {…}}."""
    cid, secret = env("GOOGLE_CLIENT_ID"), env("GOOGLE_CLIENT_SECRET")
    if cid and secret:
        return ClientConfig(cid, secret)
    for f in files:
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        data = data.get("installed") or data.get("web") or data
        if data.get("client_id") and data.get("client_secret"):
            return ClientConfig(data["client_id"], data["client_secret"])
    return None


def _form(data: dict) -> bytes:
    return urllib.parse.urlencode(data).encode("ascii")


@dataclass
class DeviceCode:
    device_code: str
    user_code: str
    verification_url: str
    interval: int
    expires_at: float


class GoogleAuth:
    """Device-flow sign-in and access tokens (refreshed when expired)."""

    def __init__(self, client: ClientConfig, token_file: Path, http: Transport = urllib_transport,
                 clock=time.time):
        self.client = client
        self.token_file = Path(token_file)
        self.http = http
        self.clock = clock
        try:
            self.token = json.loads(self.token_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.token = {}

    @property
    def signed_in(self) -> bool:
        return bool(self.token.get("refresh_token"))

    def _save(self) -> None:
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.token_file.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(self.token, fh)
        os.replace(tmp, self.token_file)

    def sign_out(self) -> None:
        self.token = {}
        try:
            self.token_file.unlink()
        except OSError:
            pass

    def start(self) -> DeviceCode:
        r = self.http("POST", DEVICE_URL, {"Content-Type": "application/x-www-form-urlencoded"},
                      _form({"client_id": self.client.client_id, "scope": SCOPE}))
        if r.status != 200:
            raise DriveError(f"device code: HTTP {r.status} {r.body[:200]!r}")
        d = r.json()
        return DeviceCode(d["device_code"], d["user_code"], d.get("verification_url") or d.get("verification_uri"),
                          int(d.get("interval", 5)), self.clock() + int(d.get("expires_in", 1800)))

    def poll(self, dc: DeviceCode) -> str:
        """One poll of the token endpoint: 'ok' (signed in), 'pending', 'slow_down', 'denied', 'expired'."""
        if self.clock() > dc.expires_at:
            return "expired"
        r = self.http("POST", TOKEN_URL, {"Content-Type": "application/x-www-form-urlencoded"}, _form({
            "client_id": self.client.client_id, "client_secret": self.client.client_secret,
            "device_code": dc.device_code, "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}))
        d = r.json()
        if r.status == 200 and d.get("access_token"):
            self.token = {"access_token": d["access_token"], "refresh_token": d.get("refresh_token"),
                          "expires_at": self.clock() + int(d.get("expires_in", 3600)) - 60}
            self._save()
            return "ok"
        err = d.get("error", "")
        return {"authorization_pending": "pending", "slow_down": "slow_down",
                "access_denied": "denied", "expired_token": "expired"}.get(err, "denied")

    def access_token(self, force_refresh: bool = False) -> str:
        if not self.signed_in:
            raise AuthError("not signed in")
        if not force_refresh and self.token.get("access_token") and self.clock() < self.token.get("expires_at", 0):
            return self.token["access_token"]
        r = self.http("POST", TOKEN_URL, {"Content-Type": "application/x-www-form-urlencoded"}, _form({
            "client_id": self.client.client_id, "client_secret": self.client.client_secret,
            "refresh_token": self.token["refresh_token"], "grant_type": "refresh_token"}))
        d = r.json()
        if r.status != 200 or not d.get("access_token"):
            if d.get("error") in ("invalid_grant", "unauthorized_client"):
                raise AuthError(d.get("error_description") or d["error"])
            raise DriveError(f"token refresh: HTTP {r.status}")
        self.token["access_token"] = d["access_token"]
        self.token["expires_at"] = self.clock() + int(d.get("expires_in", 3600)) - 60
        self._save()
        return self.token["access_token"]


def _q(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


class DriveProvider:
    """The remote copy is the app's folder in Google Drive ("Modern Sheet", subfolders included).
    Revisions are the files' MD5 checksums. Deletions move files to Drive's trash."""

    def __init__(self, auth: GoogleAuth, http: Transport = urllib_transport, root_name: str = ROOT_NAME):
        self.auth = auth
        self.http = http
        self.root_name = root_name
        self.root_id: str | None = None
        self.fresh = False                     # the app folder did not exist and was just created
        self.files: dict[str, dict] = {}       # rel -> {"id", "md5"}
        self.folders: dict[str, str] = {}      # rel folder ("" = root) -> id

    # ---- HTTP
    def _call(self, method: str, url: str, params: dict | None = None, body: bytes | None = None,
              content_type: str | None = None) -> Response:
        if params:
            url += "?" + urllib.parse.urlencode(params)
        for attempt in (0, 1):
            headers = {"Authorization": f"Bearer {self.auth.access_token(force_refresh=attempt == 1)}"}
            if content_type:
                headers["Content-Type"] = content_type
            r = self.http(method, url, headers, body)
            if r.status != 401:
                break
        if r.status == 401:
            raise AuthError("unauthorized")
        if r.status >= 400:
            raise DriveError(f"{method} {url.split('?')[0]}: HTTP {r.status} {r.body[:200]!r}")
        return r

    def account(self) -> dict:
        """{'emailAddress': …, 'displayName': …} of the signed-in user."""
        return self._call("GET", f"{API}/about", {"fields": "user(emailAddress,displayName)"}).json().get("user", {})

    def _ensure_root(self) -> str:
        if self.root_id:
            return self.root_id
        q = f"name='{_q(self.root_name)}' and mimeType='{FOLDER_MIME}' and 'root' in parents and trashed=false"
        found = self._call("GET", f"{API}/files", {"q": q, "fields": "files(id)", "spaces": "drive"}).json()["files"]
        if found:
            self.root_id = found[0]["id"]
        else:
            self.root_id = self._create_folder(self.root_name, "root")
            self.fresh = True
        self.folders[""] = self.root_id
        return self.root_id

    def _create_folder(self, name: str, parent: str) -> str:
        meta = json.dumps({"name": name, "mimeType": FOLDER_MIME, "parents": [parent]}).encode("utf-8")
        return self._call("POST", f"{API}/files", {"fields": "id"}, meta, "application/json").json()["id"]

    # ---- Provider interface
    def list(self) -> dict[str, RemoteFile]:
        if self.root_id and self.root_id not in self._live_folders():
            self.root_id = None                # renamed, moved or deleted since the last sync
        root = self._ensure_root()
        items: list[dict] = []
        token = None
        while True:
            params = {"q": "trashed=false", "spaces": "drive", "pageSize": "1000",
                      "fields": "nextPageToken,files(id,name,mimeType,parents,md5Checksum,modifiedTime)"}
            if token:
                params["pageToken"] = token
            page = self._call("GET", f"{API}/files", params).json()
            items += page.get("files", [])
            token = page.get("nextPageToken")
            if not token:
                break
        by_id = {it["id"]: it for it in items}

        def path(it: dict, depth: int = 0) -> str | None:
            parents = it.get("parents") or []
            if not parents or depth > 64:
                return None
            if parents[0] == root:
                return it["name"]
            parent = by_id.get(parents[0])
            if not parent or parent.get("mimeType") != FOLDER_MIME:
                return None
            base = path(parent, depth + 1)
            return f"{base}/{it['name']}" if base else None

        self.files, self.folders = {}, {"": root}
        newest: dict[str, str] = {}
        for it in items:
            rel = path(it)
            if rel is None:
                continue
            if it.get("mimeType") == FOLDER_MIME:
                self.folders[rel] = it["id"]
            elif is_synced(rel) and it.get("md5Checksum"):
                if rel in newest and newest[rel] >= it.get("modifiedTime", ""):
                    continue                     # same name twice: the most recent one wins
                newest[rel] = it.get("modifiedTime", "")
                self.files[rel] = {"id": it["id"], "md5": it["md5Checksum"]}
        return {rel: RemoteFile(f["md5"]) for rel, f in self.files.items()}

    def _live_folders(self) -> set[str]:
        q = f"name='{_q(self.root_name)}' and mimeType='{FOLDER_MIME}' and 'root' in parents and trashed=false"
        return {f["id"] for f in self._call("GET", f"{API}/files", {"q": q, "fields": "files(id)",
                                                                       "spaces": "drive"}).json()["files"]}

    def download(self, rel: str) -> bytes:
        return self._call("GET", f"{API}/files/{self.files[rel]['id']}", {"alt": "media"}).body

    def _check(self, rel: str, expected: str | None) -> None:
        if rel not in self.files:
            if expected is not None:
                raise RemoteChanged(rel)
            return
        meta = self._call("GET", f"{API}/files/{self.files[rel]['id']}", {"fields": "md5Checksum,trashed"}).json()
        current = None if meta.get("trashed") else meta.get("md5Checksum")
        if current != expected:
            raise RemoteChanged(rel)

    def _folder_id(self, rel_folder: str) -> str:
        if rel_folder in self.folders:
            return self.folders[rel_folder]
        parent, _, name = rel_folder.rpartition("/")
        fid = self._create_folder(name, self._folder_id(parent))
        self.folders[rel_folder] = fid
        return fid

    def upload(self, rel: str, data: bytes, expected_rev: str | None) -> str:
        self._ensure_root()
        self._check(rel, expected_rev)
        if rel in self.files:
            r = self._call("PATCH", f"{UPLOAD}/files/{self.files[rel]['id']}",
                           {"uploadType": "media", "fields": "id,md5Checksum"}, data, "application/octet-stream")
        else:
            folder, _, name = rel.rpartition("/")
            boundary = uuid.uuid4().hex
            meta = json.dumps({"name": name, "parents": [self._folder_id(folder)]}).encode("utf-8")
            body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode() + meta +
                    f"\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n".encode() + data +
                    f"\r\n--{boundary}--".encode())
            r = self._call("POST", f"{UPLOAD}/files", {"uploadType": "multipart", "fields": "id,md5Checksum"},
                           body, f"multipart/related; boundary={boundary}")
        d = r.json()
        md5 = d.get("md5Checksum") or hashlib.md5(data).hexdigest()
        self.files[rel] = {"id": d["id"], "md5": md5}
        return md5

    def delete(self, rel: str, expected_rev: str | None) -> None:
        self._check(rel, expected_rev)
        self._call("PATCH", f"{API}/files/{self.files[rel]['id']}", {"fields": "id"},
                   json.dumps({"trashed": True}).encode("utf-8"), "application/json")
        del self.files[rel]

    def remove_empty_folder(self, rel: str) -> bool:
        """Move a library subfolder to Drive's trash if Drive says it holds nothing at all (also no
        file the app does not sync, e.g. a PDF put there by hand)."""
        fid = self.folders.get(rel)
        if not rel or not fid:
            return False
        children = self._call("GET", f"{API}/files", {"q": f"'{_q(fid)}' in parents and trashed=false",
                                                      "fields": "files(id)", "pageSize": "1",
                                                      "spaces": "drive"}).json().get("files", [])
        if children:
            return False
        self._call("PATCH", f"{API}/files/{fid}", {"fields": "id"},
                   json.dumps({"trashed": True}).encode("utf-8"), "application/json")
        self.folders = {k: v for k, v in self.folders.items() if k != rel and not k.startswith(rel + "/")}
        return True
