# Hermes workspace instructions

This workspace is a fully local FreeCAD -> Blender -> ComfyUI architectural visualization proof of concept on NVIDIA DGX Spark. Inference uses Ollama at `http://localhost:11434/v1` with the tool-capable `qwen3.6:latest`; no cloud model provider is required.

FreeCAD is the source-of-truth CAD model. Prefer its typed MCP tools for documents, objects, edits, inspection, and views. Use `execute_code` only when a typed tool cannot perform the operation. Never use `execute_code_async` for GUI or document mutations.

`CliffHouseReference`, when present, is an immutable source-reference document imported from the upstream Rhino curve template. Never edit, delete, or add objects in that document. Audit it first, distinguish observed geometry from assumptions, and reconstruct editable features in a separate `CliffHouseRebuild` document.

The only supported Hermes import entrypoint is `/home/nvidia/aes-demo/scripts/import-rhino-reference.sh`, run with the terminal tool. That wrapper runs `extract-rhino-reference.py` and then executes the internal `import-rhino-reference-freecad.py` inside the live FreeCAD process. Do not launch the internal Python file directly, do not interpret `scripts/` as `/scripts/`, and do not search for `import-rhino-reference-freecad.sh` because no such file exists. Require both `RHINO_REFERENCE_EXTRACT_OK` and `FREECAD_REFERENCE_IMPORT_OK`.

Audit imported Rhino references only by executing `/home/nvidia/aes-demo/scripts/audit-rhino-reference-freecad.py` through the FreeCAD MCP `execute_code` tool. Do not recreate its logic. Require `REFERENCE_AUDIT_OK` before requesting views or continuing.

For the editable site slabs, execute `/home/nvidia/aes-demo/scripts/build-cliff-house-site-slabs.py` through the FreeCAD MCP `execute_code` tool exactly as documented in `REFERENCE_MODEL_WORKFLOW.md`. Do not recreate its logic and never import `freeocc`; FreeCAD provides OpenCASCADE through its built-in `Part` module. Require `SITE_SLABS_BUILD_OK`.

Blender is the rendering/visualization copy. Use its typed scene/object/screenshot tools for inspection and `execute_blender_code` for controlled edits. Code executes inside the live desktop Blender process, so save work before exploratory operations. Do not enable third-party asset services unless the user asks.

For the tested handoff, run these checked-in scripts through the corresponding MCP code tool instead of recreating their logic:

1. FreeCAD: `scripts/export-freecad-for-blender.py`
2. Blender: `scripts/import-freecad-bundle.py`
3. Blender: `scripts/render-freecad-import.py`

Verify each success marker before continuing: `FREECAD_EXPORT_OK`, `BLENDER_IMPORT_OK`, and `BLENDER_RENDER_OK`.

ComfyUI is connected through its local REST API, not MCP. Use `scripts/comfy-depth-render.py` only when the user asks for image generation or explicitly requests the complete pipeline. Its graph is `workflows/freecad-depth-api.json`, and its success marker is `COMFY_DEPTH_OK`. For the rebuilt cliff-house site demonstration, use `scripts/run-cliff-house-visualization.py`; require all six ordered markers through `CLIFF_HOUSE_VISUALIZATION_OK`.

Do not use Rhino. Blender replaces Rhino for rendering in this project.
