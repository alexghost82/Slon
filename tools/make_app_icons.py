"""Render platform app-icon assets from the source logo.

Source of truth is ``logo.png`` at the repository root. The desktop HUD loads
that file directly, but iOS needs a square, fully opaque PNG inside an asset
catalog, so this tool derives it:

* crop the transparent margin and the outer glow of the source artwork;
* pad the artwork to a square canvas;
* composite it on the HUD background colour so the iOS squircle mask cuts
  through flat dark pixels instead of transparency;
* downscale to the 1024x1024 App Store size and drop the alpha channel.

Run after replacing ``logo.png``:

    .venv/bin/python -m tools.make_app_icons
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_LOGO = ROOT / "logo.png"
IOS_APPICON = (
    ROOT
    / "ios"
    / "AppProject"
    / "Sources"
    / "Assets.xcassets"
    / "AppIcon.appiconset"
    / "AppIcon-1024.png"
)

# ui.Theme.BG — keeps the icon plate identical to the HUD background.
BACKGROUND_RGB = (0, 6, 10)
IOS_ICON_SIZE = 1024

# Alpha level that separates the icon plate from its soft outer glow.
_PLATE_ALPHA_THRESHOLD = 200


def plate_bounds(
    source: Image.Image,
    threshold: int = _PLATE_ALPHA_THRESHOLD,
) -> tuple[int, int, int, int]:
    """Bounding box of the near-opaque artwork, excluding glow and shadow."""
    if source.mode != "RGBA":
        return (0, 0, source.width, source.height)
    mask = source.getchannel("A").point(lambda value: 255 if value >= threshold else 0)
    box = mask.getbbox()
    if box is None:
        raise ValueError("source logo has no opaque pixels")
    return box


def render_icon(source: Image.Image, size: int = IOS_ICON_SIZE) -> Image.Image:
    """Return an opaque square RGB icon of ``size`` pixels."""
    if size <= 0:
        raise ValueError("icon size must be positive")
    rgba = source.convert("RGBA")
    plate = rgba.crop(plate_bounds(rgba))
    side = max(plate.size)
    canvas = Image.new("RGBA", (side, side), (*BACKGROUND_RGB, 255))
    canvas.alpha_composite(plate, ((side - plate.width) // 2, (side - plate.height) // 2))
    return canvas.convert("RGB").resize((size, size), Image.LANCZOS)


def write_ios_appicon(source_path: Path = SOURCE_LOGO, target_path: Path = IOS_APPICON) -> Path:
    """Write the iOS AppIcon PNG derived from ``source_path``."""
    with Image.open(source_path) as source:
        icon = render_icon(source)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    icon.save(target_path, format="PNG", optimize=True)
    return target_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_LOGO, help="source logo PNG")
    args = parser.parse_args(argv)

    if not args.source.is_file():
        parser.error(f"source logo not found: {args.source}")

    written = write_ios_appicon(args.source)
    print(f"iOS AppIcon: {written.relative_to(ROOT)} ({IOS_ICON_SIZE}x{IOS_ICON_SIZE}, no alpha)")
    print(f"Desktop icon: {args.source.relative_to(ROOT)} (loaded at runtime by ui.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
