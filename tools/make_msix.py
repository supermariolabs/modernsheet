#!/usr/bin/env python3
"""Pack the Windows app (the folder made by `flet build windows`) as an MSIX package for the Microsoft Store.

    python tools/make_msix.py build/windows store/ModernSheet-windows.msix
    python tools/make_msix.py build/windows out.msix --stage-only     # only prepare the folder (no Windows SDK)

The package identity comes from the environment (the Store assigns it when the app name is reserved; in the
release workflow these are GitHub variables): MSIX_IDENTITY_NAME, MSIX_PUBLISHER, MSIX_PUBLISHER_DISPLAY_NAME.
The package is not signed: the Microsoft Store signs it when it publishes the app. The app runs as a full-trust
desktop app (same behaviour as the zip download: its own folders, settings and library), with internet access
for Google Drive. Needs Pillow (tiles from src/assets/icon.png) and, unless --stage-only, MakeAppx.exe from the
Windows SDK (present on GitHub's Windows runners)."""
from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "src" / "assets" / "icon.png"

MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
         IgnorableNamespaces="uap rescap">
  <Identity Name="{name}" Publisher="{publisher}" Version="{version}" ProcessorArchitecture="x64"/>
  <Properties>
    <DisplayName>Modern Sheet</DisplayName>
    <PublisherDisplayName>{publisher_display}</PublisherDisplayName>
    <Logo>Assets\\StoreLogo.png</Logo>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.26100.0"/>
  </Dependencies>
  <Resources>
    <Resource Language="it-IT"/>
    <Resource Language="en-US"/>
  </Resources>
  <Applications>
    <Application Id="ModernSheet" Executable="{exe}" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="Modern Sheet" Description="Chord charts written as text, laid out as lead sheets"
                          BackgroundColor="transparent"
                          Square150x150Logo="Assets\\Square150x150Logo.png" Square44x44Logo="Assets\\Square44x44Logo.png">
        <uap:DefaultTile Wide310x150Logo="Assets\\Wide310x150Logo.png"/>
      </uap:VisualElements>
      <Extensions>
        <uap:Extension Category="windows.fileTypeAssociation">
          <uap:FileTypeAssociation Name="chs">
            <uap:DisplayName>Modern Sheet</uap:DisplayName>
            <uap:SupportedFileTypes>
              <uap:FileType>.chs</uap:FileType>
            </uap:SupportedFileTypes>
          </uap:FileTypeAssociation>
        </uap:Extension>
      </Extensions>
    </Application>
  </Applications>
  <Capabilities>
    <Capability Name="internetClient"/>
    <rescap:Capability Name="runFullTrust"/>
  </Capabilities>
</Package>
"""


def msix_version() -> str:
    """The app version as the four numbers MSIX wants; the Store requires the last one to be 0."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version = "(\d+)\.(\d+)\.(\d+)"', text, re.M)
    if not m:
        sys.exit("version not found in pyproject.toml")
    return ".".join(m.groups()) + ".0"


def find_exe(build: Path) -> str:
    """The app's executable at the top of the build folder."""
    exes = [p.name for p in build.glob("*.exe") if "unins" not in p.name.lower()]
    if len(exes) != 1:
        sys.exit(f"expected one .exe in {build}, found: {exes}")
    return exes[0]


def tiles(assets: Path) -> None:
    """Store and Start tiles from the app icon (transparent background, centred)."""
    assets.mkdir(parents=True, exist_ok=True)
    icon = Image.open(ICON).convert("RGBA")
    for name, (w, h) in {"Square44x44Logo.png": (44, 44), "Square150x150Logo.png": (150, 150),
                         "StoreLogo.png": (50, 50), "Wide310x150Logo.png": (310, 150)}.items():
        side = min(w, h)
        tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        tile.paste(icon.resize((side, side), Image.LANCZOS), ((w - side) // 2, (h - side) // 2))
        tile.save(assets / name)


def makeappx() -> str:
    found = sorted(glob.glob(r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe"))
    if not found:
        sys.exit("MakeAppx.exe (Windows SDK) not found")
    return found[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("build", type=Path, help="folder made by flet build windows")
    ap.add_argument("out", type=Path, help="the .msix to write")
    ap.add_argument("--stage-only", action="store_true", help="prepare the package folder, do not pack it")
    args = ap.parse_args()
    identity = {k: os.environ.get(f"MSIX_{k.upper()}", "").strip()
                for k in ("identity_name", "publisher", "publisher_display_name")}
    missing = [k for k, v in identity.items() if not v]
    if missing:
        sys.exit("missing environment variables: " + ", ".join(f"MSIX_{k.upper()}" for k in missing))
    stage = args.out.with_suffix(".stage")
    shutil.rmtree(stage, ignore_errors=True)
    shutil.copytree(args.build, stage)
    tiles(stage / "Assets")
    (stage / "AppxManifest.xml").write_text(MANIFEST.format(
        name=escape(identity["identity_name"]), publisher=escape(identity["publisher"]),
        publisher_display=escape(identity["publisher_display_name"]), version=msix_version(),
        exe=escape(find_exe(args.build))), encoding="utf-8")
    print(f"staged {stage} (version {msix_version()})")
    if args.stage_only:
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([makeappx(), "pack", "/d", str(stage), "/p", str(args.out), "/o"], check=True)
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
