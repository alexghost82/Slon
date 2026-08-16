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
APP_EXECUTABLE = APP_BUNDLE / "Contents" / "MacOS" / "Slon"
SETUP_FILE = ROOT / "packaging" / "macos" / "setup.py"
ENTITLEMENTS = ROOT / "packaging" / "macos" / "entitlements.plist"
MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce",
    b"\xfe\xed\xfa\xcf",
    b"\xce\xfa\xed\xfe",
    b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca",
}


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


def is_macho(path: Path) -> bool:
    """Return whether *path* starts with a thin or universal Mach-O header."""
    if not path.is_file() or path.is_symlink():
        return False
    try:
        with path.open("rb") as stream:
            return stream.read(4) in MACHO_MAGICS
    except OSError:
        return False


def sign_app_bundle() -> None:
    """Ad-hoc sign nested code from the inside out, then sign the app container."""
    for path in sorted(APP_BUNDLE.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        # The app container signs its main executable. Signing that file as an
        # independent code object makes codesign validate the surrounding,
        # not-yet-signed bundle and fail before the final step.
        if path != APP_EXECUTABLE and is_macho(path):
            run("codesign", "--force", "--sign", "-", str(path))

    nested_bundles = (
        path
        for path in APP_BUNDLE.rglob("*")
        if path.is_dir() and path.suffix in {".framework", ".plugin", ".xpc", ".app"}
    )
    for path in sorted(nested_bundles, key=lambda item: len(item.parts), reverse=True):
        run("codesign", "--force", "--sign", "-", str(path))

    run(
        "codesign",
        "--force",
        "--sign",
        "-",
        "--entitlements",
        str(ENTITLEMENTS),
        str(APP_BUNDLE),
    )
    run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(APP_BUNDLE))


def repair_rewritten_liblzma() -> None:
    """Replace py2app's malformed rewritten Pillow liblzma before signing."""
    source = Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
    source /= "site-packages/PIL/.dylibs/liblzma.5.dylib"
    destination = APP_BUNDLE / "Contents/Frameworks/liblzma.5.dylib"
    if not source.is_file() or not destination.exists():
        return
    shutil.copy2(source, destination)
    run(
        "install_name_tool",
        "-id",
        "@executable_path/../Frameworks/liblzma.5.dylib",
        str(destination),
    )


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
        repair_rewritten_liblzma()
        sign_app_bundle()
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
