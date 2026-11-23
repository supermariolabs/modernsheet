"""Build the app icons in src/assets/ from the artwork "MS icon.jpeg" (1024×1024, a cream rounded
tile with the logo, drawn with its own drop shadow).

    python tools/make_icons.py ["MS icon.jpeg"]

Outputs (read by `flet build`, see SPEC §8.3):
    icon.png              the logo alone on a transparent background; flet build frames it per
                          platform: iOS flattened on `icon_background`, Android adaptive icon on
                          that colour, macOS inside Apple's squircle tile of that colour
    icon_ios.png          full-bleed cream square with the logo at the artwork's proportions (iOS rounds the
                          corners itself; flet build would shrink a generic icon more than needed)
    icon_windows.png      the cream rounded tile with transparent corners, used as is
    icon_linux.png        (same)
    icon_web.png          (same)
    favicon.png           64×64 tile (browser tab with `flet run --web`)
    icon.ico              the tile at 16–256 px: window icon of `flet run` on Windows
    icons/*.png           the iOS square at the names of Flet's web icons (apple-touch-icon-192, icon-192/512,
                          icon-maskable-192/512): with `flet run --ios/--android` the assets take precedence
                          over Flet's files, so the Flet app on the device shows our icon, opaque (transparent
                          corners there look dark); src/assets/manifest.json points to them
Requires Pillow (installed with reportlab).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "assets"
CREAM = (246, 241, 230)              # the tile colour of the artwork (also [tool.flet] icon_background)
ART_BOX = (100, 136, 924, 870)       # where the logo is in the 1024×1024 artwork (with some margin)
SIZE = 1024


def logo_on_transparent(src: Image.Image) -> Image.Image:
    """The logo only: pixels close to the cream background become transparent (soft edge),
    with their colour un-mixed from the cream so anti-aliased strokes stay clean."""
    art = src.crop(ART_BOX).convert("RGB")
    bg = Image.new("RGB", art.size, CREAM)
    diff = ImageChops.difference(art, bg).convert("L")
    lo, hi = 10, 46                  # JPEG noise below lo; full opacity above hi
    alpha = diff.point(lambda d: 0 if d <= lo else 255 if d >= hi else int((d - lo) * 255 / (hi - lo)))
    px, al = art.load(), alpha.load()
    for y in range(art.height):
        for x in range(art.width):
            a = al[x, y] / 255
            if 0 < a < 1:
                px[x, y] = tuple(max(0, min(255, round((c - (1 - a) * b) / a))) for c, b in zip(px[x, y], CREAM))
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    logo = art.convert("RGBA")
    logo.putalpha(alpha)
    bbox = logo.getbbox()
    logo = logo.crop(bbox)
    out.alpha_composite(logo, ((SIZE - logo.width) // 2, (SIZE - logo.height) // 2))
    return out


def tile(logo: Image.Image, margin: int = 40, radius: int = 210) -> Image.Image:
    """The cream rounded tile (transparent outside) with the logo, as in the original artwork."""
    scale = 4                         # supersampled mask for smooth corners
    mask = Image.new("L", (SIZE * scale, SIZE * scale), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (margin * scale, margin * scale, (SIZE - margin) * scale - 1, (SIZE - margin) * scale - 1),
        radius=radius * scale, fill=255)
    mask = mask.resize((SIZE, SIZE), Image.LANCZOS)
    out = Image.new("RGBA", (SIZE, SIZE), CREAM + (255,))
    out.putalpha(mask)
    out.alpha_composite(logo)          # same proportions as the original artwork (logo ≈ 85% of the tile)
    return out


def main(argv: list[str]) -> None:
    src = Image.open(argv[0] if argv else ROOT / "MS icon.jpeg").convert("RGB")
    if src.size != (SIZE, SIZE):
        src = src.resize((SIZE, SIZE), Image.LANCZOS)
    ASSETS.mkdir(parents=True, exist_ok=True)
    logo = logo_on_transparent(src)
    logo.save(ASSETS / "icon.png")
    ios = Image.new("RGBA", (SIZE, SIZE), CREAM + (255,))
    ios.alpha_composite(logo)
    ios.convert("RGB").save(ASSETS / "icon_ios.png")          # the App Store rejects alpha in icons
    web = ASSETS / "icons"
    web.mkdir(exist_ok=True)
    for name, px in (("apple-touch-icon-192", 192), ("icon-192", 192), ("icon-512", 512),
                     ("icon-maskable-192", 192), ("icon-maskable-512", 512)):
        ios.convert("RGB").resize((px, px), Image.LANCZOS).save(web / f"{name}.png")
    t = tile(logo)
    for name in ("icon_windows.png", "icon_linux.png", "icon_web.png"):
        t.save(ASSETS / name)
    t.resize((64, 64), Image.LANCZOS).filter(ImageFilter.SHARPEN).save(ASSETS / "favicon.png")
    t.save(ASSETS / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("written:", ", ".join(str(p.relative_to(ASSETS)) for p in sorted([*ASSETS.glob("*.png"), *ASSETS.glob("*.ico"), *web.glob("*.png")])))


if __name__ == "__main__":
    main(sys.argv[1:])
