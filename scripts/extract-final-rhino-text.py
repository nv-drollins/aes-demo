#!/usr/bin/env python3
"""Extract text annotations and layer context from a Rhino model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import rhino3dm


def xyz(point) -> list[float]:
    return [float(point.X), float(point.Y), float(point.Z)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    model = rhino3dm.File3dm.Read(str(args.source))
    if model is None:
        raise RuntimeError(f"rhino3dm could not read {args.source}")
    layers = [layer.FullPath for layer in model.Layers]
    records = []
    for index, file_object in enumerate(model.Objects):
        geometry = file_object.Geometry
        if not isinstance(geometry, (rhino3dm.Text, rhino3dm.TextDot)):
            continue
        if isinstance(geometry, rhino3dm.Text):
            text = geometry.PlainTextWithFields or geometry.PlainText
            point = geometry.Plane.Origin
        else:
            text = geometry.Text
            point = geometry.Point
        records.append(
            {
                "index": index,
                "text": text.replace("\r\n", "\n").replace("\r", "\n"),
                "layer": layers[file_object.Attributes.LayerIndex],
                "point": xyz(point),
                "visible": bool(file_object.Attributes.Visible),
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"FINAL_RHINO_TEXT_OK={args.output.resolve()} annotations={len(records)}")


if __name__ == "__main__":
    main()
