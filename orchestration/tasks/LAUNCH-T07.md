# LAUNCH-T07 — launch-verify-audit

## Objective

Зафиксировать verification первого запуска: автоматические тесты + шаблон ручного smoke в `docs/audit/launch-smoke.md`.

## Context

- Выполняется **после** merge T01–T06 интегратором.
- Не требует реального микрофона в CI; manual section — для оператора.

## Owned paths

- `docs/audit/launch-smoke.md` (new)
- Optional update pointer in `docs/audit/beta-gates.md` (one short row) — only if no concurrent owner; else skip and note in CR

## Forbidden paths

- Feature code changes (bugs found → file CR / new task, don’t silent-fix across tree)
- Committing pytest logs with secrets
- Running destructive git commands

## Acceptance checklist to record

### Automated

- [ ] `pytest tests/unit -q` — count passed/skipped; note regressions vs pre-wave
- [ ] `pytest tests/unit/speech/test_wake_word.py` — pass
- [ ] `python -m mark.app.preflight` — expected exit on CI agent env (may be exit 1 without keys/deps; document)

### Manual (operator, mark pass/fail/deferred)

- [ ] venv 3.11/3.12 + requirements-macos + playwright
- [ ] `python main.py` opens HUD
- [ ] Standby + wake word Slon
- [ ] One tool success
- [ ] Mute/unmute OK
- [ ] macOS Privacy grants noted

## Acceptance

- Audit file filled with dates, commands, results, blockers left.
- No secret values.
- One commit.

## Stop conditions

- Discover P0 launch bug → stop expanding scope; open change request with repro.
