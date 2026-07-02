# Hermes / FreeCAD MCP smoke-test workspace

The immediate goal is to verify that Hermes can inspect and control the locally running FreeCAD instance through the `freecad` MCP server.

Inference is local through Ollama at `http://localhost:11434/v1` using the
tool-capable `qwen3.6:latest` model. No cloud model provider is required.

For the first test:

1. Confirm the FreeCAD MCP connection by calling `list_documents`.
2. Create a document named `HermesSmokeTest` if it does not exist.
3. Create one `Part::Box` named `TestBox` with Length 20, Width 15, and Height 10.
4. Use `get_object` to verify its dimensions.
5. Use `get_view` with the Isometric view to inspect the result.
6. Do not use Blender, ComfyUI, Rhino, OBS, or the Rhino-oriented phase prompts yet.

Prefer the typed FreeCAD MCP tools. Use `execute_code` only when a typed tool cannot perform the operation. Never use `execute_code_async` for GUI or document mutations.
