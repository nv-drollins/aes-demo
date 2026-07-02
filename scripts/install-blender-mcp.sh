#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM="$ROOT/blender-mcp"
HERMES="${HERMES:-$HOME/.local/bin/hermes}"
UVX="${UVX:-$HOME/.hermes/bin/uvx}"
command -v blender >/dev/null || { echo "Blender is not installed." >&2; exit 1; }
[[ -f "$UPSTREAM/addon.py" ]] || git clone https://github.com/ahujasid/blender-mcp.git "$UPSTREAM"
ADDON_DIR="$(blender -b --python-expr \
  "import bpy; print('AES_ADDON_DIR=' + bpy.utils.user_resource('SCRIPTS', path='addons', create=True))" \
  2>&1 | sed -n 's/^AES_ADDON_DIR=//p' | tail -1)"
[[ -n "$ADDON_DIR" ]] || { echo "Could not determine Blender's add-on directory." >&2; exit 1; }
install -Dm644 "$UPSTREAM/addon.py" "$ADDON_DIR/blender_mcp.py"
blender -b --python-expr \
  "import bpy; bpy.ops.preferences.addon_enable(module='blender_mcp'); bpy.context.preferences.addons['blender_mcp'].preferences.telemetry_consent=False; bpy.ops.wm.save_userpref()"
if ! "$HERMES" mcp list | grep -qE '^  blender[[:space:]]'; then
  printf 'y\n' | "$HERMES" mcp add blender --command "$UVX" \
    --env DISABLE_TELEMETRY=true UV_PYTHON_PREFERENCE=only-managed \
      BLENDER_HOST=127.0.0.1 BLENDER_PORT=9876 \
    --args --python 3.11 blender-mcp
fi
echo "Blender MCP is installed. Start Blender with scripts/start-blender.sh"
