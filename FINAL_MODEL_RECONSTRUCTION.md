# Complete cliff-house reconstruction

This workflow uses the supplied complete Rhino model as semantic evidence and
the STEP export as exact CAD geometry. The original files remain immutable.

## Verified sources

- `aec_deno_rhino_13.3dm`
  - SHA-256: `a097afeb6d7178719161e53d57957e9b41deef0a55f2f4cca51947ed93207ff8`
  - Rhino 8 archive, metres
  - 206 layers and 700 objects
  - 329 Breps, 12 extrusions, 116 curves, plus plans and annotations
- `cliff_house_exp.stp`
  - SHA-256: `54a92968a8dd3273c074ca3426de64f907211b1815c3f74dc29b0093ea0fdd41`
  - AP242 STEP from Rhino 8.32
  - 136 closed solids and 10 surface models

The Rhino branch `House_02_finish::H02_finishes` contains exactly 146 final
components: the same 136-solid/10-surface split as the STEP file. STEP entity
names match the reversed Rhino export sequence for all 146 components.

## Current reconstruction

The generated FreeCAD documents are:

- `source_models/cliff_house/cliff_house_final_reference.FCStd`
- `source_models/cliff_house/cliff_house_final_reconstruction.FCStd`

The protected reference holds the imported STEP geometry. The reconstruction
creates separately named `Part::Feature` objects, restores Rhino object and
layer provenance, assigns semantic material roles, and organizes the model into
14 construction phases:

1. Site support
2. Level 1 floors
3. Level 1 walls
4. Level 1 glazing and frames
5. Level 2 floors
6. Level 2 walls
7. Level 2 glazing and frames
8. Level 2 balconies and roof
9. Level 3 floors
10. Level 3 walls
11. Level 3 glazing and frames
12. Level 3 balconies and roof
13. Entry and cladding
14. Infinity pool

All 146 reconstructed shapes match their STEP reference geometry exactly by
volume, area, and bounds. This is currently a semantic B-rep decomposition and
reassembly, not a recovered Rhino feature history. Individual phases can later
be replaced with native parametric FreeCAD constructors without changing the
overall demonstration structure.

## Checked scripts

- `scripts/audit-final-rhino-model.py` creates the complete Rhino inventory.
- `scripts/import-final-step-freecad.py` creates the protected STEP reference.
- `scripts/build-final-reconstruction-spec.py` creates the phased manifest.
- `scripts/validate-final-reconstruction-mapping.py` validates all 146 mappings.
- `scripts/reconstruct-final-freecad.py` performs the staged FreeCAD rebuild.
- `scripts/style-final-cliff-house-blender.py` assigns final materials and water.
- `scripts/render-final-cliff-house.py` creates the hero beauty/depth renders.

## Generated visualization assets

Runtime assets are under `outputs/final-demo/`:

- `blender/cliff-house-final.blend`
- `blender/cliff-house-beauty.png`
- `blender/cliff-house-depth.png`
- `comfyui/freecad-depth_00002_.png` — conservative geometry-first concept
- `comfyui/freecad-depth_00003_.png` — more creative architectural concept
- `cliff-house-final-api.json` — current ComfyUI API graph

The Blender file contains 146 FreeCAD-derived objects, a reconstructed infinity
pool water surface, the hero camera, lighting, and ten architectural materials.
ComfyUI runs locally through its REST API using the Blender beauty and depth
images.

## Next demo step

Package these operations behind a Hermes reconstruction skill and a single
checked runner. For the recorded demonstration, use a small nonzero replay
delay so FreeCAD visibly builds each phase, then stop for review before the
Blender and ComfyUI handoff.
