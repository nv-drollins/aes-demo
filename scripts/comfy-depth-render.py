#!/usr/bin/env python3
"""Submit Blender beauty/depth renders to the local ComfyUI depth-ControlNet graph."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import time
import uuid
import requests
from PIL import Image, ImageStat

BASE_URL = "http://127.0.0.1:8188"
ROOT = Path(__file__).resolve().parent.parent


def validate_image_bytes(content, label):
    if not content:
        raise RuntimeError(f"ComfyUI returned an empty image for {label}")
    try:
        with Image.open(BytesIO(content)) as probe:
            probe.verify()
        with Image.open(BytesIO(content)) as decoded:
            width, height = decoded.size
            rgb = decoded.convert("RGB")
    except Exception as exc:
        raise RuntimeError(
            f"ComfyUI returned an invalid image for {label}: {exc}"
        ) from exc
    if width < 64 or height < 64:
        raise RuntimeError(
            f"ComfyUI image is unexpectedly small: {width}x{height}"
        )
    statistics = ImageStat.Stat(rgb)
    means = tuple(float(value) for value in statistics.mean)
    deviations = tuple(float(value) for value in statistics.stddev)
    extrema = rgb.getextrema()
    dynamic_range = max(high for _, high in extrema) - min(
        low for low, _ in extrema
    )
    if max(deviations) < 1.0 or dynamic_range < 8:
        raise RuntimeError(
            "ComfyUI image appears blank or nearly uniform: "
            f"mean={means} stddev={deviations} range={dynamic_range}"
        )
    return {
        "width": width,
        "height": height,
        "mean": means,
        "stddev": deviations,
        "dynamic_range": dynamic_range,
    }


def report_image_ok(path, statistics):
    mean = ",".join(f"{value:.2f}" for value in statistics["mean"])
    stddev = ",".join(
        f"{value:.2f}" for value in statistics["stddev"]
    )
    print(
        f"COMFY_IMAGE_OK={path} "
        f"size={statistics['width']}x{statistics['height']} "
        f"mean_rgb=[{mean}] stddev_rgb=[{stddev}] "
        f"range={statistics['dynamic_range']}"
    )


def upload(path, remote_name):
    with path.open("rb") as image:
        response = requests.post(
            f"{BASE_URL}/upload/image",
            files={"image": (remote_name, image, "image/png")},
            data={"type": "input", "subfolder": "aes-demo", "overwrite": "true"},
            timeout=120,
        )
    response.raise_for_status()
    uploaded = response.json()
    return f"{uploaded.get('subfolder', '')}/{uploaded['name']}".lstrip("/")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--beauty", type=Path, default=Path("/tmp/aes-demo-render/freecad-beauty.png"))
    parser.add_argument("--depth", type=Path, default=Path("/tmp/aes-demo-render/freecad-depth.png"))
    parser.add_argument("--prompt", default="professional architectural visualization, contemporary small pavilion, realistic concrete and timber materials, landscaped site, soft daylight, physically based rendering, highly detailed")
    parser.add_argument("--negative", default="distorted architecture, warped walls, extra buildings, text, watermark, people, low resolution, blurry, oversaturated")
    parser.add_argument("--seed", type=int, default=20260702)
    parser.add_argument("--control-strength", type=float, default=1.0)
    parser.add_argument("--control-end", type=float, default=1.0)
    parser.add_argument("--denoise", type=float, default=0.55)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "comfyui")
    parser.add_argument(
        "--validate-only",
        type=Path,
        help="Validate an existing generated image without calling ComfyUI",
    )
    args = parser.parse_args()
    if args.validate_only:
        statistics = validate_image_bytes(
            args.validate_only.read_bytes(),
            str(args.validate_only),
        )
        report_image_ok(args.validate_only, statistics)
        return
    graph = json.loads((ROOT / "workflows" / "freecad-depth-api.json").read_text())
    graph["4"]["inputs"]["image"] = upload(args.beauty, "freecad-beauty.png")
    graph["7"]["inputs"]["image"] = upload(args.depth, "freecad-depth.png")
    graph["2"]["inputs"]["text"] = args.prompt
    graph["3"]["inputs"]["text"] = args.negative
    graph["11"]["inputs"]["seed"] = args.seed
    graph["10"]["inputs"]["strength"] = args.control_strength
    graph["10"]["inputs"]["end_percent"] = args.control_end
    graph["11"]["inputs"]["denoise"] = args.denoise
    response = requests.post(f"{BASE_URL}/prompt", json={"prompt": graph, "client_id": str(uuid.uuid4())}, timeout=30)
    response.raise_for_status()
    queued = response.json()
    if queued.get("node_errors"):
        raise RuntimeError(queued["node_errors"])
    prompt_id = queued["prompt_id"]
    for _ in range(1800):
        history = requests.get(f"{BASE_URL}/history/{prompt_id}", timeout=30).json()
        if prompt_id not in history:
            time.sleep(0.5)
            continue
        record = history[prompt_id]
        messages = record.get("status", {}).get("messages", [])
        errors = [message for message in messages if message and message[0] == "execution_error"]
        if errors:
            raise RuntimeError(errors)
        images = [image for output in record.get("outputs", {}).values() for image in output.get("images", [])]
        if not images:
            raise RuntimeError(f"Prompt completed without an image: {record}")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        saved = []
        for image in images:
            view_response = requests.get(
                f"{BASE_URL}/view", params=image, timeout=120
            )
            view_response.raise_for_status()
            content = view_response.content
            path = args.output_dir / image["filename"]
            statistics = validate_image_bytes(content, str(path))
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_bytes(content)
            temporary.replace(path)
            report_image_ok(path, statistics)
            saved.append(str(path))
        print(f"COMFY_DEPTH_OK prompt_id={prompt_id} outputs={','.join(saved)}")
        return
    raise TimeoutError(f"ComfyUI prompt {prompt_id} did not finish")

if __name__ == "__main__":
    main()
