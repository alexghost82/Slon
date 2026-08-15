"""Offline-safe launch preflight checks before ``python main.py``.

Run::

    python -m mark.app.preflight

Exit codes:
    0 — no blockers; ready enough to attempt ``python main.py``
    1 — blockers present (unsupported Python, missing critical imports,
        or Gemini API key not resolvable)

Severity:
    blocker — must be fixed before launch
    warning — optional assets / deps; launch may still work with degradation

Never prints or logs API key values. Never runs ``pip install``, never
downloads models, and never writes secrets or ``api_keys.json``.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TextIO

Severity = Literal["blocker", "warning"]
SecretPresenceFn = Callable[[str], bool]
ImportCheckFn = Callable[[str], bool]

SUPPORTED_PYTHON_MIN: tuple[int, int] = (3, 11)
SUPPORTED_PYTHON_MAX: tuple[int, int] = (3, 12)

CRITICAL_IMPORTS: tuple[str, ...] = (
    "PyQt6",
    "sounddevice",
    "google.genai",
    "psutil",
)

WARNING_IMPORTS: tuple[str, ...] = ("playwright",)

GEMINI_SECRET_NAME = "gemini_api_key"
OPENROUTER_SECRET_NAME = "openrouter_api_key"
DEFAULT_PIPER_VOICE = "ru_RU-dmitri-medium"


@dataclass(frozen=True)
class CheckResult:
    """One preflight check outcome (messages must never contain secrets)."""

    name: str
    ok: bool
    severity: Severity
    message: str


@dataclass(frozen=True)
class PreflightReport:
    """Aggregated preflight results."""

    checks: tuple[CheckResult, ...]

    @property
    def blockers(self) -> tuple[CheckResult, ...]:
        return tuple(c for c in self.checks if c.severity == "blocker" and not c.ok)

    @property
    def warnings(self) -> tuple[CheckResult, ...]:
        return tuple(c for c in self.checks if c.severity == "warning" and not c.ok)

    @property
    def ok(self) -> bool:
        return not self.blockers

    @property
    def exit_code(self) -> int:
        return 0 if self.ok else 1


def default_repo_root() -> Path:
    """Repository root containing ``main.py`` / ``config/``."""
    return Path(__file__).resolve().parents[2]


def _try_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
    except Exception:
        return False
    return True


def _file_has_nonempty_secret_field(path: Path, name: str) -> bool:
    """Return True when ``path`` JSON has a non-empty string for ``name``.

    The field value is discarded immediately and never returned or logged.
    """
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if not isinstance(payload, Mapping):
        return False
    raw = payload.get(name)
    return isinstance(raw, str) and bool(raw.strip())


def _default_secret_present(name: str, *, api_keys_path: Path) -> bool:
    """True when secrets API or fallback file has a non-empty named secret."""
    value: str | None = None
    try:
        from config.secrets import get_secret

        value = get_secret(name)
    except Exception:
        # A missing or broken OS secret store must degrade to file presence
        # rather than abort preflight.
        value = None
    if isinstance(value, str) and value.strip():
        return True
    return _file_has_nonempty_secret_field(api_keys_path, name)


def _check_python_version(version: tuple[int, int]) -> CheckResult:
    major, minor = version
    supported = SUPPORTED_PYTHON_MIN <= version <= SUPPORTED_PYTHON_MAX
    if supported:
        message = f"Python {major}.{minor} is supported (need 3.11–3.12)"
    else:
        message = (
            f"Python {major}.{minor} is unsupported; "
            "Slon requires Python 3.11–3.12"
        )
    return CheckResult(
        name="python_version",
        ok=supported,
        severity="blocker",
        message=message,
    )


def _check_imports(
    modules: Sequence[str],
    *,
    severity: Severity,
    import_check: ImportCheckFn,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    for module_name in modules:
        present = bool(import_check(module_name))
        if present:
            message = f"import {module_name}: present"
        else:
            message = (
                f"import {module_name}: missing "
                "(install from requirements-base.txt; preflight does not pip install)"
            )
        results.append(
            CheckResult(
                name=f"import:{module_name}",
                ok=present,
                severity=severity,
                message=message,
            )
        )
    return results


def _check_secret_presence(
    name: str,
    *,
    severity: Severity,
    secret_present: SecretPresenceFn,
    label: str,
) -> CheckResult:
    present = bool(secret_present(name))
    if present:
        message = f"{label}: present"
    else:
        message = f"{label}: missing"
    return CheckResult(
        name=f"secret:{name}",
        ok=present,
        severity=severity,
        message=message,
    )


def _check_path_exists(
    name: str,
    path: Path,
    *,
    severity: Severity,
    missing_message: str,
) -> CheckResult:
    exists = path.is_file()
    if exists:
        message = f"{name}: present ({path})"
    else:
        message = f"{name}: missing — {missing_message}"
    return CheckResult(
        name=name,
        ok=exists,
        severity=severity,
        message=message,
    )


def _check_piper_assets(piper_dir: Path) -> CheckResult:
    binary = piper_dir / "piper"
    model = piper_dir / f"{DEFAULT_PIPER_VOICE}.onnx"
    sidecar = Path(str(model) + ".json")
    binary_ok = binary.is_file()
    voice_ok = model.is_file() and sidecar.is_file()
    ok = binary_ok and voice_ok
    parts: list[str] = []
    parts.append("binary present" if binary_ok else "binary missing")
    parts.append("voice present" if voice_ok else "voice/onnx(+json) missing")
    detail = ", ".join(parts)
    if ok:
        message = f"piper assets: present under {piper_dir} ({detail})"
    else:
        message = (
            f"piper assets: incomplete under {piper_dir} ({detail}); "
            "optional local TTS will degrade"
        )
    return CheckResult(
        name="piper_assets",
        ok=ok,
        severity="warning",
        message=message,
    )


def run_preflight(
    *,
    repo_root: Path | None = None,
    version: tuple[int, int] | None = None,
    import_check: ImportCheckFn | None = None,
    secret_present: SecretPresenceFn | None = None,
) -> PreflightReport:
    """Run offline preflight checks and return a structured report.

    Callers may inject fakes for unit tests. Production defaults use the
    live interpreter, ``importlib``, and ``config.secrets`` / file presence.
    """
    root = (repo_root or default_repo_root()).resolve()
    running_version = version or (sys.version_info.major, sys.version_info.minor)
    check_import = import_check or _try_import
    api_keys_path = root / "config" / "api_keys.json"

    if secret_present is None:

        def _secret_present(name: str) -> bool:
            return _default_secret_present(name, api_keys_path=api_keys_path)

        present_fn: SecretPresenceFn = _secret_present
    else:
        present_fn = secret_present

    checks: list[CheckResult] = []
    checks.append(_check_python_version(running_version))
    checks.extend(
        _check_imports(
            CRITICAL_IMPORTS,
            severity="blocker",
            import_check=check_import,
        )
    )
    checks.append(
        _check_secret_presence(
            GEMINI_SECRET_NAME,
            severity="blocker",
            secret_present=present_fn,
            label="Gemini API key",
        )
    )
    checks.append(
        _check_secret_presence(
            OPENROUTER_SECRET_NAME,
            severity="warning",
            secret_present=present_fn,
            label="OpenRouter API key",
        )
    )
    checks.append(
        _check_path_exists(
            "face.png",
            root / "face.png",
            severity="warning",
            missing_message="HUD may use a geometric fallback",
        )
    )
    checks.append(
        _check_path_exists(
            "settings.json",
            root / "config" / "settings.json",
            severity="warning",
            missing_message="defaults will be used until first save",
        )
    )
    checks.append(_check_piper_assets(root / "models" / "piper"))
    checks.extend(
        _check_imports(
            WARNING_IMPORTS,
            severity="warning",
            import_check=check_import,
        )
    )
    return PreflightReport(checks=tuple(checks))


def format_report(report: PreflightReport) -> str:
    """Human-readable report text (never includes secret values)."""
    lines: list[str] = ["Slon launch preflight", ""]
    for check in report.checks:
        if check.severity == "blocker":
            tag = "OK " if check.ok else "FAIL"
        else:
            tag = "OK " if check.ok else "WARN"
        lines.append(f"[{tag}] {check.message}")
    lines.append("")
    if report.ok:
        warn_n = len(report.warnings)
        if warn_n:
            lines.append(
                f"Result: ready enough for main.py ({warn_n} warning(s); exit 0)"
            )
        else:
            lines.append("Result: ready for main.py (exit 0)")
    else:
        lines.append(
            f"Result: blocked ({len(report.blockers)} blocker(s); exit 1)"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="python -m mark.app.preflight",
        description=(
            "Offline launch preflight for Slon. Exit 0 = no blockers, "
            "exit 1 = blockers. Never prints API key values."
        ),
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    stream: TextIO | None = None,
) -> int:
    """CLI entry for ``python -m mark.app.preflight``."""
    build_parser().parse_args(list(argv) if argv is not None else None)
    out = stream if stream is not None else sys.stdout
    report = run_preflight()
    out.write(format_report(report))
    return report.exit_code


__all__ = [
    "CRITICAL_IMPORTS",
    "WARNING_IMPORTS",
    "CheckResult",
    "PreflightReport",
    "build_parser",
    "default_repo_root",
    "format_report",
    "main",
    "run_preflight",
]


if __name__ == "__main__":
    raise SystemExit(main())
