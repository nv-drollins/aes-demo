"""Create the final Blender hero scene and beauty/depth renders."""

from __future__ import annotations

import glob
import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


OUTPUT_DIR = Path(
    os.environ.get(
        "AEC_FINAL_RENDER_OUTPUT_DIR",
        "/tmp/aec-demo-final-render",
    )
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
collection = bpy.data.collections.get("FreeCAD Import")
if collection is None or not collection.objects:
    raise RuntimeError("FreeCAD Import collection is empty")
render_objects = [obj for obj in collection.objects if obj.type == "MESH"]
environment = bpy.data.collections.get("AEC Environment")
if environment is not None:
    render_objects.extend(obj for obj in environment.objects if obj.type == "MESH")


def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
camera_data = bpy.data.cameras.get("Cliff House Hero Camera") or bpy.data.cameras.new("Cliff House Hero Camera")
camera = bpy.data.objects.get("Cliff House Hero Camera") or bpy.data.objects.new("Cliff House Hero Camera", camera_data)
if not camera.users_collection:
    scene.collection.objects.link(camera)
camera.data.lens = 46
camera.data.sensor_width = 36
camera.data.clip_start = 0.05
camera.data.clip_end = 1000
camera.location = (-27.0, -28.0, 16.0)
look_at(camera, Vector((4.0, -2.0, 4.5)))
scene.camera = camera

sun_data = bpy.data.lights.get("Cliff House Sunset") or bpy.data.lights.new("Cliff House Sunset", "SUN")
sun = bpy.data.objects.get("Cliff House Sunset") or bpy.data.objects.new("Cliff House Sunset", sun_data)
if not sun.users_collection:
    scene.collection.objects.link(sun)
sun.data.energy = 2.8
sun.data.angle = math.radians(8)
sun.data.color = (1.0, 0.54, 0.32)
sun.rotation_euler = (math.radians(55), math.radians(-20), math.radians(-125))

area_data = bpy.data.lights.get("Cliff House Fill") or bpy.data.lights.new("Cliff House Fill", "AREA")
area = bpy.data.objects.get("Cliff House Fill") or bpy.data.objects.new("Cliff House Fill", area_data)
if not area.users_collection:
    scene.collection.objects.link(area)
area.location = (15.0, -5.0, 22.0)
area.data.energy = 950
area.data.shape = "DISK"
area.data.size = 18
look_at(area, Vector((4.0, -2.0, 4.0)))

if scene.world is None:
    scene.world = bpy.data.worlds.new("Cliff House World")
scene.world.use_nodes = True
background = scene.world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.055, 0.075, 0.12, 1.0)
background.inputs["Strength"].default_value = 0.32

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1152
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = False
scene.render.filepath = str(OUTPUT_DIR / "cliff-house-beauty.png")
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.45
for obj in scene.objects:
    obj.hide_render = obj not in render_objects and obj.type not in {"CAMERA", "LIGHT"}

view_layer = bpy.context.view_layer
view_layer.use_pass_z = True
scene.use_nodes = True
tree = scene.node_tree
tree.nodes.clear()
render_layers = tree.nodes.new("CompositorNodeRLayers")
composite = tree.nodes.new("CompositorNodeComposite")
tree.links.new(render_layers.outputs["Image"], composite.inputs["Image"])
normalize = tree.nodes.new("CompositorNodeNormalize")
invert = tree.nodes.new("CompositorNodeInvert")
depth_output = tree.nodes.new("CompositorNodeOutputFile")
depth_output.base_path = str(OUTPUT_DIR)
depth_output.format.file_format = "PNG"
depth_output.format.color_mode = "BW"
depth_output.format.color_depth = "16"
depth_output.file_slots[0].path = "cliff-house-depth-"
tree.links.new(render_layers.outputs["Depth"], normalize.inputs[0])
tree.links.new(normalize.outputs[0], invert.inputs["Color"])
tree.links.new(invert.outputs["Color"], depth_output.inputs[0])

bpy.ops.render.render(write_still=True)
depth_candidates = glob.glob(str(OUTPUT_DIR / "cliff-house-depth-*.png"))
if not depth_candidates:
    raise RuntimeError("Blender did not write the final depth pass")
depth_path = OUTPUT_DIR / "cliff-house-depth.png"
os.replace(max(depth_candidates, key=os.path.getmtime), depth_path)
blend_path = OUTPUT_DIR / "cliff-house-final.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
print(
    f"FINAL_BLENDER_RENDER_OK beauty={scene.render.filepath} "
    f"depth={depth_path} blend={blend_path} objects={len(render_objects)}"
)
