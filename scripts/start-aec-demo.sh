#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/scripts/start-freecad.sh"
for _ in {1..30}; do
  "$ROOT/scripts/check-freecad-rpc.py" >/dev/null 2>&1 && break
  sleep 1
done
"$ROOT/scripts/check-freecad-rpc.py"
"$ROOT/scripts/start-blender.sh"
"$ROOT/scripts/start-comfyui.sh"
"$ROOT/scripts/check-blender-rpc.py"
"$ROOT/scripts/check-comfyui.py"
exec "$HOME/.local/bin/hermes" chat "$@"
