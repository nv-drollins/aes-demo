#!/usr/bin/env python3
"""Create a complete geometry and layer inventory for the final Rhino model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import rhino3dm


def point_xyz(point) -> list[float]:
    return [float(point.X), float(point.Y), float(point.Z)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    model = rhino3dm.File3dm.Read(str(args.source))
    if model is None:
        raise RuntimeError(f"rhino3dm could not read {args.source}")

    layers = [
        {
            "index": index,
            "id": str(layer.Id),
            "parent_id": str(layer.ParentLayerId),
            "name": layer.Name,
            "full_path": layer.FullPath,
            "visible": bool(layer.Visible),
            "color_rgba": [int(value) for value in layer.Color],
        }
        for index, layer in enumerate(model.Layers)
    ]

    objects = []
    for index, file_object in enumerate(model.Objects):
        geometry = file_object.Geometry
        attributes = file_object.Attributes
        box = geometry.GetBoundingBox()
        item = {
            "index": index,
            "id": str(attributes.Id),
            "name": attributes.Name or "",
            "type": type(geometry).__name__,
            "layer_index": int(attributes.LayerIndex),
            "layer_path": layers[attributes.LayerIndex]["full_path"],
            "visible": bool(attributes.Visible),
            "bounds_source_units": {
                "min": point_xyz(box.Min),
                "max": point_xyz(box.Max),
            },
            "user_strings": {
                str(key): str(value)
                for key, value in attributes.GetUserStrings()
            },
        }
        if isinstance(geometry, rhino3dm.Brep):
            item.update(
                {
                    "is_solid": bool(geometry.IsSolid),
                    "face_count": len(geometry.Faces),
                    "edge_count": len(geometry.Edges),
                }
            )
        elif isinstance(geometry, rhino3dm.Extrusion):
            item.update(
                {
                    "is_solid": bool(geometry.IsSolid),
                    "profile_count": int(geometry.ProfileCount),
                }
            )
        objects.append(item)

    inventory = {
        "format": "aec-demo-final-rhino-inventory-v1",
        "source": {
            "path": str(args.source.resolve()),
            "sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
            "archive_version": int(model.ArchiveVersion),
            "units": str(model.Settings.ModelUnitSystem).rsplit(".", 1)[-1],
        },
        "layers": layers,
        "objects": objects,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(
        f"FINAL_RHINO_AUDIT_OK={args.output.resolve()} "
        f"layers={len(layers)} objects={len(objects)}"
    )


if __name__ == "__main__":
    main()
