#!/usr/bin/env python3
"""Run the approved template-to-native-FreeCAD cliff-house reconstruction."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import time
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
FREECAD_URL = "http://127.0.0.1:9875"
DOCUMENT = "CliffHouseTemplateBuild"
OUTPUT = ROOT / "source_models/cliff_house/cliff_house_template_build.FCStd"
SCREENSHOT = ROOT / "outputs/template-reconstruction/freecad/cliff-house-template-build.png"


def execute(rpc, path: Path, environment: dict[str, str]) -> str:
    lines = ["import os"]
    for name, value in environment.items():
        lines.append(f"os.environ[{name!r}] = {value!r}")
    lines.append(
        f"exec(compile(open({str(path)!r}, encoding='utf-8').read(), "
        f"{str(path)!r}, 'exec'))"
    )
    result = rpc.execute_code("\n".join(lines))
    if not result.get("success"):
        raise RuntimeError(f"FreeCAD execution failed for {path.name}: {result.get('error', result)}")
    message = result.get("message", "")
    output = message.rsplit("Output: ", 1)[-1].strip()
    if output:
        print(output)
    return output


def require(output: str, marker: str) -> None:
    if marker not in output:
        raise RuntimeError(f"Missing FreeCAD success marker: {marker}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pause-seconds", type=float, default=0.0)
    parser.add_argument("--object-delay", type=float, default=0.0)
    parser.add_argument("--keep-existing", action="store_true")
    args = parser.parse_args()

    subprocess.run(
        ["python3", str(ROOT / "scripts/validate-template-reconstruction-project.py"), "--require-approved"],
        cwd=ROOT,
        check=True,
    )
    rpc = xmlrpc.client.ServerProxy(FREECAD_URL, allow_none=True)
    if not rpc.ping():
        raise RuntimeError("FreeCAD MCP RPC did not answer on 127.0.0.1:9875")
    documents = set(rpc.list_documents())
    missing = {"CliffHouseReference", "CliffHouseFinalReference"} - documents
    if missing:
        raise RuntimeError(f"Required protected FreeCAD references are not open: {sorted(missing)}")

    builder = ROOT / "scripts/build-template-cliff-house.py"
    common = {
        "AEC_TEMPLATE_BUILD_DOCUMENT": DOCUMENT,
        "AEC_TEMPLATE_BUILD_DELAY": str(max(0.0, args.object_delay)),
    }
    output = execute(
        rpc,
        builder,
        {**common, "AEC_TEMPLATE_BUILD_PHASE": "00_template_audit", "AEC_TEMPLATE_BUILD_RESET": "0" if args.keep_existing else "1"},
    )
    require(output, "TEMPLATE_AUDIT_OK")
    time.sleep(max(0.0, args.pause_seconds))

    output = execute(
        rpc,
        ROOT / "scripts/build-cliff-house-terrain.py",
        {
            "AEC_RHINO_REFERENCE_DOCUMENT": "CliffHouseReference",
            "AEC_REBUILD_DOCUMENT": DOCUMENT,
            "AEC_REBUILD_FCSTD": str(OUTPUT),
        },
    )
    require(output, "TERRAIN_BUILD_OK=")
    time.sleep(max(0.0, args.pause_seconds))

    output = execute(
        rpc,
        ROOT / "scripts/build-cliff-house-site-slabs.py",
        {
            "AEC_REBUILD_DOCUMENT": DOCUMENT,
            "AEC_REBUILD_FCSTD": str(OUTPUT),
        },
    )
    require(output, "SITE_SLABS_BUILD_OK=")
    site_check = rpc.execute_code(
        "import FreeCAD as App\n"
        f"doc=App.getDocument({DOCUMENT!r})\n"
        "names=('building_plan_Shell','garage_plan_Shell','driveway_plan_Shell','patio_stairs_plan_Shell','patio_plan_Shell')\n"
        "missing=[name for name in names if doc.getObject(name) is None]\n"
        "if missing: raise RuntimeError(f'Missing site support: {missing}')\n"
        "print(f'SITE_SUPPORT_BUILD_OK document={doc.Name} objects={len(names)}')"
    )
    if not site_check.get("success"):
        raise RuntimeError(site_check.get("error", site_check))
    site_output = site_check.get("message", "").rsplit("Output: ", 1)[-1].strip()
    print(site_output)
    require(site_output, "SITE_SUPPORT_BUILD_OK")
    time.sleep(max(0.0, args.pause_seconds))

    for phase, marker in (
        ("03_level_1_structure", "L1_STRUCTURE_BUILD_OK"),
        ("04_level_1_envelope", "L1_ENVELOPE_BUILD_OK"),
        ("05_level_2_structure", "L2_STRUCTURE_BUILD_OK"),
        ("06_level_2_envelope", "L2_ENVELOPE_BUILD_OK"),
        ("07_level_3_structure", "L3_STRUCTURE_BUILD_OK"),
        ("08_level_3_envelope", "L3_ENVELOPE_BUILD_OK"),
        ("09_entry_cladding", "ENTRY_CLADDING_BUILD_OK"),
        ("10_infinity_pool", "POOL_BUILD_OK"),
        ("11_reference_comparison", "FINAL_REFERENCE_COMPARISON_OK"),
    ):
        output = execute(rpc, builder, {**common, "AEC_TEMPLATE_BUILD_PHASE": phase, "AEC_TEMPLATE_BUILD_RESET": "0"})
        require(output, marker)
        time.sleep(max(0.0, args.pause_seconds))

    SCREENSHOT.parent.mkdir(parents=True, exist_ok=True)
    capture = rpc.execute_code(
        "import FreeCAD as App\nimport FreeCADGui as Gui\n"
        f"App.setActiveDocument({DOCUMENT!r})\n"
        "Gui.activeDocument().activeView().viewAxonometric()\n"
        "Gui.activeDocument().activeView().fitAll()\n"
        "Gui.updateGui()\n"
        f"Gui.activeDocument().activeView().saveImage({str(SCREENSHOT)!r}, 1920, 1080, 'Current')\n"
        f"print('TEMPLATE_BUILD_SCREENSHOT_OK={SCREENSHOT}')"
    )
    if not capture.get("success"):
        raise RuntimeError(capture.get("error", capture))
    print(capture.get("message", "").rsplit("Output: ", 1)[-1].strip())
    print(f"TEMPLATE_RECONSTRUCTION_OK document={DOCUMENT} output={OUTPUT} screenshot={SCREENSHOT}")


if __name__ == "__main__":
    main()
