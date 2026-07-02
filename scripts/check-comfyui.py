#!/usr/bin/env python3
"""Check the local ComfyUI HTTP API."""
import json
import sys
from urllib.request import urlopen

try:
    with urlopen("http://127.0.0.1:8188/system_stats", timeout=5) as response:
        data = json.load(response)
    devices = data.get("devices", [])
    device = devices[0] if devices else {}
    print("ComfyUI API is healthy on 127.0.0.1:8188 "
          f"(device={device.get('name')!r}, type={device.get('type')!r})")
except Exception as exc:
    print(f"ComfyUI API is unavailable: {exc}", file=sys.stderr)
    raise SystemExit(1)
