"""Run inside Blender to frame the imported FreeCAD collection and render beauty/depth."""
import glob
import math
import os
from pathlib import Path
import bpy
from mathutils import Vector

OUTPUT_DIR = Path(os.environ.get("AES_RENDER_OUTPUT_DIR", "/tmp/aes-demo-render"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
collection = bpy.data.collections.get("FreeCAD Import")
if collection is None or not collection.objects:
    raise RuntimeError("The 'FreeCAD Import' collection is empty")
render_objects = [obj for obj in collection.objects if obj.type == "MESH"]
if not render_objects:
    raise RuntimeError("The 'FreeCAD Import' collection has no meshes")
by_freecad_name = {}
for obj in render_objects:
    source_name = obj.get("freecad_name")
    if not source_name:
        raise RuntimeError(f"Imported object {obj.name!r} has no freecad_name metadata")
    if source_name in by_freecad_name:
        raise RuntimeError(
            f"Duplicate FreeCAD identity {source_name!r}: "
            f"{by_freecad_name[source_name].name!r} and {obj.name!r}. Re-run the importer."
        )
    by_freecad_name[source_name] = obj
for obj in bpy.context.scene.objects:
    obj.hide_render = obj not in render_objects

corners = [obj.matrix_world @ Vector(corner) for obj in render_objects for corner in obj.bound_box]
minimum = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
maximum = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
center = (minimum + maximum) / 2
max_dimension = max(maximum - minimum)
if max_dimension <= 0:
    raise RuntimeError("Imported geometry has zero-size bounds")

def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()

camera_data = bpy.data.cameras.get("FreeCAD Render Camera") or bpy.data.cameras.new("FreeCAD Render Camera")
camera = bpy.data.objects.get("FreeCAD Render Camera") or bpy.data.objects.new("FreeCAD Render Camera", camera_data)
if not camera.users_collection:
    bpy.context.scene.collection.objects.link(camera)
camera.hide_render = False
camera.data.lens = 52
camera.data.clip_start = max(max_dimension / 1000, 0.0001)
camera.data.clip_end = max_dimension * 100
fov = camera.data.angle
camera_distance = (max_dimension / (2 * math.tan(fov / 2))) * 2.0
camera.location = center + Vector((1.35, -1.55, 1.05)).normalized() * camera_distance
look_at(camera, center)
scene = bpy.context.scene
scene.camera = camera

def make_area(name, location, energy, size):
    light_data = bpy.data.lights.get(name) or bpy.data.lights.new(name, "AREA")
    light = bpy.data.objects.get(name) or bpy.data.objects.new(name, light_data)
    if not light.users_collection:
        scene.collection.objects.link(light)
    light.hide_render = False
    light.location = location
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    look_at(light, center)
    return light

make_area("FreeCAD Key", center + Vector((1.5, -1.5, 2.0)) * max_dimension, 1800, max_dimension * 1.5)
make_area("FreeCAD Fill", center + Vector((-1.2, -0.4, 1.0)) * max_dimension, 700, max_dimension * 1.5)
sun_data = bpy.data.lights.get("FreeCAD Sun") or bpy.data.lights.new("FreeCAD Sun", "SUN")
sun = bpy.data.objects.get("FreeCAD Sun") or bpy.data.objects.new("FreeCAD Sun", sun_data)
if not sun.users_collection:
    scene.collection.objects.link(sun)
sun.hide_render = False
sun.data.energy = 2.5
sun.rotation_euler = (math.radians(28), math.radians(-18), math.radians(-35))
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1024
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = False
scene.render.filepath = str(OUTPUT_DIR / "freecad-beauty.png")
if scene.world is None:
    scene.world = bpy.data.worlds.new("FreeCAD Render World")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.035, 0.045, 0.06, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
scene.view_settings.exposure = 1.0

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
depth_output.file_slots[0].path = "freecad-depth-"
tree.links.new(render_layers.outputs["Depth"], normalize.inputs[0])
tree.links.new(normalize.outputs[0], invert.inputs["Color"])
tree.links.new(invert.outputs["Color"], depth_output.inputs[0])

bpy.ops.render.render(write_still=True)
depth_candidates = glob.glob(str(OUTPUT_DIR / "freecad-depth-*.png"))
if not depth_candidates:
    raise RuntimeError("Blender did not write the depth pass")
depth_path = OUTPUT_DIR / "freecad-depth.png"
os.replace(max(depth_candidates, key=os.path.getmtime), depth_path)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_DIR / "freecad-render.blend"))
print(f"BLENDER_RENDER_OK beauty={scene.render.filepath} depth={depth_path}")
