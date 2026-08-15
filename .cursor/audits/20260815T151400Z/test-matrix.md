# Test matrix — Slon full audit `20260815T151400Z`

Revision: `7a9c0f8d93181c950d3d1b02efed5b8ea18d00c9`  
Roles: local operator (personal); no multi-tenant roles.  
INFERRED requirements labeled.

| ID | Feature / journey | Role | Path | Risk | Method | Evidence | Status |
|----|-------------------|------|------|------|--------|----------|--------|
| P0-01 | Preflight ready | operator | `python -m mark.app.preflight` | med | automated | `logs/preflight.txt` exit 0 | PASS |
| P0-02 | Desktop launch (process) | operator | `python main.py` | high | smoke 6s | `logs/main-launch-summary.txt` alive | PASS (process only) |
| P0-03 | HUD visual + SAY SLON | operator | interactive UI | high | manual | none this audit | NOT RUN |
| P0-04 | Wake word → voice reply | operator | mic + Gemini Live | high | manual | none this audit | NOT RUN |
| P0-05 | ≥1 tool success | operator | open_app/web_search/screen | high | manual + unit | unit/security only | NOT RUN (live) |
| P0-06 | Mute/unmute F4 | operator | HUD | med | unit + manual | unit wake tests; live NOT RUN | PARTIAL |
| P0-07 | Desktop API loopback | operator | `python -m server` | high | unit/integration | suites PASS; live listen NOT RUN | PARTIAL |
| P0-08 | iOS package XCTest | developer | `xcrun swift test` | med | automated | `logs/ios-swift-test.txt` ~72 pass | PASS |
| P0-09 | iOS app simulator build | developer | xcodebuild MarkRemote | med | automated | `logs/ios-app-build.txt` SUCCEEDED | PASS |
| P0-10 | iOS↔desktop pairing E2E | operator | UITests + server | high | e2e | requires live server | NOT RUN |
| C-01 | Unit tests | CI | `pytest tests/unit` | med | automated | 703 passed | PASS |
| C-02 | Security gates | CI | `pytest tests/security` | high | automated | 10 passed | PASS |
| C-03 | Offline gates | CI | `pytest tests/offline` | med | automated | 3 passed | PASS |
| C-04 | Integration gates | CI | `pytest tests/integration` | high | automated | 5 passed | PASS |
| C-05 | Combined pytest | CI | unit+sec+off+int | med | automated | 721 passed | PASS |
| C-06 | Ruff tests | CI | `ruff check tests` | low | automated | 2× E501 | FAIL |
| C-07 | Mypy | CI | `mypy` | med | automated | numpy stub syntax abort | BLOCKED |
| C-08 | Secret scan tracked | sec | pattern scan | high | automated | fixtures+placeholders only | PASS |
| C-09 | pip-audit | sec | deps | med | tool | not installed | NOT RUN |
| C-10 | SAST-lite shell=True | sec | ripgrep | high | static | `dev_agent`, `computer_settings` Linux | FAIL (findings) |
| D-01 | Clean install from empty | ops | venv+pip | med | documented prior | prior launch-smoke; not re-run clean | NOT RUN |
| D-02 | Upgrade migration | ops | settings/memory | med | — | — | NOT RUN |
| D-03 | Offline launch | ops | network off | med | — | — | NOT RUN |
| E-01 | Desktop UI a11y | QA | HUD | med | — | — | NOT RUN |
| G-01 | Startup timing | perf | cold start | low | — | — | NOT RUN |
| G-02 | Load/soak | perf | — | high | — | forbidden vs prod cloud | NOT RUN |
| H-01 | Bind wildcard denied | sec | bind_policy | high | runtime+tests | `logs/runtime-smoke.txt` | PASS |
| H-02 | SSRF/traversal/injection | sec | safety | high | tests/security | PASS | PASS |
| I-01 | CI workflows | ops | `.github` | med | discovery | absent | FAIL (gap) |
| I-02 | Observability | ops | crash/logs | med | docs/code | local logs only; no remote APM | PARTIAL |
| I-03 | Commercial/App Store | legal | CC BY-NC | blocker | docs | explicitly out | NOT APPLICABLE (excluded) |

## P0 priority (INFERRED for personal beta)

1. Preflight → launch → HUD standby
2. Wake word conversation
3. One tool
4. Mute/unmute stability
5. Optional: Desktop API + iOS pairing on loopback/LAN

## High-risk flags

- Tool surface (`actions/*`, `cmd_control`, `dev_agent`, screen/file)
- Secrets (`config/secrets.py`, Keychain, api_keys.json)
- LAN/TLS bind opt-in
- `shell=True` on Linux brightness + VS Code open path
