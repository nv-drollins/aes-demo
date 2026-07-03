"""Run inside live FreeCAD to reconstruct a read-only Rhino reference document."""

from collections import Counter
import json
import os
from pathlib import Path
import re

import FreeCAD as App
import FreeCADGui as Gui
import Part


MANIFEST_PATH = Path(
    os.environ.get(
        "AES_RHINO_REFERENCE_JSON",
        "/tmp/aes-demo-rhino-reference.json",
    )
)
OUTPUT_PATH = Path(
    os.environ.get(
        "AES_RHINO_REFERENCE_FCSTD",
        "/home/nvidia/aes-demo/source_models/cliff_house/cliff_house_reference.FCStd",
    )
)
DOCUMENT_NAME = os.environ.get(
    "AES_RHINO_REFERENCE_DOCUMENT",
    "CliffHouseReference",
)
FORMAT = "aes-demo-rhino-reference-v1"


def safe_name(value):
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    if not value or value[0].isdigit():
        value = "Reference_" + value
    return value[:120]


def add_read_only_property(
    obj,
    property_type,
    name,
    value,
    group="Rhino Reference",
):
    obj.addProperty(property_type, name, group)
    setattr(obj, name, value)
    obj.setEditorMode(name, 1)


def scaled_vector(point, scale):
    return App.Vector(
        float(point[0]) * scale,
        float(point[1]) * scale,
        float(point[2]) * scale,
    )


def unique_knots_and_multiplicities(raw_knots):
    unique = []
    multiplicities = []
    for knot in raw_knots:
        if unique and abs(knot - unique[-1]) <= 1e-12:
            multiplicities[-1] += 1
        else:
            unique.append(float(knot))
            multiplicities.append(1)

    # openNURBS omits one superfluous knot at each end; OCC expects degree + 1.
    if multiplicities:
        multiplicities[0] += 1
        multiplicities[-1] += 1
    return unique, multiplicities


def shape_for(item, scale):
    if item["geometry"] == "polyline":
        points = [
            scaled_vector(point, scale)
            for point in item["points"]
        ]
        return Part.makePolygon(points), "exact polyline"

    if item["geometry"] == "nurbs":
        try:
            poles = [
                scaled_vector(point[:3], scale)
                for point in item["control_points_xyzw"]
            ]
            weights = [
                float(point[3])
                for point in item["control_points_xyzw"]
            ]
            knots, multiplicities = unique_knots_and_multiplicities(
                item["rhino_knots"]
            )
            curve = Part.BSplineCurve()
            curve.buildFromPolesMultsKnots(
                poles,
                multiplicities,
                knots,
                bool(item["closed"]),
                int(item["degree"]),
                weights,
            )
            return curve.toShape(), "exact NURBS"
        except Exception as exc:
            points = [
                scaled_vector(point, scale)
                for point in item["preview_points"]
            ]
            return (
                Part.makePolygon(points),
                f"sampled NURBS fallback: {exc}",
            )

    raise ValueError(
        f"Cannot create a shape for {item['geometry']}"
    )


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
if manifest.get("format") != FORMAT:
    raise RuntimeError(
        f"Expected manifest format {FORMAT!r}, "
        f"got {manifest.get('format')!r}"
    )

if DOCUMENT_NAME in App.listDocuments():
    previous = App.getDocument(DOCUMENT_NAME)
    metadata = previous.getObject("RhinoImportMetadata")
    if (
        metadata is None
        or getattr(metadata, "ManifestFormat", "") != FORMAT
    ):
        raise RuntimeError(
            f"Document {DOCUMENT_NAME!r} already exists but was not "
            "created by this importer; refusing to replace it"
        )
    App.closeDocument(DOCUMENT_NAME)

doc = App.newDocument(DOCUMENT_NAME)
doc.Label = "[REFERENCE] Cliff House Rhino Curves"
scale = float(manifest["source"]["millimetres_per_unit"])

metadata = doc.addObject(
    "App::FeaturePython",
    "RhinoImportMetadata",
)
metadata.Label = "REFERENCE IMPORT — DO NOT EDIT"
add_read_only_property(
    metadata,
    "App::PropertyString",
    "ManifestFormat",
    FORMAT,
)
add_read_only_property(
    metadata,
    "App::PropertyString",
    "SourceFile",
    manifest["source"]["path"],
)
add_read_only_property(
    metadata,
    "App::PropertyString",
    "SourceSHA256",
    manifest["source"]["sha256"],
)
add_read_only_property(
    metadata,
    "App::PropertyString",
    "SourceUnits",
    manifest["source"]["units"],
)
add_read_only_property(
    metadata,
    "App::PropertyFloat",
    "MillimetresPerUnit",
    scale,
)
source_bounds = manifest["bounds_source_units"]
add_read_only_property(
    metadata,
    "App::PropertyVector",
    "SourceBoundsMinMM",
    scaled_vector(source_bounds["min"], scale),
)
add_read_only_property(
    metadata,
    "App::PropertyVector",
    "SourceBoundsMaxMM",
    scaled_vector(source_bounds["max"], scale),
)
add_read_only_property(
    metadata,
    "App::PropertyInteger",
    "ImportedCurveCount",
    int(manifest["counts"]["curves"]),
)
add_read_only_property(
    metadata,
    "App::PropertyInteger",
    "ImportedLabelCount",
    int(manifest["counts"]["labels"]),
)
add_read_only_property(
    metadata,
    "App::PropertyString",
    "ImportPolicy",
    "Immutable reference; reconstruct in a separate document",
)

root_group = doc.addObject(
    "App::DocumentObjectGroup",
    "RhinoReferenceLayers",
)
root_group.Label = "Rhino layers (reference only)"
layer_groups = {}
for layer in sorted(
    manifest["layers"],
    key=lambda value: (
        value["full_path"].count("::"),
        value["index"],
    ),
):
    full_path = layer["full_path"]
    group = doc.addObject(
        "App::DocumentObjectGroup",
        safe_name("Layer_" + full_path),
    )
    group.Label = "Layer: " + layer["name"]
    add_read_only_property(
        group,
        "App::PropertyInteger",
        "RhinoLayerIndex",
        int(layer["index"]),
    )
    add_read_only_property(
        group,
        "App::PropertyString",
        "RhinoLayerPath",
        full_path,
    )
    add_read_only_property(
        group,
        "App::PropertyString",
        "RhinoColorRGBA",
        json.dumps(layer["color_rgba"]),
    )
    parent_path = full_path.rpartition("::")[0]
    (
        layer_groups[parent_path]
        if parent_path
        else root_group
    ).addObject(group)
    layer_groups[full_path] = group

created_curves = 0
created_labels = 0
representations = Counter()
for item in manifest["objects"]:
    object_stem = (
        item["name"]
        or item.get("text")
        or item["type"]
    )
    internal_name = safe_name(
        f"Rhino_{item['index']:03d}_{object_stem}"
    )
    group = layer_groups[item["layer_path"]]

    if item["geometry"] in {"polyline", "nurbs"}:
        obj = doc.addObject("Part::Feature", internal_name)
        obj.Label = (
            item["name"]
            or f"{item['type']} {item['index']:03d}"
        )
        obj.Shape, representation = shape_for(item, scale)
        obj.setEditorMode("Shape", 1)
        color = manifest["layers"][
            item["layer_index"]
        ]["color_rgba"]
        obj.ViewObject.LineColor = tuple(
            channel / 255.0
            for channel in color[:3]
        )
        obj.ViewObject.LineWidth = (
            4.0
            if item["geometry"] == "polyline"
            else 2.0
        )
        obj.ViewObject.Visibility = bool(item["visible"])
        created_curves += 1
        representations[representation] += 1
    elif item["geometry"] == "text_dot":
        obj = doc.addObject("App::Annotation", internal_name)
        obj.Label = item["text"]
        obj.LabelText = [item["text"]]
        obj.Position = scaled_vector(item["point"], scale)
        obj.ViewObject.FontSize = max(
            10,
            min(18, int(item["font_height"])),
        )
        obj.ViewObject.TextColor = (1.0, 0.85, 0.0)
        obj.ViewObject.Visibility = bool(item["visible"])
        representation = "FreeCAD annotation"
        created_labels += 1
    else:
        continue

    add_read_only_property(
        obj,
        "App::PropertyInteger",
        "RhinoObjectIndex",
        int(item["index"]),
    )
    add_read_only_property(
        obj,
        "App::PropertyString",
        "RhinoObjectId",
        item["id"],
    )
    add_read_only_property(
        obj,
        "App::PropertyString",
        "RhinoObjectType",
        item["type"],
    )
    add_read_only_property(
        obj,
        "App::PropertyString",
        "RhinoObjectName",
        item["name"],
    )
    add_read_only_property(
        obj,
        "App::PropertyString",
        "RhinoLayerPath",
        item["layer_path"],
    )
    add_read_only_property(
        obj,
        "App::PropertyString",
        "Representation",
        representation,
    )
    add_read_only_property(
        obj,
        "App::PropertyBool",
        "ReadOnlyReference",
        True,
    )
    group.addObject(obj)

doc.recompute()
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
doc.saveAs(str(OUTPUT_PATH))
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
print(
    f"FREECAD_REFERENCE_IMPORT_OK={OUTPUT_PATH} "
    f"curves={created_curves} labels={created_labels} "
    f"layers={len(layer_groups)} "
    f"representations={dict(representations)}"
)
