#!/usr/bin/env python3
"""Safe, read-only project stack detection for Production Readiness Auditor.

Does NOT install packages, mutate the project, or print secret values.
Emits machine-readable JSON (default) or a Markdown summary.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECRET_NAME_RE = re.compile(
    r"(api[_-]?key|secret|password|token|private[_-]?key|credentials)",
    re.I,
)
INLINE_SECRET_RE = re.compile(
    r"(api[_-]?key|secret|password|token|passwd)\s*[=:]\s*"
    r"([^\s'\";]+|'[^']+'|\"[^\"]+\")",
    re.I,
)


def which(cmd: str) -> str | None:
    from shutil import which as _which

    return _which(cmd)


def run_version(cmd: list[str], timeout: float = 8.0) -> dict[str, Any]:
    exe = which(cmd[0])
    if not exe:
        return {"command": cmd[0], "available": False}
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        out = (proc.stdout or proc.stderr or "").strip().splitlines()
        version_line = out[0] if out else ""
        return {
            "command": cmd[0],
            "path": exe,
            "available": True,
            "exit_code": proc.returncode,
            "version_line": version_line[:240],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "command": cmd[0],
            "path": exe,
            "available": True,
            "error": type(exc).__name__,
        }


def git_info(root: Path) -> dict[str, Any]:
    if not which("git"):
        return {"available": False}
    info: dict[str, Any] = {"available": True}
    try:
        def git(*args: str) -> str:
            r = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return (r.stdout or "").strip()

        info["commit"] = git("rev-parse", "HEAD") or None
        info["branch"] = git("rev-parse", "--abbrev-ref", "HEAD") or None
        status = git("status", "--porcelain")
        info["dirty"] = bool(status)
        info["dirty_entry_count"] = len(status.splitlines()) if status else 0
    except (OSError, subprocess.TimeoutExpired) as exc:
        info["error"] = type(exc).__name__
    return info


def exists_any(root: Path, patterns: list[str]) -> list[str]:
    found: list[str] = []
    for pat in patterns:
        if any(ch in pat for ch in "*?[]"):
            matches = list(root.glob(pat))
            for m in matches[:20]:
                try:
                    rel = str(m.relative_to(root))
                except ValueError:
                    rel = str(m)
                if "node_modules" in rel.split(os.sep) or ".git" in rel.split(os.sep):
                    continue
                found.append(rel)
        else:
            p = root / pat
            if p.exists():
                found.append(pat)
    return found


def read_text_limited(path: Path, max_bytes: int = 200_000) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def detect_platforms(root: Path) -> tuple[list[str], dict[str, Any], list[str]]:
    platforms: list[str] = []
    signals: dict[str, Any] = {}
    notes: list[str] = []

    # Apple ecosystem
    xcode = exists_any(
        root,
        [
            "*.xcodeproj",
            "*.xcworkspace",
            "Project.swift",
            "project.yml",
            "Tuist.swift",
            "Package.swift",
        ],
    )
    swift_files = []
    for p in root.rglob("*.swift"):
        rel = str(p.relative_to(root))
        if "node_modules" in rel.split(os.sep) or ".git" in rel.split(os.sep):
            continue
        swift_files.append(rel)
        if len(swift_files) >= 8:
            break
    if xcode or swift_files:
        signals["apple"] = {"paths": xcode, "sample_swift": swift_files}
        blob = " ".join(xcode + swift_files).lower()
        looks_macos = any(k in blob for k in ("macos", "appkit")) or bool(
            exists_any(root, ["macos/**", "MacOS/**"])
        )
        looks_ios = any(
            k in blob for k in ("ios", "ipados", "uikit", "iphone", "watchos", "tvos")
        ) or bool(exists_any(root, ["ios/**", "iOS/**"]))
        if looks_ios or (xcode and not looks_macos):
            platforms.append("ios-ipados")
        if looks_macos:
            platforms.append("macos-native")
        if not looks_ios and not looks_macos and (xcode or swift_files):
            platforms.append("apple-native-unspecified")
            notes.append(
                "Apple/Swift signals found but iOS vs macOS not confidently distinguished."
            )

    android = exists_any(
        root,
        [
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle",
            "settings.gradle.kts",
            "android/app/build.gradle",
            "android/app/build.gradle.kts",
            "**/AndroidManifest.xml",
        ],
    )
    if android:
        platforms.append("android")
        signals["android"] = android

    pubspec = root / "pubspec.yaml"
    if pubspec.exists():
        text = read_text_limited(pubspec)
        if "flutter:" in text or "sdk: flutter" in text:
            platforms.append("flutter")
            signals["flutter"] = ["pubspec.yaml"]
            for sub in ("android", "ios", "macos", "windows", "linux", "web"):
                if (root / sub).exists():
                    notes.append(f"Flutter project includes {sub}/")

    pkg = root / "package.json"
    pkg_text = read_text_limited(pkg) if pkg.exists() else ""
    if pkg.exists():
        if (
            "react-native" in pkg_text
            or (root / "metro.config.js").exists()
            or (root / "metro.config.ts").exists()
        ):
            platforms.append("react-native")
            signals["react-native"] = ["package.json"]
        if "electron" in pkg_text or "electron-builder" in pkg_text:
            platforms.append("electron")
            signals["electron"] = ["package.json"]
        if '"workspaces"' in pkg_text:
            signals.setdefault("monorepo", []).append("npm-workspaces")

    if exists_any(
        root, ["src-tauri/tauri.conf.json", "src-tauri/Cargo.toml", "tauri.conf.json"]
    ):
        platforms.append("tauri")
        signals["tauri"] = exists_any(
            root, ["src-tauri/tauri.conf.json", "src-tauri/Cargo.toml", "tauri.conf.json"]
        )

    dotnet = exists_any(root, ["*.sln", "*.csproj", "*.fsproj", "*.vbproj"])
    if dotnet:
        platforms.append("dotnet")
        signals["dotnet"] = dotnet[:30]
        csproj_sample = ""
        for rel in dotnet:
            if rel.endswith(".csproj"):
                csproj_sample += read_text_limited(root / rel, 80_000)
        blob = (" ".join(dotnet) + csproj_sample).lower()
        if "maui" in blob or "usemaui" in blob:
            platforms.append("dotnet-maui")
        if "usewpf" in blob or ".useWpf".lower() in blob or "wpf" in blob:
            platforms.append("dotnet-wpf")
        if "winui" in blob or "microsoft.windowsappsdk" in blob:
            platforms.append("dotnet-winui")

    qt_paths = exists_any(root, ["CMakeLists.txt", "*.pro", "*.qrc"])
    if qt_paths:
        cmake = (
            read_text_limited(root / "CMakeLists.txt")
            if (root / "CMakeLists.txt").exists()
            else ""
        )
        pro_hits = [p for p in qt_paths if p.endswith(".pro")]
        if "qt" in cmake.lower() or "find_package(qt" in cmake.lower() or pro_hits:
            platforms.append("qt")
            signals["qt"] = qt_paths[:20]

    cmake = read_text_limited(root / "CMakeLists.txt").lower() if (root / "CMakeLists.txt").exists() else ""
    meson_hits = []
    for p in root.rglob("meson.build"):
        rel = str(p.relative_to(root))
        if "node_modules" in rel.split(os.sep):
            continue
        meson_hits.append(p)
        if len(meson_hits) >= 10:
            break
    meson_txt = "".join(read_text_limited(p) for p in meson_hits).lower()
    if "gtk" in cmake or "gtk" in meson_txt:
        platforms.append("gtk")
        signals["gtk"] = True

    if pkg.exists() and "electron" not in signals and "react-native" not in platforms:
        signals["node_package"] = True

    py = exists_any(
        root,
        ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
    )
    # also requirements*.txt via glob
    py += exists_any(root, ["requirements*.txt"])
    if py:
        signals["python"] = list(dict.fromkeys(py))[:20]

    monorepo: list[str] = list(signals.get("monorepo") or [])
    if (root / "pnpm-workspace.yaml").exists() or (root / "lerna.json").exists() or (root / "nx.json").exists():
        monorepo.append("js-workspaces")
    if (root / "Cargo.toml").exists() and "[workspace]" in read_text_limited(root / "Cargo.toml"):
        monorepo.append("cargo-workspace")
    if (root / "settings.gradle").exists() or (root / "settings.gradle.kts").exists():
        monorepo.append("gradle-multi")
    if (root / "go.work").exists():
        monorepo.append("go-work")
    if monorepo:
        signals["monorepo"] = list(dict.fromkeys(monorepo))
        notes.append("Possible monorepo/workspaces detected: " + ", ".join(signals["monorepo"]))

    backend = exists_any(
        root,
        [
            "docker-compose.yml",
            "docker-compose.yaml",
            "Dockerfile",
            "**/openapi.yaml",
            "**/openapi.json",
            "**/swagger.json",
        ],
    )
    if backend:
        signals["backend_surface"] = backend[:20]

    seen: set[str] = set()
    uniq: list[str] = []
    for p in platforms:
        if p not in seen:
            seen.add(p)
            uniq.append(p)

    if not uniq:
        notes.append(
            "No known app platform confidently detected. "
            "Do not guess build commands; inspect README/CI and mark unknown checks BLOCKED."
        )

    return uniq, signals, notes


def find_docs(root: Path) -> list[str]:
    candidates = [
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        "README.MD",
        "readme.md",
        "CONTRIBUTING.md",
        "CONTRIBUTING.MD",
        "Makefile",
        "makefile",
        "Taskfile.yml",
        "Justfile",
        "package.json",
        "pyproject.toml",
    ]
    found = [c for c in candidates if (root / c).exists()]
    ci: list[str] = []
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        for f in sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml")):
            ci.append(str(f.relative_to(root)))
    for base in (".gitlab-ci.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml"):
        if (root / base).is_file():
            ci.append(base)
    return found + ci[:30]


def extract_npm_scripts(root: Path) -> dict[str, str]:
    pkg = root / "package.json"
    if not pkg.exists():
        return {}
    try:
        data = json.loads(read_text_limited(pkg, 500_000))
    except json.JSONDecodeError:
        return {}
    scripts = data.get("scripts") or {}
    if not isinstance(scripts, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in list(scripts.items())[:80]:
        sv = str(v)
        if SECRET_NAME_RE.search(sv) and INLINE_SECRET_RE.search(sv):
            out[str(k)] = "[REDACTED]"
        else:
            out[str(k)] = sv[:200]
    return out


def toolchains() -> dict[str, Any]:
    checks = [
        ["xcodebuild", "-version"],
        ["xcrun", "--version"],
        ["adb", "version"],
        ["flutter", "--version"],
        ["dotnet", "--version"],
        ["node", "--version"],
        ["npm", "--version"],
        ["pnpm", "--version"],
        ["yarn", "--version"],
        ["cargo", "--version"],
        ["rustc", "--version"],
        ["cmake", "--version"],
        ["python3", "--version"],
        ["java", "-version"],
        ["gradle", "--version"],
        ["go", "version"],
        ["swift", "--version"],
        ["pod", "--version"],
        ["tuist", "version"],
        ["xcodegen", "version"],
    ]
    return {cmd[0]: run_version(cmd) for cmd in checks}


def suspicious_secret_files(root: Path) -> list[str]:
    """Report paths that may contain secrets — names only, never contents."""
    patterns = [
        ".env",
        ".env.*",
        "**/api_keys.json",
        "**/secrets.json",
        "**/*.pem",
        "**/*.p12",
        "**/*.mobileprovision",
        "**/google-services.json",
        "**/GoogleService-Info.plist",
        "**/*keystore*",
        "**/credentials.json",
    ]
    hits: list[str] = []
    for pat in patterns:
        for m in root.glob(pat):
            rel = str(m.relative_to(root))
            parts = rel.split(os.sep)
            if "node_modules" in parts or ".git" in parts:
                continue
            hits.append(rel)
            if len(hits) >= 40:
                return hits
    return hits


def build_manifest(root: Path) -> dict[str, Any]:
    platforms, signals, notes = detect_platforms(root)
    return {
        "schema_version": 1,
        "generator": "production-readiness-auditor/detect-project.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root.resolve()),
        "git": git_info(root),
        "platforms_detected": platforms,
        "signals": signals,
        "docs_and_ci": find_docs(root),
        "npm_scripts": extract_npm_scripts(root),
        "toolchains": toolchains(),
        "possible_secret_files": suspicious_secret_files(root),
        "notes": notes,
        "safety": {
            "read_only": True,
            "installs_packages": False,
            "mutates_project": False,
            "prints_secret_values": False,
        },
    }


def to_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Detect project result",
        "",
        f"- Generated: `{manifest.get('generated_at')}`",
        f"- Root: `{manifest.get('root')}`",
        f"- Platforms: {', '.join(manifest.get('platforms_detected') or ['(none)'])}",
        "",
        "## Git",
        "```json",
        json.dumps(manifest.get("git"), indent=2),
        "```",
        "",
        "## Notes",
    ]
    for n in manifest.get("notes") or []:
        lines.append(f"- {n}")
    if not manifest.get("notes"):
        lines.append("- (none)")
    lines += ["", "## Docs / CI"]
    for d in manifest.get("docs_and_ci") or []:
        lines.append(f"- `{d}`")
    lines += ["", "## Possible secret files (names only)"]
    secs = manifest.get("possible_secret_files") or []
    if not secs:
        lines.append("- (none matched)")
    else:
        for s in secs:
            lines.append(f"- `{s}`")
    lines += ["", "## Toolchains (availability)"]
    for name, info in (manifest.get("toolchains") or {}).items():
        avail = info.get("available")
        ver = info.get("version_line") or info.get("error") or ""
        lines.append(f"- `{name}`: {'yes' if avail else 'no'} {ver}".rstrip())
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe read-only project detection")
    parser.add_argument("--root", default=".", help="Project root (default: .)")
    parser.add_argument("--json", action="store_true", help="Emit JSON (default)")
    parser.add_argument("--md", action="store_true", help="Emit Markdown summary")
    parser.add_argument("-o", "--output", help="Write output to file path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2

    manifest = build_manifest(root)
    if args.md and not args.json:
        text = to_markdown(manifest)
    else:
        text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
