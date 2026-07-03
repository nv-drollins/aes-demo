#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${1:-$ROOT/aec-cptx-demo/_scene_templates/base_model_template.3dm}"
MANIFEST="${AES_RHINO_REFERENCE_JSON:-/tmp/aes-demo-rhino-reference.json}"
UV="${UV:-$HOME/.hermes/bin/uv}"

"$UV" run --with rhino3dm python \
  "$ROOT/scripts/extract-rhino-reference.py" \
  "$SOURCE" \
  "$MANIFEST"

AES_RHINO_REFERENCE_JSON="$MANIFEST" ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path
import xmlrpc.client

root = Path(os.environ["ROOT"])
manifest = os.environ["AES_RHINO_REFERENCE_JSON"]
rpc = xmlrpc.client.ServerProxy(
    "http://127.0.0.1:9875",
    allow_none=True,
)
if not rpc.ping():
    raise SystemExit(
        "FreeCAD MCP RPC did not answer on 127.0.0.1:9875"
    )
script = root / "scripts" / "import-rhino-reference-freecad.py"
code = (
    "import os\n"
    f"os.environ['AES_RHINO_REFERENCE_JSON'] = {manifest!r}\n"
    f"exec(compile(open({str(script)!r}, encoding='utf-8').read(), "
    f"{str(script)!r}, 'exec'))"
)
result = rpc.execute_code(code)
if not result.get("success"):
    raise SystemExit(
        "FreeCAD reference import failed: "
        f"{result.get('error', result)}"
    )
print(
    result["message"]
    .rsplit("Output: ", 1)[-1]
    .strip()
)
PY
