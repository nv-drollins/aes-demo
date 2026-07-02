# aes-demo

Local AI-to-CAD proof of concept for NVIDIA DGX Spark.

The current milestone connects a locally hosted model to FreeCAD through Hermes Agent and the FreeCAD MCP server. Blender, ComfyUI, Rhino, and rendering automation are intentionally out of scope for now.

```text
Qwen3.6 (Ollama, local)
  -> Hermes Agent
     -> FreeCAD MCP (stdio)
        -> FreeCAD MCP add-on (XML-RPC on localhost:9875)
           -> FreeCAD 1.1.1
```

## Verified state

- DGX Spark / Ubuntu ARM64
- Ollama with `qwen3.6:latest` running on the GPU
- Hermes Agent configured for `http://localhost:11434/v1`
- FreeCAD 1.1.1 ARM64 AppImage
- 14 FreeCAD MCP tools discovered by Hermes
- Read test passed: Hermes listed the open `HermesSmokeTest` document
- Write test passed: Hermes created and verified `HermesLocalCylinder`

No cloud inference account or model API key is required.

## Start

```bash
cd /home/nvidia/aes-demo
./scripts/start-hermes.sh
```

This starts FreeCAD if necessary, waits for the add-on's RPC server, and opens standard Hermes chat.

Use `hermes chat`, not `hermes -z`, for MCP work with Hermes 0.18.0. The one-shot path can take its tool snapshot before background MCP discovery finishes.

## Test

Copy the prompts in [PROMPT_TESTS.md](PROMPT_TESTS.md) into Hermes in order. They progress from a read-only connection check to structured modeling, inspection, viewport feedback, and saving.

Health checks:

```bash
./scripts/check-freecad-rpc.py
hermes mcp test freecad
ollama list
ollama ps
```

## Upstream projects

- [stwagstaff/2026_aec_cptx_demo](https://github.com/stwagstaff/2026_aec_cptx_demo) — source workflow and prompt-system reference
- [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) — FreeCAD MCP server and add-on
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — agent runtime

The upstream repositories and downloaded FreeCAD binary are local dependencies and are deliberately excluded from this repository.
