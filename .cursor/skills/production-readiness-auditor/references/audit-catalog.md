# Audit catalog

Каталог применимых проверок. После discovery отмечай каждую как `PASS` / `FAIL` / `BLOCKED` / `NOT RUN` / `NOT APPLICABLE`. Не отмечай `PASS` без evidence ([evidence-policy.md](evidence-policy.md)).

Режимы включают подмножества:

| Mode | Primary phases |
|------|----------------|
| quick smoke | A (light), C build, D launch, E/F P0 only |
| full audit | A–J |
| release gate | A–J focused on gates |
| regression | impact analysis + related checks |
| ui audit | A, B, E (+ related F) |
| performance audit | A, G |
| security audit | A, C security, H |
| load audit | A, G load |
| installation audit | A, D install/upgrade |
| fix and verify | defect fixes + targeted retest |
| resume audit | continue from manifest |

---

## A. Discovery

| ID | Check | Evidence |
|----|-------|----------|
| A01 | Project docs found (README, AGENTS, CONTRIBUTING, CI) | paths |
| A02 | Git status / commit SHA / dirty summary | command output |
| A03 | detect-project executed | JSON/manifest excerpt |
| A04 | App type & platforms identified | detect + docs |
| A05 | Build system & package managers | files/commands |
| A06 | Entry points / schemes / flavors / configs | project files |
| A07 | Existing test commands mapped | CI/scripts |
| A08 | Backend/API/DB/cache/queue deps mapped | configs (redacted) |
| A09 | Auth model / roles / test accounts availability | roles only |
| A10 | Storage, migrations, backup/restore surfaces | paths |
| A11 | Permissions / entitlements / manifests / signing surfaces | paths |
| A12 | Observability surfaces (logs/metrics/crash/tracing) | paths |
| A13 | Stated requirements / SLO / critical journeys | docs or INFERRED |
| A14 | audit-manifest.md created | path |

---

## B. Product model & risk

| ID | Check |
|----|-------|
| B01 | Feature inventory from code/nav/docs/routes/menus/API |
| B02 | test-matrix.md with role × path × risk × method × status |
| B03 | P0 journeys listed and prioritized |
| B04 | INFERRED requirements labeled |
| B05 | High-risk areas flagged (auth, payments, data delete, sync, IPC) |

---

## C. Static

| ID | Check | Notes |
|----|-------|-------|
| C01 | Deterministic dependency restore | lockfile respected |
| C02 | Compile/build all in-scope release targets | |
| C03 | Lint / format check | project tools first |
| C04 | Typecheck / compiler warnings triage | |
| C05 | Unit tests | |
| C06 | Component / widget tests | |
| C07 | Integration tests (non-UI) | |
| C08 | Dead code / TODO/FIXME/HACK in critical paths | not vanity repo-wide noise |
| C09 | Dependency vulnerabilities | tool output |
| C10 | Outdated / abandoned packages & license risk | |
| C11 | Secret scanning (no secret values in report) | |
| C12 | SAST / insecure API patterns | |
| C13 | Debug vs release / feature flags / env separation | |
| C14 | Hardcoded endpoints / credentials / insecure transport | |
| C15 | Verbose logging risky for production | |
| C16 | DB schema & forward/back migrations | if rollback claimed |
| C17 | Privacy manifests / permissions minimization | |
| C18 | Lockfiles present & CI parity | |
| C19 | Reproducible build notes / gaps | |

---

## D. Build, install, launch

| ID | Check |
|----|-------|
| D01 | Clean build |
| D02 | Incremental build |
| D03 | Debug build run |
| D04 | Release (or release-like) build run |
| D05 | Clean install |
| D06 | First launch |
| D07 | Subsequent launch |
| D08 | Upgrade from last supported version + data migration |
| D09 | Uninstall / reinstall & data retention expectations |
| D10 | Launch offline |
| D11 | Slow / unstable network |
| D12 | Network recovery |
| D13 | Backend unavailable |
| D14 | Background / foreground / suspend / resume |
| D15 | Minimize / restore (desktop) |
| D16 | Force-kill & recovery |
| D17 | Reboot / relogin / autostart (if applicable) |
| D18 | Deep links / URI handlers |
| D19 | File associations |
| D20 | Notifications |
| D21 | Background tasks |
| D22 | Signing / package metadata / version / icons |
| D23 | Permission prompts correctness |
| D24 | Installer / package validation |

---

## E. UI / E2E

| ID | Check |
|----|-------|
| E01 | App actually launched for interactive audit |
| E02 | Buttons / menus / tabs / links reachable |
| E03 | Gestures / keyboard shortcuts / context menus |
| E04 | Forms: valid |
| E05 | Forms: invalid / empty / boundary |
| E06 | Forms: Unicode / RTL / emoji / long / paste / autofill |
| E07 | Loading / empty / success / warning / error states |
| E08 | Offline / permission-denied UI states |
| E09 | Back navigation / cancel |
| E10 | Double click/tap / rapid taps |
| E11 | Duplicate submit protection |
| E12 | Focus order / keyboard-only |
| E13 | Screen reader labels / dynamic text |
| E14 | Contrast / clipping / overlap / truncation |
| E15 | Scrollability / touch target size |
| E16 | Window/screen sizes / orientation |
| E17 | DPI / scaling / safe areas / notch |
| E18 | Split screen / multi-window (if supported) |
| E19 | Light / dark / high-contrast |
| E20 | Locale / date-time-number / timezone / RTL |
| E21 | Software & hardware keyboard |
| E22 | Mouse / trackpad / touch / stylus / gamepad (only if supported) |
| E23 | Dialogs / sheets / popovers / toasts |
| E24 | System permission dialogs interaction |
| E25 | Accessibility tree / focus traps |
| E26 | Visual regression vs baseline (or screenshots without pixel-perfect claim) |

Destructive UI actions require disposable data and explicit permission for pay/send/delete-real/publish.

---

## F. Functional & data integrity

| ID | Check |
|----|-------|
| F01 | CRUD & business rules |
| F02 | Role / permission enforcement |
| F03 | Tenant isolation |
| F04 | Object-level authorization |
| F05 | Concurrent edits |
| F06 | Idempotency |
| F07 | Race conditions (targeted) |
| F08 | Retry / timeout / cancellation |
| F09 | Partial failure handling |
| F10 | UI ↔ local storage ↔ API ↔ DB consistency |
| F11 | Migrations |
| F12 | Import / export |
| F13 | Backup / restore |
| F14 | Corrupted / partial / old data handling |
| F15 | Large datasets / long lists |
| F16 | Pagination / search / sort / filter |
| F17 | File upload/download |
| F18 | Unsupported / corrupted files |
| F19 | Local time / UTC / DST / timezone change |
| F20 | Network loss during write |
| F21 | Disk / permission loss |
| F22 | Session expiry / token refresh |
| F23 | Restart recovery without silent data loss |

---

## G. Performance & load

Пороги: project SLO first; else measure baseline and mark `PROPOSED`.

| ID | Check |
|----|-------|
| G01 | Cold startup |
| G02 | Warm startup |
| G03 | Time to interactive |
| G04 | Key action latency |
| G05 | UI responsiveness / jank / dropped frames |
| G06 | Main-thread blocking |
| G07 | CPU usage |
| G08 | RAM / peak / growth |
| G09 | Leak signals / object growth |
| G10 | GPU (if relevant) |
| G11 | Disk I/O |
| G12 | Network traffic volume |
| G13 | Package / app size |
| G14 | Mobile battery / thermal / background consumption |
| G15 | Desktop idle consumption |
| G16 | Handles / FDs / threads |
| G17 | API concurrency / throughput (test stand) |
| G18 | Spike test |
| G19 | Stress test |
| G20 | Soak / endurance |
| G21 | Recovery after load |
| G22 | Queues / backpressure / rate limits |
| G23 | Retry storms / graceful degradation |

**Never** run dangerous load against production.

---

## H. Security & privacy

Чеклист в духе OWASP MASVS/MSTG / ASVS — **без** формальной сертификации.

| ID | Check |
|----|-------|
| H01 | Authentication flows |
| H02 | Authorization / session lifecycle |
| H03 | MFA / recovery (if claimed) |
| H04 | IDOR / privilege escalation probes (authorized env) |
| H05 | Input validation / injection surfaces |
| H06 | Secrets in repo / build / logs / crash dumps |
| H07 | TLS / certificate validation |
| H08 | Storage encryption / Keychain/Keystore/Credential Manager |
| H09 | Sensitive data in clipboard / screenshots / recents / temp / cache / backups |
| H10 | WebView security |
| H11 | Deep links / intents / URL handlers / IPC |
| H12 | Update mechanism & package/code signing trust |
| H13 | Dependency / supply-chain risk |
| H14 | Permissions & privacy disclosures |
| H15 | Logging redaction |
| H16 | Account / data deletion (if applicable) |
| H17 | Brute force / replay / duplicate request (test env) |
| H18 | Offline abuse / local tampering risk model |
| H19 | Jailbreak/root/debugger/emulator assumptions as risk (no absolute protection claim) |

Active destructive tests / external fuzzing — only on allowed test environment.

---

## I. Operability

| ID | Check |
|----|-------|
| I01 | Production configs correct; no debug artifacts in release |
| I02 | Feature flags / kill switch |
| I03 | Rollback plan documented or rehearsable |
| I04 | Crash handling |
| I05 | Structured logs / metrics / traces |
| I06 | Alertability (how failures surface) |
| I07 | Health / readiness checks (services) |
| I08 | Offline / maintenance / degraded mode |
| I09 | Min OS / compatibility policy |
| I10 | Update cadence & migration policy |
| I11 | Data retention / export / delete |
| I12 | Backup restore drill |
| I13 | Support diagnostics without PII leak |
| I14 | Store/package metadata / privacy labels |
| I15 | Release notes adequacy |
| I16 | Reproducible release procedure |
| I17 | CI gates & artifact provenance |
| I18 | Runbooks for known failures |
| I19 | Accessibility as release requirement |
| I20 | Localization as release requirement |

---

## J. Reporting

| ID | Check |
|----|-------|
| J01 | audit-manifest.md complete |
| J02 | test-matrix.md complete |
| J03 | production-readiness-report.md complete (all 13 sections) |
| J04 | defects/ filed for FAIL items becoming defects |
| J05 | evidence/ and logs/ referenced |
| J06 | Verdict issued per [severity-and-release-gates.md](severity-and-release-gates.md) |
| J07 | Residual risks & exit conditions listed |
| J08 | Product defects vs environment issues separated |
| J09 | No automatic git commit of audit artifacts |

---

## Quick smoke minimal set

A03–A06, A14, C02, C05 (if exists), D04–D07, E01 + P0 subset of E/F, J06 as **smoke verdict only** (not full production GO unless user asked release gate and gates met).
