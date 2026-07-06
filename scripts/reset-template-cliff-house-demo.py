#!/usr/bin/env python3
"""Reset only the template-driven cliff-house build for a clean replay."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
ARCHIVE = ROOT / "outputs/template-reconstruction/archives" / STAMP
DOCUMENT = "CliffHouseTemplateBuild"


def archive(path: Path) -> None:
    if not path.exists():
        return
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    destination = ARCHIVE / path.name
    shutil.move(str(path), str(destination))
    print(f"ARCHIVED={path} -> {destination}")


def main() -> None:
    rpc = xmlrpc.client.ServerProxy("http://127.0.0.1:9875", allow_none=True)
    if not rpc.ping():
        raise RuntimeError("FreeCAD MCP RPC did not answer on 127.0.0.1:9875")
    documents = set(rpc.list_documents())
    if DOCUMENT in documents:
        result = rpc.execute_code(
            "import FreeCAD as App\n"
            f"doc=App.getDocument({DOCUMENT!r})\n"
            "metadata=doc.getObject('TemplateBuildMetadata')\n"
            "if metadata is None or getattr(metadata, 'ManifestFormat', '') != "
            "'aec-demo-template-construction-v1':\n"
            "    raise RuntimeError('Refusing to close an unrecognized document')\n"
            f"App.closeDocument({DOCUMENT!r})\n"
            f"print('CLOSED_DOCUMENT={DOCUMENT}')"
        )
        if not result.get("success"):
            raise RuntimeError(result.get("error", result))
        print(result.get("message", "").rsplit("Output: ", 1)[-1].strip())

    archive(ROOT / "source_models/cliff_house/cliff_house_template_build.FCStd")
    archive(ROOT / "source_models/cliff_house/cliff_house_template_build.FCBak")
    archive(ROOT / "outputs/template-reconstruction/freecad/cliff-house-template-build.png")

    remaining = set(rpc.list_documents())
    required = {"CliffHouseReference", "CliffHouseFinalReference"}
    missing = required - remaining
    if missing:
        raise RuntimeError(
            "Build reset completed, but required protected references are not open: "
            f"{sorted(missing)}"
        )
    print(
        "TEMPLATE_DEMO_RESET_OK "
        "brief=preserved references=preserved build=cleared"
    )


if __name__ == "__main__":
    main()
