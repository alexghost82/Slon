"""App icon wiring: desktop window icon plus the generated iOS AppIcon asset."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
IOS_APPICON_DIR = (
    ROOT / "ios" / "AppProject" / "Sources" / "Assets.xcassets" / "AppIcon.appiconset"
)


def test_app_icon_path_found(tmp_path: Path) -> None:
    pytest.importorskip("PyQt6")
    from ui import APP_ICON_FILE, app_icon_path

    logo = tmp_path / APP_ICON_FILE
    logo.write_bytes(b"png-placeholder")
    assert app_icon_path(tmp_path) == logo


def test_app_icon_path_missing(tmp_path: Path) -> None:
    pytest.importorskip("PyQt6")
    from ui import app_icon_path

    assert app_icon_path(tmp_path) is None


def test_apply_app_icon_skips_missing_asset(tmp_path: Path) -> None:
    """Absent or unreadable art must not raise and must not touch the app."""
    pytest.importorskip("PyQt6")
    from ui import apply_app_icon

    class _AppStub:
        def __init__(self) -> None:
            self.icon = None

        def setWindowIcon(self, icon: object) -> None:  # noqa: N802 - Qt API name
            self.icon = icon

    app = _AppStub()
    assert apply_app_icon(app, tmp_path) is False  # type: ignore[arg-type]
    assert app.icon is None

    (tmp_path / "logo.png").write_bytes(b"not-a-png")
    assert apply_app_icon(app, tmp_path) is False  # type: ignore[arg-type]
    assert app.icon is None


def test_root_logo_is_the_desktop_icon_source() -> None:
    from ui import APP_ICON_FILE

    assert (ROOT / APP_ICON_FILE).is_file()


def test_slon_ui_applies_app_icon_in_source() -> None:
    """AST guard: the icon is set on the QApplication before the window shows."""
    src = (ROOT / "ui.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    init = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "SlonUI":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    init = item
    assert init is not None
    init_src = ast.get_source_segment(src, init)
    assert init_src is not None
    assert "apply_app_icon(self._app)" in init_src


def test_ios_appicon_asset_is_square_and_opaque() -> None:
    """iOS rejects app icons with an alpha channel or a non-1024 master size."""
    image_module = pytest.importorskip("PIL.Image")

    png = IOS_APPICON_DIR / "AppIcon-1024.png"
    assert png.is_file()
    with image_module.open(png) as icon:
        assert icon.size == (1024, 1024)
        assert "A" not in icon.getbands()


def test_ios_appicon_contents_json_points_at_the_png() -> None:
    import json

    raw = (IOS_APPICON_DIR / "Contents.json").read_text(encoding="utf-8")
    contents = json.loads(raw)
    filenames = {image.get("filename") for image in contents["images"]}
    assert filenames == {"AppIcon-1024.png"}


def test_xcode_project_uses_the_appicon_asset() -> None:
    pbxproj = (
        ROOT / "ios" / "AppProject" / "MarkRemote.xcodeproj" / "project.pbxproj"
    ).read_text(encoding="utf-8")
    assert 'ASSETCATALOG_COMPILER_APPICON_NAME = ""' not in pbxproj
    assert pbxproj.count("ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;") == 2
    assert "Assets.xcassets in Resources" in pbxproj
