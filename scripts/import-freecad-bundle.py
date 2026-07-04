"""Run inside Blender to import a bundle from export-freecad-for-blender.py."""

import json
import os
from pathlib import Path

import bpy


BUNDLE_DIR = Path(
    os.environ.get(
        "AES_FREECAD_EXPORT_DIR",
        "/tmp/aes-demo-freecad-export",
    )
)
MANIFEST_PATH = BUNDLE_DIR / "manifest.json"
manifest = json.loads(
    MANIFEST_PATH.read_text(encoding="utf-8")
)
collection_name = "FreeCAD Import"
collection = bpy.data.collections.get(collection_name)
if collection is None:
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)

# Remove prior imports even if an interrupted run linked one elsewhere.
stale_objects = set(collection.objects)
for candidate in bpy.data.objects:
    if (
        candidate.get("freecad_source_document")
        == manifest["document"]
    ):
        stale_objects.add(candidate)
for old_object in stale_objects:
    bpy.data.objects.remove(old_object, do_unlink=True)

role_materials = {
    "terrain": {
        "color": (0.20, 0.30, 0.10, 1.0),
        "roughness": 0.92,
    },
    "building_pad": {
        "color": (0.34, 0.36, 0.40, 1.0),
        "roughness": 0.72,
    },
    "garage": {
        "color": (0.48, 0.50, 0.53, 1.0),
        "roughness": 0.68,
    },
    "driveway": {
        "color": (0.055, 0.06, 0.07, 1.0),
        "roughness": 0.82,
    },
    "patio": {
        "color": (0.60, 0.56, 0.47, 1.0),
        "roughness": 0.78,
    },
    "stairs": {
        "color": (0.52, 0.50, 0.45, 1.0),
        "roughness": 0.74,
    },
    "generic": {
        "color": (0.72, 0.72, 0.72, 1.0),
        "roughness": 0.55,
    },
}

scale = float(manifest.get("blender_scale", 0.001))
imported_count = 0
seen_names = set()
for item in manifest["objects"]:
    source_name = item["freecad_name"]
    if source_name in seen_names:
        raise RuntimeError(
            f"Duplicate FreeCAD identity in manifest: {source_name}"
        )
    seen_names.add(source_name)

    bpy.ops.object.select_all(action="DESELECT")
    result = bpy.ops.wm.obj_import(
        filepath=str(BUNDLE_DIR / item["mesh"])
    )
    if "FINISHED" not in result:
        raise RuntimeError(
            f"OBJ import failed for {item['mesh']}: {result}"
        )
    new_objects = list(bpy.context.selected_objects)
    mesh_objects = [
        obj
        for obj in new_objects
        if obj.type == "MESH"
    ]
    if len(mesh_objects) != 1:
        raise RuntimeError(
            f"Expected one mesh from {item['mesh']}, got "
            f"{[(obj.name, obj.type) for obj in new_objects]}"
        )
    obj = mesh_objects[0]
    for extra in new_objects:
        if extra is not obj:
            bpy.data.objects.remove(extra, do_unlink=True)

    existing = bpy.data.objects.get(item["label"])
    if existing is not None and existing is not obj:
        raise RuntimeError(
            f"Object name collision while importing "
            f"{item['label']!r}"
        )
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.name = item["label"]
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (scale, scale, scale)
    obj["freecad_name"] = source_name
    obj["freecad_type_id"] = item["type_id"]
    obj["freecad_geometry_kind"] = item.get(
        "geometry_kind",
        "part_shape",
    )
    obj["freecad_source_document"] = manifest["document"]
    role = item.get("material_role", "generic")
    obj["material_role"] = role

    settings = role_materials.get(
        role,
        role_materials["generic"],
    )
    color = settings.get(
        "color",
        item.get(
            "color_rgba",
            [0.72, 0.72, 0.72, 1.0],
        ),
    )
    material_name = f"AEC::{role}"
    material = (
        bpy.data.materials.get(material_name)
        or bpy.data.materials.new(material_name)
    )
    material.diffuse_color = color
    material.use_nodes = True
    principled = material.node_tree.nodes.get(
        "Principled BSDF"
    )
    if principled:
        principled.inputs[
            "Base Color"
        ].default_value = color
        principled.inputs[
            "Roughness"
        ].default_value = settings["roughness"]
    obj.data.materials.clear()
    obj.data.materials.append(material)

    if role == "terrain":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    if max(obj.dimensions) <= 0:
        raise RuntimeError(
            f"Imported mesh {obj.name!r} has zero-size bounds"
        )
    imported_count += 1

if imported_count != len(manifest["objects"]):
    raise RuntimeError(
        f"Imported {imported_count} meshes for "
        f"{len(manifest['objects'])} manifest objects"
    )

bpy.context.scene["freecad_manifest"] = str(MANIFEST_PATH)
bpy.context.scene[
    "freecad_source_document"
] = manifest["document"]
bpy.ops.wm.save_as_mainfile(
    filepath="/tmp/aes-demo-freecad-import.blend"
)
print(
    f"BLENDER_IMPORT_OK={MANIFEST_PATH} "
    f"objects={imported_count} "
    f"roles={sorted({item.get('material_role', 'generic') for item in manifest['objects']})}"
)
