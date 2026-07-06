"""Create and render a minimal Blender scene for ARM64/GPU validation."""

import math
from pathlib import Path

import bpy
from mathutils import Vector


OUTPUT = Path("/tmp/aec-demo-blender-smoke.png")


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(OUTPUT)

bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
ground = bpy.context.object
ground.name = "Ground"

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
cube = bpy.context.object
cube.name = "BlenderMCP_TestCube"
cube.scale = (2.5, 1.8, 1.0)

material = bpy.data.materials.new("TestBlue")
material.diffuse_color = (0.04, 0.24, 0.8, 1.0)
cube.data.materials.append(material)

bpy.ops.object.light_add(type="AREA", location=(4, -4, 7))
key = bpy.context.object
key.name = "KeyLight"
key.data.energy = 1200
key.data.shape = "DISK"
key.data.size = 5
point_at(key, (0, 0, 1))

bpy.ops.object.light_add(type="SUN", location=(0, 0, 6))
sun = bpy.context.object
sun.name = "Sun"
sun.data.energy = 2.0
sun.rotation_euler = (math.radians(25), math.radians(-20), math.radians(-35))

bpy.ops.object.camera_add(location=(8, -9, 6))
camera = bpy.context.object
camera.name = "Camera"
point_at(camera, (0, 0, 1))
scene.camera = camera

scene.world = bpy.data.worlds.new("Smoke Test World")
scene.world.color = (0.04, 0.04, 0.04)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/aec-demo-blender-smoke.blend")
bpy.ops.render.render(write_still=True)
print(f"BLENDER_SMOKE_OK={OUTPUT}")
