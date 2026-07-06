#!/usr/bin/env python3
"""Archive prior outputs and reset live application state for a clean recording."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import socket
import subprocess
import urllib.error
import urllib.request
import xmlrpc.client


ROOT = Path(__file__).resolve().parent.parent
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
ARCHIVE = ROOT / "outputs" / "demo-archives" / STAMP


def unique_destination(category: str, name: str) -> Path:
    destination = ARCHIVE / category / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        return destination
    index = 2
    while True:
        candidate = destination.with_name(
            f"{destination.stem}-{index}{destination.suffix}"
        )
        if not candidate.exists():
            return candidate
        index += 1


def archive_path(path: Path, category: str) -> bool:
    if not path.exists():
        return False
    destination = unique_destination(category, path.name)
    shutil.move(str(path), str(destination))
    print(f"ARCHIVED={path} -> {destination}")
    return True


def reset_freecad() -> None:
    subprocess.run(
        [str(ROOT / "scripts" / "reset-reference-workflow.sh")],
        cwd=ROOT,
        check=True,
    )
    try:
        rpc = xmlrpc.client.ServerProxy(
            "http://127.0.0.1:9875",
            allow_none=True,
        )
        if not rpc.ping():
            raise RuntimeError("FreeCAD MCP RPC did not answer")
    except Exception as exc:
        print(f"FREECAD_RECORDING_RESET_SKIPPED={exc}")
        return

    code = """for name in ('PromptTest', 'HermesSmokeTest'):
    if name in App.listDocuments():
        App.closeDocument(name)
        print('CLOSED_DOCUMENT=' + name)
"""
    result = rpc.execute_code(code)
    if not result.get("success"):
        raise RuntimeError(
            f"FreeCAD recording reset failed: "
            f"{result.get('error', result)}"
        )
    output = result.get("message", "").rsplit(
        "Output: ",
        1,
    )[-1].strip()
    if output:
        print(output)
    print(
        "FREECAD_RECORDING_RESET_OK="
        f"documents={rpc.list_documents()}"
    )


def blender_command(code: str) -> str:
    payload = json.dumps(
        {
            "type": "execute_code",
            "params": {"code": code},
        }
    ).encode()
    try:
        with socket.create_connection(
            ("127.0.0.1", 9876),
            timeout=3,
        ) as client:
            client.settimeout(30)
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
    except OSError as exc:
        print(f"BLENDER_RECORDING_RESET_SKIPPED={exc}")
        return ""

    if not response:
        raise RuntimeError("Blender MCP returned no response")
    if "decoded" not in locals():
        raise RuntimeError(
            f"Blender MCP returned invalid JSON: "
            f"{response[:500]!r}"
        )
    if decoded.get("status") != "success":
        raise RuntimeError(
            f"Blender recording reset failed: {decoded}"
        )
    result = decoded["result"]
    if not result.get("executed"):
        raise RuntimeError(
            f"Blender did not execute reset: {result}"
        )
    output = result.get("result", "").strip()
    if output:
        print(output)
    return output


def reset_blender() -> None:
    code = """for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for collection in list(bpy.data.collections):
    if collection.name == 'FreeCAD Import':
        bpy.data.collections.remove(collection)
for material in list(bpy.data.materials):
    if material.name.startswith(('AEC::', 'FreeCAD::')):
        bpy.data.materials.remove(material)
scene = bpy.context.scene
for key in ('freecad_manifest', 'freecad_source_document'):
    if key in scene:
        del scene[key]
scene.camera = None
scene.use_nodes = False
print('BLENDER_RECORDING_RESET_OK objects=%d' % len(bpy.data.objects))
"""
    blender_command(code)


def reset_comfyui_history() -> None:
    request = urllib.request.Request(
        "http://127.0.0.1:8188/history",
        data=json.dumps({"clear": True}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"ComfyUI history reset returned "
                    f"HTTP {response.status}"
                )
    except (urllib.error.URLError, OSError) as exc:
        print(f"COMFYUI_HISTORY_RESET_SKIPPED={exc}")
        return
    print("COMFYUI_HISTORY_RESET_OK")


def main() -> None:
    archived = 0

    for path in (
        ROOT / "PromptTest.FCStd",
        ROOT / "HermesSmokeTest.FCStd",
        ROOT / "HermesSmokeTest.png",
        Path("/tmp/aec-demo-freecad-import.blend"),
        Path("/tmp/aec-demo-freecad-import.blend1"),
        Path("/tmp/aec-demo-cliff-house-reference.png"),
    ):
        archived += archive_path(path, "individual-files")

    for directory in (
        Path("/tmp/aec-demo-render"),
        Path("/tmp/aec-demo-cliff-house-export"),
        Path("/tmp/aec-demo-freecad-export"),
        Path("/tmp/aec-demo-regression-export"),
    ):
        archived += archive_path(directory, "runtime-directories")

    source_directory = (
        ROOT / "source_models" / "cliff_house"
    )
    if source_directory.is_dir():
        for path in sorted(source_directory.glob("cliff_house_*")):
            archived += archive_path(path, "freecad-models")

    client_output = ROOT / "outputs" / "comfyui"
    if client_output.is_dir():
        for path in sorted(client_output.glob("*.png")):
            archived += archive_path(
                path,
                "comfyui-client",
            )

    server_output = (
        ROOT / "comfyui" / "output" / "aec-demo"
    )
    if server_output.is_dir():
        for path in sorted(server_output.glob("*.png")):
            archived += archive_path(
                path,
                "comfyui-server",
            )

    server_input = (
        ROOT / "comfyui" / "input" / "aec-demo"
    )
    if server_input.is_dir():
        for name in (
            "freecad-beauty.png",
            "freecad-depth.png",
        ):
            archived += archive_path(
                server_input / name,
                "comfyui-input",
            )

    reset_freecad()
    reset_blender()
    reset_comfyui_history()

    print(
        f"RECORDING_DEMO_RESET_OK archive={ARCHIVE} "
        f"archived_items={archived}"
    )


if __name__ == "__main__":
    main()
