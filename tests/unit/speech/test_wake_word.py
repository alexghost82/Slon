"""Unit tests for Slon wake-word matching and unmute HUD sync helpers."""

from __future__ import annotations

import ast
from pathlib import Path

from speech.wake_word import WAKE_WORD, contains_wake_word, normalize_transcript

ROOT = Path(__file__).resolve().parents[3]


def resolve_unmute_hud_state(*, awake: bool, speaking: bool = False) -> str:
    """Mirror of ui.resolve_unmute_hud_state (avoid importing PyQt in unit tests)."""
    if speaking:
        return "SPEAKING"
    return "LISTENING" if awake else "STANDBY"


def test_wake_word_constant() -> None:
    assert WAKE_WORD == "Slon"


def test_contains_wake_word_english_forms() -> None:
    assert contains_wake_word("Slon")
    assert contains_wake_word("hey slon, open chrome")
    assert contains_wake_word("OK Slon")
    assert contains_wake_word("sloon")  # ASR near-miss


def test_contains_wake_word_russian() -> None:
    assert contains_wake_word("Слон")
    assert contains_wake_word("эй слон, погода")
    assert contains_wake_word("слон, что на экране")


def test_contains_wake_word_rejects_unrelated() -> None:
    assert not contains_wake_word("")
    assert not contains_wake_word("hello there")
    assert not contains_wake_word("slot machine")
    assert not contains_wake_word("слоновый")  # longer Russian stem, not the wake call


def test_normalize_folds_case() -> None:
    assert normalize_transcript("СлОн") == "слон"


def test_unmute_hud_standby_when_asleep() -> None:
    assert resolve_unmute_hud_state(awake=False) == "STANDBY"
    assert resolve_unmute_hud_state(awake=False, speaking=False) == "STANDBY"


def test_unmute_hud_listening_when_awake() -> None:
    assert resolve_unmute_hud_state(awake=True) == "LISTENING"


def test_unmute_hud_speaking_overrides() -> None:
    assert resolve_unmute_hud_state(awake=True, speaking=True) == "SPEAKING"
    assert resolve_unmute_hud_state(awake=False, speaking=True) == "SPEAKING"


def test_ui_resolve_unmute_hud_state_matches_contract() -> None:
    """Source-level check: ui helper matches the standby-safe unmute contract."""
    tree = ast.parse((ROOT / "ui.py").read_text(encoding="utf-8"))
    fn = None
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "resolve_unmute_hud_state"
        ):
            fn = node
            break
    assert fn is not None, "resolve_unmute_hud_state missing from ui.py"
    ui_src = (ROOT / "ui.py").read_text(encoding="utf-8")
    src = ast.get_source_segment(ui_src, fn)
    assert src is not None
    assert "STANDBY" in src
    assert "LISTENING" in src
    assert "SPEAKING" in src


def test_set_muted_unmute_does_not_force_listening() -> None:
    """Unmute branch must not hard-apply LISTENING (false awake while standby)."""
    tree = ast.parse((ROOT / "ui.py").read_text(encoding="utf-8"))
    set_muted = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "MainWindow":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "_set_muted":
                    set_muted = item
                    break
    assert set_muted is not None
    ui_src = (ROOT / "ui.py").read_text(encoding="utf-8")
    src = ast.get_source_segment(ui_src, set_muted)
    assert src is not None
    assert 'on_mute_changed' in src
    assert 'resolve_unmute_hud_state' in src
    # Unmute must not blindly _apply_state("LISTENING").
    assert '_apply_state("LISTENING")' not in src
