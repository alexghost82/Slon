"""Unit tests for Slon wake-word matching."""

from __future__ import annotations

from speech.wake_word import WAKE_WORD, contains_wake_word, normalize_transcript


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
