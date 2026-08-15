# LAUNCH-AGENT-PROMPTS — запуск код-агентов (LAUNCH-MVP)

Связанные файлы:

- Мастер-ТЗ: `orchestration/tasks/LAUNCH-MVP.md`
- Ownership: `orchestration/FILE_OWNERSHIP.md` → секция **LAUNCH-MVP**
- Task specs: `orchestration/tasks/LAUNCH-T01.md` … `LAUNCH-T07.md`
- Правила: `AGENTS.md`

---

## 0. Интегратор — до спавна агентов

Выполни **один раз** в интеграционном клоне:

```bash
cd /Users/slon/Documents/GitHub/Slon
# 1) Закоммить текущий WIP (Slon rename, wake word, LAUNCH task specs),
#    ИЛИ перенеси его в integration/main иначе агенты стартуют без wake word.
git status -sb
# 2) Зафиксируй BASE:
git rev-parse HEAD   # → подставь вместо BASE_LAUNCH во FILE_OWNERSHIP и промптах
# 3) Worktrees root:
#    /Users/slon/mark-worktrees/
```

Шаблон worktree (для каждой задачи):

```bash
BASE_LAUNCH=<SHA>
TASK=launch-t01-docs-readme   # см. таблицу ниже
git worktree add -b agent/${TASK} \
  /Users/slon/mark-worktrees/${TASK} ${BASE_LAUNCH}
```

| Task | Branch / worktree short-name |
|---|---|
| LAUNCH-T01 | `launch-t01-docs-readme` |
| LAUNCH-T02 | `launch-t02-docs-runbook` |
| LAUNCH-T03 | `launch-t03-tooling-preflight` |
| LAUNCH-T04 | `launch-t04-ui-assets` |
| LAUNCH-T05 | `launch-t05-config-bootstrap` |
| LAUNCH-T06 | `launch-t06-wake-word-polish` |
| LAUNCH-T07 | `launch-t07-launch-verify` |

Расписание:

```text
T01 || T02 || T03     ← Group A (parallel)
integrator cherry-pick/merge each
T04 → T05 → T06       ← Group B (serial; ui.py / main.py)
integrator merge
T07                   ← verify only
```

---

## 1. Общий префикс саб-агента (вставлять в КАЖДЫЙ промпт)

```text
Ты работаешь как изолированный implementation sub-agent по AGENTS.md.

Репозиторий: worktree ниже. Ветка: ниже. Base commit: BASE_LAUNCH (см. FILE_OWNERSHIP / этот промпт).
Разрешено менять ТОЛЬКО Owned paths из своего task-файла.
Все остальные файлы — read-only.
Не делай merge / rebase / cherry-pick / pull чужих веток.
Не правь код вне задачи. Не форматируй весь проект.
Не коммить secrets, api_keys.json, memory/*.json, .venv, models/**.
Не push на remote (local by default; alexghost82 only if user explicitly asks).
Лицензия: personal / non-commercial CC BY-NC — не заявляй commercial-ready.
Python target: 3.11–3.12 (не расширяй до 3.14).

Перед завершением:
1) прогони только релевантные тесты задачи;
2) git diff — нет изменений вне Owned paths;
3) один логический commit;
4) верни: SHA, список файлов, тесты, limitations, integration notes.
Если нужен Forbidden path — СТОП + change request интегратору.
```

---

## 2. Group A — параллельный запуск (3 агента)

### Промпт LAUNCH-T01 (docs-readme)

```text
[Вставь общий префикс]

Worktree: /Users/slon/mark-worktrees/launch-t01-docs-readme
Branch: agent/launch-t01-docs-readme
Base: BASE_LAUNCH=<SHA>
Task file: orchestration/tasks/LAUNCH-T01.md
FILE_OWNERSHIP: LAUNCH-T01 docs-readme

Owned paths:
- readme.md

Сделай Objective/Acceptance из LAUNCH-T01.md: восстановить непустой readme.md для продукта Slon (Quick Start на Python 3.11–3.12, wake word Slon, CC BY-NC, без секретов и без commercial-ready).
```

### Промпт LAUNCH-T02 (docs-launch-runbook)

```text
[Вставь общий префикс]

Worktree: /Users/slon/mark-worktrees/launch-t02-docs-runbook
Branch: agent/launch-t02-docs-runbook
Base: BASE_LAUNCH=<SHA>
Task file: orchestration/tasks/LAUNCH-T02.md
FILE_OWNERSHIP: LAUNCH-T02 docs-launch-runbook

Owned paths:
- docs/audit/launch-runbook.md

Сделай Objective/Acceptance из LAUNCH-T02.md: операторский runbook первого запуска + macOS Privacy (Microphone, Accessibility, Screen Recording). Не редактируй readme.md.
```

### Промпт LAUNCH-T03 (tooling-preflight)

```text
[Вставь общий префикс]

Worktree: /Users/slon/mark-worktrees/launch-t03-tooling-preflight
Branch: agent/launch-t03-tooling-preflight
Base: BASE_LAUNCH=<SHA>
Task file: orchestration/tasks/LAUNCH-T03.md
FILE_OWNERSHIP: LAUNCH-T03 tooling-preflight

Owned paths:
- mark/app/preflight.py
- mark/app/__main__.py   # только если нужен entry `python -m mark.app`; не ломай setup_wizard
- tests/unit/app/test_preflight.py

Сделай Objective/Acceptance из LAUNCH-T03.md: offline-safe preflight (version/imports/key presence boolean/assets warnings). Никогда не печатай значения API keys. Не pip install из preflight.
```

**Интегратор после Group A:** cherry-pick по одному коммиту с каждой ветки → `integration/main` (или текущий интеграционный бранч). Зафиксируй `BASE_LAUNCH_B` = SHA после merge A — base для T04.

---

## 3. Group B — строго serial

### Промпт LAUNCH-T04 (ui-assets) — base = после merge A

```text
[Вставь общий префикс]

Worktree: /Users/slon/mark-worktrees/launch-t04-ui-assets
Branch: agent/launch-t04-ui-assets
Base: BASE_LAUNCH_B=<SHA after Group A>
Task file: orchestration/tasks/LAUNCH-T04.md
FILE_OWNERSHIP: LAUNCH-T04 ui-assets

Owned paths:
- ui.py   # только face load / HUD fallback / один SYS log

Сделай Acceptance из LAUNCH-T04.md. Не трогай main.py. Не коммить крупные бинарники face art без запроса пользователя.
```

Интегратор: merge T04 → `BASE_LAUNCH_B4`.

### Промпт LAUNCH-T05 (config-bootstrap) — base = после T04

```text
[Вставь общий префикс]

Worktree: /Users/slon/mark-worktrees/launch-t05-config-bootstrap
Branch: agent/launch-t05-config-bootstrap
Base: BASE_LAUNCH_B4=<SHA after T04>
Task file: orchestration/tasks/LAUNCH-T05.md
FILE_OWNERSHIP: LAUNCH-T05 config-bootstrap

Owned paths:
- config/settings.py
- tests/unit/config/test_settings_bootstrap.py
- (опционально) mark/app/setup_wizard.py — ТОЛЬКО если нужен call site и файл свободен; иначе оставь ensure_settings_file() callable без UI glue

Сделай Acceptance из LAUNCH-T05.md. Не трогай api_keys.json / ui.py / main.py. Не перезаписывай существующий settings.json.
```

Интегратор: merge T05 → `BASE_LAUNCH_B5`.

### Промпт LAUNCH-T06 (wake-word-polish) — base = после T05

```text
[Вставь общий префикс]

Worktree: /Users/slon/mark-worktrees/launch-t06-wake-word-polish
Branch: agent/launch-t06-wake-word-polish
Base: BASE_LAUNCH_B5=<SHA after T05>
Task file: orchestration/tasks/LAUNCH-T06.md
FILE_OWNERSHIP: LAUNCH-T06 wake-word-polish

Owned paths:
- ui.py
- main.py          # только если нужен unmute→re-assert standby callback
- tests/unit/speech/test_wake_word.py

Сделай Acceptance из LAUNCH-T06.md: unmute в standby не показывает ложный LISTENING; wake word Slon/Слон сохраняется. Не добавляй новые hotword-зависимости.
```

Интегратор: merge T06.

---

## 4. Group C — verify

### Промпт LAUNCH-T07 (launch-verify)

```text
[Вставь общий префикс]

Worktree: /Users/slon/mark-worktrees/launch-t07-launch-verify
Branch: agent/launch-t07-launch-verify
Base: BASE_LAUNCH_C=<SHA after T04–T06 integrate>
Task file: orchestration/tasks/LAUNCH-T07.md
FILE_OWNERSHIP: LAUNCH-T07 launch-verify

Owned paths:
- docs/audit/launch-smoke.md
- (optional one row) docs/audit/beta-gates.md

Запиши automated + manual smoke checklist. Feature-баги не чини по всему дереву — change request. Секреты в отчёт не включать.
```

---

## 5. Промпт интегратора (оркестрация всей волны)

```text
Ты главный интегратор LAUNCH-MVP для Slon.

Прочитай:
- AGENTS.md
- orchestration/tasks/LAUNCH-MVP.md
- orchestration/tasks/LAUNCH-AGENT-PROMPTS.md
- orchestration/FILE_OWNERSHIP.md (секция LAUNCH-MVP)

План:
1) Убедись, что WIP (Slon + wake word + task specs) закоммичен; выстави BASE_LAUNCH.
2) Создай 3 worktree и запусти параллельно LAUNCH-T01, T02, T03 с промптами из LAUNCH-AGENT-PROMPTS.md.
3) Прими по одному commit с каждой ветки (cherry-pick), проверь owned_paths / secret scan.
4) Serial: T04 → merge → T05 → merge → T06 → merge.
5) Запусти T07; обнови INTEGRATION_LOG.md кратким блоком LAUNCH-MVP.
6) Не push на third-party; local by default.

Стоп: конфликт owned_paths, секрет в diff, запрос Python 3.14 / public bind / commercial claim.
```

---

## 6. Шаблон отчёта саб-агента (ожидаемый ответ)

```text
TASK: LAUNCH-T0X
SHA: <commit>
FILES:
- ...
TESTS:
- pytest <paths> → N passed
LIMITATIONS:
- ...
INTEGRATION NOTES:
- ...
CHANGE REQUESTS:
- (none | ...)
```
