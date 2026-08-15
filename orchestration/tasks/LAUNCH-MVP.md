# LAUNCH-MVP — ТЗ для код-агентов: первый полноценный запуск Slon

**Тип:** integration / launch-hardening wave  
**Продукт:** Slon (personal / non-commercial, CC BY-NC 4.0)  
**Цель волны:** довести репозиторий до состояния, в котором оператор на macOS может выполнить **первый полноценный desktop-запуск** без догадок: окружение → HUD → wake word → голос → хотя бы один tool.  
**Не цель:** Epic 14 (APNs / VPN / публичный интернет), App Store, commercial-ready.

Интегратор: только главный агент. Саб-агенты работают в своих worktree/ветках и **только** в `owned_paths`.

---

## 1. Контекст (verified 2026-08-15)

| Факт | Статус |
|---|---|
| Waves 0–12 accepted; Wave 13 glue in progress | ok |
| Unit tests ~652 passed | ok |
| Бренд/личность: Slon + JARVIS-like тон; wake word `Slon`/`Слон` | в дереве (часть незакоммичена) |
| `readme.md` | **пустой (0 байт) — блокер документации** |
| `face.png` | отсутствует (HUD деградирует без краша) |
| `config/settings.json` | отсутствует (есть только `settings.example.json`) |
| Runtime deps в текущем system Python 3.14 | **не установлены**; проект требует **3.11–3.12** |
| `.venv` | отсутствует |
| `config/api_keys.json` | локально есть gemini + openrouter (не коммитить) |
| Piper `models/piper/` | бинарь + `ru_RU-dmitri-medium` на месте (gitignored) |
| Dual stack | legacy `main.py`/`ui.py`/`actions/` + new `mark/`/`providers/`/`server/` |

---

## 2. Definition of Done — «первый полноценный запуск»

Оператор после выполнения волны может:

1. Создать venv на **Python 3.11 или 3.12**.
2. Установить deps одной документированной командой (+ Playwright browsers).
3. Запустить `python main.py` и увидеть HUD.
4. Увидеть в логе online + **Standby — say «Slon»**.
5. Сказать wake word **Slon** / **Слон** → получить голосовой ответ.
6. Выполнить ≥1 tool (например `open_app` или `web_search` или `screen_process`).
7. Mute/unmute (F4) не роняет сессию.

**Вне DoD этой волны:** iOS remote e2e, Bonjour, TLS LAN productization, полный mypy green, offline-only Live.

---

## 3. Жёсткие правила для всех агентов

1. Не коммитить `config/api_keys.json`, `memory/*.json`, `.venv/`, `models/**`, секреты.
2. Не `git reset --hard`, не трогать чужие незакоммиченные изменения вне owned paths.
3. Не пушить на third-party remotes; push только по запросу пользователя на `alexghost82`.
4. Не заявлять commercial-ready.
5. Не ломать Gemini Live path в `main.py` без явного owned ownership.
6. Python target: **3.11–3.12**; не «чинить» под 3.14 расширением upper bound без отдельного решения пользователя.
7. Один логический commit на задачу; вернуть SHA, файлы, тесты, limitations, integration notes.
8. Shared files (`main.py`, `ui.py`, `pyproject.toml`, `requirements*.txt`, …) — **не раздавать двум агентам параллельно**.

---

## 4. Карта задач (параллельные группы)

### Group A — docs & operator path (параллельно, disjoint)

| ID | Agent | Суть |
|---|---|---|
| LAUNCH-T01 | docs-readme | Восстановить `readme.md` под Slon + Quick Start 3.12 |
| LAUNCH-T02 | docs-launch-runbook | Runbook первого запуска + macOS Privacy checklist |
| LAUNCH-T03 | tooling-preflight | Скрипт/модуль preflight: python version, imports, keys presence (без печати секретов), face/settings |

### Group B — app launch resilience (serial после A или с интегратором; shared files)

| ID | Agent | Суть |
|---|---|---|
| LAUNCH-T04 | ui-assets | Graceful `face.png` + опциональный placeholder; не падать |
| LAUNCH-T05 | config-bootstrap | Bootstrap `settings.json` из example при первом старте (без секретов) |
| LAUNCH-T06 | wake-word-polish | UX standby/unmute sync с wake state; тесты matcher уже есть |

### Group C — verify (после интеграции B)

| ID | Agent | Суть |
|---|---|---|
| LAUNCH-T07 | launch-verify | Offline pytest + документированный manual smoke checklist результат в `docs/audit/launch-smoke.md` |

Детальные ТЗ: `orchestration/tasks/LAUNCH-T0N.md`.  
Промпты запуска агентов + worktree: `orchestration/tasks/LAUNCH-AGENT-PROMPTS.md`.  
Ownership table: `orchestration/FILE_OWNERSHIP.md` → **LAUNCH-MVP**.

---

## 5. Порядок интеграции

```text
LAUNCH-T01 || LAUNCH-T02 || LAUNCH-T03
        \________|________/
                 v
     integrator merges docs/tooling
                 v
     LAUNCH-T04 → LAUNCH-T05 → LAUNCH-T06
                 v
            LAUNCH-T07
```

`ui.py` / `main.py` / `config/*` не отдавать параллельно разным агентам.

---

## 6. Критерии приёмки волны (integrator)

- [ ] `readme.md` непустой, Quick Start для Slon, Python 3.11–3.12, macOS/Windows/Linux указаны.
- [ ] Runbook: Privacy (Microphone, Accessibility, Screen Recording), wake word, Playwright.
- [ ] Preflight команда: `python -m mark.app.preflight` (или согласованный путь из T03) exit 0/1 с человекочитаемым отчётом **без** значений API keys.
- [ ] Отсутствие `face.png` не крашит UI.
- [ ] Первый старт создаёт `config/settings.json` из example, если файла нет.
- [ ] Standby/wake word документированы и согласованы с HUD.
- [ ] `pytest tests/unit -q` не деградировал относительно текущего baseline.
- [ ] Нет секретов в diff; `models/` не в git.

---

## 7. Stop / change-request triggers

- Нужен Python 3.14 support → стоп, спросить пользователя.
- Нужно ротировать/печатать API keys → стоп.
- Нужен публичный bind Desktop API → стоп (Epic 14).
- Конфликт с незакоммиченными правками пользователя в том же файле → стоп, не перезаписывать.

---

## 8. Ручной smoke (для LAUNCH-T07 / оператора)

```bash
cd /Users/slon/Documents/GitHub/Slon
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-macos.txt && playwright install
python -m mark.app.preflight    # после T03
python main.py
# HUD → SAY SLON → голосом «Slon» → команда tool → F4 mute/unmute
```

Успех = 5 пунктов Definition of Done §2.
