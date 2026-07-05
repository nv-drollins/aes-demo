"""Run inside FreeCAD to export render meshes plus an object metadata manifest."""

import json
import os
from pathlib import Path
import re

import FreeCAD as App
import Mesh


OUTPUT_DIR = Path(
    os.environ.get(
        "AES_FREECAD_EXPORT_DIR",
        "/tmp/aes-demo-freecad-export",
    )
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENT_NAME = os.environ.get(
    "AES_FREECAD_DOCUMENT",
    "PromptTest",
)
doc = (
    App.getDocument(DOCUMENT_NAME)
    if DOCUMENT_NAME in App.listDocuments()
    else App.ActiveDocument
)
if doc is None:
    raise RuntimeError("FreeCAD has no active document")


def safe_name(value):
    value = re.sub(
        r"[^A-Za-z0-9_.-]+",
        "_",
        value,
    ).strip("._")
    return value or "object"


def color_for(obj):
    view = getattr(obj, "ViewObject", None)
    rgb = tuple(
        getattr(view, "ShapeColor", (0.72, 0.72, 0.72))
    )
    transparency = float(
        getattr(view, "Transparency", 0.0)
    )
    return [
        *map(float, rgb[:3]),
        1.0 - transparency / 100.0,
    ]


def inferred_material_role(obj):
    explicit = str(
        getattr(obj, "MaterialRole", "") or ""
    )
    if explicit:
        return explicit
    lowered = f"{obj.Name} {obj.Label}".lower()
    for token, role in (
        ("terrain", "terrain"),
        ("driveway", "driveway"),
        ("garage", "garage"),
        ("stairs", "stairs"),
        ("patio", "patio"),
        ("building", "building_pad"),
    ):
        if token in lowered:
            return role
    return "generic"


objects = []
used_names = set()
for obj in doc.Objects:
    shape = getattr(obj, "Shape", None)
    mesh = getattr(obj, "Mesh", None)
    has_shape = (
        obj.TypeId.startswith("Part::")
        and shape is not None
        and not shape.isNull()
    )
    has_mesh = (
        obj.TypeId.startswith("Mesh::")
        and mesh is not None
        and getattr(mesh, "CountFacets", 0) > 0
    )
    if not has_shape and not has_mesh:
        continue

    stem = safe_name(obj.Label or obj.Name)
    candidate = stem
    index = 2
    while candidate in used_names:
        candidate = f"{stem}_{index}"
        index += 1
    used_names.add(candidate)

    mesh_file = f"{candidate}.obj"
    Mesh.export([obj], str(OUTPUT_DIR / mesh_file))
    geometry = shape if has_shape else mesh
    bounds = geometry.BoundBox
    objects.append(
        {
            "freecad_name": obj.Name,
            "label": obj.Label,
            "type_id": obj.TypeId,
            "geometry_kind": (
                "part_shape"
                if has_shape
                else "mesh"
            ),
            "material_role": inferred_material_role(obj),
            "mesh": mesh_file,
            "color_rgba": color_for(obj),
            "bounds_mm": {
                "min": [
                    bounds.XMin,
                    bounds.YMin,
                    bounds.ZMin,
                ],
                "max": [
                    bounds.XMax,
                    bounds.YMax,
                    bounds.ZMax,
                ],
            },
        }
    )

if not objects:
    inventory = [
        (obj.Name, obj.TypeId)
        for obj in doc.Objects
    ]
    raise RuntimeError(
        f"FreeCAD document {doc.Name!r} contains no "
        f"exportable shapes or meshes. Open documents: "
        f"{list(App.listDocuments())}; "
        f"object inventory: {inventory}"
    )

manifest = {
    "format": "aes-demo-freecad-bundle-v1",
    "document": doc.Name,
    "source_file": doc.FileName,
    "source_units": "millimetres",
    "blender_scale": 0.001,
    "objects": objects,
}
manifest_path = OUTPUT_DIR / "manifest.json"
manifest_path.write_text(
    json.dumps(manifest, indent=2),
    encoding="utf-8",
)
print(
    f"FREECAD_EXPORT_OK={manifest_path} "
    f"objects={len(objects)} "
    f"parts={sum(item['geometry_kind'] == 'part_shape' for item in objects)} "
    f"meshes={sum(item['geometry_kind'] == 'mesh' for item in objects)}"
)
