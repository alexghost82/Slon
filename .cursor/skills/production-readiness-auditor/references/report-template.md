# Production readiness report template

Сохранить как `.cursor/audits/<timestamp>/production-readiness-report.md`.
Заполнять только проверенными данными. Пустые секции — с явным `NOT RUN` / `NOT APPLICABLE` / `BLOCKED`, не удалять.

---

```markdown
# Production Readiness Report

- Product / repo:
- Audit ID / timestamp:
- Mode:
- Revision (commit SHA):
- Dirty worktree: yes/no (summary, no secrets)
- Auditor:
- Platforms in scope:
- Verdict: GO | CONDITIONAL GO | NO-GO

## 1. Executive summary

[2–6 предложений: scope, ключевые находки, вердикт, главные условия]

## 2. Scope и exclusions

### In scope
- …

### Explicit exclusions
- … (с причиной)

### Assumed / INFERRED requirements
- …

## 3. Environment и revision

| Item | Value |
|------|-------|
| Commit | |
| Branch | |
| Host OS | |
| SDKs / toolchains | |
| Devices / emulators / simulators | |
| Backend / endpoints (redacted) | |
| Accounts / roles used | (имена ролей, не пароли) |
| Build types tested | debug / release / … |

Ссылка на `audit-manifest.md`.

## 4. Results by area

| Area | Status | Evidence | Notes |
|------|--------|----------|-------|
| Discovery / inventory | | | |
| Static analysis / build | | | |
| Unit / integration tests | | | |
| Installation / upgrade | | | |
| UI / E2E | | | |
| Functional / data integrity | | | |
| Performance | | | |
| Load | | | |
| Security / privacy | | | |
| Operability / release ops | | | |

Status ∈ PASS, FAIL, BLOCKED, NOT RUN, NOT APPLICABLE, STALE.

## 5. Feature coverage и critical journeys

### Coverage summary
- Features inventoried:
- Features tested:
- Features NOT RUN / BLOCKED:

### P0 critical journeys

| Journey | Platforms | Status | Evidence |
|---------|-----------|--------|----------|
| Launch | | | |
| Onboarding / login | | | |
| Core product outcome | | | |
| Save / sync | | | |
| Error recovery | | | |
| Logout / exit / data retention | | | |

Полная матрица: `test-matrix.md`.

## 6. Defects

Сортировка: severity ↓, затем confidence ↓.

| ID | Title | Severity | Priority | Confidence | Repro | Status |
|----|-------|----------|----------|------------|-------|--------|
| DEF-001 | | | | | | open/fixed/waived |

Детали: `defects/DEF-XXX.md` по формату skill.

## 7. Security / privacy findings

| ID | Finding | Severity | Confidence | Evidence | Notes |
|----|---------|----------|------------|----------|-------|
| | | | | | |

Явно: формальная сертификация OWASP **не** заявляется.

## 8. Performance baseline и regressions

| Metric | Value | Unit | Env | Build | n | Method | Threshold | Result |
|--------|-------|------|-----|-------|---|--------|-----------|--------|
| Cold startup | | | | | | | project / PROPOSED | |

Если выборка мала — указать insufficient samples. Регрессии vs previous audit/baseline — со ссылками.

## 9. Blocked / not-run

| Check | Status | What is required to run |
|--------|--------|-------------------------|
| | BLOCKED / NOT RUN | SDK / device / account / permission / stand |

## 10. Residual risks

| Risk | Likelihood | Impact | Mitigation / owner / due |
|------|------------|--------|---------------------------|
| | | | |

## 11. Verdict

**Verdict:** GO | CONDITIONAL GO | NO-GO

Обоснование относительно gates (ссылка на severity-and-release-gates.md).  
Список открытых Blocker/Critical (должен быть пуст для GO).

## 12. Production exit conditions

Чеклист условий, без которых нельзя/можно выходить:

- [ ] …
- [ ] …

Для CONDITIONAL GO — каждый condition с owner и due date.

## 13. Fix plan и retest

| Priority | Defect / gap | Action | Retest procedure | Owner |
|----------|--------------|--------|------------------|-------|
| P0 | | | | |

## Appendix

- Paths: manifest, matrix, evidence/, logs/
- Commands index (high level)
- Tool versions
```

---

## Defect file template

`defects/DEF-XXX.md`:

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

## Audit manifest skeleton

`audit-manifest.md`:

```markdown
# Audit manifest

- Timestamp:
- Mode:
- Root:
- Commit:
- Dirty:
- Detect script output path / summary:
- Platforms detected:
- Platforms in scope:
- Constraints / blockers known at start:
- Endpoints (redacted):
- Secrets policy: values never logged
- Phase progress: A…J with timestamps
```
