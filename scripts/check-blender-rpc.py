#!/usr/bin/env python3
"""Check the Blender MCP add-on socket without starting an MCP client."""
import json
import socket
import sys

request = json.dumps({"type": "get_scene_info", "params": {}}).encode()
try:
    with socket.create_connection(("127.0.0.1", 9876), timeout=3) as client:
        client.settimeout(10)
        client.sendall(request)
        payload = b""
        while True:
            payload += client.recv(65536)
            try:
                response = json.loads(payload)
                break
            except json.JSONDecodeError:
                continue
    if response.get("status") != "success":
        raise RuntimeError(response)
    scene = response.get("result", {})
    print("Blender MCP RPC is healthy on 127.0.0.1:9876 "
          f"(scene={scene.get('name')!r}, objects={scene.get('object_count')})")
except Exception as exc:
    print(f"Blender MCP RPC is unavailable: {exc}", file=sys.stderr)
    raise SystemExit(1)
