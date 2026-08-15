# Production Readiness Report

- Product / repo: Slon (`/Users/slon/Documents/GitHub/Slon`)
- Audit ID / timestamp: `20260815T151400Z` / 2026-08-15
- Mode: `full audit`
- Revision (commit SHA): `7a9c0f8d93181c950d3d1b02efed5b8ea18d00c9`
- Dirty worktree: yes (untracked `.cursor/` only)
- Auditor: production-readiness-auditor skill (Cursor agent)
- Platforms in scope: macOS desktop (primary); iOS MarkRemote simulator (secondary)
- Verdict: **CONDITIONAL GO** (personal / non-commercial beta on macOS only)

## 1. Executive summary

Slon’s automated foundation is strong on this revision: Desktop API bind policy denies wildcards, secrets are gitignored with placeholder-only hits in tracked code, preflight exit 0 on Python 3.12 venv, `main.py` stayed alive ≥6s (original audit), and MarkRemote **simulator build succeeded** with package XCTest ~72 pass. **Fix-and-verify (same audit ID):** DEF-003/004/002 closed — no `shell=True` under `actions/`, `.github/workflows/ci.yml` added, ruff green; security suite **11 passed**; gate pytest **716 passed / 2 skipped** (excluding host-blocked `test_face_load`). Remaining gaps for unqualified GO: interactive P0 mic/HUD/tool journeys **NOT RUN**, remote GitHub Actions green **NOT RUN** (no push), DEF-001 `face.png` WARN, dependency CVE scanning **NOT RUN**, CC BY-NC / **not commercial-ready**. Verdict remains **CONDITIONAL GO** for personal macOS beta; commercial/App Store/public-internet goals remain **NO-GO / out of scope**.

## 2. Scope и exclusions

### In scope
- Desktop Slon on macOS (Python 3.11–3.12 path via `.venv` 3.12.14)
- Automated tests, preflight, brief process launch, static security smokes
- iOS MarkRemote package tests + Debug simulator build
- Docs/gates under `docs/audit/`

### Explicit exclusions
- Commercial distribution / App Store (CC BY-NC; product docs forbid commercial-ready claims)
- Epic 14: APNs, VPN productization, public internet Desktop API bind
- Windows/Linux clean-install matrices (claimed supported; not re-proven here)
- Live cloud load/soak (cost + abuse risk)
- Paying, sending real messages, deleting real user data
- Formal OWASP certification

### Assumed / INFERRED requirements
- INFERRED: “production” for this repo means **personal beta operator-ready**, not SaaS production
- INFERRED P0 journeys from `orchestration/tasks/LAUNCH-MVP.md` and `docs/audit/launch-smoke.md`
- PROPOSED: no silent data loss on restart for memory/settings (not measured this run)

## 3. Environment и revision

| Item | Value |
|------|-------|
| Commit | `7a9c0f8d93181c950d3d1b02efed5b8ea18d00c9` |
| Branch | `integration/main` |
| Host OS | macOS 27.0 (arm64) |
| SDKs / toolchains | Python 3.12.14 (venv); Xcode 27.0 beta; Swift 6.4 via xcrun |
| Devices / emulators / simulators | iPhone 17 Pro simulator (booted) |
| Backend / endpoints (redacted) | loopback Desktop API; Gemini/OpenRouter cloud |
| Accounts / roles used | local operator; API key **presence** only |
| Build types tested | desktop debug process; iOS Debug-iphonesimulator |

Ссылка: `audit-manifest.md`.

## 4. Results by area

| Area | Status | Evidence | Notes |
|------|--------|----------|-------|
| Discovery / inventory | PASS | manifest + detect JSON | Dual stack + iOS mapped |
| Static analysis / build | PASS / PARTIAL | ruff PASS post-fix; mypy BLOCKED; iOS build PASS | DEF-002 fixed |
| Unit / integration tests | PASS | `fix-and-verify.md` | 716+ gates; face_load env BLOCKED here |
| Installation / upgrade | NOT RUN | — | Clean install not re-done |
| UI / E2E | NOT RUN / PARTIAL | process launch only | Mic/HUD interactive skipped |
| Functional / data integrity | PARTIAL | security+unit | Live tool path NOT RUN |
| Performance | NOT RUN | — | No baselines measured |
| Load | NOT RUN | — | Not authorized vs live cloud |
| Security / privacy | PASS (gates) | security 11 PASS; DEF-003 fixed | No formal cert claim |
| Operability / release ops | PASS (local) | CI YAML added (DEF-004) | Remote Actions green NOT RUN |

## 5. Feature coverage и critical journeys

### Coverage summary
- Features inventoried: desktop HUD/voice/tools/providers/memory/safety/server + iOS remote surfaces (~20 action modules; MarkRemote feature tabs)
- Features tested (automated): safety, bind, pairing unit, providers contracts, speech wake unit, iOS package
- Features NOT RUN / BLOCKED: live wake/tool, iOS↔desktop UITests, perf, pip-audit, Win/Linux install

### P0 critical journeys

| Journey | Platforms | Status | Evidence |
|---------|-----------|--------|----------|
| Launch | macOS | PASS (process) / visual NOT RUN | preflight + 6s alive |
| Onboarding / login | N/A keys local | PARTIAL | key presence OK; no OAuth product |
| Core product outcome (wake→reply) | macOS | NOT RUN | needs mic + Live |
| Save / sync | memory | PARTIAL | unit/migrate only |
| Error recovery | mixed | PARTIAL | offline suite; kill recovery NOT RUN |
| Logout / exit / data retention | desktop | NOT RUN | force-kill after 6s only |

Полная матрица: `test-matrix.md`.

## 6. Defects

| ID | Title | Severity | Priority | Confidence | Repro | Status |
|----|-------|----------|----------|------------|-------|--------|
| DEF-003 | `shell=True` in action helpers | MAJOR | P1 | High | static | **fixed** |
| DEF-004 | No CI workflows | MAJOR | P1 | Confirmed | 1/1 | **fixed** (remote green NOT RUN) |
| DEF-002 | Ruff E501 in wake tests | MINOR | P2 | Confirmed | 1/1 | **fixed** |
| DEF-001 | Missing `face.png` | MINOR | P3 | Confirmed | 1/1 | open |

Детали: `defects/DEF-XXX.md`.

## 7. Security / privacy findings

| ID | Finding | Severity | Confidence | Evidence | Notes |
|----|---------|----------|------------|----------|-------|
| DEF-003 | shell=True in `dev_agent` / Linux `computer_settings` | MAJOR | High | fixed | argv-only; security regression PASS |
| — | Wildcard/public bind denied | — | Confirmed | bind_policy + tests | Positive control |
| — | SSRF/traversal/injection smokes | — | Confirmed | tests/security 11 PASS | Not full MSTG |
| — | Tracked secret scan | — | Confirmed | fixtures + UI placeholders | Live keys gitignored |
| — | Certificate pinning (iOS) | — | Code present | CertificatePinningDelegate | Runtime pin efficacy NOT RUN |

Явно: формальная сертификация OWASP **не** заявляется.

## 8. Performance baseline и regressions

| Metric | Value | Unit | Env | Build | n | Method | Threshold | Result |
|--------|-------|------|-----|-------|---|--------|-----------|--------|
| Cold startup | — | — | — | — | 0 | — | PROPOSED | NOT RUN |
| Process alive window | ≥6 | s | macOS M2 | debug | 1 | manual kill | smoke | PASS (insufficient for latency SLO) |

## 9. Blocked / not-run

| Check | Status | What is required to run |
|--------|--------|-------------------------|
| Interactive wake/tool/mute | NOT RUN | Operator mic + TCC Privacy grants + Live session |
| iOS UITests vs desktop | NOT RUN | `python -m server` + `xcodebuild test` |
| mypy full | BLOCKED | Isolate numpy stubs / align `python_version` (docs claim 0 errors in prior wave) |
| pip-audit | NOT RUN | Install pip-audit with permission |
| Win/Linux install | NOT RUN | Those hosts |
| Perf/load | NOT RUN | Local SLO + disposable stand |
| Release signing / notarization | NOT RUN | Apple Developer identity (desktop packaging not in scope) |

## 10. Residual risks

| Risk | Likelihood | Impact | Mitigation / owner / due |
|------|------------|--------|---------------------------|
| Unverified interactive P0 | med | high | Owner runs launch-runbook checklist before trusting daily use |
| shell=True helpers | low | high | **Mitigated** — DEF-003 fixed; keep loopback-only before LAN trust |
| No CI drift | med | med | Workflow added; first remote green still pending |
| Dual-stack legacy (`actions/` mypy ignore) | med | med | Continue mark/ safety enforcement; reduce legacy surface |
| Cloud key/file fallback | low | high | Prefer OS keychain; never commit api_keys.json |
| CC BY-NC commercial misuse | low | legal | Keep non-commercial posture in all releases |

## 11. Verdict

**Verdict:** CONDITIONAL GO

Обоснование: нет подтверждённых BLOCKER/CRITICAL дефектов продукта в выполненных проверках; автоматизированные security/unit gates зелёные; обязательные интерактивные P0 и CI остаются открытыми с документированным принятием риска владельцем. Коммерческий / публичный интернет релиз — **вне scope и NO-GO**.

Открытые Blocker/Critical (confirmed): **нет**.

## 12. Production exit conditions

Для unqualified **GO** (personal beta):

- [ ] Operator completes interactive checklist in `docs/audit/launch-runbook.md` (wake, ≥1 tool, F4)
- [x] DEF-003 fixed (argv-only subprocess; security regression)
- [x] `ruff check tests` green (DEF-002)
- [x] CI workflow added (DEF-004); [ ] first remote Actions green on push/PR
- [ ] pip-audit (or equivalent) run with accepted vulns list
- [ ] Owner reaffirmation: CC BY-NC personal use only

Для **commercial / public**:

- [ ] License/business decision (currently closed as non-commercial)
- [ ] Epic 14 security productization
- [ ] Full platform install + a11y + perf gates

## 13. Fix plan и retest

| Priority | Defect / gap | Action | Retest procedure | Owner |
|----------|--------------|--------|------------------|-------|
| P0 | Interactive P0 | Operator manual smoke | launch-runbook checklist | product owner |
| P1 | DEF-003 | Remove shell=True | **done** — see `fix-and-verify.md` | engineering |
| P1 | DEF-004 | Add CI workflow | **done** locally; remote green pending | engineering |
| P2 | DEF-002 | Fix line length | **done** | engineering |
| P3 | DEF-001 | Ship face asset or accept WARN | preflight | engineering |

## Appendix

- Paths: this dir — `audit-manifest.md`, `test-matrix.md`, `defects/`, `evidence/`, `logs/`
- Commands index:
  - `python3 .cursor/skills/production-readiness-auditor/scripts/detect-project.py --root . --json`
  - `.venv/bin/python -m mark.app.preflight`
  - `.venv/bin/python -m pytest tests/unit tests/security tests/offline tests/integration -q`
  - `.venv/bin/python -m ruff check tests`
  - `export DEVELOPER_DIR=…/Xcode-beta.app/Contents/Developer && cd ios && xcrun swift test`
  - `xcodebuild -project ios/AppProject/MarkRemote.xcodeproj -scheme MarkRemote -destination 'id=<sim>' -derivedDataPath .build-xcode build`
- Tool versions: Python 3.12.14; Xcode 27.0 (27A5237l); Swift 6.4
- Artifacts not auto-committed (per skill)
