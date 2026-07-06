"""Reassemble the complete cliff house in staged semantic groups in FreeCAD.

Run inside the live FreeCAD process through FreeCAD MCP ``execute_code``.
The reconstruction copies exact B-rep geometry from the protected STEP reference
while restoring Rhino identity, layer provenance, semantic phase, and material role.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

import FreeCAD as App


SPEC_PATH = Path(
    os.environ.get(
        "AEC_FINAL_RECONSTRUCTION_SPEC",
        "/home/nvidia/aec-demo/source_models/cliff_house/"
        "final_reconstruction_spec.json",
    )
).resolve()
REFERENCE_PATH = Path(
    os.environ.get(
        "AEC_FINAL_STEP_FCSTD",
        "/home/nvidia/aec-demo/source_models/cliff_house/"
        "cliff_house_final_reference.FCStd",
    )
).resolve()
OUTPUT_PATH = Path(
    os.environ.get(
        "AEC_FINAL_RECONSTRUCTION_FCSTD",
        "/home/nvidia/aec-demo/source_models/cliff_house/"
        "cliff_house_final_reconstruction.FCStd",
    )
).resolve()
DOCUMENT_NAME = os.environ.get(
    "AEC_FINAL_RECONSTRUCTION_DOCUMENT",
    "CliffHouseFinalReconstruction",
)
DELAY = max(0.0, min(float(os.environ.get("AEC_RECONSTRUCTION_DELAY", "0")), 1.0))
FORMAT = "aec-demo-final-reconstruction-v1"


if not SPEC_PATH.is_file():
    raise RuntimeError(f"Reconstruction specification does not exist: {SPEC_PATH}")
spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
if spec.get("format") != FORMAT:
    raise RuntimeError(f"Unexpected reconstruction format: {spec.get('format')!r}")

if "CliffHouseFinalReference" not in App.listDocuments():
    if not REFERENCE_PATH.is_file():
        raise RuntimeError(f"Final STEP reference does not exist: {REFERENCE_PATH}")
    App.openDocument(str(REFERENCE_PATH))
reference = App.getDocument("CliffHouseFinalReference")
reference_metadata = reference.getObject("FinalReferenceMetadata")
if reference_metadata is None or not reference_metadata.ReadOnlyReference:
    raise RuntimeError("Final STEP reference metadata is missing or unprotected")
if reference_metadata.SourceSHA256 != spec["source_step"]["sha256"]:
    raise RuntimeError("Final STEP reference SHA256 does not match the reconstruction spec")

if DOCUMENT_NAME in App.listDocuments():
    previous = App.getDocument(DOCUMENT_NAME)
    metadata = previous.getObject("ReconstructionMetadata")
    if metadata is None or getattr(metadata, "ManifestFormat", "") != FORMAT:
        raise RuntimeError(f"Refusing to replace unrecognized document {DOCUMENT_NAME!r}")
    App.closeDocument(DOCUMENT_NAME)

document = App.newDocument(DOCUMENT_NAME)
document.Label = "Cliff House — Staged Final Reconstruction"
phase_groups = {}
for phase in spec["phases"]:
    group = document.addObject("App::DocumentObjectGroup", phase)
    group.Label = phase.replace("_", " ").title()
    phase_groups[phase] = group

metadata = document.addObject("App::FeaturePython", "ReconstructionMetadata")
metadata.Label = "CHECKED RECONSTRUCTION METADATA"
for name, value in (
    ("ManifestFormat", FORMAT),
    ("SpecificationId", spec["id"]),
    ("SpecificationPath", str(SPEC_PATH)),
    ("SourceRhinoSHA256", spec["source_rhino"]["sha256"]),
    ("SourceStepSHA256", spec["source_step"]["sha256"]),
):
    metadata.addProperty("App::PropertyString", name, "Reconstruction")
    setattr(metadata, name, value)

created = []
phase_counts = {phase: 0 for phase in spec["phases"]}
for component_index, component in enumerate(spec["components"], start=1):
    source = reference.getObject(component["source_step_object"])
    if source is None or not hasattr(source, "Shape") or source.Shape.isNull():
        raise RuntimeError(
            f"Missing STEP leaf {component['source_step_object']!r} "
            f"for Rhino object {component['source_rhino_index']}"
        )
    target = document.addObject("Part::Feature", component["freecad_name"])
    target.Label = component["name"]
    target.Shape = source.Shape.copy()
    for property_name, property_value in (
        ("ReconstructionPhase", component["phase"]),
        ("MaterialRole", component["material_role"]),
        ("SourceStepObject", component["source_step_object"]),
        ("SourceRhinoId", component["source_rhino_id"]),
        ("SourceRhinoLayer", component["source_rhino_layer"]),
        ("SourceRhinoType", component["source_rhino_type"]),
    ):
        target.addProperty("App::PropertyString", property_name, "Provenance")
        setattr(target, property_name, property_value)
    target.addProperty("App::PropertyInteger", "SourceRhinoIndex", "Provenance")
    target.SourceRhinoIndex = int(component["source_rhino_index"])
    target.addProperty("App::PropertyBool", "ReconstructedFromFinalReference", "Provenance")
    target.ReconstructedFromFinalReference = True
    phase_groups[component["phase"]].addObject(target)
    try:
        target.ViewObject.ShapeColor = source.ViewObject.ShapeColor
        target.ViewObject.LineColor = source.ViewObject.LineColor
        target.ViewObject.Transparency = source.ViewObject.Transparency
    except Exception:
        pass
    created.append(target)
    phase_counts[component["phase"]] += 1
    document.recompute()
    if DELAY:
        try:
            import FreeCADGui as Gui

            App.setActiveDocument(document.Name)
            if component_index == 1:
                Gui.activeDocument().activeView().viewAxonometric()
            if component_index <= 5 or component_index % 10 == 0:
                Gui.activeDocument().activeView().fitAll()
            Gui.updateGui()
        except Exception:
            pass
        time.sleep(DELAY)

expected = spec["expected"]
solid_count = sum(obj.Shape.ShapeType == "Solid" for obj in created)
surface_count = sum(obj.Shape.ShapeType == "Shell" for obj in created)
if len(created) != expected["components"]:
    raise RuntimeError(f"Component count mismatch: {len(created)} != {expected['components']}")
if solid_count != expected["solid_components"]:
    raise RuntimeError(f"Solid count mismatch: {solid_count} != {expected['solid_components']}")
if surface_count != expected["surface_components"]:
    raise RuntimeError(
        f"Surface count mismatch: {surface_count} != {expected['surface_components']}"
    )

metadata.addProperty("App::PropertyInteger", "ComponentCount", "Audit")
metadata.ComponentCount = len(created)
metadata.addProperty("App::PropertyInteger", "SolidComponentCount", "Audit")
metadata.SolidComponentCount = solid_count
metadata.addProperty("App::PropertyInteger", "SurfaceComponentCount", "Audit")
metadata.SurfaceComponentCount = surface_count
metadata.addProperty("App::PropertyString", "PhaseCounts", "Audit")
metadata.PhaseCounts = json.dumps(phase_counts, sort_keys=True)
try:
    metadata.ViewObject.Visibility = False
    import FreeCADGui as Gui

    App.setActiveDocument(document.Name)
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.activeDocument().activeView().fitAll()
except Exception:
    pass

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
document.recompute()
document.saveAs(str(OUTPUT_PATH))
print(
    "FINAL_RECONSTRUCTION_OK "
    f"document={document.Name} components={len(created)} "
    f"solids={solid_count} surfaces={surface_count} "
    f"phases={len(phase_counts)} output={OUTPUT_PATH}"
)
for phase in spec["phases"]:
    print(f"RECONSTRUCTION_PHASE phase={phase} objects={phase_counts[phase]}")
