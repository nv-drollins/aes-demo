"""Apply complete cliff-house materials and missing water features in Blender."""

from __future__ import annotations

import json
import os
from pathlib import Path

import bpy


ROOT = Path("/home/nvidia/aec-demo")
SPEC_PATH = Path(
    os.environ.get(
        "AEC_FINAL_RECONSTRUCTION_SPEC",
        ROOT / "source_models/cliff_house/final_reconstruction_spec.json",
    )
)
INVENTORY_PATH = Path(
    os.environ.get(
        "AEC_FINAL_RHINO_INVENTORY",
        ROOT / "source_models/cliff_house/final_rhino_inventory.json",
    )
)


def shader_input(shader, names, value):
    for name in names:
        socket = shader.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def material(
    name,
    color,
    roughness,
    metallic=0.0,
    transmission=0.0,
    alpha=1.0,
):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    result.diffuse_color = (*color, alpha)
    shader = result.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader_input(shader, ("Base Color",), (*color, 1.0))
        shader_input(shader, ("Roughness",), roughness)
        shader_input(shader, ("Metallic",), metallic)
        shader_input(shader, ("Transmission Weight", "Transmission"), transmission)
        shader_input(shader, ("Alpha",), alpha)
        shader_input(shader, ("IOR",), 1.45)
    if alpha < 1.0:
        try:
            result.surface_render_method = "DITHERED"
        except Exception:
            pass
    return result


materials = {
    "white_stone": material("AEC::White Ashlar", (0.82, 0.80, 0.74), 0.72),
    "dark_concrete": material("AEC::Dark Concrete", (0.075, 0.085, 0.095), 0.78),
    "light_concrete": material("AEC::Light Concrete", (0.42, 0.43, 0.43), 0.68),
    "bronze": material("AEC::Bronze Anodized", (0.19, 0.095, 0.045), 0.27, metallic=0.82),
    "glass": material("AEC::Tinted Glass", (0.075, 0.16, 0.18), 0.10, transmission=0.62, alpha=0.42),
    "frosted_glass": material("AEC::Frosted Glass", (0.48, 0.58, 0.58), 0.38, transmission=0.38, alpha=0.68),
    "wood": material("AEC::Warm Timber", (0.24, 0.075, 0.025), 0.42),
    "pool_tile": material("AEC::Pool Tile", (0.008, 0.028, 0.038), 0.18),
    "pool_stone": material("AEC::Pool Coping", (0.55, 0.53, 0.48), 0.64),
    "water": material("AEC::Pool Water", (0.015, 0.14, 0.18), 0.06, transmission=0.74, alpha=0.68),
}

spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
components = {item["freecad_name"]: item for item in spec["components"]}
collection = bpy.data.collections.get("FreeCAD Import")
if collection is None or not collection.objects:
    raise RuntimeError("FreeCAD Import collection is empty")


def choose_material(component):
    role = component["material_role"]
    name = component["name"].lower()
    layer = component["source_rhino_layer"].lower()
    if role == "glazing":
        return materials["frosted_glass"] if "frost" in layer or "frost" in name else materials["glass"]
    if role == "metal_frame":
        return materials["bronze"]
    if role == "wood_door":
        return materials["wood"]
    if role == "cladding_dark":
        return materials["dark_concrete"]
    if role == "cladding_light":
        return materials["white_stone"]
    if role == "pool":
        if "stone_rim" in layer or "rim" in name:
            return materials["pool_stone"]
        if "infinity_weir" in layer or "weir" in name:
            return materials["bronze"]
        if "new_deck" in layer:
            return materials["light_concrete"]
        if "retaining_wall" in layer:
            return materials["dark_concrete"]
        return materials["pool_tile"]
    if role == "wall":
        return materials["white_stone"]
    if role in {"concrete_slab", "roof"}:
        return materials["light_concrete"]
    return materials["white_stone"]


styled = 0
for obj in collection.objects:
    source_name = obj.get("freecad_name")
    component = components.get(source_name)
    if component is None:
        raise RuntimeError(f"No reconstruction component for {source_name!r}")
    obj["reconstruction_phase"] = component["phase"]
    obj["source_rhino_index"] = component["source_rhino_index"]
    obj["source_rhino_layer"] = component["source_rhino_layer"]
    obj.data.materials.clear()
    obj.data.materials.append(choose_material(component))
    styled += 1

environment = bpy.data.collections.get("AEC Environment")
if environment is None:
    environment = bpy.data.collections.new("AEC Environment")
    bpy.context.scene.collection.children.link(environment)
for obj in list(environment.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
water_source = next(item for item in inventory["objects"] if item["name"] == "water_surface_new")
minimum = water_source["bounds_source_units"]["min"]
maximum = water_source["bounds_source_units"]["max"]
center = tuple((low + high) / 2 for low, high in zip(minimum, maximum))
dimensions = tuple(max(high - low, 0.015) for low, high in zip(minimum, maximum))
bpy.ops.mesh.primitive_cube_add(location=center)
water = bpy.context.object
water.name = "Infinity Pool Water"
water.dimensions = dimensions
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
water.data.materials.append(materials["water"])
water["material_role"] = "water"
for owner in list(water.users_collection):
    owner.objects.unlink(water)
environment.objects.link(water)

print(
    f"FINAL_BLENDER_STYLE_OK objects={styled} "
    f"materials={len(materials)} water={water.name!r}"
)
