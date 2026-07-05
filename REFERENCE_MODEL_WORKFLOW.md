# End-to-end Rhino to FreeCAD, Blender, and ComfyUI demo

This is one linear walkthrough. Do not run the Rhino import manually, do not start a second Hermes session, and do not skip ahead. Hermes performs the import in Prompt 1.

## Step 1 — Reset the previous demo

Run this from a terminal while the demo applications are still open:

```bash
cd /home/nvidia/aes-demo
./scripts/reset-recording-demo.py
```

Wait for:

```text
RECORDING_DEMO_RESET_OK
```

Close FreeCAD, Blender, ComfyUI, Hermes, and the image viewer normally. If Blender asks to save the empty scene, choose **Don't Save**.

## Step 2 — Start the complete local stack

Begin the recording, open a terminal, and run:

```bash
cd /home/nvidia/aes-demo
./scripts/start-aes-demo.sh
```

Wait for FreeCAD, Blender, and ComfyUI health checks to pass and for the interactive Hermes prompt to appear.

## Step 3 — Prompt 1: import and audit the Rhino reference

Paste this into Hermes:

```text
Run the cliff-house reference intake using the checked project scripts. Rhino is replaced by FreeCAD; never call Rhino, RhinoMCP, or RhinoCommon.

First read /home/nvidia/aes-demo/HERMES.md. Then use the terminal tool exactly once from /home/nvidia/aes-demo to run:
/home/nvidia/aes-demo/scripts/import-rhino-reference.sh

This absolute wrapper path is the only import command. Do not run `import-rhino-reference-freecad.py` directly and do not look for an `import-rhino-reference-freecad.sh` file.

Require RHINO_REFERENCE_EXTRACT_OK and FREECAD_REFERENCE_IMPORT_OK. If either marker is missing, stop and report the real error.

After the import, use the FreeCAD MCP execute_code tool to execute exactly:

exec(compile(open('/home/nvidia/aes-demo/scripts/audit-rhino-reference-freecad.py', encoding='utf-8').read(), '/home/nvidia/aes-demo/scripts/audit-rhino-reference-freecad.py', 'exec'))

Do not rewrite the audit, do not inspect FreeCAD with improvised Python, and do not import any third-party CAD module. Require REFERENCE_AUDIT_OK with 16 objects, 10 curves, 6 labels, and 11 layers.

Then use FreeCAD MCP get_view for Isometric and Top views of CliffHouseReference. Treat the document as immutable. Summarize the checked audit output and what is visible in those two views, then stop. Do not create CliffHouseRebuild, export to Blender, or run ComfyUI yet.
```

Let Hermes finish. Prompt 1 is successful when it reports both import markers and confirms that `CliffHouseReference` contains the Rhino source curves.

## Step 4 — Prompt 2: create the editable FreeCAD site plan

Paste this into the same Hermes session:

```text
Continue with the editable site-plan rebuild. Never modify CliffHouseReference.

Use FreeCAD MCP tools to inspect the five closed PolylineCurve reference objects in CliffHouseReference. Identify the building, garage, driveway, patio stairs, and patio footprints from their RhinoObjectName and RhinoLayerPath metadata. Report their source objects, bounding boxes, and base elevations. Do not modify CliffHouseReference.

Then use the FreeCAD MCP execute_code tool to execute exactly:

exec(compile(open('/home/nvidia/aes-demo/scripts/build-cliff-house-site-slabs.py', encoding='utf-8').read(), '/home/nvidia/aes-demo/scripts/build-cliff-house-site-slabs.py', 'exec'))

Do not rewrite that script, do not use the terminal tool, and do not import any third-party CAD module. The checked script uses FreeCAD's built-in Part module and derives every footprint coordinate and elevation from the imported source Shapes.

Require SITE_SLABS_BUILD_OK. After it succeeds, call get_objects on CliffHouseRebuild and verify these five output names:
- building_plan_Shell
- garage_plan_Shell
- driveway_plan_Shell
- patio_stairs_plan_Shell
- patio_plan_Shell

Report each slab's source object, derived base elevation, dimensions, and bounding box from the tool results. Show an Isometric fitted view of CliffHouseRebuild and stop. Do not create terrain manually and do not add walls, roofs, or other architecture.
```

Keep FreeCAD visible while Hermes works. Prompt 2 is successful when the five planning slabs are visible in `CliffHouseRebuild`.

## Step 5 — Prompt 3: run Blender and ComfyUI

Paste this into the same Hermes session:

```text
Run the checked visualization pipeline for CliffHouseRebuild.

First use FreeCAD MCP get_objects and verify that CliffHouseRebuild contains exactly these required site objects:
building_plan_Shell
garage_plan_Shell
driveway_plan_Shell
patio_stairs_plan_Shell
patio_plan_Shell

If any are missing, stop and report them. Otherwise use the terminal tool exactly once from /home/nvidia/aes-demo to run:
/home/nvidia/aes-demo/scripts/run-cliff-house-visualization.py

Report these real success markers in order:
TERRAIN_BUILD_OK
FREECAD_EXPORT_OK
BLENDER_IMPORT_OK
BLENDER_RENDER_OK
COMFY_DEPTH_OK
COMFY_RESULT_OPENED
CLIFF_HOUSE_VISUALIZATION_OK

After the command succeeds, use Blender MCP get_scene_info and confirm that Blender contains the five site-plan objects plus Terrain Surface. Report the Blender beauty/depth paths and the generated ComfyUI output path. Describe the ComfyUI result as a depth-constrained concept visualization, not CAD geometry.
```

The pipeline clears stale Blender objects, builds the terrain from the five Rhino NURBS guides, exports the FreeCAD site, assigns Blender materials and lighting, renders beauty and depth images, runs local ComfyUI, and opens the generated PNG automatically.

## Step 6 — Show the final results

After Prompt 3 finishes:

1. Switch to Blender and show the imported site, terrain, camera, materials, and lighting.
2. Show the Blender beauty render at `/tmp/aes-demo-render/freecad-beauty.png`.
3. Show the Blender depth render at `/tmp/aes-demo-render/freecad-depth.png`.
4. Show the single ComfyUI image that opened automatically. Blender creates two source images (beauty and depth); ComfyUI combines them into one final concept PNG.

The Blender scene and renders represent the FreeCAD geometry. The ComfyUI image is an AI concept visualization constrained by Blender's depth render.
