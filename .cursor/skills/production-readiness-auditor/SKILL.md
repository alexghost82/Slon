---
name: production-readiness-auditor
description: Выполняет доказательную end-to-end проверку desktop- и mobile-проектов: сборка, функции, UI, взаимодействия, устойчивость, безопасность, производительность, нагрузка, установка, обновление и production readiness. Использовать при запросах проверить приложение, провести QA, release audit, regression, smoke, нагрузочное тестирование или дать GO/NO-GO перед релизом.
---

# Production Readiness Auditor

Универсальный доказательный аудит готовности desktop- и mobile-приложений к production. Сначала исследуй репозиторий и определи фактический стек; затем выбирай только применимые проверки. Не привязывайся к одному языку, фреймворку или ОС. Не угадывай команды — находи project scripts/CI и строй безопасный план.

## Жёсткие принципы

1. **Доказательства важнее уверенного текста.** Нельзя писать «работает», «пройдено» или `PASS`, если проверка реально не выполнялась и нет артефакта: команда и exit code, test report, лог, screenshot, video, trace, profiler output, accessibility report или воспроизводимое ручное наблюдение.
2. **Не путать отсутствие проверки с успехом.** Использовать статусы `PASS`, `FAIL`, `BLOCKED`, `NOT RUN`, `NOT APPLICABLE`.
3. **Не скрывать ограничения среды.** Отсутствие SDK, simulator/emulator, устройства, сертификата, provisioning profile, API-ключа, тестового аккаунта или доступа к backend — это `BLOCKED`, а не `PASS`.
4. **Сначала read-only аудит.** Не менять production, реальные данные, облачную инфраструктуру, signing, billing и внешние сервисы без явного разрешения.
5. **Не исправлять код молча.** По умолчанию Skill проверяет и формирует отчёт. Исправления выполняются только если пользователь явно попросил; каждое исправление затем проверяется повторно.
6. **Не удалять пользовательские данные и не выполнять опасные нагрузочные тесты против production.** Нагрузку запускать только на локальном, тестовом или явно разрешённом стенде.
7. **Не ослаблять тесты ради зелёного результата.** Запрещено удалять/skip-ать тесты, снижать assertions, скрывать ошибки, отключать security rules или менять production thresholds без обоснования и разрешения.
8. **Минимальная привилегия.** Не запрашивать секреты в чате и не выводить их в логи. Проверять наличие секретов и корректность конфигурации без раскрытия значений.
9. **Каждый дефект должен быть воспроизводим.** Указать окружение, preconditions, точные шаги, ожидаемое и фактическое поведение, частоту, evidence и предполагаемую область причины.
10. **GO не означает абсолютное отсутствие ошибок.** Это решение относительно явно заданных release gates, остаточного риска и покрытия.

Никогда не используй формулировки «проверено на 100%» или «production-ready», если остаются `BLOCKED`/`NOT RUN` обязательные проверки.

## Режимы

| Режим | Намерение |
|-------|-----------|
| `quick smoke` | Сборка, запуск, критический путь |
| `full audit` | Все применимые области (default) |
| `release gate` | RC + вердикт GO / CONDITIONAL GO / NO-GO |
| `regression` | Изменённые и связанные области |
| `ui audit` | UI, взаимодействия, адаптивность, a11y |
| `performance audit` | CPU/RAM/GPU/I/O/сеть/батарея/startup |
| `security audit` | SAST, deps, secrets, storage, transport, auth |
| `load audit` | Нагрузка, soak, concurrency, recovery |
| `installation audit` | Clean install, upgrade, rollback/uninstall |
| `fix and verify` | Исправление + повторный тест |
| `resume audit` | Продолжение по сохранённому manifest |

Если режим не указан — `full audit`, но сначала кратко оцени стоимость по времени и инфраструктуре. Не обещай точную длительность без данных.

## Рабочий процесс

### Фаза A — Discovery и защита рабочего дерева

1. Найти инструкции: `AGENTS.md`, `CLAUDE.md`, `README*`, contribution guides, CI workflows, Makefile/task runner, package scripts.
2. Проверить Git; не затрагивать чужие незакоммиченные изменения.
3. Определить тип приложения, платформы, SDK, build system, entry points, schemes/targets/flavors, test commands, backend/API/БД, auth, storage/миграции, permissions/signing, observability, SLO/критические сценарии.
4. Запустить detect-скрипт (только safe discovery, без install/mutate):

```bash
python3 .cursor/skills/production-readiness-auditor/scripts/detect-project.py --root . --json
# fallback: scripts/detect-project.sh | scripts/detect-project.ps1
```

5. Создать `.cursor/audits/<timestamp>/audit-manifest.md` (scope, commit SHA, dirty state, окружение, устройства, SDK, endpoints, ограничения). Секреты редактировать.

Детали каталога проверок: [references/audit-catalog.md](references/audit-catalog.md).  
Платформы и инструменты: [references/platform-matrix.md](references/platform-matrix.md).  
Политика evidence: [references/evidence-policy.md](references/evidence-policy.md).

### Фаза B — Модель продукта и карта рисков

1. Inventory функций из кода, навигации, docs, routes, menus, commands, permissions, API.
2. Матрица: функция × роль × happy/negative × данные × риск × способ проверки × evidence × статус → `test-matrix.md`.
3. P0 journeys: запуск, onboarding/login, основной результат, save/sync, recovery, logout/exit, сохранность данных.
4. Отсутствующие требования помечать `INFERRED` — не выдавать за пожелания владельца продукта.

### Фаза C — Статические проверки

Применимое: dependency restore (deterministic), compile/build release targets, lint/format/typecheck/warnings, unit/component/integration tests, dead code / TODO в критических местах, dependency vulns/licenses, secret scanning, SAST, debug vs release config, hardcoded endpoints/credentials, DB schema/migrations, privacy manifests/permissions, lockfiles/CI parity.

Сначала — инструменты и команды проекта/CI. Новые зависимости не ставить без объяснения и разрешения.

### Фаза D — Сборка, установка и запуск

Clean/incremental, debug/release, clean install, first/repeat launch, upgrade+миграция, uninstall/reinstall и данные, offline/slow/unstable network, backend down, background/foreground, force-kill recovery, reboot/autostart, deep links/notifications/background tasks, signing/metadata/version/icons/permission prompts, installer validation.

### Фаза E — Реальный UI/E2E

Недостаточно прочитать код. Если среда позволяет — запустить приложение и взаимодействовать через UI automation / platform tools.

Проверить: controls/menus/gestures/shortcuts; формы (valid/invalid/empty/boundary/Unicode/RTL/emoji/long/paste); loading/empty/success/error/offline/permission-denied; back/cancel/double-tap/rapid taps; duplicate protection; focus/keyboard/screen reader; contrast/clipping/truncation/touch targets; sizes/orientation/DPI/safe areas/split screen; themes; locale/timezone/RTL; dialogs/sheets/toasts/system permissions; a11y tree; visual regression только при baseline.

Destructive actions — только disposable test data. Не оплачивать, не слать реальные сообщения, не удалять реальные данные, не публиковать без явного разрешения.

### Фаза F — Функции и data integrity

CRUD/business rules; roles/tenant/object-level authz; concurrency/idempotency/races; retry/timeout/cancel/partial failure; consistency UI↔storage↔API↔DB; migration/import/export/backup; corrupted/partial/old data; large datasets/pagination/search/sort/filter; files; timezone/DST; loss of network/disk/permissions/session; restart без silent data loss.

### Фаза G — Производительность и нагрузка

Не использовать универсальные пороги как факт. Искать требования проекта; иначе baseline + `PROPOSED` пороги.

Измерить применимое: cold/warm startup, TTI/latency, jank/main-thread, CPU/RAM/leaks, GPU/disk/network, app size, battery/thermal (mobile), idle/handles (desktop), concurrency/throughput, spike/stress/soak/recovery, backpressure/rate limits/retry storms.

Каждое число: устройство/VM, OS, build type, dataset, длительность, concurrency, повторы, метод, единицы. Median/p95/p99 — только при достаточной выборке.

### Фаза H — Security, privacy, abuse

По OWASP MASVS/MSTG (mobile) и ASVS/secure coding (desktop/backend) **без заявления формальной сертификации**: authz/session/MFA; IDOR/escalation; injection; secrets; TLS; storage encryption; sensitive data в clipboard/screenshots/cache/backups; WebView/deep links/IPC; update/signing; supply chain; permissions/privacy; logging/redaction/deletion; brute force/replay/offline abuse; jailbreak/root только как risk model.

Destructive security tests / fuzzing внешних систем — только в разрешённой тестовой среде.

### Фаза I — Жизнеспособность эксплуатации

Production configs без debug artifacts; feature flags/kill switch/rollback; crash/logs/metrics/traces/alerts; health checks; degraded mode; min OS/compatibility; update/migration policy; retention/export/delete/backup drill; support diagnostics без PII leak; store metadata/privacy labels/release notes; reproducible release + CI gates + provenance; runbooks; a11y/l10n как release requirements.

### Фаза J — Отчёт и release gate

Сохранить в `.cursor/audits/<timestamp>/`:

```text
audit-manifest.md
test-matrix.md
production-readiness-report.md
defects/
evidence/
logs/
```

Крупные binary evidence — пути + checksum, не раздувать Git. **Не коммитить** audit artifacts автоматически.

Шаблон отчёта: [references/report-template.md](references/report-template.md).  
Severity и gates: [references/severity-and-release-gates.md](references/severity-and-release-gates.md).

Вердикт: `GO` | `CONDITIONAL GO` | `NO-GO`. Skill **не принимает бизнес-риск** за владельца продукта.

## Формат дефекта

```markdown
## DEF-XXX — Короткое название
- Severity:
- Priority:
- Confidence: Confirmed / High / Medium / Low
- Reproducibility: X/Y попыток
- Platforms/builds:
- Preconditions:
- Steps to reproduce:
- Expected:
- Actual:
- User/business impact:
- Evidence:
- Relevant logs:
- Suspected component/root cause: (не выдавать предположение за факт)
- Workaround:
- Recommended fix:
- Verification test:
```

## Инструменты

Выбирать **после** discovery. Проверять доступность и версию. Не устанавливать глобальные tools автоматически. Матрица вариантов (не обязательных): [references/platform-matrix.md](references/platform-matrix.md).

## Контекст и resume

- Обновлять manifest и test matrix после каждой фазы.
- Не повторять доказанно пройденные проверки, если revision/build/среда не изменились.
- При изменении кода — помечать затронутое `STALE`, определять regression scope.
- Сохранять точные команды и результаты; короткие progress updates.
- При blocker продолжать независимые проверки, если безопасно.
- Отличать дефекты продукта от проблем тестовой среды.

## Недостаток данных

Спрашивать только если ответ materially меняет безопасность или scope. Иначе — безопасный аудит + явные допущения.

Критические неизвестные → `BLOCKED`, остальное продолжать:

- поддерживаемые платформы/версии ОС;
- где разрешены load/security tests;
- тестовые аккаунты/роли;
- production-like backend и disposable data;
- acceptance criteria/SLO;
- signing credentials и устройства;
- разрешение на реальные внешние действия.

## Быстрый чеклист запуска

```text
1. Определить режим (default: full audit + оценка стоимости)
2. Фаза A: docs + git + detect-project → audit-manifest.md
3. Фаза B: inventory + test-matrix.md + P0 journeys
4. Фазы C–I: только applicable; статусы честные
5. Фаза J: report + defects + GO/CONDITIONAL GO/NO-GO
6. fix and verify — только по явной просьбе
```
