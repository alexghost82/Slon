# Slon — first-launch runbook (operator)

Personal / non-commercial use under **CC BY-NC 4.0**. This document is an
operator checklist for a full desktop first run. It is **not** a
commercial-readiness claim.

For a short Quick Start, see `readme.md` (LAUNCH-T01). This runbook expands
install, Privacy, wake word, tool smoke, and troubleshooting.

Primary target: **macOS**. Windows / Linux notes are brief where commands differ.

---

## 1. Prerequisites

- [ ] OS: macOS (full UX), or Windows / Linux (tools + HUD; Privacy steps differ)
- [ ] Python **3.11 or 3.12** only (`pyproject.toml`: `>=3.11,<3.13`)
- [ ] Do **not** use system Python **3.14** — deps and tooling are not supported
- [ ] Disk space for a venv + Playwright browser binaries
- [ ] Network for `pip install` and first cloud provider calls (hybrid mode)

Check version:

```bash
python3.12 --version   # or python3.11 --version
# Expect: Python 3.11.x or 3.12.x
```

---

## 2. Install

From the repo root (this worktree or integration clone):

```bash
# Prefer an explicit 3.11/3.12 interpreter
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# OS-specific requirements (preferred)
#   macOS:   pip install -r requirements-macos.txt
#   Windows: pip install -r requirements-windows.txt
#   Linux:   pip install -r requirements-linux.txt
# Or: python setup.py   (picks OS file + installs Playwright browsers)

pip install -r requirements-macos.txt   # change file on Windows/Linux
python -m playwright install
```

Checklist:

- [ ] venv created with 3.11 or 3.12
- [ ] OS requirements file installed
- [ ] `python -m playwright install` completed (browser tools need it)
- [ ] Optional: `pip install -r requirements-dev.txt` if you will run pytest

`requirements.txt` only pulls `requirements-base.txt` (cross-platform shim). Prefer
the OS-specific file on a real machine.

---

## 3. Config — secrets (no values in this doc)

Secrets are **never** committed. Supported names
(`config/secrets.py` → `KNOWN_SECRET_NAMES`):

| Name | Typical use |
|---|---|
| `gemini_api_key` | Default Gemini path (`settings.example.json` → `provider_id: gemini`) |
| `openrouter_api_key` | OpenRouter / some tool fallbacks |
| `openai_api_key` | OpenAI provider path |

Resolution order (see `config/secrets.py`):

1. **macOS Keychain** — service `Slon`, account = secret name (`security` CLI)
2. **Windows Credential Manager** — target `Slon/<name>`
3. **Linux Secret Service** — `secret-tool` with service `Slon`, account = name
4. Fallback file **`config/api_keys.json`** mode `0600` only if no OS store is available

Operator checklist:

- [ ] Store at least the key for your chosen provider (usually `gemini_api_key`)
- [ ] Prefer OS secret store; use `api_keys.json` only as fallback
- [ ] Confirm `config/api_keys.json` is **not** staged for git (gitignored / local only)
- [ ] Never paste live key material into docs, tickets, or screenshots

Do not put secret fields inside `settings.json` (schema rejects them).

---

## 4. `settings.json` bootstrap (expected; LAUNCH-T05)

Expected first-run behavior (LAUNCH-T05 — may land after this doc):

- If `config/settings.json` is **missing**, create it from
  `config/settings.example.json` (or `config.settings` API /
  `ensure_settings_file`), **without** writing secrets.
- If `settings.json` **already exists**, do **not** overwrite.
- Invalid existing JSON → clear error; do not clobber the file.

Example defaults today (`config/settings.example.json`):

- `language`: `ru`
- `privacy_profile`: `hybrid`
- `provider_id`: `gemini`
- `network_mode`: `hybrid`

Checklist:

- [ ] After first launch (or after T05 merge), `config/settings.json` exists
- [ ] Secrets still only in OS store / `api_keys.json`, not in settings
- [ ] Existing user settings were not wiped

If bootstrap is not yet merged: copy `config/settings.example.json` →
`config/settings.json` manually once, then edit non-secret fields only.

---

## 5. macOS Privacy checklist

Full desktop UX needs three TCC grants. Grant them for the **Python /
Terminal / IDE** process that launches Slon (or a future bundled app).

### Microphone

- [ ] **System Settings → Privacy & Security → Microphone** — enable for the
      launcher (Terminal, iTerm, Cursor, etc.)
- Needed for local STT / Live voice path (`speech/stt/mic.py`, HUD mute toggle)

### Accessibility

- [ ] **System Settings → Privacy & Security → Accessibility** — enable for the
      same launcher
- Needed for input automation / desktop control tools

### Screen Recording

- [ ] **System Settings → Privacy & Security → Screen Recording** — enable for
      the same launcher
- Needed for screen tools (`actions/screen_processor.py` → screenshot path)

Notes:

- After toggling a permission, **quit and relaunch** the host app (Terminal /
  IDE), then restart Slon.
- Windows / Linux: use OS equivalents for mic and screen capture; there is no
  macOS TCC dialog. Accessibility / automation depends on the OS and packages
  (e.g. Windows `pywinauto` stack from `requirements-windows.txt`).

If the app never prompts for a permission, that is a product gap — file a
change request for LAUNCH-T04 / LAUNCH-T06 (UI / wake polish), not a doc edit.

---

## 6. First-run steps + wake word

Wake word logic: `speech/wake_word.py` (`WAKE_WORD = "Slon"`; ASR variants
`slon` / `sloon` / `слон`). Idle gate: `main.py` → `WAKE_IDLE_SECONDS = 45.0`
(after the last finished turn while awake, return to standby).

```bash
source .venv/bin/activate
python main.py
```

Optional same-LAN Desktop Control API (loopback default; see
`docs/audit/lan-bind.md`):

```bash
python -m server
# or: python -m server --host 127.0.0.1 --port 8765
```

Do **not** bind publicly. Wildcards (`0.0.0.0`, `::`) are rejected.

Operator checklist:

- [ ] `python main.py` opens the HUD / UI
- [ ] Boot enters **standby** — say **«Slon»** (or RU «слон») to wake
- [ ] Typed commands bypass the wake word (intentional)
- [ ] After ~45s idle while awake → standby again; wake word required
- [ ] Mute / unmute in UI works (muted mic → no listening)

iOS remote / Epic 14 / APNs — **out of scope** for first launch.

---

## 7. Minimal tool smoke matrix

Run while **awake** (after wake word). Soft-blocked tools stay idle in standby.

| Tool | Module | Smoke intent | Pass? |
|---|---|---|---|
| `open_app` | `actions/open_app.py` | Ask to open a known app (e.g. Safari / Calculator); app launches | [ ] |
| `web_search` | `actions/web_search.py` | Short factual query; non-empty answer (needs provider key / network) | [ ] |
| `screen_process` | `actions/screen_processor.py` | Ask what is on screen; needs Screen Recording + capture success | [ ] |

Notes:

- Browser automation paths need Playwright browsers installed (§2).
- `screen_process` fails closed if capture is denied or broken — recheck Privacy.
- One successful tool is enough for a minimal first-run gate; full matrix is for
  operator confidence.

---

## 8. Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| Import / venv errors; odd crashes | Python **3.14** (or &lt;3.11) | Recreate venv with **3.11 or 3.12** only |
| Browser tool fails / Playwright errors | Browsers not installed | `python -m playwright install` inside the same venv |
| No wake / no STT | Mic muted in UI, or Microphone TCC denied | Unmute HUD; grant Microphone; relaunch host app |
| Stuck in standby / tools soft-blocked | Need wake word; or idle ~45s returned to standby | Say **Slon**; typed input still works |
| Screen tool fails | Screen Recording denied | Grant TCC; relaunch; retry `screen_process` |
| Automation / clicks fail | Accessibility denied | Grant Accessibility; relaunch |
| Provider / search errors | Missing secret or wrong store | Ensure `gemini_api_key` (or chosen provider key) via OS store / `api_keys.json` |
| `settings.json` missing | T05 not merged yet | Manual copy from `settings.example.json` (§4) |

---

## 9. Out of scope (first launch)

- Public / internet bind of Desktop API (default is loopback; see
  `docs/audit/lan-bind.md`)
- APNs / push / VPN product / iOS remote (Epic 14)
- Commercial distribution or “commercial-ready” claims (CC BY-NC)
- Expanding Python upper bound to 3.14

---

## Quick cross-links

| Topic | Where |
|---|---|
| Wake word | `speech/wake_word.py` |
| Idle → standby | `main.py` (`WAKE_IDLE_SECONDS`) |
| Secrets | `config/secrets.py` |
| Settings example | `config/settings.example.json` |
| Optional Desktop API | `python -m server` · `docs/audit/lan-bind.md` |
| Quick Start | `readme.md` |
| Later smoke audit template | `docs/audit/launch-smoke.md` (LAUNCH-T07) |
