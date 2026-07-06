"""Run inside FreeCAD to build terrain from the five imported Rhino guide curves.

This is the checked-in, idempotent successor to the exploratory ~/terrain.py.
It uses a Coons-style boundary blend plus the middle U guide instead of sampling
the south guide for both north and south elevations.
"""

import os
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
import Mesh


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
        "/home/nvidia/aec-demo/source_models/cliff_house/cliff_house_rebuild.FCStd",
    )
)
NX = int(os.environ.get("AEC_TERRAIN_NX", "81"))
NY = int(os.environ.get("AEC_TERRAIN_NY", "73"))
if NX < 3 or NY < 3:
    raise RuntimeError("Terrain grid dimensions must each be at least 3")


def source_edge(reference, name):
    obj = reference.getObject(name)
    if obj is None or obj.Shape.isNull() or len(obj.Shape.Edges) != 1:
        raise RuntimeError(f"Missing one-edge reference curve: {name}")
    return obj.Shape.Edges[0]


def point_fraction(edge, fraction):
    start, end = edge.ParameterRange
    return edge.valueAt(start + (end - start) * fraction)


def horizontal_point(edge, u):
    # Rhino horizontal guides run east -> west; u runs west -> east.
    return point_fraction(edge, 1.0 - u)


def vertical_point(edge, v):
    # Rhino vertical guides run north -> south; v runs south -> north.
    return point_fraction(edge, 1.0 - v)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def set_string_property(obj, name, value):
    if name not in obj.PropertiesList:
        obj.addProperty("App::PropertyString", name, "AEC Demo")
    setattr(obj, name, value)


reference = App.getDocument(REFERENCE_DOCUMENT)
if reference is None:
    raise RuntimeError(
        f"FreeCAD document {REFERENCE_DOCUMENT!r} is not open"
    )
document = (
    App.getDocument(REBUILD_DOCUMENT)
    if REBUILD_DOCUMENT in App.listDocuments()
    else App.newDocument(REBUILD_DOCUMENT)
)

south = source_edge(reference, "Rhino_004_NurbsCurve")
north = source_edge(reference, "Rhino_011_NurbsCurve")
east = source_edge(reference, "Rhino_012_NurbsCurve")
west = source_edge(reference, "Rhino_013_NurbsCurve")
middle = source_edge(reference, "Rhino_014_NurbsCurve")

west_south = vertical_point(west, 0.0)
west_north = vertical_point(west, 1.0)
east_south = vertical_point(east, 0.0)
east_north = vertical_point(east, 1.0)
x_min = min(west_south.x, west_north.x)
x_max = max(east_south.x, east_north.x)
y_min = min(west_south.y, east_south.y)
y_max = max(west_north.y, east_north.y)

corner_sw = horizontal_point(south, 0.0).z
corner_se = horizontal_point(south, 1.0).z
corner_nw = horizontal_point(north, 0.0).z
corner_ne = horizontal_point(north, 1.0).z
guide_edges = (south, north, east, west, middle)
guide_elevations = [
    point_fraction(edge, sample / 200.0).z
    for edge in guide_edges
    for sample in range(201)
]
guide_z_min = min(guide_elevations)
guide_z_max = max(guide_elevations)


def boundary_surface_z(u, v, west_z, east_z):
    south_z = horizontal_point(south, u).z
    north_z = horizontal_point(north, u).z
    bilinear = (
        (1.0 - u) * (1.0 - v) * corner_sw
        + u * (1.0 - v) * corner_se
        + (1.0 - u) * v * corner_nw
        + u * v * corner_ne
    )
    return (
        (1.0 - v) * south_z
        + v * north_z
        + (1.0 - u) * west_z
        + u * east_z
        - bilinear
    )


vertices = []
for row in range(NY):
    v = row / (NY - 1)
    west_point = vertical_point(west, v)
    east_point = vertical_point(east, v)
    middle_point = vertical_point(middle, v)
    middle_u = (middle_point.x - x_min) / (x_max - x_min)
    middle_base = boundary_surface_z(
        middle_u,
        v,
        west_point.z,
        east_point.z,
    )
    middle_delta = middle_point.z - middle_base

    for column in range(NX):
        u = column / (NX - 1)
        x = x_min + u * (x_max - x_min)
        y = y_min + v * (y_max - y_min)
        base_z = boundary_surface_z(
            u,
            v,
            west_point.z,
            east_point.z,
        )
        if u <= middle_u:
            guide_weight = u / middle_u if middle_u > 0.0 else 0.0
        else:
            guide_weight = (
                (1.0 - u) / (1.0 - middle_u)
                if middle_u < 1.0
                else 0.0
            )
        z = base_z + smoothstep(guide_weight) * middle_delta
        z = max(guide_z_min, min(guide_z_max, z))
        vertices.append(App.Vector(x, y, z))

triangles = []
for row in range(NY - 1):
    for column in range(NX - 1):
        southwest = row * NX + column
        southeast = southwest + 1
        northwest = (row + 1) * NX + column
        northeast = northwest + 1
        triangles.append(
            [
                vertices[southwest],
                vertices[southeast],
                vertices[northwest],
            ]
        )
        triangles.append(
            [
                vertices[southeast],
                vertices[northeast],
                vertices[northwest],
            ]
        )

for old in list(document.Objects):
    if (
        old.Name.startswith("TerrainSurface")
        and old.TypeId in {"Mesh::Feature", "Part::Feature"}
    ):
        document.removeObject(old.Name)

terrain = document.addObject("Mesh::Feature", "TerrainSurface")
terrain.Label = "Terrain Surface"
terrain.Mesh = Mesh.Mesh(triangles)
set_string_property(
    terrain,
    "GeneratedBy",
    "scripts/build-cliff-house-terrain.py",
)
set_string_property(terrain, "SourceDocument", REFERENCE_DOCUMENT)
set_string_property(
    terrain,
    "SourceGuideCurves",
    "Rhino_004,Rhino_011,Rhino_012,Rhino_013,Rhino_014",
)
set_string_property(terrain, "MaterialRole", "terrain")
terrain.addProperty("App::PropertyInteger", "GridNX", "AEC Demo")
terrain.addProperty("App::PropertyInteger", "GridNY", "AEC Demo")
terrain.GridNX = NX
terrain.GridNY = NY
terrain.ViewObject.ShapeColor = (0.27, 0.36, 0.18)
terrain.ViewObject.LineColor = (0.11, 0.15, 0.08)

role_settings = {
    "building_plan_Shell": (
        "building_pad",
        (0.42, 0.44, 0.48),
    ),
    "garage_plan_Shell": (
        "garage",
        (0.52, 0.54, 0.57),
    ),
    "driveway_plan_Shell": (
        "driveway",
        (0.16, 0.17, 0.18),
    ),
    "patio_stairs_plan_Shell": (
        "stairs",
        (0.62, 0.60, 0.55),
    ),
    "patio_plan_Shell": (
        "patio",
        (0.70, 0.68, 0.62),
    ),
}
for name, (role, color) in role_settings.items():
    obj = document.getObject(name)
    if obj is None:
        continue
    set_string_property(obj, "MaterialRole", role)
    obj.ViewObject.ShapeColor = color

document.recompute()
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
document.saveAs(str(OUTPUT_PATH))
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
box = terrain.Mesh.BoundBox
print(
    f"TERRAIN_BUILD_OK={OUTPUT_PATH} "
    f"vertices={len(vertices)} faces={len(triangles)} "
    f"bounds_mm=[{box.XMin:.3f},{box.YMin:.3f},{box.ZMin:.3f}]-"
    f"[{box.XMax:.3f},{box.YMax:.3f},{box.ZMax:.3f}]"
)
