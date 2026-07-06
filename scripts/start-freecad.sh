#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FREECAD="$ROOT/apps/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"

export DISPLAY="${DISPLAY:-:1}"
export XAUTHORITY="${XAUTHORITY:-/run/user/$(id -u)/gdm/Xauthority}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

"$ROOT/scripts/repair-freecad-mcp-links.sh"

if pgrep -x freecad >/dev/null; then
  if "$ROOT/scripts/check-freecad-rpc.py" >/dev/null 2>&1; then
    echo "FreeCAD is already running and its MCP RPC is healthy."
    exit 0
  fi
  echo "FreeCAD is running, but its MCP RPC is unavailable." >&2
  echo "The add-on links are now correct; close FreeCAD and rerun this launcher." >&2
  exit 1
fi

nohup "$FREECAD" >"$ROOT/freecad.log" 2>&1 &
echo $! >"$ROOT/freecad.pid"
echo "Started FreeCAD (PID $(cat "$ROOT/freecad.pid")) on $DISPLAY"
