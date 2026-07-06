"""Build five site slabs from the imported Rhino reference curves.

Run inside FreeCAD through the FreeCAD MCP execute_code tool.
All footprint coordinates and elevations come from the source Shapes.
"""

import os
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
import Part


REFERENCE_NAME = "CliffHouseReference"
REBUILD_NAME = os.environ.get(
    "AEC_REBUILD_DOCUMENT",
    "CliffHouseRebuild",
)
OUTPUT = Path(
    os.environ.get(
        "AEC_REBUILD_FCSTD",
        "/home/nvidia/aec-demo/source_models/cliff_house/cliff_house_rebuild.FCStd",
    )
)
THICKNESS = 50.0
GENERATOR = "scripts/build-cliff-house-site-slabs.py"
SOURCES = [
    (
        "Rhino_000_building_plan",
        "building_plan_Shell",
        "building_pad",
        (0.42, 0.44, 0.48),
    ),
    (
        "Rhino_002_garage_plan",
        "garage_plan_Shell",
        "garage",
        (0.52, 0.54, 0.57),
    ),
    (
        "Rhino_001_driveway_plan",
        "driveway_plan_Shell",
        "driveway",
        (0.16, 0.17, 0.18),
    ),
    (
        "Rhino_003_patio_stairs_plan",
        "patio_stairs_plan_Shell",
        "stairs",
        (0.62, 0.60, 0.55),
    ),
    (
        "Rhino_008_PolylineCurve",
        "patio_plan_Shell",
        "patio",
        (0.70, 0.68, 0.62),
    ),
]


def string_property(obj, name, value):
    if name not in obj.PropertiesList:
        obj.addProperty(
            "App::PropertyString",
            name,
            "AEC Demo",
        )
    setattr(obj, name, value)


if REFERENCE_NAME not in App.listDocuments():
    raise RuntimeError(
        "CliffHouseReference is not open"
    )
reference = App.getDocument(REFERENCE_NAME)
document = (
    App.getDocument(REBUILD_NAME)
    if REBUILD_NAME in App.listDocuments()
    else App.newDocument(REBUILD_NAME)
)

created = []
for source_name, output_name, role, color in SOURCES:
    source = reference.getObject(source_name)
    if source is None or source.Shape.isNull():
        raise RuntimeError(
            f"Missing source curve {source_name}"
        )
    wire = (
        source.Shape
        if source.Shape.ShapeType == "Wire"
        else Part.Wire(source.Shape.Edges)
    )
    if not wire.isClosed():
        raise RuntimeError(
            f"Source curve {source_name} is not closed"
        )

    existing = document.getObject(output_name)
    if existing is not None:
        if (
            getattr(existing, "GeneratedBy", "")
            != GENERATOR
        ):
            raise RuntimeError(
                f"Refusing to replace {output_name}"
            )
        document.removeObject(existing.Name)
        document.recompute()

    face = Part.Face(wire)
    solid = face.extrude(
        App.Vector(0.0, 0.0, THICKNESS)
    )
    if solid.isNull() or len(solid.Solids) != 1:
        raise RuntimeError(
            f"Failed to extrude {source_name}"
        )

    obj = document.addObject(
        "Part::Feature",
        output_name,
    )
    obj.Label = output_name
    obj.Shape = solid
    string_property(
        obj,
        "GeneratedBy",
        GENERATOR,
    )
    string_property(
        obj,
        "SourceReferenceObject",
        source.Name,
    )
    string_property(
        obj,
        "SourceRhinoName",
        str(
            getattr(
                source,
                "RhinoObjectName",
                "",
            )
            or ""
        ),
    )
    string_property(
        obj,
        "SourceRhinoLayer",
        str(
            getattr(
                source,
                "RhinoLayerPath",
                "",
            )
            or ""
        ),
    )
    string_property(
        obj,
        "MaterialRole",
        role,
    )
    obj.ViewObject.ShapeColor = color
    created.append(obj)

document.recompute()
OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)
document.saveAs(str(OUTPUT))
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()

for obj in created:
    box = obj.Shape.BoundBox
    print(
        f"SITE_SLAB_DERIVED name={obj.Name} "
        f"source={obj.SourceReferenceObject} "
        f"base_z_mm={box.ZMin:.3f} "
        f"size_mm=[{box.XLength:.3f},"
        f"{box.YLength:.3f},{box.ZLength:.3f}]"
    )

print(
    f"SITE_SLABS_BUILD_OK={OUTPUT} "
    f"objects={len(created)} "
    f"thickness_mm={THICKNESS:.3f}"
)
