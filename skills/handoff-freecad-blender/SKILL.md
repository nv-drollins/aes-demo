---
name: handoff-freecad-blender
description: "Validate and transfer approved FreeCAD Part shapes and Mesh features into Blender as render meshes plus a JSON metadata manifest, preserving object identity, units, bounds, and material roles. Use when exporting, synchronizing, or checking a FreeCAD-to-Blender scene handoff."
---

# Handoff FreeCAD to Blender

Keep FreeCAD authoritative and Blender disposable. Export a checked mesh bundle and metadata manifest, then import that bundle into a clean Blender collection.

## Prerequisites

- Require human approval of the current FreeCAD phase.
- Name the FreeCAD source document explicitly. For the demo use `CliffHouseRebuild`.
- Require healthy FreeCAD and Blender MCP connections.
- Save the FreeCAD document before export.

## Procedure

1. Inspect the FreeCAD document and reject an empty export set, null Shapes, zero-facet Meshes, or zero-size bounds.
2. Through FreeCAD MCP `execute_code`, set `AEC_FREECAD_DOCUMENT` and `AEC_FREECAD_EXPORT_DIR`, then execute `ROOT/scripts/export-freecad-for-blender.py` with `compile(open(...).read(), ...)`.
3. Require `FREECAD_EXPORT_OK`. Read `manifest.json` and verify:
   - format is `aec-demo-freecad-bundle-v1`;
   - source units are millimetres and Blender scale is `0.001`;
   - every object has a unique FreeCAD identity, mesh file, bounds, geometry kind, and material role.
4. Through Blender MCP `execute_blender_code`, set the same `AEC_FREECAD_EXPORT_DIR` and execute `ROOT/scripts/import-freecad-bundle.py`.
5. Set `AEC_BLENDER_CLEAR_SCENE=1` for a recorded clean demo. Preserve unrelated scene objects only when the user explicitly requests it.
6. Require `BLENDER_IMPORT_OK`. Use typed Blender inspection to compare imported object count, names, roles, and bounds with the manifest.
7. Save the Blender checkpoint and stop at the handoff review gate. Do not run ComfyUI unless requested.

## Integrity rules

- Never treat Blender meshes as an editable CAD replacement.
- Never claim that OBJ preserves constraints, NURBS, BIM properties, or FreeCAD topology.
- Preserve `freecad_name`, `freecad_type_id`, `freecad_geometry_kind`, `freecad_source_document`, and `material_role` as Blender custom properties.
- Fail on duplicate source identities, name collisions, missing mesh files, or object-count mismatches.

## Verification

Success requires both markers plus a manifest-to-scene comparison:

```text
FREECAD_EXPORT_OK
BLENDER_IMPORT_OK
```
