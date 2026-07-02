#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMFY="$ROOT/comfyui"
[[ -x "$COMFY/.venv/bin/python" ]] || { echo "ComfyUI is not installed." >&2; exit 1; }
if [[ -f "$ROOT/comfyui.pid" ]] && kill -0 "$(<"$ROOT/comfyui.pid")" 2>/dev/null; then
  echo "ComfyUI is already running."
else
  nohup "$COMFY/.venv/bin/python" "$COMFY/main.py" --listen 127.0.0.1 \
    >"$ROOT/comfyui.log" 2>&1 &
  echo $! >"$ROOT/comfyui.pid"
  echo "Started ComfyUI (PID $(<"$ROOT/comfyui.pid"))"
fi
for _ in {1..60}; do
  if python3 "$ROOT/scripts/check-comfyui.py" >/dev/null 2>&1; then
    python3 "$ROOT/scripts/check-comfyui.py"
    echo "Open http://127.0.0.1:8188 in the Spark browser."
    exit 0
  fi
  sleep 1
done
echo "ComfyUI did not become ready; see $ROOT/comfyui.log" >&2
exit 1
