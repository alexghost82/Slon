"""Headless checks for face.png load resilience (no QApplication)."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def test_face_missing_sys_notice_without_file(tmp_path: Path) -> None:
    pytest.importorskip("PyQt6")
    from localization import tr
    from ui import face_missing_sys_notice

    missing = tmp_path / "face.png"
    expected = f"{tr('log.prefix_system')} {tr('log.face_missing')}"
    assert face_missing_sys_notice(str(missing)) == expected
    assert "face.png" in expected


def test_face_missing_sys_notice_with_file(tmp_path: Path) -> None:
    pytest.importorskip("PyQt6")
    from ui import face_missing_sys_notice

    present = tmp_path / "face.png"
    present.write_bytes(b"not-a-real-png-but-file-exists")
    assert face_missing_sys_notice(str(present)) is None


def test_hud_load_face_handles_missing_path_in_source() -> None:
    """AST guard: _load_face must not re-raise; geometric Slon fallback stays."""
    import ast

    src = (ROOT / "ui.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    load_fn = None
    paint_fn = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "HudCanvas":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "_load_face":
                    load_fn = item
                if isinstance(item, ast.FunctionDef) and item.name == "paintEvent":
                    paint_fn = item
    assert load_fn is not None, "HudCanvas._load_face missing"
    assert paint_fn is not None, "HudCanvas.paintEvent missing"

    load_src = ast.get_source_segment(src, load_fn)
    assert load_src is not None
    assert "face_missing_sys_notice" in load_src
    assert "except Exception" in load_src

    paint_src = ast.get_source_segment(src, paint_fn)
    assert paint_src is not None
    assert '"Slon"' in paint_src or "'Slon'" in paint_src


def test_mainwindow_emits_face_sys_once_in_source() -> None:
    """MainWindow must emit the face SYS notice once after log connect."""
    import ast

    src = (ROOT / "ui.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    init = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "MainWindow":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    init = item
    assert init is not None
    init_src = ast.get_source_segment(src, init)
    assert init_src is not None
    assert "_face_sys_notice" in init_src
    assert init_src.count("_face_sys_notice") >= 1
    assert "_log_sig.emit(self.hud._face_sys_notice)" in init_src
