# LAUNCH-T01 — restore-readme-slon

## Objective

Восстановить корневой `readme.md` (сейчас 0 байт) как операторский вход в **Slon**: что это, Quick Start, требования, лицензия CC BY-NC, wake word, без commercial-ready claims.

## Context

- Продукт переименован в Slon; личность агента Slon, тон JARVIS-like.
- `pyproject.toml` / requirements: Python `>=3.11,<3.13`.
- Wake word: `Slon` / `Слон` (см. `speech/wake_word.py`).
- Upstream attribution без встраивания чужих GitHub/social handles.

## Owned paths

- `readme.md`

## Forbidden paths

- Everything else.
- Не коммитить ключи, не ссылаться на реальные значения secrets.
- Не обещать public internet / App Store / commercial use.

## Deliverable content (обязательные секции)

1. Title: Slon  
2. One-paragraph overview (desktop personal AI; Windows/macOS/Linux)  
3. Quick Start:
   - Python 3.11 or 3.12 venv
   - `pip install -r requirements-macos.txt` (и аналоги win/linux) **или** `python setup.py`
   - `playwright install`
   - `python main.py`
4. Requirements table: OS, Python, mic, Gemini (+ optional OpenRouter)  
5. Wake word note: say **Slon** after start  
6. Optional: Desktop API `python -m server` (loopback default)  
7. License: personal/non-commercial CC BY-NC 4.0  
8. Attribution short block (no third-party handles)

## Acceptance

- `readme.md` size > 0; UTF-8; markdown renders.
- Commands copy-pasteable; Python upper bound не 3.14.
- Нет живых ключей / placeholder-секретов вида `AIza…` / `sk-or-v1-…` реальных.
- One commit message focusing on why (restore operator entrypoint for Slon).

## Stop conditions

- Need to edit `setup.py` / requirements → change request to integrator (LAUNCH-T03 may own tooling).
