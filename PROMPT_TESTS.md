# Prompt test ladder

For the optional Rhino-source reverse-engineering test, see [REFERENCE_MODEL_WORKFLOW.md](REFERENCE_MODEL_WORKFLOW.md). It imports the upstream checkout's `.3dm` curve template into an immutable `CliffHouseReference` document and provides audit and rebuild-forward prompts.

Start FreeCAD and Hermes with:

```bash
./scripts/start-hermes.sh
```

Run these prompts one at a time. Keep FreeCAD visible so you can watch the document tree and viewport change.

## 1. Read-only connection

```text
Use the FreeCAD MCP list_documents tool now. Do not guess and do not use shell commands. Tell me the exact names of all documents currently open in FreeCAD.
```

Expected: Hermes calls the MCP tool and reports `HermesSmokeTest` if the supplied smoke-test document is open.

## 2. Inspect existing geometry

```text
Use only FreeCAD MCP tools. Inspect every object in the HermesSmokeTest document. Summarize each object's type and dimensions, then request an isometric view. Do not change the model.
```

Expected: `TestBox` and `HermesLocalCylinder` are reported, and FreeCAD changes to an isometric fitted view.

## 3. Create a clean prompt-test document

```text
Use only FreeCAD MCP tools. Create a new document named PromptTest. In it create a Part::Box named BaseSlab with Length 120, Width 80, and Height 8. After creating it, call get_object and confirm the returned dimensions. Make one modeling tool call at a time.
```

Expected: a new document and one 120 x 80 x 8 mm box.

## 4. Structured edit

```text
Use only FreeCAD MCP tools. In PromptTest, edit BaseSlab so its Height is 12. Then call get_object and report the verified Length, Width, Height, volume, and face count. Do not claim success until you have read the object back.
```

Expected: Height `12.0 mm`, volume `115200.0`, and six faces.

## 5. Multi-object architectural massing

```text
Use only FreeCAD MCP tools. In PromptTest, create three separate Part::Box objects one at a time:
- Level1: Length 70, Width 50, Height 30, placed at x=10, y=10, z=12
- Level2: Length 60, Width 45, Height 28, placed at x=20, y=12, z=42
- Roof: Length 76, Width 56, Height 4, placed at x=7, y=7, z=70
After all three are created, call get_objects and verify that PromptTest contains exactly BaseSlab, Level1, Level2, and Roof. Then request an isometric view.
```

Expected: a simple stepped building mass, with every object independently editable.

## 6. View feedback

```text
Use the FreeCAD MCP get_view tool to inspect PromptTest from the Front, Right, Top, and Isometric views in that order. Describe any obvious alignment problem you can actually observe. Do not modify geometry.
```

Expected: four viewport calls and an observation grounded in the returned images.

## 7. Save a checkpoint

```text
Use the FreeCAD MCP execute_code tool on the GUI thread to recompute PromptTest and save it as /home/nvidia/aes-demo/PromptTest.FCStd. Then use list_documents and get_objects to confirm the document remains open and contains the four expected objects.
```

Expected: `PromptTest.FCStd` appears in the workspace. It is ignored by Git.

## 8. Recovery behavior

```text
Use only FreeCAD MCP tools. Try to inspect an object named DoesNotExist in PromptTest. Report the actual tool error without inventing properties, and do not create or modify anything.
```

Expected: Hermes accurately reports the missing object. This checks that it does not hallucinate success after a tool failure.

## 9. Read Blender through Hermes

Start the full stack with `./scripts/start-aes-demo.sh`, then ask:

```text
Use the Blender MCP get_scene_info tool now. Tell me the exact scene name and list every object name and type. Do not use shell commands and do not guess.
```

Expected: Hermes reports the live Blender scene using the MCP result.

## 10. Export FreeCAD and import into Blender

```text
Perform this handoff using MCP tools only and make one tool call at a time.
First use FreeCAD MCP get_objects on PromptTest and verify that BaseSlab, Level1, Level2, and Roof are all present. If any are missing, stop and report which objects are missing; do not run either script.
Next use FreeCAD MCP execute_code to execute:
exec(compile(open('/home/nvidia/aes-demo/scripts/export-freecad-for-blender.py', encoding='utf-8').read(), '/home/nvidia/aes-demo/scripts/export-freecad-for-blender.py', 'exec'))
Then use Blender MCP execute_blender_code to execute:
exec(compile(open('/home/nvidia/aes-demo/scripts/import-freecad-bundle.py', encoding='utf-8').read(), '/home/nvidia/aes-demo/scripts/import-freecad-bundle.py', 'exec'))
Finally use Blender MCP get_scene_info and verify that BaseSlab, Level1, Level2, and Roof are present. Do not claim success until both scripts and the readback succeed.
```

Expected: `FREECAD_EXPORT_OK` reports four objects, `BLENDER_IMPORT_OK` reports four objects, and all four names are read back from Blender.

## 11. Render Blender beauty and depth

```text
Use Blender MCP execute_blender_code to execute exactly:
exec(compile(open('/home/nvidia/aes-demo/scripts/render-freecad-import.py', encoding='utf-8').read(), '/home/nvidia/aes-demo/scripts/render-freecad-import.py', 'exec'))
Report the BLENDER_RENDER_OK output. Do not use shell commands.
```

Expected: `/tmp/aes-demo-render/freecad-beauty.png` and `/tmp/aes-demo-render/freecad-depth.png`. The beauty is 1024x768 RGBA; depth is 1024x768 16-bit grayscale.

## 12. Generate the ComfyUI visualization

This final leg is REST automation rather than MCP. You can run it directly in a terminal:

```bash
comfyui/.venv/bin/python scripts/comfy-depth-render.py \
  --prompt "professional architectural visualization, contemporary timber and concrete pavilion, landscaped site, soft daylight"
```

Or explicitly authorize Hermes to run only that checked-in command:

```text
Use the terminal tool to run this exact command from /home/nvidia/aes-demo and return its COMFY_IMAGE_OK and final COMFY_DEPTH_OK lines:
comfyui/.venv/bin/python scripts/comfy-depth-render.py --prompt "professional architectural visualization, contemporary timber and concrete pavilion, landscaped site, soft daylight"
Do not modify any files or run any other command.
```

Expected: `COMFY_IMAGE_OK`, then `COMFY_DEPTH_OK`, and a generated PNG under `outputs/comfyui/` showing the stepped building mass with AI-applied material/lighting variation. A blank or nearly uniform result now fails before `COMFY_DEPTH_OK`; inspect the Blender beauty/depth inputs or ComfyUI history.

## Optional cleanup after completing all 12 steps

Do not run this during the prompt ladder. It deliberately deletes the four `PromptTest` objects used by steps 10–12.

```text
Use only FreeCAD MCP tools. Delete Roof, Level2, Level1, and BaseSlab from PromptTest in that order, one object per call. Call get_objects afterward and confirm the document is empty.
```
