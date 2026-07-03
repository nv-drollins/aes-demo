#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - <<'PY'
import xmlrpc.client

try:
    rpc = xmlrpc.client.ServerProxy(
        "http://127.0.0.1:9875",
        allow_none=True,
    )
    if not rpc.ping():
        raise RuntimeError("FreeCAD MCP RPC did not answer")
except Exception as exc:
    print(
        "FreeCAD is not reachable; generated files will still "
        f"be removed ({exc})"
    )
else:
    code = """for name in ('CliffHouseRebuild', 'CliffHouseReference'):
    if name not in App.listDocuments():
        continue
    if name == 'CliffHouseReference':
        doc = App.getDocument(name)
        metadata = doc.getObject('RhinoImportMetadata')
        if metadata is None or getattr(metadata, 'ManifestFormat', '') != 'aes-demo-rhino-reference-v1':
            raise RuntimeError('Refusing to close an unrecognized CliffHouseReference document')
    App.closeDocument(name)
    print('CLOSED_DOCUMENT=' + name)
"""
    result = rpc.execute_code(code)
    if not result.get("success"):
        raise SystemExit(
            f"FreeCAD reset failed: {result.get('error', result)}"
        )
    output = (
        result["message"]
        .rsplit("Output: ", 1)[-1]
        .strip()
    )
    if output:
        print(output)
PY

rm -f \
  "$ROOT/source_models/cliff_house/cliff_house_reference.FCStd" \
  "$ROOT/source_models/cliff_house"/cliff_house_reference*.FCBak \
  "$ROOT/source_models/cliff_house/cliff_house_rebuild.FCStd" \
  "$ROOT/source_models/cliff_house"/cliff_house_rebuild*.FCBak \
  "$ROOT/CliffHouseRebuild.FCStd" \
  "$ROOT"/CliffHouseRebuild*.FCBak \
  /tmp/aes-demo-rhino-reference.json \
  /tmp/aes-demo-cliff-house-reference.png

echo "REFERENCE_WORKFLOW_RESET_OK"
