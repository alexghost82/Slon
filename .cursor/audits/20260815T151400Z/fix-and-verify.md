# Fix and verify — 2026-08-15 (post DEF-003 / DEF-004)

Audit ID: `20260815T151400Z`  
Branch: `integration/main` @ `7a9c0f8d93181c950d3d1b02efed5b8ea18d00c9` (+ uncommitted fixes below)  
Python: `.venv` 3.12.14  
No git commit created this session. No push. Secrets not printed / not staged.

## Fixes applied

### DEF-003 (MAJOR) — closed
- `actions/dev_agent.py` — `_open_vscode`: `shell=False`; Windows `.cmd` via `["cmd.exe", "/c", cmd, path]`
- `actions/computer_settings.py` — Linux brightness fallback: `_linux_adjust_brightness_xrandr` (argv-only `xrandr`); no shell pipelines
- `tests/security/test_beta_security_gates.py` — regression assert: no `shell=True` in those modules

### DEF-004 (MAJOR) — closed (workflow added; remote Actions green NOT RUN)
- `.github/workflows/ci.yml` — push/PR on `integration/main`/`main`/`master`: Python 3.12, apt portaudio/Qt libs, `requirements-linux.txt` + `requirements-dev.txt`, `ruff check tests`, pytest gate suites with `QT_QPA_PLATFORM=offscreen`

### DEF-002 (MINOR) — closed opportunistically
- `tests/unit/speech/test_wake_word.py` — E501 wraps

## Commands and results

| Command | Exit | Result |
|---------|------|--------|
| `.venv/bin/python -m mark.app.preflight` | 0 | PASS (1 WARN: missing `face.png`) |
| `rg 'shell=True' actions/` | 0 matches | PASS (no production `shell=True`) |
| `.venv/bin/python -m ruff check tests` | 0 | PASS |
| `.venv/bin/python -m pytest -q tests/security` | 0 | **11 passed** |
| `.venv/bin/python -m pytest -q tests/unit tests/security tests/offline tests/integration --ignore=tests/unit/ui/test_face_load.py` | 0 | **716 passed, 2 skipped** |
| Same suites **including** `tests/unit/ui/test_face_load.py` | 1 | **2 failed**, 718 passed, 2 skipped — failures are `PermissionError` on `psutil.net_io_counters()` while importing `ui` (agent/host sysctl restriction). Prior audit on same machine: 721 passed. Treat as **environment BLOCKED**, not a regression from DEF-003/004. |
| GitHub Actions remote run | — | **NOT RUN** (no push; prefer no commit) |

## Remaining gaps (do not claim full GO)

- Interactive P0: mic / wake word / HUD / tool smoke / TCC grants — **NOT RUN** (see `launch-runbook-execution.md`)
- DEF-001 missing `face.png` — still open (MINOR)
- Remote CI green on GitHub — pending first push/PR
- `test_face_load` under this agent host — BLOCKED by macOS `sysctl` PermissionError for `psutil`
- Commercial / public internet / App Store — still out of scope (CC BY-NC)

## Secrets / git hygiene

- `config/api_keys.json` gitignored (`!!` ignored); not staged
- `.venv/` ignored; not staged
- No commit made
- Modified/untracked application paths: `actions/computer_settings.py`, `actions/dev_agent.py`, `tests/security/test_beta_security_gates.py`, `tests/unit/speech/test_wake_word.py`, `.github/workflows/ci.yml`, audit artifacts under `.cursor/audits/`
