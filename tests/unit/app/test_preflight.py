"""Offline preflight tests. No display, no network, no live secrets."""

from __future__ import annotations

import io
import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from mark.app import preflight
from mark.app.preflight import (
    CRITICAL_IMPORTS,
    WARNING_IMPORTS,
    PreflightReport,
    build_parser,
    format_report,
    main,
    run_preflight,
)

PREFLIGHT_SOURCE = (
    Path(__file__).resolve().parents[3] / "mark" / "app" / "preflight.py"
)
SENTINEL_KEY = "dummy-not-a-live-key-XYZ-4242"
SUPPORTED_VERSION: tuple[int, int] = (3, 12)
UNSUPPORTED_VERSION: tuple[int, int] = (3, 14)


def _all_imports_present(_module: str) -> bool:
    return True


def _no_imports_present(_module: str) -> bool:
    return False


def _imports_missing(missing: Iterable[str]):
    absent = frozenset(missing)

    def check(module: str) -> bool:
        return module not in absent

    return check


def _keys_present(_name: str) -> bool:
    return True


def _no_keys(_name: str) -> bool:
    return False


def _ready_repo(root: Path) -> Path:
    """Create the optional assets a fully provisioned checkout would have."""
    (root / "face.png").write_bytes(b"png")
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "settings.json").write_text("{}", encoding="utf-8")
    piper_dir = root / "models" / "piper"
    piper_dir.mkdir(parents=True, exist_ok=True)
    (piper_dir / "piper").write_text("#!/bin/sh\n", encoding="utf-8")
    model = piper_dir / f"{preflight.DEFAULT_PIPER_VOICE}.onnx"
    model.write_bytes(b"onnx")
    Path(str(model) + ".json").write_text("{}", encoding="utf-8")
    return root


def _report(
    root: Path,
    *,
    version: tuple[int, int] = SUPPORTED_VERSION,
    import_check=_all_imports_present,
    secret_present=_keys_present,
) -> PreflightReport:
    return run_preflight(
        repo_root=root,
        version=version,
        import_check=import_check,
        secret_present=secret_present,
    )


def _names(checks: Iterable[preflight.CheckResult]) -> set[str]:
    return {check.name for check in checks}


def test_ready_checkout_has_no_blockers_and_exit_zero(tmp_path: Path) -> None:
    report = _report(_ready_repo(tmp_path))
    assert report.blockers == ()
    assert report.warnings == ()
    assert report.ok is True
    assert report.exit_code == 0


@pytest.mark.parametrize("version", [(3, 9), (3, 10), (3, 13), (3, 14), (4, 0)])
def test_unsupported_python_is_blocker(
    tmp_path: Path, version: tuple[int, int]
) -> None:
    report = _report(_ready_repo(tmp_path), version=version)
    assert report.exit_code == 1
    assert "python_version" in _names(report.blockers)


@pytest.mark.parametrize("version", [(3, 11), (3, 12)])
def test_supported_python_versions_pass(
    tmp_path: Path, version: tuple[int, int]
) -> None:
    report = _report(_ready_repo(tmp_path), version=version)
    assert "python_version" not in _names(report.blockers)


@pytest.mark.parametrize("module", CRITICAL_IMPORTS)
def test_missing_critical_import_blocks(tmp_path: Path, module: str) -> None:
    report = _report(_ready_repo(tmp_path), import_check=_imports_missing([module]))
    assert report.exit_code == 1
    assert f"import:{module}" in _names(report.blockers)


@pytest.mark.parametrize("module", WARNING_IMPORTS)
def test_missing_optional_import_only_warns(tmp_path: Path, module: str) -> None:
    report = _report(_ready_repo(tmp_path), import_check=_imports_missing([module]))
    assert report.exit_code == 0
    assert f"import:{module}" in _names(report.warnings)


def test_missing_gemini_key_blocks_and_openrouter_only_warns(tmp_path: Path) -> None:
    root = _ready_repo(tmp_path)
    report = _report(root, secret_present=_no_keys)
    assert report.exit_code == 1
    assert f"secret:{preflight.GEMINI_SECRET_NAME}" in _names(report.blockers)
    assert f"secret:{preflight.OPENROUTER_SECRET_NAME}" in _names(report.warnings)

    only_gemini = _report(
        root, secret_present=lambda name: name == preflight.GEMINI_SECRET_NAME
    )
    assert only_gemini.exit_code == 0
    assert f"secret:{preflight.OPENROUTER_SECRET_NAME}" in _names(only_gemini.warnings)


def test_missing_optional_assets_are_warnings_not_blockers(tmp_path: Path) -> None:
    report = _report(tmp_path)
    warned = _names(report.warnings)
    assert report.exit_code == 0
    assert {"face.png", "settings.json", "piper_assets"} <= warned
    assert report.blockers == ()


def test_partial_piper_install_warns(tmp_path: Path) -> None:
    root = _ready_repo(tmp_path)
    (root / "models" / "piper" / f"{preflight.DEFAULT_PIPER_VOICE}.onnx").unlink()
    report = _report(root)
    assert "piper_assets" in _names(report.warnings)
    assert report.exit_code == 0


def test_all_blockers_reported_together(tmp_path: Path) -> None:
    report = _report(
        tmp_path,
        version=(3, 14),
        import_check=_no_imports_present,
        secret_present=_no_keys,
    )
    assert _names(report.blockers) == {
        "python_version",
        *(f"import:{module}" for module in CRITICAL_IMPORTS),
        f"secret:{preflight.GEMINI_SECRET_NAME}",
    }


def test_secret_presence_callback_receives_names_only(tmp_path: Path) -> None:
    seen: list[str] = []

    def spy(name: str) -> bool:
        seen.append(name)
        return True

    _report(_ready_repo(tmp_path), secret_present=spy)
    assert seen == [preflight.GEMINI_SECRET_NAME, preflight.OPENROUTER_SECRET_NAME]


def test_report_text_never_contains_key_values(tmp_path: Path, monkeypatch) -> None:
    root = _ready_repo(tmp_path)
    (root / "config" / "api_keys.json").write_text(
        json.dumps({preflight.GEMINI_SECRET_NAME: SENTINEL_KEY}), encoding="utf-8"
    )
    monkeypatch.setattr("config.secrets.get_secret", lambda _name: SENTINEL_KEY)

    report = run_preflight(
        repo_root=root,
        version=SUPPORTED_VERSION,
        import_check=_all_imports_present,
    )
    text = format_report(report)
    assert SENTINEL_KEY not in text
    assert "Gemini API key: present" in text
    assert all(SENTINEL_KEY not in check.message for check in report.checks)


def test_secret_resolved_from_secrets_api(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "config.secrets.get_secret",
        lambda name: SENTINEL_KEY if name == preflight.GEMINI_SECRET_NAME else None,
    )
    report = run_preflight(
        repo_root=_ready_repo(tmp_path),
        version=SUPPORTED_VERSION,
        import_check=_all_imports_present,
    )
    assert f"secret:{preflight.GEMINI_SECRET_NAME}" not in _names(report.blockers)
    assert f"secret:{preflight.OPENROUTER_SECRET_NAME}" in _names(report.warnings)


@pytest.mark.parametrize(
    "payload",
    ["not json at all", json.dumps([1, 2]), json.dumps({"gemini_api_key": "   "})],
)
def test_unusable_api_keys_file_counts_as_missing(
    tmp_path: Path, monkeypatch, payload: str
) -> None:
    root = _ready_repo(tmp_path)
    (root / "config" / "api_keys.json").write_text(payload, encoding="utf-8")
    monkeypatch.setattr("config.secrets.get_secret", lambda _name: None)

    report = run_preflight(
        repo_root=root,
        version=SUPPORTED_VERSION,
        import_check=_all_imports_present,
    )
    assert f"secret:{preflight.GEMINI_SECRET_NAME}" in _names(report.blockers)


def test_file_fallback_detects_present_key(tmp_path: Path, monkeypatch) -> None:
    root = _ready_repo(tmp_path)
    (root / "config" / "api_keys.json").write_text(
        json.dumps({preflight.GEMINI_SECRET_NAME: SENTINEL_KEY}), encoding="utf-8"
    )

    def boom(_name: str) -> str | None:
        raise RuntimeError("secret store unavailable")

    monkeypatch.setattr("config.secrets.get_secret", boom)

    report = run_preflight(
        repo_root=root,
        version=SUPPORTED_VERSION,
        import_check=_all_imports_present,
    )
    assert f"secret:{preflight.GEMINI_SECRET_NAME}" not in _names(report.blockers)
    assert SENTINEL_KEY not in format_report(report)


def test_real_import_check_detects_stdlib_and_missing_module() -> None:
    assert preflight._try_import("json") is True
    assert preflight._try_import("slon_module_that_does_not_exist") is False


def test_format_report_marks_blockers_and_warnings(tmp_path: Path) -> None:
    blocked = _report(tmp_path, version=(3, 14), secret_present=_no_keys)
    text = format_report(blocked)
    assert "[FAIL]" in text
    assert "[WARN]" in text
    assert "exit 1" in text

    ready = _report(_ready_repo(tmp_path))
    ready_text = format_report(ready)
    assert "[FAIL]" not in ready_text
    assert "exit 0" in ready_text


def test_main_writes_report_and_returns_exit_code(monkeypatch) -> None:
    stream = io.StringIO()
    monkeypatch.setattr(
        preflight,
        "run_preflight",
        lambda: PreflightReport(
            checks=(
                preflight.CheckResult(
                    name="python_version",
                    ok=False,
                    severity="blocker",
                    message="Python 3.14 is unsupported",
                ),
            )
        ),
    )
    assert main([], stream=stream) == 1
    assert "Python 3.14 is unsupported" in stream.getvalue()
    assert SENTINEL_KEY not in stream.getvalue()


def test_main_returns_zero_when_no_blockers(monkeypatch) -> None:
    stream = io.StringIO()
    monkeypatch.setattr(
        preflight,
        "run_preflight",
        lambda: PreflightReport(
            checks=(
                preflight.CheckResult(
                    name="face.png",
                    ok=False,
                    severity="warning",
                    message="face.png: missing",
                ),
            )
        ),
    )
    assert main([], stream=stream) == 0
    assert "exit 0" in stream.getvalue()


def test_cli_rejects_unknown_flags() -> None:
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(["--install-deps"])
    assert exc_info.value.code == 2


def test_default_repo_root_contains_main_py() -> None:
    root = preflight.default_repo_root()
    assert (root / "main.py").is_file()
    assert (root / "config").is_dir()


def test_preflight_never_installs_or_calls_network() -> None:
    source = PREFLIGHT_SOURCE.read_text(encoding="utf-8")
    for forbidden in ("subprocess", "urllib", "socket", "-m pip", "http"):
        assert forbidden not in source
