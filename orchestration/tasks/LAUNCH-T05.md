# LAUNCH-T05 — settings-bootstrap

## Objective

При первом запуске, если нет `config/settings.json`, создать его из `config/settings.example.json` (или через `config.settings` API), **не трогая** secrets.

## Context

- Example уже задаёт `language: ru`, `privacy_profile: hybrid`, `provider_id: gemini`.
- Secrets живут отдельно (`config/secrets.py` / `api_keys.json`).
- Не перезаписывать существующий `settings.json` пользователя.

## Owned paths

- `config/settings.py` and/or `config/__init__.py` — функция `ensure_settings_file(path=...)`
- `tests/unit/config/test_settings_bootstrap.py` (new)
- Glue call site: **либо** минимальный вызов из `mark/app/setup_wizard.py`, **либо** change request на `ui.py`/`main.py` (предпочтительно вызвать из уже существующего startup wizard / UI setup path без дублирования)

## Forbidden paths

- `config/api_keys.json`, secret values
- Parallel edit of `ui.py` if LAUNCH-T04/T06 in flight — integrator sequences
- Changing schema defaults to break Wave 1 contracts without tests

## Acceptance

- Missing settings → file created with validated example defaults.
- Existing settings → no overwrite.
- Invalid existing JSON → clear error / non-destructive (document choice; prefer do not clobber).
- Tests offline.
- One commit.

## Stop conditions

- Conflict with uncommitted user `settings.json` behavior → CR.
- Need `main.py` only for call site while another agent owns `main.py` → CR.
