#!/usr/bin/env python3
"""Extract Rhino layers, curves, and labels into a FreeCAD-neutral manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import rhino3dm


UNIT_TO_MM = {
    "Microns": 0.001,
    "Millimeters": 1.0,
    "Centimeters": 10.0,
    "Meters": 1000.0,
    "Kilometers": 1_000_000.0,
    "Microinches": 0.0000254,
    "Mils": 0.0254,
    "Inches": 25.4,
    "Feet": 304.8,
    "Yards": 914.4,
    "Miles": 1_609_344.0,
}


def xyz(point) -> list[float]:
    return [float(point.X), float(point.Y), float(point.Z)]


def rgba(color) -> list[int]:
    return [int(channel) for channel in color]


def sample_curve(curve, count: int) -> list[list[float]]:
    domain = curve.Domain
    start, end = float(domain.T0), float(domain.T1)
    return [
        xyz(curve.PointAt(start + (end - start) * index / count))
        for index in range(count + 1)
    ]


def update_bounds(bounds: list[list[float]], points: list[list[float]]) -> None:
    for point in points:
        for axis in range(3):
            bounds[0][axis] = min(bounds[0][axis], point[axis])
            bounds[1][axis] = max(bounds[1][axis], point[axis])


def extract(source: Path, samples: int) -> dict:
    model = rhino3dm.File3dm.Read(str(source))
    if model is None:
        raise RuntimeError(f"rhino3dm could not read {source}")

    unit_name = str(model.Settings.ModelUnitSystem).rsplit(".", 1)[-1]
    if unit_name not in UNIT_TO_MM:
        raise RuntimeError(f"Unsupported Rhino unit system: {unit_name}")

    layers = []
    for index, layer in enumerate(model.Layers):
        layers.append(
            {
                "index": index,
                "id": str(layer.Id),
                "parent_id": str(layer.ParentLayerId),
                "name": layer.Name,
                "full_path": layer.FullPath,
                "visible": bool(layer.Visible),
                "color_rgba": rgba(layer.Color),
            }
        )

    bounds = [[float("inf")] * 3, [float("-inf")] * 3]
    objects = []
    type_counts: dict[str, int] = {}
    for index, file_object in enumerate(model.Objects):
        geometry = file_object.Geometry
        attributes = file_object.Attributes
        type_name = type(geometry).__name__
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
        layer = layers[attributes.LayerIndex]
        item = {
            "index": index,
            "id": str(attributes.Id),
            "name": attributes.Name or "",
            "type": type_name,
            "layer_index": int(attributes.LayerIndex),
            "layer_path": layer["full_path"],
            "visible": bool(attributes.Visible),
        }

        if isinstance(geometry, rhino3dm.PolylineCurve):
            polyline = geometry.TryGetPolyline()
            points = [xyz(polyline[i]) for i in range(len(polyline))]
            item.update(
                {
                    "geometry": "polyline",
                    "closed": bool(geometry.IsClosed),
                    "points": points,
                }
            )
            update_bounds(bounds, points)
        elif isinstance(geometry, rhino3dm.NurbsCurve):
            control_points = [
                [float(point.X), float(point.Y), float(point.Z), float(point.W)]
                for point in geometry.Points
            ]
            preview = sample_curve(geometry, samples)
            item.update(
                {
                    "geometry": "nurbs",
                    "closed": bool(geometry.IsClosed),
                    "degree": int(geometry.Degree),
                    "order": int(geometry.Order),
                    "domain": [
                        float(geometry.Domain.T0),
                        float(geometry.Domain.T1),
                    ],
                    "control_points_xyzw": control_points,
                    "rhino_knots": [float(knot) for knot in geometry.Knots],
                    "preview_points": preview,
                }
            )
            update_bounds(bounds, preview)
        elif isinstance(geometry, rhino3dm.TextDot):
            point = xyz(geometry.Point)
            item.update(
                {
                    "geometry": "text_dot",
                    "text": geometry.Text,
                    "font_height": int(geometry.FontHeight),
                    "point": point,
                }
            )
            update_bounds(bounds, [point])
        else:
            item.update(
                {
                    "geometry": "unsupported",
                    "reason": f"Unsupported {type_name}",
                }
            )
        objects.append(item)

    if bounds[0][0] == float("inf"):
        bounds = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]

    return {
        "format": "aec-demo-rhino-reference-v1",
        "source": {
            "path": str(source.resolve()),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "archive_version": int(model.ArchiveVersion),
            "units": unit_name,
            "millimetres_per_unit": UNIT_TO_MM[unit_name],
            "absolute_tolerance": float(model.Settings.ModelAbsoluteTolerance),
        },
        "bounds_source_units": {"min": bounds[0], "max": bounds[1]},
        "layers": layers,
        "objects": objects,
        "counts": {
            "layers": len(layers),
            "objects": len(objects),
            "curves": sum(
                item["geometry"] in {"polyline", "nurbs"} for item in objects
            ),
            "labels": sum(
                item["geometry"] == "text_dot" for item in objects
            ),
            "types": type_counts,
        },
        "notes": [
            "Coordinates remain in the source unit system; consumers must apply millimetres_per_unit.",
            "NURBS retain Rhino control points, weights, knots, degree, and domain; preview points are fallback geometry only.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Rhino .3dm file")
    parser.add_argument("manifest", type=Path, help="Output JSON manifest")
    parser.add_argument(
        "--samples",
        type=int,
        default=64,
        help="Fallback samples per NURBS curve",
    )
    args = parser.parse_args()
    if args.samples < 4:
        parser.error("--samples must be at least 4")
    if not args.source.is_file():
        parser.error(f"source does not exist: {args.source}")

    manifest = extract(args.source, args.samples)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    counts = manifest["counts"]
    print(
        f"RHINO_REFERENCE_EXTRACT_OK={args.manifest.resolve()} "
        f"objects={counts['objects']} curves={counts['curves']} "
        f"labels={counts['labels']}"
    )


if __name__ == "__main__":
    main()
