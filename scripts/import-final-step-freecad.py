"""Import the approved final STEP model into a protected FreeCAD reference.

Run inside live FreeCAD through FreeCAD MCP ``execute_code``. Source and output
paths can be overridden with ``AEC_FINAL_STEP_SOURCE`` and
``AEC_FINAL_STEP_FCSTD``.
"""

from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path

import FreeCAD as App
import Import


SOURCE = Path(
    os.environ.get(
        "AEC_FINAL_STEP_SOURCE",
        "/home/nvidia/aec-demo/cliff_house_exp.stp",
    )
).resolve()
OUTPUT = Path(
    os.environ.get(
        "AEC_FINAL_STEP_FCSTD",
        "/home/nvidia/aec-demo/source_models/cliff_house/"
        "cliff_house_final_reference.FCStd",
    )
).resolve()
DOCUMENT_NAME = os.environ.get(
    "AEC_FINAL_STEP_DOCUMENT",
    "CliffHouseFinalReference",
)
FORMAT = "aec-demo-final-step-reference-v1"

if not SOURCE.is_file():
    raise RuntimeError(f"Final STEP source does not exist: {SOURCE}")
source_sha256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

if DOCUMENT_NAME in App.listDocuments():
    previous = App.getDocument(DOCUMENT_NAME)
    metadata = previous.getObject("FinalReferenceMetadata")
    if metadata is None or getattr(metadata, "ManifestFormat", "") != FORMAT:
        raise RuntimeError(
            f"Refusing to replace unrecognized document {DOCUMENT_NAME!r}"
        )
    App.closeDocument(DOCUMENT_NAME)

document = App.newDocument(DOCUMENT_NAME)
document.Label = "[REFERENCE] Complete Cliff House STEP"
Import.insert(str(SOURCE), document.Name)
document.recompute()

shape_objects = [
    obj
    for obj in document.Objects
    if obj.TypeId == "Part::Feature"
    and hasattr(obj, "Shape")
    and not obj.Shape.isNull()
]
solid_count = sum(obj.Shape.ShapeType == "Solid" for obj in shape_objects)
shell_count = sum(obj.Shape.ShapeType == "Shell" for obj in shape_objects)
face_count = sum(len(obj.Shape.Faces) for obj in shape_objects)
if not shape_objects or not face_count:
    App.closeDocument(document.Name)
    raise RuntimeError("STEP import produced no usable leaf geometry")

bounds = None
for obj in shape_objects:
    box = obj.Shape.BoundBox
    values = [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax]
    if not all(math.isfinite(value) and abs(value) < 1e20 for value in values):
        continue
    if bounds is None:
        bounds = values
    else:
        bounds[0] = min(bounds[0], box.XMin)
        bounds[1] = min(bounds[1], box.YMin)
        bounds[2] = min(bounds[2], box.ZMin)
        bounds[3] = max(bounds[3], box.XMax)
        bounds[4] = max(bounds[4], box.YMax)
        bounds[5] = max(bounds[5], box.ZMax)
if bounds is None:
    App.closeDocument(document.Name)
    raise RuntimeError("STEP import produced no finite architectural bounds")

metadata = document.addObject("App::FeaturePython", "FinalReferenceMetadata")
metadata.Label = "FINAL STEP REFERENCE — DO NOT EDIT"
for name, value in (
    ("ManifestFormat", FORMAT),
    ("SourcePath", str(SOURCE)),
    ("SourceSHA256", source_sha256),
):
    metadata.addProperty("App::PropertyString", name, "Reference")
    setattr(metadata, name, value)
metadata.addProperty("App::PropertyBool", "ReadOnlyReference", "Reference")
metadata.ReadOnlyReference = True
for name, value in (
    ("ShapeObjectCount", len(shape_objects)),
    ("SolidCount", solid_count),
    ("ShellCount", shell_count),
    ("FaceCount", face_count),
):
    metadata.addProperty("App::PropertyInteger", name, "Audit")
    setattr(metadata, name, int(value))
metadata.addProperty("App::PropertyString", "BoundsMillimetres", "Audit")
metadata.BoundsMillimetres = ",".join(f"{value:.6f}" for value in bounds)

try:
    metadata.ViewObject.Visibility = False
    for obj in document.Objects:
        if obj.TypeId in {"App::Line", "App::Plane"}:
            obj.ViewObject.Visibility = False
    for obj in shape_objects:
        if hasattr(obj.ViewObject, "Selectable"):
            obj.ViewObject.Selectable = False
except Exception:
    pass

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
document.recompute()
document.saveAs(str(OUTPUT))
print(
    "FINAL_STEP_IMPORT_OK "
    f"document={document.Name} objects={len(shape_objects)} "
    f"solids={solid_count} shells={shell_count} faces={face_count} "
    f"bounds_mm={[round(value, 3) for value in bounds]} "
    f"output={OUTPUT} sha256={source_sha256}"
)
