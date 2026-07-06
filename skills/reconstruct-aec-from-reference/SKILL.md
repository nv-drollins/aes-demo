---
name: reconstruct-aec-from-reference
description: "Analyze a completed Rhino .3dm plus STEP reference, recover semantic layers and exact geometry, prepare a pre-populated architectural project brief and construction specification, obtain one human approval for subjective assumptions, then rebuild from an immutable base template in staged FreeCAD phases and validate against the final reference. Use for AEC reverse engineering, template-driven reconstruction, design-intent recovery, or the Cliff House 02 live-build demonstration."
---

# Reconstruct AEC from reference

Treat the base template as the authoritative starting state, the final Rhino
file as semantic evidence, and STEP as protected validation geometry. Never
present copied STEP B-reps as recovered parametric construction history.

## Project files

Read `references/project-files.md` for canonical paths, source hashes, generated
documents, and success markers. For Cliff House 02, also read:

- `projects/cliff_house_template_reconstruction/project_prompt.md`
- `projects/cliff_house_template_reconstruction/SUBJECTIVE_ASSUMPTIONS.md`
- `projects/cliff_house_template_reconstruction/construction_spec.json`

## Workflow

### 1. Validate evidence

1. Hash the base `.3dm`, final `.3dm`, and final STEP; require the values in the
   construction specification.
2. Run the checked Rhino audit and annotation extraction scripts. Do not use
   Rhino, RhinoCommon, or an improvised parser.
3. Import STEP only into `CliffHouseFinalReference` with
   `scripts/import-final-step-freecad.py` through FreeCAD MCP.
4. Keep the final reference immutable and separate from the live build.
5. Require `FINAL_RHINO_AUDIT_OK`, `FINAL_RHINO_TEXT_OK`, and
   `FINAL_STEP_IMPORT_OK` before interpreting the design.

### 2. Prepare and approve the brief

1. Separate objective evidence from subjective interpretation.
2. Populate objective values from template bounds, final layers, floor-plan
   labels, area schedules, component names, and STEP geometry.
3. Put atmosphere, landscaping, camera, client intent, and render-style guesses
   in `SUBJECTIVE_ASSUMPTIONS.md` with confidence levels.
4. Present one concise assumptions summary. Do not repeat the long interview.
5. If the brief status is not `approved_for_template_build`, stop after the
   approval request. Never begin construction from a draft brief.

### 3. Build from the base template

1. Import and audit the base template into immutable
   `CliffHouseReference`; require the recorded source SHA and
   `REFERENCE_AUDIT_OK`.
2. Create or replace only the recognized `CliffHouseTemplateBuild` document.
3. Execute checked native FreeCAD builders in construction-spec phase order.
4. Derive placements from template anchors and approved parameters. Use the
   final reference only to measure or validate; do not clone its shapes in
   template-build mode.
5. Require the phase marker and typed-object audit after each phase. Show a
   fitted view and update the GUI so the live build is visible.
6. Stop on a missing builder. Propose a reusable checked implementation instead
   of writing a long ad-hoc FreeCAD program in chat.

### 4. Compare and visualize

1. Compare names, roles, bounds, areas, volumes, and component counts with the
   protected final reference. Report tolerances and intentional design deltas.
2. Distinguish native parametric objects, derived profile objects, and interim
   reference-replay objects in the report.
3. Require human approval before Blender handoff.
4. Use the existing checked FreeCAD-to-Blender bundle, then apply final
   materials, camera, and ComfyUI assets. Do not let ComfyUI change claimed CAD
   geometry.

## Modes

- `template-build`: Required for the authentic demo. Start from the base
  template and use native checked builders.
- `reference-replay`: Existing exact B-rep decomposition/reassembly fallback.
  Label it clearly and never describe it as template-driven reconstruction.

## Integrity rules

- Preserve all earlier demo workflows and files.
- Never edit the source `.3dm`, STEP, or protected FreeCAD reference documents.
- Keep design intent in `project_prompt.md` and exact dimensions/dependencies in
  `construction_spec.json`; do not rely on prose alone.
- Record provenance and confidence for inferred values.
- One approval freezes the brief for recorded runs; resets must not delete it.
- A valid image is not proof of a valid CAD rebuild.

## Completion

The workflow is complete only when the brief is approved, every native phase
marker passes, the final comparison passes, Blender contains the approved CAD
handoff, and ComfyUI returns a validated nonblank image.
