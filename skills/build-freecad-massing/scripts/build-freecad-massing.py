"""Build checked FreeCAD massing from a versioned JSON specification.

Run inside FreeCAD through the FreeCAD MCP execute_code tool.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
import Part


FORMAT = "aec-demo-freecad-massing-v1"
GENERATOR = (
    "skills/build-freecad-massing/scripts/"
    "build-freecad-massing.py"
)
SPEC_PATH = Path(
    os.environ.get(
        "AEC_MASSING_SPEC",
        "/home/nvidia/aec-demo/skills/build-freecad-massing/"
        "assets/cliff-house-massing-v1.json",
    )
)
REFERENCE_DOCUMENT = os.environ.get(
    "AEC_RHINO_REFERENCE_DOCUMENT",
    "CliffHouseReference",
)
REBUILD_DOCUMENT = os.environ.get(
    "AEC_REBUILD_DOCUMENT",
    "CliffHouseRebuild",
)
OUTPUT_PATH = Path(
    os.environ.get(
        "AEC_REBUILD_FCSTD",
        "/home/nvidia/aec-demo/source_models/cliff_house/"
        "cliff_house_rebuild.FCStd",
    )
)
TOLERANCE_MM = 0.1


def add_string(obj, name, value):
    if name not in obj.PropertiesList:
        obj.addProperty(
            "App::PropertyString",
            name,
            "AEC Massing",
        )
    setattr(obj, name, str(value))


def add_string_list(obj, name, values):
    if name not in obj.PropertiesList:
        obj.addProperty(
            "App::PropertyStringList",
            name,
            "AEC Massing",
        )
    setattr(obj, name, [str(value) for value in values])


def checked_triplet(value, label):
    if not isinstance(value, list) or len(value) != 3:
        raise RuntimeError(f"{label} must contain three numbers")
    return [float(item) for item in value]


def close_enough(actual, expected):
    return abs(float(actual) - float(expected)) <= TOLERANCE_MM


spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
if spec.get("format") != FORMAT:
    raise RuntimeError(
        f"Unexpected massing spec format: {spec.get('format')!r}"
    )
spec_id = str(spec.get("id", "")).strip()
if not spec_id:
    raise RuntimeError("Massing spec id is required")
if spec.get("source_units") != "metres":
    raise RuntimeError("Massing spec source_units must be metres")
scale = float(spec.get("scale_to_mm", 0.0))
if scale <= 0:
    raise RuntimeError("Massing scale_to_mm must be positive")
translation = checked_triplet(
    spec.get("translation_mm"),
    "translation_mm",
)

if REFERENCE_DOCUMENT not in App.listDocuments():
    raise RuntimeError(
        f"Reference document {REFERENCE_DOCUMENT!r} is not open"
    )
reference = App.getDocument(REFERENCE_DOCUMENT)
for check in spec.get("reference_checks", []):
    source = reference.getObject(str(check["object"]))
    if source is None:
        raise RuntimeError(
            f"Reference anchor {check['object']!r} is missing"
        )
    shape = getattr(source, "Shape", None)
    if shape is None or shape.isNull():
        raise RuntimeError(
            f"Reference anchor {source.Name!r} has no Shape"
        )
    expected_min = checked_triplet(
        check["bounds_mm"]["min"],
        f"{source.Name} expected min",
    )
    expected_max = checked_triplet(
        check["bounds_mm"]["max"],
        f"{source.Name} expected max",
    )
    box = shape.BoundBox
    actual_min = [box.XMin, box.YMin, box.ZMin]
    actual_max = [box.XMax, box.YMax, box.ZMax]
    if not all(
        close_enough(actual, expected)
        for actual, expected in zip(
            actual_min + actual_max,
            expected_min + expected_max,
        )
    ):
        raise RuntimeError(
            f"Reference anchor mismatch for {source.Name}: "
            f"actual={actual_min}-{actual_max} "
            f"expected={expected_min}-{expected_max}"
        )

groups = spec.get("groups", [])
objects = spec.get("objects", [])
group_names = [str(item["name"]) for item in groups]
object_names = [str(item["name"]) for item in objects]
if len(group_names) != len(set(group_names)):
    raise RuntimeError("Massing group names must be unique")
if len(object_names) != len(set(object_names)):
    raise RuntimeError("Massing object names must be unique")
if len(objects) != 11:
    raise RuntimeError(
        f"Expected the upstream 11-object recipe, found {len(objects)}"
    )
if any(item["group"] not in group_names for item in objects):
    raise RuntimeError("Every massing object must reference a known group")

validated = []
for item in objects:
    source_min = checked_triplet(
        item["bounds_source_m"]["min"],
        f"{item['name']} source min",
    )
    source_max = checked_triplet(
        item["bounds_source_m"]["max"],
        f"{item['name']} source max",
    )
    built_min = [
        source_min[index] * scale + translation[index]
        for index in range(3)
    ]
    built_max = [
        source_max[index] * scale + translation[index]
        for index in range(3)
    ]
    size = [
        built_max[index] - built_min[index]
        for index in range(3)
    ]
    if any(value <= 0 for value in size):
        raise RuntimeError(
            f"{item['name']} has non-positive size {size}"
        )
    color = checked_triplet(
        item.get("color_rgb", [0.75, 0.75, 0.75]),
        f"{item['name']} color",
    )
    if any(value < 0 or value > 1 for value in color):
        raise RuntimeError(
            f"{item['name']} color must be in [0, 1]"
        )
    validated.append(
        (item, source_min, source_max, built_min, built_max, size, color)
    )

document = (
    App.getDocument(REBUILD_DOCUMENT)
    if REBUILD_DOCUMENT in App.listDocuments()
    else App.newDocument(REBUILD_DOCUMENT)
)

for name in object_names + ["CliffHouseMassing"] + group_names:
    existing = document.getObject(name)
    if existing is not None and getattr(existing, "GeneratedBy", "") != GENERATOR:
        raise RuntimeError(
            f"Refusing to replace unmanaged object {name!r}"
        )

managed_features = [
    obj
    for obj in document.Objects
    if getattr(obj, "GeneratedBy", "") == GENERATOR
    and obj.TypeId == "Part::Feature"
]
managed_groups = [
    obj
    for obj in document.Objects
    if getattr(obj, "GeneratedBy", "") == GENERATOR
    and obj.TypeId == "App::DocumentObjectGroup"
]
for obj in managed_features + managed_groups:
    document.removeObject(obj.Name)
document.recompute()

parent = document.addObject(
    "App::DocumentObjectGroup",
    "CliffHouseMassing",
)
parent.Label = "Cliff House Massing"
add_string(parent, "GeneratedBy", GENERATOR)
add_string(parent, "MassingSpecId", spec_id)
add_string(parent, "MassingSpecPath", str(SPEC_PATH))
add_string(
    parent,
    "Provenance",
    spec.get("provenance", {}).get("note", ""),
)

created_groups = {}
for group_spec in groups:
    group = document.addObject(
        "App::DocumentObjectGroup",
        str(group_spec["name"]),
    )
    group.Label = str(group_spec.get("label", group.Name))
    add_string(group, "GeneratedBy", GENERATOR)
    add_string(group, "MassingSpecId", spec_id)
    parent.addObject(group)
    created_groups[group.Name] = group

created = []
for (
    item,
    source_min,
    source_max,
    built_min,
    built_max,
    size,
    color,
) in validated:
    shape = Part.makeBox(
        size[0],
        size[1],
        size[2],
        App.Vector(*built_min),
    )
    if shape.isNull() or len(shape.Solids) != 1:
        raise RuntimeError(
            f"Failed to create one solid for {item['name']}"
        )
    obj = document.addObject(
        "Part::Feature",
        str(item["name"]),
    )
    obj.Label = str(item["name"])
    obj.Shape = shape
    add_string(obj, "GeneratedBy", GENERATOR)
    add_string(obj, "MassingSpecId", spec_id)
    add_string(obj, "MassingSpecPath", str(SPEC_PATH))
    add_string(obj, "DesignPhase", "massing")
    add_string(obj, "ArchitecturalRole", item["role"])
    add_string(obj, "MaterialRole", item["role"])
    add_string(obj, "UpstreamLayer", item["upstream_layer"])
    add_string(
        obj,
        "UpstreamBoundsMetres",
        json.dumps(
            {"min": source_min, "max": source_max},
            separators=(",", ":"),
        ),
    )
    add_string(
        obj,
        "BuiltBoundsMillimetres",
        json.dumps(
            {"min": built_min, "max": built_max},
            separators=(",", ":"),
        ),
    )
    add_string_list(
        obj,
        "SourceReferenceObjects",
        item.get("source_reference_objects", []),
    )
    obj.ViewObject.ShapeColor = tuple(color)
    created_groups[str(item["group"])].addObject(obj)
    created.append(obj)

document.recompute()
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
document.saveAs(str(OUTPUT_PATH))
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()

total_volume = 0.0
for obj in created:
    box = obj.Shape.BoundBox
    total_volume += float(obj.Shape.Volume)
    print(
        f"MASSING_OBJECT name={obj.Name} "
        f"role={obj.MaterialRole} "
        f"source_bounds_m={obj.UpstreamBoundsMetres} "
        f"built_bounds_mm=[{box.XMin:.3f},{box.YMin:.3f},"
        f"{box.ZMin:.3f}]-[{box.XMax:.3f},"
        f"{box.YMax:.3f},{box.ZMax:.3f}] "
        f"volume_mm3={obj.Shape.Volume:.3f}"
    )

print(
    f"FREECAD_MASSING_BUILD_OK={OUTPUT_PATH} "
    f"spec={spec_id} objects={len(created)} "
    f"translation_mm={translation} "
    f"total_volume_mm3={total_volume:.3f}"
)
