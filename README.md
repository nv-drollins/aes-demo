# aes-demo

A fully local AI-to-CAD-to-render proof of concept for NVIDIA DGX Spark. Hermes uses a local Qwen model to control FreeCAD and Blender through MCP; Blender turns CAD geometry into beauty/depth renders; ComfyUI uses those images for depth-guided architectural visualization.

```text
Qwen3.6 (Ollama, local)
  -> Hermes Agent
     |-> FreeCAD MCP -> FreeCAD add-on (XML-RPC 127.0.0.1:9875)
     `-> Blender MCP -> Blender add-on (TCP 127.0.0.1:9876)

FreeCAD objects -> OBJ meshes + JSON metadata -> Blender
Blender beauty + 16-bit depth -> ComfyUI REST API (127.0.0.1:8188)
  -> SD 1.5 img2img + Depth ControlNet -> architectural image
```

Rhino is not required. No cloud inference account or model API key is required.

## Verified on the Spark

- Ubuntu ARM64 on NVIDIA GB10
- Ollama 0.31.1 with local `qwen3.6:latest`
- Hermes Agent 0.18.0
- FreeCAD 1.1.1 and 14 FreeCAD MCP tools
- Blender 4.0.2 and 22 Blender MCP tools
- PyTorch 2.12.1 + CUDA 13.0 in an isolated ComfyUI environment
- Hermes read/write/render tests against both desktop applications
- Four live FreeCAD objects exported and imported into Blender with names, types, colors, bounds, and unit scale
- 1024x768 Blender beauty image and 16-bit depth pass
- ComfyUI upload, queue, history, output retrieval, and a real 768x576 depth-ControlNet generation

## Start everything

```bash
cd /home/nvidia/aes-demo
./scripts/start-aes-demo.sh
```

This starts FreeCAD, Blender, and ComfyUI, verifies all three local endpoints, then opens standard Hermes chat. ComfyUI is available in the Spark browser at <http://127.0.0.1:8188>.

The stack launcher registers the source-controlled skill library with Hermes automatically. To register it without starting the applications, run:

```bash
./scripts/register-hermes-skills.py
```

The repository currently provides four phase skills: `ingest-rhino-reference`, `rebuild-freecad-reference`, `handoff-freecad-blender`, and `visualize-blender-comfyui`. They appear in Hermes skill search and slash-command completion after restarting Hermes or running `/reload-skills`.

Use `hermes chat`, not `hermes -z`, for MCP work with Hermes 0.18.0. The one-shot path can snapshot tools before background MCP discovery finishes.

Individual services and checks:

```bash
./scripts/start-freecad.sh
./scripts/start-blender.sh
./scripts/start-comfyui.sh
./scripts/check-freecad-rpc.py
./scripts/check-blender-rpc.py
./scripts/check-comfyui.py
hermes mcp test freecad
hermes mcp test blender
```

## Run the pipeline

Use the prompt ladder in [PROMPT_TESTS.md](PROMPT_TESTS.md) to build and verify a FreeCAD massing model. The bridge is made of three scripts designed to be invoked by Hermes through the relevant MCP:

1. `scripts/export-freecad-for-blender.py` runs inside FreeCAD and writes individual OBJ meshes plus `manifest.json` to `/tmp/aes-demo-freecad-export`.
2. `scripts/import-freecad-bundle.py` runs inside Blender, imports the bundle into the `FreeCAD Import` collection, preserves metadata as custom properties, converts millimetres to metres, and saves `/tmp/aes-demo-freecad-import.blend`.
3. `scripts/render-freecad-import.py` frames the collection and writes beauty, 16-bit depth, and `.blend` outputs under `/tmp/aes-demo-render`.

Then run the local ComfyUI workflow:

```bash
comfyui/.venv/bin/python scripts/comfy-depth-render.py \
  --prompt "professional architectural visualization, timber and concrete pavilion, landscaped site, soft daylight"
```

The versioned API graph is [workflows/freecad-depth-api.json](workflows/freecad-depth-api.json). Generated images are copied to `outputs/comfyui/` and deliberately excluded from Git.

A fast no-model REST test is also available:

```bash
comfyui/.venv/bin/python scripts/comfy-api-smoke.py
```

## Installation helpers

FreeCAD/Hermes setup details are in [LOCAL_SETUP.md](LOCAL_SETUP.md). For the added rendering stack:

```bash
./scripts/install-blender-mcp.sh
./scripts/install-comfyui.sh
```

The ComfyUI installer follows NVIDIA's DGX Spark CUDA 13 approach and downloads two public local models: the SD 1.5 FP16 checkpoint and the SD 1.5 FP16 depth ControlNet. Expect roughly 5 GB for the Python/CUDA environment and models.

## Safety and repository scope

The MCP code-execution tools can run arbitrary Python inside FreeCAD and Blender. Keep the applications and MCP ports local, save work before exploratory prompts, and inspect unfamiliar code before asking Hermes to execute it. Blender MCP telemetry is disabled in both its add-on preference and MCP process environment.

## Rhino reference curves without Rhino

The upstream Rhino 8 source-curve template can be read locally on the Spark and reconstructed as native FreeCAD reference geometry:

```bash
./scripts/import-rhino-reference.sh
```

This uses the open-source `rhino3dm` reader at runtime, preserves layer and curve metadata, converts metres to millimetres, and creates `CliffHouseReference` in the live FreeCAD GUI. See [REFERENCE_MODEL_WORKFLOW.md](REFERENCE_MODEL_WORKFLOW.md) for the Hermes audit and rebuild-forward prompts. The upstream checkout's `.3dm` contains planning/terrain curves rather than a finished building, so this workflow provides a controlled starting reference rather than a one-click final-model conversion.

Downloaded applications, upstream checkouts, model weights, virtual environments, runtime logs, CAD outputs, and generated images are ignored. This public repository contains only reproducible scripts, configuration examples, prompts, and workflow JSON.

## Upstream projects

- [stwagstaff/2026_aec_cptx_demo](https://github.com/stwagstaff/2026_aec_cptx_demo) — source workflow and prompt-system reference
- [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) — FreeCAD MCP server and add-on
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — Blender MCP server and add-on
- [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) — local node-based image pipeline and REST API
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — agent runtime
