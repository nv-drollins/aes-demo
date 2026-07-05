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
./scripts/import-rhino-reference.sh

Require RHINO_REFERENCE_EXTRACT_OK and FREECAD_REFERENCE_IMPORT_OK. If either marker is missing, stop and report the real error.

After the import, use FreeCAD MCP list_documents, get_object, get_objects, and get_view to inspect CliffHouseReference. Treat that document as immutable. Verify the source units, converted millimetre bounds, 10 curves, 6 labels, 11 Rhino layers, five closed planning polylines, and five terrain-construction NURBS curves. Show Isometric and Top views.

Report the verified results and stop. Do not create CliffHouseRebuild, export to Blender, or run ComfyUI yet.
```

Let Hermes finish. Prompt 1 is successful when it reports both import markers and confirms that `CliffHouseReference` contains the Rhino source curves.

## Step 4 — Prompt 2: create the editable FreeCAD site plan

Paste this into the same Hermes session:

```text
Continue with the editable site-plan rebuild. Never modify CliffHouseReference.

Use FreeCAD MCP tools to inspect the five closed PolylineCurve reference objects in CliffHouseReference. Identify the building, garage, driveway, patio stairs, and patio footprints from their RhinoObjectName and RhinoLayerPath metadata. Read their exact vertices and source elevations; if the typed inspection tools do not expose vertex coordinates, use read-only execute_code to extract them from each source Shape. Do not use dimensions or coordinates supplied by me.

Create a new document named CliffHouseRebuild. For each source footprint, reproduce its exact closed wire as a Part::Feature and extrude it 50 mm upward as a thin visualization slab. The 50 mm thickness is the only demo convention; every X, Y, and base-Z value must be derived from the imported source curve.

Use these output names because the checked visualization pipeline consumes them:
- building_plan_Shell
- garage_plan_Shell
- driveway_plan_Shell
- patio_stairs_plan_Shell
- patio_plan_Shell

After creating them, call get_objects and verify all five names. Read back and report each slab's derived source object, base elevation, footprint dimensions, and bounding box. Show an Isometric fitted view of CliffHouseRebuild and stop. Do not create terrain manually and do not add walls, roofs, or other architecture.
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
./scripts/run-cliff-house-visualization.py

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
4. Show the ComfyUI image that opened automatically.

The Blender scene and renders represent the FreeCAD geometry. The ComfyUI image is an AI concept visualization constrained by Blender's depth render.
