# LAUNCH-T06 — wake-word-launch-polish

## Objective

Согласовать UX wake word с unmute/startup для первого запуска: после unmute не показывать ложный `LISTENING`, если агент в standby; сохранить matcher `Slon`/`Слон`.

## Context

- Уже реализовано: `speech/wake_word.py`, gating в `SlonLive` (`STANDBY` / awake / idle 45s).
- Известный gap: `ui.py` `_set_muted(False)` форсит `LISTENING`, даже если Live в standby.
- Text input уже bypass wake word — сохранить.

## Owned paths

- `ui.py` (unmute/state sync only)
- `main.py` (только если нужен callback `ui.on_mute_changed` / re-assert standby — **integrator must not schedule T04/T05 parallel on same files**)
- `tests/unit/speech/test_wake_word.py` (расширить кейсы при необходимости)
- Optional: `tests/unit/main/` узкий тест на contains/gate helpers if extracted

## Forbidden paths

- Замена wake word на отдельный Whisper hotword engine (out of scope)
- Network STT для wake
- Breaking tool pipeline when awake

## Acceptance

- Unmute while asleep → HUD `STANDBY` / `SAY SLON`, не «ложный LISTENING».
- Wake word behavior regress-tests still pass.
- Document in integration notes: mic must be unmuted + say Slon.
- One commit.

## Stop conditions

- Требуется локальный porcupine/openwakeword dependency → CR / user decision.
- Conflict with uncommitted wake-word WIP in `main.py` → stop, don't overwrite blindly.
