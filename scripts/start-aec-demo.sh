#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/scripts/start-freecad.sh"
for _ in {1..60}; do
  "$ROOT/scripts/check-freecad-rpc.py" >/dev/null 2>&1 && break
  sleep 1
done
if ! "$ROOT/scripts/check-freecad-rpc.py"; then
  echo "FreeCAD started, but its MCP RPC did not become ready within 60 seconds." >&2
  echo "See $ROOT/freecad.log and run $ROOT/scripts/repair-freecad-mcp-links.sh." >&2
  exit 1
fi
"$ROOT/scripts/start-blender.sh"
"$ROOT/scripts/start-comfyui.sh"
"$ROOT/scripts/check-blender-rpc.py"
"$ROOT/scripts/check-comfyui.py"
exec "$HOME/.local/bin/hermes" chat "$@"
