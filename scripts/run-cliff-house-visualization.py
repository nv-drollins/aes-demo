#!/usr/bin/env python3
"""Run the CliffHouseRebuild -> Blender -> ComfyUI visualization demo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import subprocess
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
FREECAD_URL = "http://127.0.0.1:9875"
BLENDER_ADDRESS = ("127.0.0.1", 9876)
BUNDLE_DIR = Path("/tmp/aes-demo-cliff-house-export")
RENDER_DIR = Path("/tmp/aes-demo-render")
DEFAULT_PROMPT = (
    "architectural site concept visualization, modernist cliff house "
    "planning study on a steep coastal hillside, dark concrete building "
    "pad, garage and driveway, broad patio terrace, ocean-facing landscape, "
    "realistic green terrain, soft clear daylight, aerial oblique view, "
    "preserve the site layout and topography, professional competition rendering"
)
DEFAULT_NEGATIVE = (
    "flat grey square, blank image, distorted terrain, warped site plan, "
    "floating geometry, extra roads, text, labels, watermark, people, "
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
    args = parser.parse_args()

    terrain_script = (
        ROOT / "scripts" / "build-cliff-house-terrain.py"
    )
    export_script = (
        ROOT / "scripts" / "export-freecad-for-blender.py"
    )
    freecad_code = (
        "import os\n"
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
    if "COMFY_DEPTH_OK" not in comfy_output:
        raise RuntimeError(
            "Missing ComfyUI success marker"
        )
    print(
        "CLIFF_HOUSE_VISUALIZATION_OK "
        f"beauty={beauty} depth={depth}"
    )


if __name__ == "__main__":
    main()
