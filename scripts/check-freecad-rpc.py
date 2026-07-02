#!/usr/bin/env python3
import sys
import xmlrpc.client


try:
    rpc = xmlrpc.client.ServerProxy("http://127.0.0.1:9875", allow_none=True)
    if rpc.ping():
        print("FreeCAD MCP RPC is healthy on 127.0.0.1:9875")
        raise SystemExit(0)
except Exception as exc:
    print(f"FreeCAD MCP RPC is unavailable: {exc}", file=sys.stderr)

raise SystemExit(1)
