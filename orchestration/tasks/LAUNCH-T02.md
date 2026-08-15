# LAUNCH-T02 — launch-runbook

## Objective

Написать операторский runbook первого полноценного запуска Slon на macOS (с краткими ветками Windows/Linux): Privacy permissions, deps, wake word, tool smoke, known non-goals.

## Context

- Полный desktop UX требует Microphone + Accessibility + Screen Recording.
- Playwright browsers обязательны для browser tools.
- Wake word gate в `main.py` / `speech/wake_word.py`; idle ~45s → standby.
- iOS remote / Epic 14 — вне первого запуска.

## Owned paths

- `docs/audit/launch-runbook.md` (new)

## Forbidden paths

- Application code (`main.py`, `ui.py`, `actions/**`, …)
- `readme.md` (owned by LAUNCH-T01) — можно сказать «см. readme Quick Start», не дублировать весь README wholesale.

## Required sections

1. Prerequisites (Python 3.11–3.12, venv, OS)  
2. Install commands (macos/windows/linux requirements files + playwright)  
3. Config: `api_keys.json` / OS secret store names (`gemini_api_key`, …) — **без значений**  
4. `settings.json` bootstrap note (ссылка на T05 поведение, если ещё не смержено — описать expected)  
5. macOS Privacy checklist:
   - Microphone
   - Accessibility (input automation)
   - Screen Recording (screen tools)
6. First-run steps + wake word  
7. Minimal tool smoke matrix (open_app / web_search / screen_process)  
8. Troubleshooting: wrong Python 3.14, missing playwright browsers, muted mic, standby  
9. Out of scope: public bind, APNs, commercial

## Acceptance

- Doc exists; actionable checkboxes for operator.
- No secrets; no commercial-ready claim.
- Cross-links to `speech/wake_word.py` and `python -m server` as optional.
- One commit.

## Stop conditions

- Need code changes for permissions prompts → change request (T04/T06).
