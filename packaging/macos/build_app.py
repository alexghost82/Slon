"""Build and ad-hoc sign a standalone Slon.app for local macOS use."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "build" / "macos"
DIST_DIR = ROOT / "dist"
ICONSET_DIR = BUILD_DIR / "Slon.iconset"
ICON_FILE = BUILD_DIR / "Slon.icns"
APP_BUNDLE = DIST_DIR / "Slon.app"
SETUP_FILE = ROOT / "packaging" / "macos" / "setup.py"
ENTITLEMENTS = ROOT / "packaging" / "macos" / "entitlements.plist"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def render_icon() -> None:
    shutil.rmtree(ICONSET_DIR, ignore_errors=True)
    ICONSET_DIR.mkdir(parents=True)
    with Image.open(ROOT / "logo.png") as source:
        image = source.convert("RGBA")
        for size in (16, 32, 128, 256, 512):
            image.resize((size, size), Image.Resampling.LANCZOS).save(
                ICONSET_DIR / f"icon_{size}x{size}.png"
            )
            doubled = size * 2
            image.resize((doubled, doubled), Image.Resampling.LANCZOS).save(
                ICONSET_DIR / f"icon_{size}x{size}@2x.png"
            )
    run("iconutil", "--convert", "icns", "--output", str(ICON_FILE), str(ICONSET_DIR))


def build(*, clean: bool, sign: bool) -> None:
    if sys.platform != "darwin":
        raise SystemExit("Slon.app can only be built on macOS")
    if clean:
        shutil.rmtree(ROOT / "build", ignore_errors=True)
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    render_icon()
    run(sys.executable, str(SETUP_FILE), "py2app")
    if sign:
        run(
            "codesign",
            "--force",
            "--deep",
            "--sign",
            "-",
            "--entitlements",
            str(ENTITLEMENTS),
            str(APP_BUNDLE),
        )
        run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(APP_BUNDLE))
    print(f"Built: {APP_BUNDLE}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-clean", action="store_true", help="reuse existing build output")
    parser.add_argument("--no-sign", action="store_true", help="skip ad-hoc code signing")
    args = parser.parse_args()
    build(clean=not args.no_clean, sign=not args.no_sign)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
