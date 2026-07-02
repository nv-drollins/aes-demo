# Local stack notes

## Inference

- Runtime: Ollama 0.31.1
- Model: `qwen3.6:latest`
- Architecture: 36B mixture-of-experts
- Quantization: Q4_K_M
- Context length: 262,144 tokens
- Endpoint: `http://localhost:11434/v1`
- Capabilities: completion, vision, tools, thinking

Hermes configuration lives in `~/.hermes/config.yaml` and points its main model at the local Ollama endpoint.

## FreeCAD

The ARM64 AppImage is stored under `apps/` and is excluded from Git. The FreeCAD MCP add-on is linked from the cloned `freecad-mcp` repository into FreeCAD's user module directory:

```text
~/.local/share/FreeCAD/v1-1/Mod/FreeCADMCP
```

The add-on auto-starts an XML-RPC server on `127.0.0.1:9875`. Remote connections are disabled.

## Hermes MCP

Hermes starts the cloned Python MCP server over stdio using `uv`. The server connects to FreeCAD's local XML-RPC endpoint.

Useful diagnostics:

```bash
./scripts/check-freecad-rpc.py
hermes mcp test freecad
```
