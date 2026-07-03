# Rhino reference reconstruction workflow

The upstream `base_model.3dm` is a Rhino 8 **source-curve template**, not a finished building. It contains five closed plan polylines, five cubic NURBS terrain/grid curves, and six labels on 11 layers. The local bridge preserves those layers and curve definitions in a FreeCAD reference document so Hermes can inspect the design intent and rebuild forward without Rhino.

## Import the reference

Start FreeCAD (or the full stack), then run:

```bash
./scripts/import-rhino-reference.sh
```

The command performs two local stages:

1. `rhino3dm` reads the Rhino 8 file and writes `/tmp/aes-demo-rhino-reference.json` in source units.
2. The live FreeCAD MCP RPC rebuilds native polylines, NURBS edges, annotations, and the Rhino layer hierarchy in `CliffHouseReference`.

The saved FreeCAD artifact is `source_models/cliff_house/cliff_house_reference.FCStd` and is intentionally ignored by Git. Re-running the command replaces only a prior document carrying this importer's marker; it refuses to overwrite an unrelated document with the same name.

## First Hermes audit prompt

```text
Use only FreeCAD MCP tools. Inspect the document CliffHouseReference and treat every object in it as immutable source reference: do not edit, delete, or create anything in that document. Read RhinoImportMetadata, inventory the Rhino layer groups, curves, and labels, and report the source units, converted millimetre bounds, and named plan regions. Confirm whether this is a final building model or only source curves. Request an isometric fitted view at the end. Do not guess about geometry you cannot verify.
```

Expected: Hermes identifies a metre-based Rhino curve template with 10 curves and six labels, including `building_plan`, `garage_plan`, `driveway_plan`, `patio_stairs_plan`, `PATIO`, and `TERRAIN`.

## Rebuild-forward prompt

Run the audit first. Then use this prompt to begin a separate, editable model:

```text
Use FreeCAD MCP tools to reconstruct forward from CliffHouseReference. Never modify that reference document. Create or reuse a separate document named CliffHouseRebuild. First inspect the closed source curves named building_plan, garage_plan, driveway_plan, and patio_stairs_plan and report their verified dimensions and elevations. Then create editable Part features in CliffHouseRebuild that trace those four footprints exactly. Name each new object with the suffix _Rebuild, verify every result by reading it back, and stop before adding walls, roofs, terrain, or invented dimensions. Request an isometric fitted view of CliffHouseRebuild when complete.
```

This deliberately separates **observed source facts** from **design assumptions**. Subsequent prompts can add pads, walls, terrain, and roofs one phase at a time, with a checkpoint and readback after each phase.

## Files and fidelity

- `scripts/extract-rhino-reference.py` preserves object IDs, names, layer paths/colors, source units, closed polyline vertices, NURBS degree/domain/control points/weights/knots, and label locations.
- `scripts/import-rhino-reference-freecad.py` converts metres to FreeCAD millimetres and creates native `Part::Feature` edges. It records whether each NURBS was exact or required a sampled fallback.
- The import is a reference workflow, not automatic semantic BIM conversion. A curve named `building_plan` is evidence of a footprint, but wall height, construction, openings, roof form, and IFC classes remain decisions to verify or supply.
