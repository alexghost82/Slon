#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-run}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="Slon"
APP_BUNDLE="$ROOT_DIR/dist/$APP_NAME.app"
APP_BINARY="$APP_BUNDLE/Contents/MacOS/$APP_NAME"

pkill -x "$APP_NAME" >/dev/null 2>&1 || true
"$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/packaging/macos/build_app.py"

open_app() {
  /usr/bin/open -n "$APP_BUNDLE"
}

case "$MODE" in
  run)
    open_app
    ;;
  --debug|debug)
    lldb -- "$APP_BINARY"
    ;;
  --logs|logs)
    open_app
    /usr/bin/log stream --info --style compact --predicate "process == \"$APP_NAME\""
    ;;
  --telemetry|telemetry)
    open_app
    /usr/bin/log stream --info --style compact --predicate 'subsystem == "local.slon.desktop"'
    ;;
  --verify|verify)
    VERIFY_LOG="$(mktemp -t slon-launch.XXXXXX)"
    "$APP_BINARY" >"$VERIFY_LOG" 2>&1 &
    APP_PID=$!
    sleep 5
    if ! kill -0 "$APP_PID" >/dev/null 2>&1 || grep -q '^Traceback ' "$VERIFY_LOG"; then
      echo "$APP_NAME failed during startup:" >&2
      tail -80 "$VERIFY_LOG" >&2
      rm -f "$VERIFY_LOG"
      exit 1
    fi
    rm -f "$VERIFY_LOG"
    ;;
  *)
    echo "usage: $0 [run|--debug|--logs|--telemetry|--verify]" >&2
    exit 2
    ;;
esac
