#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export DISPLAY="${DISPLAY:-:1}"
export XAUTHORITY="${XAUTHORITY:-/run/user/$(id -u)/gdm/Xauthority}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
if pgrep -x blender >/dev/null; then
  echo "Blender is already running."
else
  ARGS=()
  [[ ${1:-} == "" ]] || ARGS+=("$1")
  nohup blender "${ARGS[@]}" >"$ROOT/blender.log" 2>&1 &
  echo $! >"$ROOT/blender.pid"
  echo "Started Blender (PID $(<"$ROOT/blender.pid")) on $DISPLAY"
fi
for _ in {1..30}; do
  if python3 "$ROOT/scripts/check-blender-rpc.py" >/dev/null 2>&1; then
    python3 "$ROOT/scripts/check-blender-rpc.py"
    exit 0
  fi
  sleep 1
done
echo "Blender started, but its MCP socket did not become ready." >&2
echo "Confirm the Blender MCP add-on is enabled; see $ROOT/blender.log" >&2
exit 1
