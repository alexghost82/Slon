#!/usr/bin/env bash
# Safe read-only wrapper: prefers Python detector; falls back to minimal bash heuristics.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/detect-project.py"

ROOT="."
PASS_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="${2:-.}"
      shift 2
      ;;
    *)
      PASS_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#PASS_ARGS[@]} -eq 0 ]]; then
  PASS_ARGS=(--json)
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$PY_SCRIPT" --root "$ROOT" "${PASS_ARGS[@]}"
fi
if command -v python >/dev/null 2>&1; then
  exec python "$PY_SCRIPT" --root "$ROOT" "${PASS_ARGS[@]}"
fi

echo "warning: python3 not found; emitting minimal bash fallback JSON" >&2
ROOT_ABS="$(cd "$ROOT" && pwd)"
platforms=()
[[ -f "$ROOT/pubspec.yaml" ]] && platforms+=("flutter")
if [[ -f "$ROOT/package.json" ]] && grep -Eq 'react-native|"electron"' "$ROOT/package.json" 2>/dev/null; then
  platforms+=("node-desktop-or-rn")
fi
shopt -s nullglob
xcode=( "$ROOT"/*.xcodeproj )
((${#xcode[@]})) && platforms+=("ios-ipados")
[[ -f "$ROOT/build.gradle" || -f "$ROOT/build.gradle.kts" || -f "$ROOT/settings.gradle" || -f "$ROOT/settings.gradle.kts" ]] && platforms+=("android")
dotnet=( "$ROOT"/*.sln "$ROOT"/*.csproj )
((${#dotnet[@]})) && platforms+=("dotnet")
[[ -f "$ROOT/src-tauri/Cargo.toml" || -f "$ROOT/tauri.conf.json" ]] && platforms+=("tauri")

plat_json="[]"
if ((${#platforms[@]})); then
  plat_json=$(printf '"%s",' "${platforms[@]}")
  plat_json="[${plat_json%,}]"
fi

commit=""
branch=""
dirty=false
if command -v git >/dev/null 2>&1; then
  commit="$(git -C "$ROOT_ABS" rev-parse HEAD 2>/dev/null || true)"
  branch="$(git -C "$ROOT_ABS" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [[ -n "$(git -C "$ROOT_ABS" status --porcelain 2>/dev/null || true)" ]]; then dirty=true; fi
fi

cat <<JSON
{
  "schema_version": 1,
  "generator": "production-readiness-auditor/detect-project.sh-fallback",
  "root": "$ROOT_ABS",
  "git": {"available": true, "commit": "$commit", "branch": "$branch", "dirty": $dirty},
  "platforms_detected": $plat_json,
  "notes": ["Python unavailable; used minimal bash fallback. Prefer detect-project.py."],
  "safety": {"read_only": true, "installs_packages": false, "mutates_project": false, "prints_secret_values": false}
}
JSON
