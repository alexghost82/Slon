# LAUNCH-T04 — face-asset-resilience

## Objective

Сделать запуск HUD устойчивым к отсутствию `face.png`: явный fallback (геометрия/placeholder), лог `SYS` один раз, без traceback.

## Context

- `ui.HudCanvas._load_face` уже глотает ошибки и ставит `_face_px = None`, но оператору неочевидно.
- `main.py` передаёт `SlonUI("face.png")`.
- Нельзя требовать бинарный PNG в git, если политика репо — не тащить тяжёлые assets (решение: graceful UI **или** крошечный встроенный placeholder).

## Owned paths

- `ui.py` (только face load / HUD fallback / optional one-line SYS log path via existing signals)
- `tests/unit/ui/` — узкий тест на load-without-file **если** уже есть паттерн тестирования UI без полного GUI; иначе docstring + manual note in integration notes (**не** поднимать полный QApplication flaky suite без нужды)

## Forbidden paths

- `main.py` (кроме change request: смена дефолтного path)
- `readme.md`, requirements, iOS
- Коммит больших бинарников без спроса пользователя

## Acceptance

- Запуск без `face.png` не падает на `_load_face`.
- В UI остаётся читаемый бренд Slon (текст уже есть).
- Optional: если файла нет — один `SYS: face.png missing; using geometric HUD` через существующий log signal **без** спама каждый frame.
- One commit.

## Stop conditions

- Нужно менять `main.py` entry — CR к интегратору.
- Пользователь просит добавить proprietary face art — стоп, спросить.
