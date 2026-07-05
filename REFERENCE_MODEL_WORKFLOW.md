# End-to-end Rhino to FreeCAD, Blender, and ComfyUI demo

This is one linear walkthrough. Do not run the Rhino import manually, do not start a second Hermes session, and do not skip ahead. Hermes performs each checked phase and stops for review.

## Step 1 — Reset the previous demo

Run this from a terminal while the demo applications are still open:

```bash
cd /home/nvidia/aes-demo
./scripts/reset-recording-demo.py
```

Wait for `RECORDING_DEMO_RESET_OK`. Close FreeCAD, Blender, ComfyUI, Hermes, and the image viewer normally. If Blender asks to save the empty scene, choose **Don't Save**.

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
Use the `ingest-rhino-reference` skill for this phase. Run the cliff-house reference intake using the checked project scripts. Rhino is replaced by FreeCAD; never call Rhino, RhinoMCP, or RhinoCommon.

First read /home/nvidia/aes-demo/HERMES.md. Then use the terminal tool exactly once from /home/nvidia/aes-demo to run:
/home/nvidia/aes-demo/scripts/import-rhino-reference.sh

Require RHINO_REFERENCE_EXTRACT_OK and FREECAD_REFERENCE_IMPORT_OK. If either marker is missing, stop and report the real error.

After the import, use FreeCAD MCP execute_code to execute exactly:

exec(compile(open('/home/nvidia/aes-demo/scripts/audit-rhino-reference-freecad.py', encoding='utf-8').read(), '/home/nvidia/aes-demo/scripts/audit-rhino-reference-freecad.py', 'exec'))

Require REFERENCE_AUDIT_OK. Then use FreeCAD MCP get_view for fitted Isometric and Top views of CliffHouseReference. Treat the document as immutable. Summarize the checked audit and visible reference, then stop.
```

Prompt 1 succeeds when Hermes reports all three markers and shows the imported source curves.

## Step 4 — Prompt 2: create the editable FreeCAD site plan

Paste this into the same Hermes session:

```text
Use the `rebuild-freecad-reference` skill for this phase. Continue with the editable site-plan rebuild. Never modify CliffHouseReference.

Use FreeCAD MCP tools to inspect the five closed PolylineCurve reference objects. Identify the building, garage, driveway, patio stairs, and patio footprints from their metadata. Report their source objects, bounds, and elevations.

Then use FreeCAD MCP execute_code to execute exactly:

exec(compile(open('/home/nvidia/aes-demo/scripts/build-cliff-house-site-slabs.py', encoding='utf-8').read(), '/home/nvidia/aes-demo/scripts/build-cliff-house-site-slabs.py', 'exec'))

Require SITE_SLABS_BUILD_OK. Verify building_plan_Shell, garage_plan_Shell, driveway_plan_Shell, patio_stairs_plan_Shell, and patio_plan_Shell in CliffHouseRebuild. Show a fitted Isometric view and stop. Do not create terrain or architecture yet.
```

Prompt 2 succeeds when the five source-derived planning slabs are visible in `CliffHouseRebuild`.

## Step 5 — Prompt 3: build and review the cliff-house massing

Paste this into the same Hermes session:

```text
Use the `build-freecad-massing` skill for this phase. Build the checked upstream-guided cliff-house massing in CliffHouseRebuild without modifying CliffHouseReference.

First verify the five approved site-plan objects still exist. Then use FreeCAD MCP execute_code to execute exactly:

import os
os.environ['AES_MASSING_SPEC'] = '/home/nvidia/aes-demo/skills/build-freecad-massing/assets/cliff-house-massing-v1.json'
exec(compile(open('/home/nvidia/aes-demo/skills/build-freecad-massing/scripts/build-freecad-massing.py', encoding='utf-8').read(), '/home/nvidia/aes-demo/skills/build-freecad-massing/scripts/build-freecad-massing.py', 'exec'))

Do not rewrite the builder and do not create boxes manually. Require FREECAD_MASSING_BUILD_OK with 11 objects.

Use FreeCAD MCP get_objects to verify:
L1_east
L1_west
L2_east
L2_west
L2_balcony_south
L2_balcony_north
L2_balcony_step
L2_roof_garage
L3_main
L3_balcony_south
L3_roof_slab

Report each object's group, role, source references, and bounds. Explain the upstream coordinate provenance and documented vertical translation. Show fitted Front, Right, and Isometric views, then stop for review. Do not export to Blender or run ComfyUI yet.
```

Prompt 3 succeeds when the three-level cantilevered house is visible and you approve its proportions.

## Step 6 — Prompt 4: run Blender and ComfyUI

Paste this into the same Hermes session:

```text
Use the `handoff-freecad-blender` and `visualize-blender-comfyui` skills for this phase. Run the checked visualization pipeline for the approved CliffHouseRebuild.

Use FreeCAD MCP get_objects first. Verify the five site-plan objects and all eleven massing objects from the previous phase. If any are missing, stop and report them.

Otherwise use the terminal tool exactly once from /home/nvidia/aes-demo to run:
/home/nvidia/aes-demo/scripts/run-cliff-house-visualization.py

Report these real success markers in order:
MASSING_PREFLIGHT_OK
TERRAIN_BUILD_OK
FREECAD_EXPORT_OK
BLENDER_IMPORT_OK
BLENDER_RENDER_OK
COMFY_IMAGE_OK
COMFY_DEPTH_OK
COMFY_RESULT_OPENED
CLIFF_HOUSE_VISUALIZATION_OK

After the command succeeds, use Blender MCP get_scene_info and confirm that Blender contains five site-plan objects, eleven house-massing objects, and Terrain Surface. Report the beauty, depth, and ComfyUI paths. Describe the ComfyUI result as a depth-constrained concept visualization, not CAD geometry.
```

The pipeline exports the actual FreeCAD house massing and terrain, assigns role-based Blender materials, renders beauty and depth, validates the single ComfyUI result, and opens it automatically.

## Step 7 — Show the final results

1. Show the FreeCAD massing from the approved Isometric view.
2. Switch to Blender and show the imported site, house, terrain, camera, materials, and lighting.
3. Show `/tmp/aes-demo-render/freecad-beauty.png`.
4. Show `/tmp/aes-demo-render/freecad-depth.png`.
5. Show the single validated ComfyUI image opened by the pipeline.

Blender displays the actual FreeCAD geometry. ComfyUI produces one AI concept image constrained by Blender's beauty and depth renders.
