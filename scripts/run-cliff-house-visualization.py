#!/usr/bin/env python3
"""Run the CliffHouseRebuild -> Blender -> ComfyUI visualization demo."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
FREECAD_URL = "http://127.0.0.1:9875"
BLENDER_ADDRESS = ("127.0.0.1", 9876)
BUNDLE_DIR = Path("/tmp/aes-demo-cliff-house-export")
RENDER_DIR = Path("/tmp/aes-demo-render")
MASSING_SPEC_ID = "cliff-house-upstream-massing-v1"
MASSING_NAMES = (
    "L1_east",
    "L1_west",
    "L2_east",
    "L2_west",
    "L2_balcony_south",
    "L2_balcony_north",
    "L2_balcony_step",
    "L2_roof_garage",
    "L3_main",
    "L3_balcony_south",
    "L3_roof_slab",
)
DEFAULT_PROMPT = (
    "architectural site concept visualization, three-level modernist cliff house "
    "with strong cantilevers and broad balcony slabs on a steep coastal hillside, "
    "preserve every site footprint, dark concrete building "
    "pad, garage and driveway, broad patio terrace, ocean-facing landscape, "
    "realistic green terrain, soft clear daylight, aerial oblique view, "
    "preserve the site layout and topography, professional competition rendering"
)
DEFAULT_NEGATIVE = (
    "dollhouse, cutaway interior, floating platform, flat grey square, blank image, "
    "distorted terrain, warped site plan, floating geometry, extra roads, "
    "text, labels, watermark, people, "
    "low resolution, blurry, oversaturated"
)


def checked_freecad_execution(code: str) -> str:
    rpc = xmlrpc.client.ServerProxy(
        FREECAD_URL,
        allow_none=True,
    )
    if not rpc.ping():
        raise RuntimeError(
            "FreeCAD MCP RPC did not answer on 127.0.0.1:9875"
        )
    result = rpc.execute_code(code)
    if not result.get("success"):
        raise RuntimeError(
            f"FreeCAD execution failed: "
            f"{result.get('error', result)}"
        )
    message = result.get("message", "")
    output = message.rsplit("Output: ", 1)[-1].strip()
    if output:
        print(output)
    return output


def blender_command(
    command_type: str,
    params: dict,
    timeout: int = 300,
) -> dict:
    payload = json.dumps(
        {
            "type": command_type,
            "params": params,
        }
    ).encode()
    with socket.create_connection(
        BLENDER_ADDRESS,
        timeout=5,
    ) as client:
        client.settimeout(timeout)
        client.sendall(payload)
        response = b""
        while True:
            chunk = client.recv(65536)
            if not chunk:
                break
            response += chunk
            try:
                decoded = json.loads(response)
                break
            except json.JSONDecodeError:
                continue
        else:
            decoded = None
    if not response:
        raise RuntimeError("Blender MCP returned no response")
    if "decoded" not in locals():
        raise RuntimeError(
            f"Blender MCP returned invalid JSON: "
            f"{response[:500]!r}"
        )
    if decoded.get("status") != "success":
        raise RuntimeError(
            f"Blender MCP command failed: {decoded}"
        )
    return decoded["result"]


def checked_blender_script(
    path: Path,
    environment: dict[str, str] | None = None,
) -> str:
    lines = ["import os"]
    for name, value in (environment or {}).items():
        lines.append(
            f"os.environ[{name!r}] = {value!r}"
        )
    lines.append(
        "exec(compile("
        f"open({str(path)!r}, encoding='utf-8').read(), "
        f"{str(path)!r}, 'exec'))"
    )
    result = blender_command(
        "execute_code",
        {"code": "\n".join(lines)},
    )
    if not result.get("executed"):
        raise RuntimeError(
            f"Blender did not execute {path}: {result}"
        )
    output = result.get("result", "").strip()
    if output:
        print(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
    )
    parser.add_argument(
        "--negative",
        default=DEFAULT_NEGATIVE,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260704,
    )
    parser.add_argument(
        "--skip-comfy",
        action="store_true",
        help="Stop after the Blender beauty/depth render",
    )
    parser.add_argument(
        "--no-show-result",
        action="store_true",
        help=(
            "Do not open the generated ComfyUI PNG "
            "in the desktop image viewer"
        ),
    )
    parser.add_argument(
        "--preserve-blender-scene",
        action="store_true",
        help=(
            "Keep unrelated Blender objects instead "
            "of starting the demo import clean"
        ),
    )
    args = parser.parse_args()

    terrain_script = (
        ROOT / "scripts" / "build-cliff-house-terrain.py"
    )
    export_script = (
        ROOT / "scripts" / "export-freecad-for-blender.py"
    )
    freecad_code = (
        "import os\n"
        "import FreeCAD as App\n"
        "if 'CliffHouseRebuild' not in App.listDocuments():\n"
        "    raise RuntimeError('CliffHouseRebuild is not open')\n"
        "massing_document = App.getDocument('CliffHouseRebuild')\n"
        f"required_massing = {MASSING_NAMES!r}\n"
        "missing_massing = [name for name in required_massing "
        "if massing_document.getObject(name) is None]\n"
        "if missing_massing:\n"
        "    raise RuntimeError(f'Missing approved massing: {missing_massing}')\n"
        f"expected_spec_id = {MASSING_SPEC_ID!r}\n"
        "invalid_massing = []\n"
        "for name in required_massing:\n"
        "    obj = massing_document.getObject(name)\n"
        "    shape = getattr(obj, 'Shape', None)\n"
        "    if (getattr(obj, 'MassingSpecId', '') != expected_spec_id "
        "or shape is None or shape.isNull() or shape.Volume <= 0):\n"
        "        invalid_massing.append(name)\n"
        "if invalid_massing:\n"
        "    raise RuntimeError(f'Invalid approved massing: {invalid_massing}')\n"
        "print(f'MASSING_PREFLIGHT_OK objects={len(required_massing)} "
        "spec={expected_spec_id}')\n"
        f"exec(compile(open({str(terrain_script)!r}, encoding='utf-8').read(), "
        f"{str(terrain_script)!r}, 'exec'))\n"
        "os.environ['AES_FREECAD_DOCUMENT'] = 'CliffHouseRebuild'\n"
        f"os.environ['AES_FREECAD_EXPORT_DIR'] = {str(BUNDLE_DIR)!r}\n"
        f"exec(compile(open({str(export_script)!r}, encoding='utf-8').read(), "
        f"{str(export_script)!r}, 'exec'))"
    )
    freecad_output = checked_freecad_execution(
        freecad_code
    )
    for marker in (
        "MASSING_PREFLIGHT_OK",
        "TERRAIN_BUILD_OK=",
        "FREECAD_EXPORT_OK=",
    ):
        if marker not in freecad_output:
            raise RuntimeError(
                f"Missing FreeCAD success marker: {marker}"
            )

    import_output = checked_blender_script(
        ROOT / "scripts" / "import-freecad-bundle.py",
        {
            "AES_FREECAD_EXPORT_DIR": str(BUNDLE_DIR),
            "AES_BLENDER_CLEAR_SCENE": (
                "0"
                if args.preserve_blender_scene
                else "1"
            ),
        },
    )
    if "BLENDER_IMPORT_OK=" not in import_output:
        raise RuntimeError(
            "Missing Blender import success marker"
        )

    render_output = checked_blender_script(
        ROOT / "scripts" / "render-freecad-import.py",
    )
    if "BLENDER_RENDER_OK" not in render_output:
        raise RuntimeError(
            "Missing Blender render success marker"
        )
    beauty = RENDER_DIR / "freecad-beauty.png"
    depth = RENDER_DIR / "freecad-depth.png"
    for image in (beauty, depth):
        if not image.is_file() or image.stat().st_size == 0:
            raise RuntimeError(
                f"Blender output is missing or empty: {image}"
            )

    if args.skip_comfy:
        print(
            "CLIFF_HOUSE_VISUALIZATION_OK "
            f"beauty={beauty} depth={depth} comfy=skipped"
        )
        return

    comfy_python = (
        ROOT / "comfyui" / ".venv" / "bin" / "python"
    )
    comfy_script = (
        ROOT / "scripts" / "comfy-depth-render.py"
    )
    completed = subprocess.run(
        [
            str(comfy_python),
            str(comfy_script),
            "--beauty",
            str(beauty),
            "--depth",
            str(depth),
            "--prompt",
            args.prompt,
            "--negative",
            args.negative,
            "--seed",
            str(args.seed),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    comfy_output = completed.stdout.strip()
    if comfy_output:
        print(comfy_output)
    for marker in ("COMFY_IMAGE_OK=", "COMFY_DEPTH_OK"):
        if marker not in comfy_output:
            raise RuntimeError(
                f"Missing ComfyUI success marker: {marker}"
            )
    output_match = re.search(r"outputs=([^\n]+)", comfy_output)
    output_paths = (
        [
            Path(value)
            for value in output_match.group(1).split(",")
        ]
        if output_match
        else []
    )
    if not args.no_show_result and output_paths:
        display_path = output_paths[-1]
        if display_path.is_file():
            desktop_environment = os.environ.copy()
            uid = os.getuid()
            desktop_environment.setdefault("DISPLAY", ":1")
            desktop_environment.setdefault(
                "XAUTHORITY",
                f"/run/user/{uid}/gdm/Xauthority",
            )
            desktop_environment.setdefault(
                "DBUS_SESSION_BUS_ADDRESS",
                f"unix:path=/run/user/{uid}/bus",
            )
            viewer_commands = []
            eog = shutil.which("eog")
            if eog:
                viewer_commands.append(
                    ([eog, "--new-instance", str(display_path)], "eog")
                )
            xdg_open = shutil.which("xdg-open")
            if xdg_open:
                viewer_commands.append(
                    ([xdg_open, str(display_path)], "xdg-open")
                )
            opened_with = None
            for command, viewer_name in viewer_commands:
                process = subprocess.Popen(
                    command,
                    env=desktop_environment,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                time.sleep(1.0)
                return_code = process.poll()
                if return_code is None or return_code == 0:
                    opened_with = viewer_name
                    break
            if opened_with:
                print(
                    f"COMFY_RESULT_OPENED={display_path} "
                    f"viewer={opened_with}"
                )
            else:
                print(
                    "COMFY_RESULT_OPEN_WARNING="
                    f"no image viewer accepted {display_path}; "
                    "open it manually"
                )
    print(
        "CLIFF_HOUSE_VISUALIZATION_OK "
        f"beauty={beauty} depth={depth}"
    )


if __name__ == "__main__":
    main()
