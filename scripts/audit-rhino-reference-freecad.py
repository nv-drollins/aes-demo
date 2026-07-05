"""Read-only audit for a reference document produced by the Rhino importer.

Run inside FreeCAD through the FreeCAD MCP execute_code tool.
"""

from collections import Counter
import os

import FreeCAD as App


DOCUMENT_NAME = os.environ.get(
    "AES_RHINO_REFERENCE_DOCUMENT",
    "CliffHouseReference",
)
FORMAT = "aes-demo-rhino-reference-v1"

if DOCUMENT_NAME not in App.listDocuments():
    raise RuntimeError(
        f"Reference document {DOCUMENT_NAME!r} is not open"
    )
document = App.getDocument(DOCUMENT_NAME)
metadata = document.getObject("RhinoImportMetadata")
if metadata is None:
    raise RuntimeError(
        "RhinoImportMetadata is missing"
    )
if getattr(metadata, "ManifestFormat", "") != FORMAT:
    raise RuntimeError(
        "Unexpected Rhino reference manifest format"
    )

reference_objects = [
    obj
    for obj in document.Objects
    if "RhinoObjectIndex" in obj.PropertiesList
]
layer_groups = [
    obj
    for obj in document.Objects
    if "RhinoLayerIndex" in obj.PropertiesList
]
type_counts = Counter(
    str(getattr(obj, "RhinoObjectType", "Unknown"))
    for obj in reference_objects
)
curve_objects = [
    obj
    for obj in reference_objects
    if getattr(obj, "RhinoObjectType", "")
    in {"PolylineCurve", "NurbsCurve"}
]
label_objects = [
    obj
    for obj in reference_objects
    if getattr(obj, "RhinoObjectType", "")
    == "TextDot"
]

expected_curves = int(
    getattr(metadata, "ImportedCurveCount", -1)
)
expected_labels = int(
    getattr(metadata, "ImportedLabelCount", -1)
)
if len(curve_objects) != expected_curves:
    raise RuntimeError(
        f"Curve count mismatch: expected {expected_curves}, "
        f"found {len(curve_objects)}"
    )
if len(label_objects) != expected_labels:
    raise RuntimeError(
        f"Label count mismatch: expected {expected_labels}, "
        f"found {len(label_objects)}"
    )

bounds_min = metadata.SourceBoundsMinMM
bounds_max = metadata.SourceBoundsMaxMM
print(
    "REFERENCE_METADATA "
    f"document={document.Name} "
    f"source_units={metadata.SourceUnits} "
    f"mm_per_unit={metadata.MillimetresPerUnit:.6g} "
    f"bounds_min_mm=[{bounds_min.x:.3f},"
    f"{bounds_min.y:.3f},{bounds_min.z:.3f}] "
    f"bounds_max_mm=[{bounds_max.x:.3f},"
    f"{bounds_max.y:.3f},{bounds_max.z:.3f}]"
)
print(
    "REFERENCE_COUNTS "
    f"objects={len(reference_objects)} "
    f"curves={len(curve_objects)} "
    f"labels={len(label_objects)} "
    f"layers={len(layer_groups)} "
    f"types={dict(sorted(type_counts.items()))}"
)

for layer in sorted(
    layer_groups,
    key=lambda obj: int(obj.RhinoLayerIndex),
):
    print(
        "REFERENCE_LAYER "
        f"index={int(layer.RhinoLayerIndex)} "
        f"path={layer.RhinoLayerPath!r} "
        f"color={layer.RhinoColorRGBA}"
    )

for obj in sorted(
    reference_objects,
    key=lambda item: int(item.RhinoObjectIndex),
):
    object_type = str(obj.RhinoObjectType)
    name = str(obj.RhinoObjectName or "")
    layer_path = str(obj.RhinoLayerPath)
    shape = getattr(obj, "Shape", None)
    if shape is not None and not shape.isNull():
        box = shape.BoundBox
        print(
            "REFERENCE_OBJECT "
            f"index={int(obj.RhinoObjectIndex)} "
            f"freecad_name={obj.Name} "
            f"rhino_name={name!r} "
            f"type={object_type} "
            f"layer={layer_path!r} "
            f"edges={len(shape.Edges)} "
            f"closed={shape.isClosed()} "
            f"bounds_mm=[{box.XMin:.3f},{box.YMin:.3f},"
            f"{box.ZMin:.3f}]-[{box.XMax:.3f},"
            f"{box.YMax:.3f},{box.ZMax:.3f}]"
        )
    else:
        position = getattr(
            obj,
            "Position",
            App.Vector(),
        )
        text = " ".join(
            getattr(obj, "LabelText", [])
        )
        print(
            "REFERENCE_OBJECT "
            f"index={int(obj.RhinoObjectIndex)} "
            f"freecad_name={obj.Name} "
            f"rhino_name={name!r} "
            f"type={object_type} "
            f"layer={layer_path!r} "
            f"text={text!r} "
            f"position_mm=[{position.x:.3f},"
            f"{position.y:.3f},{position.z:.3f}]"
        )

print(
    f"REFERENCE_AUDIT_OK document={document.Name} "
    f"objects={len(reference_objects)} "
    f"curves={len(curve_objects)} "
    f"labels={len(label_objects)} "
    f"layers={len(layer_groups)}"
)
