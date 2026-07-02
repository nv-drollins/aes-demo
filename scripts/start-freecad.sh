#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FREECAD="$ROOT/apps/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"

export DISPLAY="${DISPLAY:-:1}"
export XAUTHORITY="${XAUTHORITY:-/run/user/$(id -u)/gdm/Xauthority}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

if pgrep -f "$FREECAD" >/dev/null; then
  echo "FreeCAD is already running."
  exit 0
fi

nohup "$FREECAD" >"$ROOT/freecad.log" 2>&1 &
echo $! >"$ROOT/freecad.pid"
echo "Started FreeCAD (PID $(cat "$ROOT/freecad.pid")) on $DISPLAY"
