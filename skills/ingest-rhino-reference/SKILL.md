---
name: ingest-rhino-reference
description: "Import a Rhino .3dm reference into an immutable FreeCAD document with source units, layers, names, IDs, curves, and annotations preserved, then run the checked read-only audit and visual review gate. Use when Hermes is asked to open, inspect, convert, intake, or review a Rhino reference without Rhino."
---

# Ingest a Rhino reference

Treat the `.3dm` as evidence, not as an editable design. Use the checked extractor and FreeCAD importer; never invent a replacement parser inside the prompt.

## Prerequisites

- Resolve `ROOT` to the repository containing `HERMES.md`. On the demo Spark, `ROOT=/home/nvidia/aes-demo`.
- Require a healthy FreeCAD MCP connection and a readable `.3dm` source.
- Stop if `ROOT/HERMES.md` or `ROOT/scripts/import-rhino-reference.sh` is missing. Do not search the whole filesystem.

## Procedure

1. Read `ROOT/HERMES.md`.
2. Run this once with the `terminal` tool from `ROOT`:

   ```bash
   ROOT/scripts/import-rhino-reference.sh [optional-source.3dm]
   ```

   Omit the argument only for the repository's default reference.
3. Require both `RHINO_REFERENCE_EXTRACT_OK` and `FREECAD_REFERENCE_IMPORT_OK`. Stop on a missing marker and report the real stderr/stdout.
4. Run this exact code through FreeCAD MCP `execute_code`:

   ```python
   exec(compile(open('/home/nvidia/aes-demo/scripts/audit-rhino-reference-freecad.py', encoding='utf-8').read(), '/home/nvidia/aes-demo/scripts/audit-rhino-reference-freecad.py', 'exec'))
   ```

5. Require `REFERENCE_AUDIT_OK`. Report the observed units, bounds, type counts, layer paths, object names, and unsupported-object count. Do not substitute expected project counts for the audit output.
6. Request fitted Top and Isometric views of the reference document. Present what is visible and ask for human approval before reconstruction.
7. Stop at the review gate. Do not create editable geometry, export to Blender, or run ComfyUI.

## Integrity rules

- Keep the generated reference document immutable.
- Do not import `freeocc`, `cadquery`, RhinoCommon, or third-party CAD modules in FreeCAD.
- Supported exact geometry is currently `PolylineCurve`, `NurbsCurve`, and `TextDot`. Report other Rhino object types as unsupported; never silently approximate them.
- Preserve source identity through `RhinoObjectIndex`, `RhinoObjectId`, `RhinoObjectName`, and `RhinoLayerPath`.

## Verification

Success requires all three markers and a human-viewable Top and Isometric result:

```text
RHINO_REFERENCE_EXTRACT_OK
FREECAD_REFERENCE_IMPORT_OK
REFERENCE_AUDIT_OK
```
