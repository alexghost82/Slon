# Severity и release gates

## Severity (влияние)

| Level | Определение |
|-------|-------------|
| `BLOCKER` | Невозможен запуск/установка/ключевой сценарий; потеря или повреждение данных; подтверждённый critical security issue; crash loop; массовая недоступность |
| `CRITICAL` | Критический сценарий ненадёжен; серьёзный auth/privacy/security дефект; отсутствует безопасное восстановление |
| `MAJOR` | Важная функция сломана или существенная деградация UX/performance без приемлемого workaround |
| `MINOR` | Локальный дефект с малым влиянием |
| `TRIVIAL` | Косметика без функционального влияния |

## Ортогональные оси

Разделяй всегда:

| Ось | Смысл | Примеры |
|-----|-------|---------|
| `severity` | Влияние на пользователя/данные/безопасность | BLOCKER…TRIVIAL |
| `priority` | Срочность исправления относительно релиза | P0–P3 или Immediate/Before release/Next sprint |
| `confidence` | Надёжность вывода | Confirmed / High / Medium / Low |
| `reproducibility` | Частота | `3/3`, `1/5`, `Intermittent` |

Не повышать severity из-за срочности релиза и не занижать severity из-за «потом починим».

## Confidence

| Confidence | Когда ставить |
|------------|---------------|
| `Confirmed` | Воспроизведено с evidence; root cause область подтверждена наблюдениями |
| `High` | Стабильно воспроизводится; причина вероятна, но не полностью доказана |
| `Medium` | Есть сигнал (лог/crash/один прогон), нужна доп. проверка |
| `Low` | Гипотеза или единичное наблюдение без надёжного evidence |

Для release gate учитывать как **открытые подтверждённые** (`Confirmed`/`High`) дефекты. `Low`/`Medium` без подтверждения — в residual risk и план верификации, не как скрытый PASS.

## Статусы проверок

| Status | Значение |
|--------|----------|
| `PASS` | Проверка выполнена; критерии выполнены; есть evidence |
| `FAIL` | Проверка выполнена; критерии не выполнены; есть evidence |
| `BLOCKED` | Не удалось выполнить из-за среды/доступа/секретов/устройств |
| `NOT RUN` | В scope, но ещё не выполнялась или сознательно отложена |
| `NOT APPLICABLE` | Не относится к обнаруженному стеку/продукту |
| `STALE` | Ранее PASS/FAIL, но revision/build/среда изменились |

`NOT RUN` ≠ `PASS`. `BLOCKED` ≠ `PASS`. `NOT APPLICABLE` требует краткого обоснования.

## Default release gates

### NO-GO

- Есть хотя бы один открытый подтверждённый `BLOCKER` или `CRITICAL`.
- Не пройдены critical journeys (P0).
- Не пройдены release build, clean install/launch или data integrity проверки, если они в обязательном scope.
- Обязательные security checks в scope дали `FAIL` уровня Blocker/Critical.
- Нет evidence для обязательных gates (нельзя закрыть «на словах»).

### CONDITIONAL GO

- Нет открытых подтверждённых Blocker/Critical.
- Остаются Major и/или `BLOCKED` обязательные проверки **с**:
  - документированным владельцем;
  - сроком;
  - workaround (если есть);
  - явно принятым риском ответственным человеком (не агентом).
- Performance/load gaps зафиксированы как residual risk с `PROPOSED` или project SLO.

### GO

Только когда:

1. Обязательные gates пройдены со статусом `PASS` и evidence.
2. Critical journeys зелёные на целевых платформах scope.
3. Нет открытых подтверждённых Blocker/Critical.
4. Остаточный риск явно перечислен и **принят ответственным человеком**.
5. Нет обязательных `BLOCKED`/`NOT RUN` без явного исключения из scope владельцем релиза.

## Обязательные gates по умолчанию (если applicable)

1. Release configuration собирается.
2. Clean install + first launch.
3. P0 critical journeys.
4. Нет silent data loss на restart/kill/upgrade path в scope.
5. Нет confirmed critical/blocker security findings в scope.
6. Secrets не утекают в repo/build logs (проверка выполнена).
7. Минимальный observability: crash/error path не «молчаливый» (если заявлено в продукте).

Платформенные дополнения — см. [platform-matrix.md](platform-matrix.md). Проект может ужесточить gates через CI/docs; ослабление — только явным решением владельца.

## Режим → минимальный gate set

| Режим | Минимум для вердикта |
|-------|----------------------|
| `quick smoke` | Build + launch + 1–N P0 path; вердикт «smoke only», не полный GO |
| `full audit` | Все applicable фазы; полный GO/NO-GO |
| `release gate` | Обязательные gates + открытые дефекты + residual risk |
| `regression` | Изменённые области + связанные P0; STALE вне scope пометить |
| `ui audit` | UI/a11y matrix; не выдавать полный production GO без остальных gates |
| `performance audit` | Baseline + измерения; пороги project или `PROPOSED` |
| `security audit` | Security catalog applicable; без формальной «сертификации» |
| `load audit` | Только разрешённый стенд; recovery включён |
| `installation audit` | Clean/upgrade/uninstall(+data policy) |
| `fix and verify` | Каждый fix → verification test → обновление статуса дефекта |
| `resume audit` | Продолжить с manifest; не затирать evidence |

## Mapping дефектов в вердикт

```text
open confirmed BLOCKER/CRITICAL     → NO-GO
P0 journey FAIL                     → NO-GO
release build / clean install FAIL  → NO-GO
only MAJOR + accepted risk          → CONDITIONAL GO (если documented)
only MINOR/TRIVIAL                  → может быть GO при пройденных gates
обязательные BLOCKED без waiver     → не GO (обычно NO-GO или CONDITIONAL с owner)
```

## Запреты при вынесении вердикта

- Не принимать бизнес-риск от имени владельца продукта.
- Не писать GO при обязательных `NOT RUN`/`BLOCKED` без waiver.
- Не агрегировать «в целом выглядит хорошо» вместо таблицы статусов.
- Не скрывать environment defects как product PASS.
