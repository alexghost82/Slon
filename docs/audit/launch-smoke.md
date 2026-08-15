# Launch smoke — LAUNCH-MVP (first full desktop launch)

Date: 2026-08-15  
Integrator base after T01–T06: `61599d90884aacac885fa9da332b1da3b2d94d9f`  
Product: Slon (personal / non-commercial, CC BY-NC 4.0) — **not** commercial-ready.  
Python target: **3.11–3.12** (do not treat 3.14 as supported).

Related: `readme.md`, `docs/audit/launch-runbook.md`, `python -m mark.app.preflight`.

## Automated (integrator host, 2026-08-15)

Commands were run on the integration clone after T01–T06 cherry-picks.

| Check | Result | Notes |
|---|---|---|
| `pytest tests/unit/speech/test_wake_word.py -q` | **pass** | **10 passed** (host `python3` / pytest 9.1.1) |
| `pytest tests/unit -q` | **pass** | **696 passed, 6 skipped**, 2 warnings (Gemini `asyncio.iscoroutinefunction` deprecation) |
| `python3.12 -m mark.app.preflight` | **exit 1** (expected on bare interpreter) | Python 3.12 OK; Gemini/OpenRouter key **presence** OK (values not printed); **blockers**: missing `PyQt6`, `sounddevice`, `google.genai`, `psutil` on bare 3.12; **warnings**: no `face.png`, no `settings.json`, missing `playwright`; Piper assets present under `models/piper/` (gitignored) |

Preflight does **not** pip-install and never prints API key values.

Baseline note: LAUNCH-MVP docs cited ~652 unit tests earlier; current suite is **696 passed / 6 skipped** after integrated waves — no regression observed in this verify pass.

## Manual operator checklist (macOS)

Mark each: pass / fail / deferred.

- [ ] Create venv with **Python 3.11 or 3.12** (not 3.14)
- [ ] `pip install -r requirements-macos.txt` and `playwright install`
- [ ] `python -m mark.app.preflight` → exit 0 on a provisioned machine
- [ ] `python main.py` opens HUD
- [ ] Standby / **SAY SLON** visible; say wake word **Slon** / **Слон** (mic unmuted)
- [ ] ≥1 tool succeeds (`open_app` / `web_search` / `screen_process`)
- [ ] Mute/unmute (F4) does not crash; unmute in standby does **not** show false LISTENING
- [ ] macOS Privacy: Microphone, Accessibility, Screen Recording granted as needed

See `docs/audit/launch-runbook.md` for Privacy detail.

## Known gaps / change requests (docs only — not fixed here)

1. **`ensure_settings_file()` not yet called from `main.py` / UI startup** — API exists (LAUNCH-T05); preflight still warns when `config/settings.json` is absent until a call site is wired.
2. Operator desktop smoke above left **unchecked** in this session (no interactive HUD/mic run by the verify pass).
3. Epic 14 (public bind / APNs / VPN) remains out of scope.

## Stop conditions (none hit this verify)

- No secret values recorded in this file.
- No Python 3.14 support expansion.
- No public Desktop API bind enabled.
