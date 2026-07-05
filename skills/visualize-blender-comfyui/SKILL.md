---
name: visualize-blender-comfyui
description: "Render an approved FreeCAD-derived Blender scene into beauty and depth images, submit them to the local ComfyUI depth-ControlNet workflow, validate that the returned image is non-blank, and present the result. Use for architectural concept rendering, depth-constrained AI visualization, or diagnosing a blank ComfyUI popup."
---

# Visualize with Blender and ComfyUI

Use Blender for deterministic geometry, camera, lighting, materials, beauty, and depth. Use ComfyUI only for a concept image constrained by those renders.

## Prerequisites

- Require an approved FreeCAD-to-Blender handoff or the complete checked cliff-house runner.
- Require healthy Blender MCP and ComfyUI at `http://127.0.0.1:8188`.
- Distinguish Blender's two source images from ComfyUI's one generated result.

## Procedure

1. For the complete current demo, run this once with `terminal` from `ROOT`:

   ```bash
   ROOT/scripts/run-cliff-house-visualization.py
   ```

2. Require these markers in order:

   ```text
   TERRAIN_BUILD_OK
   FREECAD_EXPORT_OK
   BLENDER_IMPORT_OK
   BLENDER_RENDER_OK
   COMFY_IMAGE_OK
   COMFY_DEPTH_OK
   COMFY_RESULT_OPENED
   CLIFF_HOUSE_VISUALIZATION_OK
   ```

3. Verify that the beauty, 16-bit depth, and ComfyUI output files exist and are non-empty.
4. Treat `COMFY_IMAGE_OK` as the content-integrity gate. It must report valid dimensions and non-trivial tonal variation; a successful HTTP request alone is insufficient.
5. If the generated file passes but the popup is blank, classify it as a presentation failure. Open the exact validated output with `eog --new-instance`; fall back to `xdg-open`. Do not rerun diffusion unless the image itself fails validation.
6. Present the Blender beauty and depth paths plus the single ComfyUI result path. Describe the last image as a depth-constrained concept visualization, not CAD geometry.

## Prompt discipline

- Preserve the site layout and topography in the positive prompt.
- Reject warped buildings, extra roads, floating geometry, cutaways, labels, and blank images in the negative prompt.
- Keep ControlNet strong for fidelity. Increase denoise only after a human asks for more creative variation.
- Do not infer missing architecture from a site-only FreeCAD model and call it reconstructed CAD.

## Troubleshooting

- `COMFY_IMAGE_OK` present but popup blank: viewer problem; reopen the validated file directly.
- `COMFY_DEPTH_OK` absent: inspect ComfyUI history and server logs for node errors.
- Image-integrity failure: retain beauty/depth inputs, report statistics, and stop before presentation.
- Nearly binary depth: increase actual modeled height variation or tune Blender depth normalization; do not hide the issue with a text prompt.

## Verification

Success requires validated files, all ordered markers, a Blender scene inventory, and a visible final image. The output path and integrity statistics must be included in the report.
