"""Run inside Blender to import a bundle from export-freecad-for-blender.py."""
import json
import os
from pathlib import Path
import bpy

BUNDLE_DIR = Path(os.environ.get("AES_FREECAD_EXPORT_DIR", "/tmp/aes-demo-freecad-export"))
MANIFEST_PATH = BUNDLE_DIR / "manifest.json"
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
collection_name = "FreeCAD Import"
collection = bpy.data.collections.get(collection_name)
if collection is None:
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
else:
    for old_object in list(collection.objects):
        bpy.data.objects.remove(old_object, do_unlink=True)
scale = float(manifest.get("blender_scale", 0.001))
imported_count = 0
for item in manifest["objects"]:
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(BUNDLE_DIR / item["mesh"]))
    new_objects = list(set(bpy.data.objects) - before)
    if not new_objects:
        raise RuntimeError(f"No object imported from {item['mesh']}")
    color = item.get("color_rgba", [0.72, 0.72, 0.72, 1.0])
    material_name = f"FreeCAD::{item['label']}"
    material = bpy.data.materials.get(material_name) or bpy.data.materials.new(material_name)
    material.diffuse_color = color
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Roughness"].default_value = 0.45
    for index, obj in enumerate(new_objects, start=1):
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        collection.objects.link(obj)
        obj.name = item["label"] if index == 1 else f"{item['label']}_{index}"
        obj.scale = (scale, scale, scale)
        obj["freecad_name"] = item["freecad_name"]
        obj["freecad_type_id"] = item["type_id"]
        obj["freecad_source_document"] = manifest["document"]
        if obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(material)
        imported_count += 1
bpy.context.scene["freecad_manifest"] = str(MANIFEST_PATH)
bpy.context.scene["freecad_source_document"] = manifest["document"]
bpy.ops.wm.save_as_mainfile(filepath="/tmp/aes-demo-freecad-import.blend")
print(f"BLENDER_IMPORT_OK={MANIFEST_PATH} objects={imported_count}")
