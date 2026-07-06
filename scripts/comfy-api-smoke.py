#!/usr/bin/env python3
"""Upload Blender beauty/depth images and execute a no-model ComfyUI API graph."""
import argparse
from pathlib import Path
import time
import uuid
import requests

BASE_URL = "http://127.0.0.1:8188"

def upload(path, remote_name):
    with path.open("rb") as image:
        response = requests.post(
            f"{BASE_URL}/upload/image",
            files={"image": (remote_name, image, "image/png")},
            data={"type": "input", "subfolder": "aec-demo", "overwrite": "true"},
            timeout=60,
        )
    response.raise_for_status()
    uploaded = response.json()
    return f"{uploaded.get('subfolder', '')}/{uploaded['name']}".lstrip("/")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--beauty", type=Path, default=Path("/tmp/aec-demo-render/freecad-beauty.png"))
    parser.add_argument("--depth", type=Path, default=Path("/tmp/aec-demo-render/freecad-depth.png"))
    args = parser.parse_args()
    beauty = upload(args.beauty, "freecad-beauty.png")
    depth = upload(args.depth, "freecad-depth.png")
    graph = {
        "1": {"class_type": "LoadImage", "inputs": {"image": beauty}},
        "2": {"class_type": "SaveImage", "inputs": {"images": ["1", 0], "filename_prefix": "aec-demo/api-beauty"}},
        "3": {"class_type": "LoadImage", "inputs": {"image": depth}},
        "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 0], "filename_prefix": "aec-demo/api-depth"}},
    }
    response = requests.post(
        f"{BASE_URL}/prompt",
        json={"prompt": graph, "client_id": str(uuid.uuid4())},
        timeout=30,
    )
    response.raise_for_status()
    queued = response.json()
    if queued.get("node_errors"):
        raise RuntimeError(queued["node_errors"])
    prompt_id = queued["prompt_id"]
    for _ in range(120):
        history = requests.get(f"{BASE_URL}/history/{prompt_id}", timeout=30).json()
        if prompt_id in history:
            record = history[prompt_id]
            messages = record.get("status", {}).get("messages", [])
            errors = [m for m in messages if m and m[0] == "execution_error"]
            if errors:
                raise RuntimeError(errors)
            output_names = [image["filename"] for node in record.get("outputs", {}).values()
                            for image in node.get("images", [])]
            print(f"COMFY_API_OK prompt_id={prompt_id} inputs={beauty},{depth} outputs={','.join(output_names)}")
            return
        time.sleep(0.5)
    raise TimeoutError(f"ComfyUI prompt {prompt_id} did not finish")

if __name__ == "__main__":
    main()
