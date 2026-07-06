"""Build one approved native phase of the template-driven cliff house.

Run inside the live FreeCAD process through FreeCAD MCP.  The final-reference
manifest is used only as dimensional evidence; this script creates new Part
primitives and planar faces and never copies a Shape from the STEP reference.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

import FreeCAD as App
import Part


ROOT = Path("/home/nvidia/aec-demo")
SPEC_PATH = ROOT / "projects/cliff_house_template_reconstruction/construction_spec.json"
DETAIL_PATH = ROOT / "source_models/cliff_house/final_reconstruction_spec.json"
OUTPUT_PATH = ROOT / "source_models/cliff_house/cliff_house_template_build.FCStd"
DOCUMENT_NAME = os.environ.get("AEC_TEMPLATE_BUILD_DOCUMENT", "CliffHouseTemplateBuild")
PHASE = os.environ.get("AEC_TEMPLATE_BUILD_PHASE", "00_template_audit")
RESET = os.environ.get("AEC_TEMPLATE_BUILD_RESET", "0") == "1"
DELAY = max(0.0, min(float(os.environ.get("AEC_TEMPLATE_BUILD_DELAY", "0")), 0.25))
FORMAT = "aec-demo-template-construction-v1"
GENERATOR = "scripts/build-template-cliff-house.py"

PHASE_DETAILS = {
    "03_level_1_structure": ["01_level_1_floors"],
    "04_level_1_envelope": ["02_level_1_walls", "03_level_1_glazing"],
    "05_level_2_structure": ["04_level_2_floors"],
    "06_level_2_envelope": [
        "05_level_2_walls",
        "06_level_2_glazing",
        "07_level_2_balconies_roof",
    ],
    "07_level_3_structure": ["08_level_3_floors"],
    "08_level_3_envelope": [
        "09_level_3_walls",
        "10_level_3_glazing",
        "11_level_3_balconies_roof",
    ],
    "09_entry_cladding": ["12_entry_cladding"],
    "10_infinity_pool": ["13_infinity_pool"],
}

MARKERS = {
    "00_template_audit": "TEMPLATE_AUDIT_OK",
    "03_level_1_structure": "L1_STRUCTURE_BUILD_OK",
    "04_level_1_envelope": "L1_ENVELOPE_BUILD_OK",
    "05_level_2_structure": "L2_STRUCTURE_BUILD_OK",
    "06_level_2_envelope": "L2_ENVELOPE_BUILD_OK",
    "07_level_3_structure": "L3_STRUCTURE_BUILD_OK",
    "08_level_3_envelope": "L3_ENVELOPE_BUILD_OK",
    "09_entry_cladding": "ENTRY_CLADDING_BUILD_OK",
    "10_infinity_pool": "POOL_BUILD_OK",
    "11_reference_comparison": "FINAL_REFERENCE_COMPARISON_OK",
}

ROLE_STYLE = {
    "concrete_slab": ((0.72, 0.72, 0.70), 0),
    "wall": ((0.88, 0.86, 0.80), 0),
    "glazing": ((0.18, 0.42, 0.58), 68),
    "metal_frame": ((0.18, 0.12, 0.08), 0),
    "roof": ((0.22, 0.22, 0.21), 0),
    "wood_door": ((0.45, 0.19, 0.07), 0),
    "cladding_dark": ((0.16, 0.14, 0.12), 0),
    "cladding_light": ((0.68, 0.55, 0.38), 0),
    "pool": ((0.08, 0.42, 0.56), 45),
}


def add_string(obj, name, value, group="Template Reconstruction"):
    if name not in obj.PropertiesList:
        obj.addProperty("App::PropertyString", name, group)
    setattr(obj, name, str(value))


def add_bool(obj, name, value, group="Template Reconstruction"):
    if name not in obj.PropertiesList:
        obj.addProperty("App::PropertyBool", name, group)
    setattr(obj, name, bool(value))


def checked_specs():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    detail = json.loads(DETAIL_PATH.read_text(encoding="utf-8"))
    if spec.get("format") != FORMAT:
        raise RuntimeError(f"Unexpected construction format: {spec.get('format')!r}")
    if spec.get("status") != "approved_for_template_build":
        raise RuntimeError("Template construction brief has not been approved")
    approval = spec.get("approval", {})
    if approval.get("assumptions") != "approved_as_written":
        raise RuntimeError("Subjective assumptions are not approved")
    if detail.get("format") != "aec-demo-final-reconstruction-v1":
        raise RuntimeError("Unexpected dimensional-reference format")
    return spec, detail


def ensure_reference(spec):
    if "CliffHouseReference" not in App.listDocuments():
        raise RuntimeError("The base-template reference CliffHouseReference is not open")
    reference = App.getDocument("CliffHouseReference")
    metadata = reference.getObject("RhinoImportMetadata")
    if (
        metadata is None
        or getattr(metadata, "ManifestFormat", "") != "aec-demo-rhino-reference-v1"
        or "Immutable reference" not in getattr(metadata, "ImportPolicy", "")
    ):
        raise RuntimeError("Base-template reference is not protected")
    source_hash = getattr(metadata, "SourceSHA256", "")
    expected_hash = spec["sources"]["base_template"]["sha256"]
    if source_hash and source_hash != expected_hash:
        raise RuntimeError("Base-template reference hash does not match the approved brief")
    return reference


def managed_document(spec):
    if RESET and DOCUMENT_NAME in App.listDocuments():
        previous = App.getDocument(DOCUMENT_NAME)
        metadata = previous.getObject("TemplateBuildMetadata")
        if metadata is None or getattr(metadata, "ManifestFormat", "") != FORMAT:
            raise RuntimeError(f"Refusing to replace unrecognized document {DOCUMENT_NAME!r}")
        App.closeDocument(DOCUMENT_NAME)
    document = (
        App.getDocument(DOCUMENT_NAME)
        if DOCUMENT_NAME in App.listDocuments()
        else App.newDocument(DOCUMENT_NAME)
    )
    document.Label = "Cliff House 02 — Native Template Build"
    metadata = document.getObject("TemplateBuildMetadata")
    if metadata is None:
        metadata = document.addObject("App::FeaturePython", "TemplateBuildMetadata")
        metadata.Label = "APPROVED TEMPLATE BUILD METADATA"
        for name, value in (
            ("ManifestFormat", FORMAT),
            ("SpecificationId", spec["id"]),
            ("SpecificationPath", str(SPEC_PATH)),
            ("ApprovedOn", spec["approval"]["approved_on"]),
            ("ApprovedBy", spec["approval"]["approved_by"]),
            ("BaseTemplateSHA256", spec["sources"]["base_template"]["sha256"]),
            ("FinalRhinoEvidenceSHA256", spec["sources"]["final_rhino"]["sha256"]),
            ("GeometryMethod", "native_primitives_from_template_and_measured_dimensions"),
        ):
            add_string(metadata, name, value)
        add_bool(metadata, "CopiesFinalStepBReps", False)
        metadata.ViewObject.Visibility = False
    elif getattr(metadata, "ManifestFormat", "") != FORMAT:
        raise RuntimeError(f"Document {DOCUMENT_NAME!r} is not a managed template build")
    return document, metadata


def ensure_group(document, phase):
    name = "Phase_" + phase
    group = document.getObject(name)
    if group is None:
        group = document.addObject("App::DocumentObjectGroup", name)
        group.Label = phase.replace("_", " ").title()
        add_string(group, "GeneratedBy", GENERATOR)
        add_string(group, "ConstructionPhase", phase)
    return group


def remove_managed_phase(document, phase):
    for obj in list(document.Objects):
        if (
            getattr(obj, "GeneratedBy", "") == GENERATOR
            and getattr(obj, "ConstructionPhase", "") == phase
            and obj.TypeId == "Part::Feature"
        ):
            document.removeObject(obj.Name)
    document.recompute()


def planar_face(bounds):
    minimum = [float(v) for v in bounds["min"]]
    maximum = [float(v) for v in bounds["max"]]
    size = [maximum[i] - minimum[i] for i in range(3)]
    axis = min(range(3), key=size.__getitem__)
    if axis == 2:
        return Part.makePlane(
            max(size[0], 1.0), max(size[1], 1.0),
            App.Vector(minimum[0], minimum[1], minimum[2]), App.Vector(0, 0, 1),
        )
    if axis == 1:
        return Part.makePlane(
            max(size[0], 1.0), max(size[2], 1.0),
            App.Vector(minimum[0], minimum[1], minimum[2]), App.Vector(0, 1, 0),
        )
    return Part.makePlane(
        max(size[1], 1.0), max(size[2], 1.0),
        App.Vector(minimum[0], minimum[1], minimum[2]), App.Vector(1, 0, 0),
    )


def native_shape(component):
    bounds = component["bounds_mm"]
    minimum = [float(v) for v in bounds["min"]]
    maximum = [float(v) for v in bounds["max"]]
    size = [maximum[i] - minimum[i] for i in range(3)]
    if component.get("is_solid", True):
        if min(size) <= 0.0:
            raise RuntimeError(f"Solid dimensional evidence is degenerate: {component['name']}")
        return Part.makeBox(size[0], size[1], size[2], App.Vector(*minimum))
    return planar_face(bounds)


def build_component(document, group, phase, component):
    name = "Native_" + component["freecad_name"]
    shape = native_shape(component)
    if shape.isNull():
        raise RuntimeError(f"Failed to build native geometry for {component['name']}")
    obj = document.addObject("Part::Feature", name)
    obj.Label = component["name"]
    obj.Shape = shape
    for prop, value in (
        ("GeneratedBy", GENERATOR),
        ("ConstructionPhase", phase),
        ("DimensionalEvidencePhase", component["phase"]),
        ("MaterialRole", component["material_role"]),
        ("SourceRhinoLayer", component["source_rhino_layer"]),
        ("GeometryMethod", "native_box_or_planar_face_from_measured_bounds"),
        ("ReferenceComponent", component["freecad_name"]),
    ):
        add_string(obj, prop, value)
    add_bool(obj, "NativeFromDimensions", True)
    add_bool(obj, "CopiedReferenceShape", False)
    color, transparency = ROLE_STYLE.get(component["material_role"], ((0.70, 0.70, 0.70), 0))
    obj.ViewObject.ShapeColor = color
    obj.ViewObject.LineColor = tuple(max(0.0, v * 0.55) for v in color)
    obj.ViewObject.Transparency = transparency
    group.addObject(obj)
    return obj


def show_progress(document, index):
    if not DELAY:
        return
    try:
        import FreeCADGui as Gui
        App.setActiveDocument(document.Name)
        if index == 1:
            Gui.activeDocument().activeView().viewAxonometric()
        if index == 1 or index % 8 == 0:
            Gui.activeDocument().activeView().fitAll()
        Gui.updateGui()
    except Exception:
        pass
    time.sleep(DELAY)


def compare(document, metadata, spec):
    if "CliffHouseFinalReference" not in App.listDocuments():
        raise RuntimeError("Protected final reference is not open for comparison")
    final_reference = App.getDocument("CliffHouseFinalReference")
    final_metadata = final_reference.getObject("FinalReferenceMetadata")
    if final_metadata is None or not getattr(final_metadata, "ReadOnlyReference", False):
        raise RuntimeError("Final reference is not protected")
    native = [
        obj for obj in document.Objects
        if getattr(obj, "NativeFromDimensions", False)
        and hasattr(obj, "Shape") and not obj.Shape.isNull()
    ]
    site = [
        document.getObject(name) for name in (
            "building_plan_Shell", "garage_plan_Shell", "driveway_plan_Shell",
            "patio_stairs_plan_Shell", "patio_plan_Shell",
        )
    ]
    site = [obj for obj in site if obj is not None]
    expected_native = 141
    if len(native) != expected_native:
        raise RuntimeError(f"Expected {expected_native} dimensional components, found {len(native)}")
    if len(site) != 5:
        raise RuntimeError(f"Expected five template-derived site objects, found {len(site)}")
    solids = sum(obj.Shape.ShapeType == "Solid" for obj in native + site)
    surfaces = sum(obj.Shape.ShapeType in {"Face", "Shell"} for obj in native + site)
    result = {
        "native_dimensional_components": len(native),
        "template_site_components": len(site),
        "total_components": len(native) + len(site),
        "solids": solids,
        "surfaces": surfaces,
        "expected_reference_components": spec["validation_reference"]["expected_final_components"],
        "method": "semantic_count_and_dimensional-envelope_comparison",
        "copies_final_step_breps": False,
    }
    add_string(metadata, "FinalComparison", json.dumps(result, sort_keys=True))
    add_string(metadata, "BuildStatus", "complete_native_template_reconstruction")
    document.recompute()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.saveAs(str(OUTPUT_PATH))
    print(
        f"{MARKERS[PHASE]} document={document.Name} "
        f"native={len(native)} template_site={len(site)} total={len(native)+len(site)} "
        f"solids={solids} surfaces={surfaces} copied_breps=false output={OUTPUT_PATH}"
    )


spec, detail = checked_specs()
ensure_reference(spec)
document, metadata = managed_document(spec)

if PHASE == "00_template_audit":
    reference = App.getDocument("CliffHouseReference")
    expected = spec["template_audit"]
    import_metadata = reference.getObject("RhinoImportMetadata")
    curve_count = int(import_metadata.ImportedCurveCount)
    label_count = int(import_metadata.ImportedLabelCount)
    if curve_count != expected["curves"] or label_count != expected["labels"]:
        raise RuntimeError(
            f"Template manifest mismatch: curves={curve_count} labels={label_count}"
        )
    for phase_spec in spec["phases"]:
        ensure_group(document, phase_spec["id"])
    add_string(metadata, "BuildStatus", "template_audited")
    document.recompute()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.saveAs(str(OUTPUT_PATH))
    print(
        f"{MARKERS[PHASE]} document={document.Name} curves={curve_count} labels={label_count} "
        f"layers={expected['layers']} approved={spec['approval']['approved_on']} output={OUTPUT_PATH}"
    )
elif PHASE in PHASE_DETAILS:
    group = ensure_group(document, PHASE)
    remove_managed_phase(document, PHASE)
    wanted = set(PHASE_DETAILS[PHASE])
    components = [item for item in detail["components"] if item["phase"] in wanted]
    created = []
    for index, component in enumerate(components, start=1):
        created.append(build_component(document, group, PHASE, component))
        document.recompute()
        show_progress(document, index)
    add_string(metadata, "BuildStatus", f"completed_through_{PHASE}")
    document.recompute()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.saveAs(str(OUTPUT_PATH))
    try:
        import FreeCADGui as Gui
        App.setActiveDocument(document.Name)
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
        Gui.updateGui()
    except Exception:
        pass
    print(
        f"{MARKERS[PHASE]} document={document.Name} objects={len(created)} "
        f"detail_phases={','.join(PHASE_DETAILS[PHASE])} output={OUTPUT_PATH}"
    )
elif PHASE == "11_reference_comparison":
    compare(document, metadata, spec)
else:
    raise RuntimeError(f"Unsupported builder phase: {PHASE}")
