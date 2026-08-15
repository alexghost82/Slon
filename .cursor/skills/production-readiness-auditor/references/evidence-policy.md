# Evidence policy

## Правило

Статус `PASS` / `FAIL` допустим только при наличии evidence. Без evidence — `NOT RUN`, `BLOCKED` или описание наблюдения без статусного вердикта.

## Допустимые типы evidence

| Тип | Примеры | Когда достаточно |
|-----|---------|------------------|
| Command result | Точная команда, cwd, exit code, stdout/stderr excerpt, timestamp | Build, tests, scanners, CLI checks |
| Test report | JUnit/XCTest/Gradle HTML/XML, CI job URL + run id | Automated suites |
| Log | App/system/test log path + релевантный excerpt (без секретов) | Crashes, errors, recovery |
| Screenshot | PNG/JPEG path + что показано | UI states, clipping, dialogs |
| Video / recording | Path + duration | Flaky UI, gestures, flows |
| Trace / profile | Instruments/xctrace, Android profiler, DevTools, perf traces | Performance |
| Accessibility report | Tree dump, VoiceOver/TalkBack notes, axe-like output | a11y |
| Manual observation | Observer, environment, steps, timestamp, result | Когда automation недоступна |
| Artifact metadata | File path, size, sha256 checksum | Packages, binaries, large media |
| Network capture | HAR/pcap **только** на test стенде; redacted | API/transport issues |

## Обязательные поля для каждой проверки

```markdown
- Check ID:
- Status: PASS | FAIL | BLOCKED | NOT RUN | NOT APPLICABLE | STALE
- Command or procedure:
- Environment: OS, device/VM, SDK, build type, locale
- Started / finished:
- Exit code / result:
- Evidence paths:
- Notes / limitations:
```

## Хранение

Корень аудита: `.cursor/audits/<timestamp>/`

```text
evidence/          # screenshots, traces, reports, copies of key logs
logs/              # raw command logs
defects/DEF-XXX.md # один дефект — один файл (или секции в report)
```

### Размер и Git

- Не коммитить audit artifacts автоматически.
- Бинарные файлы > ~5–10 MB: хранить локально, в отчёте — **path + sha256 + size**, не inline.
- Не копировать в evidence секреты, production dumps с PII, keystores, provisioning profiles.
- Redact: tokens, passwords, Authorization headers, cookies, API keys, personal data.

### Checksum

```bash
shasum -a 256 path/to/artifact
# или: python3 -c "import hashlib,pathlib; p=pathlib.Path('...'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

## Что НЕ является evidence

- «По коду должно работать»
- «У разработчика раньше проходило»
- Зелёный значок без лога/команды в этом аудите
- Скриншот чужого окружения без привязки к revision
- Уверенный текст модели без артефакта

## Ручные проверки

Минимальный шаблон наблюдения:

```markdown
### Manual observation
- Observer:
- Date/time (local + TZ):
- Build/version/commit:
- Device/OS:
- Preconditions:
- Steps:
- Expected:
- Actual:
- Attachments:
```

## Performance evidence

Каждое число сопровождается:

- device/VM и OS version;
- build type (debug/release);
- dataset size/shape;
- duration и concurrency;
- число повторов;
- метод измерения и инструмент + version;
- единицы;
- median и p95/p99 **только** если выборка позволяет; иначе «insufficient samples».

## Security evidence

- Не вставлять сырые секреты в report.
- Для secret findings: путь файла, тип находки, masked preview (`sk-***`), не полное значение.
- Для vulns: package, version, advisory id, severity source, fix version если известна.
- Помечать, была ли проверка active exploit attempt (обычно нет; только authorized test env).

## Связь с дефектами

Каждый `FAIL`, становящийся дефектом, обязан ссылаться на evidence paths. Дефект без evidence → понизить confidence или оставить как hypothesis в residual risk, не как confirmed FAIL для gate.
