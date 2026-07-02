#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT/scripts/start-freecad.sh"

for _ in $(seq 1 30); do
  if "$ROOT/scripts/check-freecad-rpc.py" >/dev/null 2>&1; then
    exec "$HOME/.local/bin/hermes" chat "$@"
  fi
  sleep 1
done

echo "FreeCAD MCP RPC did not become healthy within 30 seconds." >&2
exit 1
