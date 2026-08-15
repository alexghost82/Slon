# LAUNCH-T03 — launch-preflight

## Objective

Добавить offline-safe **preflight** проверку перед `python main.py`: версия Python, критичные imports, наличие ключей (boolean), опциональных assets (`face.png`, Piper), без печати секретов.

## Context

- На clean machine частый фейл: Python 3.14 + отсутствующие deps.
- Keys могут быть в Keychain/`config/api_keys.json`; использовать существующий `config.secrets.get_secret` / file existence — **никогда не логировать значения**.
- Piper models gitignored; preflight только сообщает missing/present.

## Owned paths

- `mark/app/preflight.py` (new) — предпочтительно рядом с `setup_wizard.py`
- `mark/app/__main__.py` **или** `python -m mark.app.preflight` entry (если нужен `__main__` только для preflight — согласовать один модуль)
- `tests/unit/app/test_preflight.py` (new)

## Forbidden paths

- `main.py`, `ui.py`, `readme.md`, `docs/audit/launch-runbook.md`
- Network calls; downloading models
- Writing secrets; creating `api_keys.json` with dummy live-looking keys

## Behavior

CLI roughly:

```bash
python -m mark.app.preflight
# exit 0 = ready enough for main.py attempt
# exit 1 = blockers (bad python, missing PyQt6/sounddevice/google.genai, missing gemini key)
# warnings (non-fatal): no face.png, no piper voice, no openrouter key, no settings.json
```

Checks (minimum):

| Check | Severity |
|---|---|
| `sys.version_info` in 3.11–3.12 | blocker |
| import `PyQt6`, `sounddevice`, `google.genai`, `psutil` | blocker |
| Gemini key resolvable via secrets API or non-empty file field | blocker |
| `face.png` exists | warning |
| `config/settings.json` exists | warning |
| Piper binary/voice under `models/piper/` | warning |
| import `playwright` | warning (or blocker if you document browser tools as required — prefer warning) |

## Acceptance

- Unit tests with fakes; offline; no real key values in asserts/output fixtures.
- Exit codes documented in module docstring.
- One commit; mypy-friendly types if touching `mark/app`.

## Stop conditions

- Need to change `config/secrets.py` contract → change request.
- Want to auto-pip-install from preflight → **forbidden** (docs only tell operator to pip install).
