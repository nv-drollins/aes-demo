#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FREECAD_DATA="${FREECAD_USER_DATA_DIR:-$HOME/.local/share/FreeCAD/v1-1}"

ensure_link() {
  local source="$1"
  local destination="$2"

  [[ -e "$source" ]] || {
    echo "Required FreeCAD MCP source is missing: $source" >&2
    exit 1
  }
  mkdir -p "$(dirname "$destination")"
  if [[ -e "$destination" && ! -L "$destination" ]]; then
    echo "Refusing to replace non-symlink FreeCAD path: $destination" >&2
    exit 1
  fi
  if [[ -L "$destination" && "$(readlink "$destination")" == "$source" ]]; then
    return
  fi
  ln -sfn "$source" "$destination"
  echo "FREECAD_MCP_LINK_REPAIRED=$destination -> $source"
}

ensure_link \
  "$ROOT/freecad-mcp/addon/FreeCADMCP" \
  "$FREECAD_DATA/Mod/FreeCADMCP"
ensure_link \
  "$ROOT/config/freecad_mcp_settings.json" \
  "$FREECAD_DATA/freecad_mcp_settings.json"

echo "FREECAD_MCP_LINKS_OK=$FREECAD_DATA"
