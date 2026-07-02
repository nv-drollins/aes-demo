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

## Blender and Blender MCP

Ubuntu's ARM64 Blender 4.0.2 package is used. The GB10 is visible to Blender's Cycles CUDA backend; the deterministic project tests currently use Eevee for speed.

The upstream `ahujasid/blender-mcp` checkout lives at `blender-mcp/` and is ignored. Its `addon.py` is installed as the user add-on module `blender_mcp`, enabled in Blender preferences, and configured to auto-start on `127.0.0.1:9876`. Telemetry consent is disabled.

Hermes launches the Blender MCP stdio server using managed Python 3.11 through `uvx`. Its environment sets `DISABLE_TELEMETRY=true`, `BLENDER_HOST=127.0.0.1`, and `BLENDER_PORT=9876`.

Install or refresh it with:

```bash
./scripts/install-blender-mcp.sh
```

Blender must run with its GUI for MCP commands, because add-on commands are dispatched on Blender's main thread. Headless `blender -b` is suitable for standalone render tests but not for the MCP socket.

Diagnostics:

```bash
./scripts/start-blender.sh
./scripts/check-blender-rpc.py
hermes mcp test blender
blender -b --python scripts/blender-smoke-test.py
```

## FreeCAD-to-Blender interchange

The bridge intentionally treats FreeCAD as the geometry authority and Blender as a visualization copy. It does not try to make Blender meshes editable CAD solids.

Each visible FreeCAD shape is tessellated to an individual OBJ. A JSON manifest preserves its internal name, label, FreeCAD type, color, bounding box, source document, source units, and the `0.001` millimetre-to-metre Blender scale. Blender imports these objects into a dedicated collection and stores FreeCAD identity fields as custom properties.

Temporary interchange files live at `/tmp/aes-demo-freecad-export`. Override this in both applications with the `AES_FREECAD_EXPORT_DIR` environment variable if needed.

## ComfyUI

ComfyUI is cloned under `comfyui/` with an isolated `.venv`; both are ignored. Its stack uses the official PyTorch CUDA 13 wheels for ARM64/Blackwell and has been verified on `NVIDIA GB10`.

The local models are:

```text
models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors
models/controlnet/control_v11f1p_sd15_depth_fp16.safetensors
```

Install the runtime and models with:

```bash
./scripts/install-comfyui.sh
```

The service listens only on `127.0.0.1:8188`. Blender and ComfyUI are connected by the checked-in REST client, not by an MCP server: it uploads the beauty/depth images, queues the versioned graph, polls prompt history, and downloads generated outputs.

Diagnostics:

```bash
./scripts/start-comfyui.sh
./scripts/check-comfyui.py
comfyui/.venv/bin/python scripts/comfy-api-smoke.py
```
