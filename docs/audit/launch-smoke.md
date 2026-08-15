# Launch smoke — LAUNCH-MVP (first full desktop launch)

Date: 2026-08-15 (follow-up: legacy `google.generativeai` → `google.genai` migration)  
Integrator base after T01–T06: `61599d90884aacac885fa9da332b1da3b2d94d9f`  
Prior follow-up HEAD: `c7ddb0ac7c1f4b6fa46aaab99768f3508af77b11` (`ensure_settings_file` wired into `main.py`)  
Product: Slon (personal / non-commercial, CC BY-NC 4.0) — **not** commercial-ready.  
Python target: **3.11–3.12** (do not treat 3.14 as supported).

Related: `readme.md`, `docs/audit/launch-runbook.md`, `python -m mark.app.preflight`.

## Automated (integrator host, 2026-08-15 follow-up)

Environment used for green preflight:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-macos.txt -r requirements-dev.txt
playwright install chromium   # browsers only; not committed
```

| Check | Result | Notes |
|---|---|---|
| `pytest tests/unit/config/test_settings_bootstrap.py -q` | **pass** | **7 passed** (includes main wiring regression) |
| `pytest tests/unit/speech/test_wake_word.py -q` | **pass** | **10 passed** |
| `pytest tests/unit/agent -q` + gemini/requirements unit | **pass** | agent **14 passed**; gemini+requirements+executor subset **37 passed** |
| `.venv/bin/python -m mark.app.preflight` | **exit 0** | Python 3.12 OK; Gemini/OpenRouter key **presence** OK (values not printed); imports OK; `settings.json` present after bootstrap; Piper OK; playwright import OK; **warning only**: no `face.png` |
| `python3.12 -m mark.app.preflight` (bare host) | **exit 1** (expected) | Same blockers as before: missing `PyQt6`, `sounddevice`, `google.genai`, `psutil`; warning: no `face.png` |
| Audio device probe (`sounddevice.query_devices`) | **pass** (host) | 4 devices visible outside sandbox; default in/out set |
| `python main.py` brief launch | **pass** (import path) | Former `ModuleNotFoundError: google.generativeai` cleared. Unsandboxed `.venv/bin/python main.py` stayed alive ≥5s with no generativeai error (process then stopped). Interactive HUD/mic not fully exercised. |

Preflight does **not** pip-install and never prints API key values.  
`.venv/`, `config/settings.json`, and `config/api_keys.json` were **not** committed.

## Manual operator checklist (macOS)

Mark each: pass / fail / deferred / blocked.

- [x] Create venv with **Python 3.11 or 3.12** (not 3.14) — **pass** (`python3.12 -m venv .venv`)
- [x] `pip install -r requirements-macos.txt` and `playwright install` — **pass** (`requirements-dev.txt` also installed for pytest; `playwright install chromium` OK)
- [x] `python -m mark.app.preflight` → exit 0 on a provisioned machine — **pass** (in `.venv`; 1 warning: missing `face.png`)
- [x] `python main.py` opens HUD — **pass** (import path / process stays up ≥5s unsandboxed; visual HUD confirmation still operator-side)
- [ ] Standby / **SAY SLON** visible; say wake word **Slon** / **Слон** (mic unmuted) — **skipped**: no interactive mic/hardware exercise in this agent session
- [ ] ≥1 tool succeeds (`open_app` / `web_search` / `screen_process`) — **skipped**: requires live HUD + model session
- [ ] Mute/unmute (F4) does not crash; unmute in standby does **not** show false LISTENING — **skipped** (interactive); unit coverage for unmute HUD exists separately (`61599d9`)
- [ ] macOS Privacy: Microphone, Accessibility, Screen Recording granted as needed — **skipped**: cannot verify TCC grants from this agent environment

See `docs/audit/launch-runbook.md` for Privacy detail.

## Known gaps / change requests

1. ~~`ensure_settings_file()` not yet called from `main.py` / UI startup~~ — **done** in `c7ddb0a` (`main._bootstrap_settings()` before HUD).
2. ~~Legacy `google.generativeai` import on `main.py` import path~~ — **done**: migrated to `google.genai` (`Client` / `models.generate_content`) in actions + agent modules. Operator interactive HUD/mic/tool smoke still **incomplete**.
3. Missing optional asset: `face.png` (preflight warning only; geometric HUD fallback).
4. Epic 14 (public bind / APNs / VPN) remains out of scope.

## Stop conditions (none hit this verify)

- No secret values recorded in this file.
- No Python 3.14 support expansion.
- No public Desktop API bind enabled.
