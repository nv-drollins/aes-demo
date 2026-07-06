# Template-driven Cliff House 02 workflow

This is a separate demonstration track. It does not replace or modify
`REFERENCE_MODEL_WORKFLOW.md` or the exact-reference reconstruction documented
in `FINAL_MODEL_RECONSTRUCTION.md`.

## Demonstration claim

Hermes examines a finished Rhino/STEP design, recovers its design intent and
construction evidence, prepares a human-approved project brief, then starts
from the original site template and constructs a new editable FreeCAD model.
The final model is a protected comparison target, not the source geometry for
the live template build.

## Offline preparation

1. Audit the base Rhino template.
2. Audit the final Rhino layers, object names, floor plans, annotations, and
   area schedule.
3. Import final STEP geometry into a read-only FreeCAD reference.
4. Prepare:
   - `projects/cliff_house_template_reconstruction/project_prompt.md`
   - `projects/cliff_house_template_reconstruction/SUBJECTIVE_ASSUMPTIONS.md`
   - `projects/cliff_house_template_reconstruction/construction_spec.json`
5. Review the twelve subjective assumptions once.
6. Freeze the approved brief for every recorded run.

## Recorded run

1. Start the local stack and a fresh Hermes session.
2. Ask Hermes to use `reconstruct-aec-from-reference` in `template-build` mode.
3. Hermes validates the approved brief and source hashes.
4. FreeCAD opens two documents:
   - `CliffHouseReference` — immutable base-template curves.
   - `CliffHouseTemplateBuild` — empty editable construction target.
5. Hermes runs checked native builders in phase order and shows each phase.
6. Hermes compares the completed build with `CliffHouseFinalReference` and
   reports intentional differences.
7. After approval, Blender receives the built FreeCAD model and applies the
   final material/camera package.
8. ComfyUI runs the displayed workflow and presents the validated final image.

## Current readiness

- Evidence extraction: validated.
- Project brief and all twelve subjective assumptions: approved on 2026-07-06.
- Machine-readable construction specification: approved and hash-checked.
- Exact reference-replay fallback: complete.
- Native template build: complete; 141 measured native architectural components
  plus five template-derived site components, with no copied STEP B-reps.
- Twelve phase markers and final protected-reference comparison: passing.
- FreeCAD build time on the Spark: approximately 19 seconds without demo pauses.
- Blender/ComfyUI final assets: the existing generated package remains available;
  owner-provided assets can replace or improve it later.

## Run the approved FreeCAD build

The protected `CliffHouseReference` and `CliffHouseFinalReference` documents must be open. Then run:

```bash
cd /home/nvidia/aec-demo
python3 scripts/run-template-cliff-house-build.py --object-delay 0.03
```

Use `--pause-seconds 1` for a slower narrated recording. The runner validates the frozen brief, constructs every phase in `CliffHouseTemplateBuild`, saves `source_models/cliff_house/cliff_house_template_build.FCStd`, captures a PNG preview, and stops on any missing checkpoint.

To return to the start without changing the approved brief or either protected reference:

```bash
python3 scripts/reset-template-cliff-house-demo.py
```

## Approval

Use this once outside the recorded demo:

```text
Approve the Cliff House 02 template-reconstruction assumptions as written.
Freeze the project brief and prepare the template-driven FreeCAD build.
```

After approval, the recorded demo contains no long interview. Hermes only
summarizes the frozen brief before construction.
