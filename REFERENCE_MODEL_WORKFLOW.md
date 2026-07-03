# Rhino reference reconstruction workflow

The upstream `base_model.3dm` is a Rhino 8 **source-curve template**, not a finished building. It contains five closed plan polylines, five cubic NURBS terrain/grid curves, and six labels on 11 layers. The local bridge preserves those layers and curve definitions in a FreeCAD reference document so Hermes can inspect the design intent and rebuild forward without Rhino.

## Recommended test: let Hermes drive the import

Reset only this workflow's generated state, then start the full local stack:

```bash
./scripts/reset-reference-workflow.sh
./scripts/start-aes-demo.sh
```

The second command opens an interactive Hermes session after FreeCAD, Blender, and ComfyUI are healthy. Paste this as the first prompt:

```text
Act as the AEC workflow orchestrator for this Spark project. The original upstream workflow assumes Rhino, but this installation replaces Rhino with FreeCAD. Never call Rhino, RhinoMCP, or execute RhinoCommon code. Preserve the original phase order and review gates, translating Rhino modeling work into FreeCAD MCP work and using the checked-in FreeCAD-to-Blender and ComfyUI scripts for later phases.

Perform only the startup and reference-intake phase now:
1. Read /home/nvidia/aes-demo/HERMES.md and /home/nvidia/aes-demo/REFERENCE_MODEL_WORKFLOW.md.
2. Use the terminal tool exactly once to run this command from /home/nvidia/aes-demo: ./scripts/import-rhino-reference.sh
3. Require both RHINO_REFERENCE_EXTRACT_OK and FREECAD_REFERENCE_IMPORT_OK. If either is absent, stop and report the real failure.
4. Use FreeCAD MCP list_documents, get_object, get_objects, and get_view to audit CliffHouseReference. Treat it as immutable. Verify its metadata, metre source units, millimetre bounds, 10 curves, 6 labels, 11-layer hierarchy, named planning curves, and Isometric and Top views. Do not modify CliffHouseReference.
5. Interpret the three uCurves and two vCurves as candidate terrain-construction curves, consistent with the upstream site-preparation phase; do not call them a closed lot boundary. Distinguish them from the five closed plan polylines.
6. Read the original brief at /home/nvidia/aes-demo/aec-cptx-demo/aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md plus system_prompts/02_phase_site_prep.md and system_prompts/03_phase_massing.md. Treat Rhino-specific code as conceptual guidance only.
7. Explain how original Phase 1 should continue in a separate editable FreeCAD document named CliffHouseRebuild. Separate facts derived from the reference from unresolved design choices.
8. Stop at the review gate. Do not create or change CliffHouseRebuild, export to Blender, or run ComfyUI until I approve the intake report.

Report the tools actually called, verified import facts, the next translated phase, and only decisions that are genuinely unobservable. Do not claim success without tool readback.
```

Expected at the review gate:

- Hermes runs `rhino3dm` indirectly through the checked-in bridge and reports both success markers.
- `CliffHouseReference` contains 10 curves and six labels in source metres converted to FreeCAD millimetres.
- The five closed plan rectangles resolve to building `12 × 20 m`, garage `10 × 10.5 m`, driveway `8 × 7 m`, patio `6 × 21 m`, and stairs `4 × 2 m`.
- The other five curves are three U and two V terrain-construction curves; they are not a finished terrain surface or a closed lot polygon.
- Hermes proposes translated FreeCAD site preparation and pauses before making design assumptions.

Use a fresh Hermes session for each approved phase. The local model is more reliable with the original workflow's phase gates than with one very long request covering FreeCAD, Blender, and ComfyUI at once.

To repeat from the beginning, exit Hermes and run the two commands above again. The reset leaves `PromptTest`, the Blender scene, and existing ComfyUI outputs untouched.

## Import the reference manually

To bypass Hermes for the import itself, start FreeCAD (or the full stack), then run:

```bash
./scripts/import-rhino-reference.sh
```

The command performs two local stages:

1. `rhino3dm` reads the Rhino 8 file and writes `/tmp/aes-demo-rhino-reference.json` in source units.
2. The live FreeCAD MCP RPC rebuilds native polylines, NURBS edges, annotations, and the Rhino layer hierarchy in `CliffHouseReference`.

The saved FreeCAD artifact is `source_models/cliff_house/cliff_house_reference.FCStd` and is intentionally ignored by Git. Re-running the command replaces only a prior document carrying this importer's marker; it refuses to overwrite an unrelated document with the same name.

## First Hermes audit prompt after a manual import

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
- `scripts/reset-reference-workflow.sh` closes only the generated reference/rebuild documents and removes their generated FreeCAD, manifest, backup, and screenshot files.
- The import is a reference workflow, not automatic semantic BIM conversion. A curve named `building_plan` is evidence of a footprint, but wall height, construction, openings, roof form, and IFC classes remain decisions to verify or supply.
