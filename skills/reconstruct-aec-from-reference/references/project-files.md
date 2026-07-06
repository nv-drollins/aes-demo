# Cliff House 02 project files

## Immutable inputs

- Base template: `/home/nvidia/aec-demo/aec-cptx-demo/_scene_templates/base_model_template.3dm`
  - SHA-256: `ddacac2ba0cea8df75a1b02b9214c64bbcbf4b5d214e60c67dac94a32e7272d0`
- Final Rhino: `/home/nvidia/aec-demo/aec_deno_rhino_13.3dm`
  - SHA-256: `a097afeb6d7178719161e53d57957e9b41deef0a55f2f4cca51947ed93207ff8`
- Final STEP: `/home/nvidia/aec-demo/cliff_house_exp.stp`
  - SHA-256: `54a92968a8dd3273c074ca3426de64f907211b1815c3f74dc29b0093ea0fdd41`

## Approved inputs

- Brief: `projects/cliff_house_template_reconstruction/project_prompt.md`
- Assumptions: `projects/cliff_house_template_reconstruction/SUBJECTIVE_ASSUMPTIONS.md`
- Construction specification: `projects/cliff_house_template_reconstruction/construction_spec.json`
- Base inventory: `projects/cliff_house_template_reconstruction/evidence/base_template_inventory.json`
- Final annotation evidence: `projects/cliff_house_template_reconstruction/evidence/final_rhino_text.json`

## Existing fallback outputs

- STEP reference: `source_models/cliff_house/cliff_house_final_reference.FCStd`
- Exact replay: `source_models/cliff_house/cliff_house_final_reconstruction.FCStd`
- Detailed final mapping: `source_models/cliff_house/final_reconstruction_spec.json`

## Checked scripts

- `scripts/extract-rhino-reference.py`
- `scripts/audit-final-rhino-model.py`
- `scripts/extract-final-rhino-text.py`
- `scripts/import-final-step-freecad.py`
- `scripts/build-final-reconstruction-spec.py`
- `scripts/validate-final-reconstruction-mapping.py`
- `scripts/reconstruct-final-freecad.py` — reference-replay mode only
- `scripts/validate-template-reconstruction-project.py`
- `scripts/build-template-cliff-house.py` — runs inside FreeCAD through MCP
- `scripts/run-template-cliff-house-build.py` — ordered live-build runner
- `scripts/reset-template-cliff-house-demo.py` — preserves brief and references

## Required markers

Evidence and approval:

```text
RHINO_REFERENCE_EXTRACT_OK
FINAL_RHINO_AUDIT_OK
FINAL_RHINO_TEXT_OK
FINAL_STEP_IMPORT_OK
PROJECT_BRIEF_READY
PROJECT_BRIEF_APPROVED
```

Template-build phases:

```text
TEMPLATE_AUDIT_OK
TERRAIN_BUILD_OK
SITE_SUPPORT_BUILD_OK
L1_STRUCTURE_BUILD_OK
L1_ENVELOPE_BUILD_OK
L2_STRUCTURE_BUILD_OK
L2_ENVELOPE_BUILD_OK
L3_STRUCTURE_BUILD_OK
L3_ENVELOPE_BUILD_OK
ENTRY_CLADDING_BUILD_OK
POOL_BUILD_OK
FINAL_REFERENCE_COMPARISON_OK
```
