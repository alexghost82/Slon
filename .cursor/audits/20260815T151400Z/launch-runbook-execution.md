# Launch runbook execution — 2026-08-15

Source checklist: `docs/audit/launch-runbook.md`  
Host: macOS arm64 · `.venv` Python 3.12.14 · branch `integration/main`  
Policy: no public Desktop API bind; no paid actions; no real messaging/deletes; no secret values logged.

Status vocabulary: **PASS** / **FAIL** / **BLOCKED** / **NOT RUN** / **NOT APPLICABLE**

## §1 Prerequisites

| Item | Status | Evidence |
|------|--------|----------|
| OS macOS | PASS | `darwin` host (user_info / audit env) |
| Python 3.11–3.12 | PASS | `.venv/bin/python --version` → `Python 3.12.14` |
| Avoid system 3.14 for app | PASS | venv is 3.12 |
| Disk / network for install | NOT RUN | venv already present; no reinstall this session |

## §2 Install

| Item | Status | Evidence |
|------|--------|----------|
| venv 3.11/3.12 | PASS | `.venv` → python3.12 |
| OS requirements installed | PASS | preflight imports PyQt6/sounddevice/genai/psutil/playwright OK |
| `playwright install` | NOT RUN | not re-run; playwright import OK |
| `requirements-dev.txt` | PASS | pytest/ruff available in venv |

## §3 Config — secrets

| Item | Status | Evidence |
|------|--------|----------|
| Provider key present (presence only) | PASS | preflight: Gemini + OpenRouter keys present (values not logged) |
| Prefer OS store / fallback file | NOT RUN | resolution path not re-probed interactively |
| `api_keys.json` not staged | PASS | `git check-ignore` → gitignored; `git status --short` does not stage it |
| No secrets in settings | PASS | settings bootstrap path; preflight settings present |

## §4 settings.json bootstrap

| Item | Status | Evidence |
|------|--------|----------|
| `config/settings.json` exists | PASS | preflight + `test -f` |
| Secrets not in settings | PASS | schema/docs; not re-dumped |
| Existing settings not wiped | PASS | file present; this session did not overwrite |

## §5 macOS Privacy (TCC)

| Item | Status | Evidence |
|------|--------|----------|
| Microphone | NOT RUN | requires human System Settings interaction |
| Accessibility | NOT RUN | requires human grant |
| Screen Recording | NOT RUN | requires human grant |

## §6 First-run + wake word

| Item | Status | Evidence |
|------|--------|----------|
| `python main.py` HUD opens | NOT RUN | interactive GUI; only `main.py` AST parse OK this session |
| Standby + wake «Slon» | NOT RUN | needs mic + live process |
| Typed commands bypass wake | NOT RUN | interactive |
| Idle ~45s → standby | NOT RUN | interactive |
| Mute / unmute | NOT RUN | interactive |
| Desktop API loopback only | PASS (policy) | `validate_bind_host('0.0.0.0')` raises `BindHostError`; `127.0.0.1` accepted. Live `python -m server` **NOT RUN** |
| Audio device probe | BLOCKED / PARTIAL | `sounddevice.query_devices()` returned **0** devices in this agent environment (sandbox/TCC); not a product PASS |

## §7 Minimal tool smoke

| Tool | Status | Evidence |
|------|--------|----------|
| `open_app` | NOT RUN | needs awake HUD + Accessibility |
| `web_search` | NOT RUN | needs network + provider + awake session |
| `screen_process` | NOT RUN | needs Screen Recording + awake session |

## §8 Troubleshooting table

Document-only; no new failures exercised beyond known WARN missing `face.png` (DEF-001).

## §9 Out of scope

Confirmed **NOT APPLICABLE** / not attempted: public bind, APNs/iOS remote, commercial claims, Python 3.14.

## Automated gates (supporting)

| Check | Status | Evidence |
|-------|--------|----------|
| Preflight | PASS | exit 0 (WARN face.png) |
| Ruff tests | PASS | exit 0 (DEF-002 fixed) |
| Pytest gates (excl. face_load env block) | PASS | 716 passed, 2 skipped |
| Security suite | PASS | 11 passed (includes DEF-003 regression) |
| face_load under agent host | BLOCKED | `psutil.net_io_counters` PermissionError |

## Verdict for operator first-launch

**CONDITIONAL** — automated install/config/preflight/gates are green enough to proceed, but **interactive P0 (Privacy + wake + tools) remain NOT RUN**. Do not treat this file as a full GO for desktop first launch.
