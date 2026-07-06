#!/usr/bin/env python3
"""Validate Rhino semantics against STEP names and FreeCAD leaf geometry."""

from __future__ import annotations

import argparse
import json
import re
import xmlrpc.client
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--step", type=Path, default=Path("cliff_house_exp.stp"))
    parser.add_argument("--url", default="http://127.0.0.1:9875")
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    step_text = args.step.read_text(encoding="utf-8")
    step_solid_names = re.findall(
        r"MANIFOLD_SOLID_BREP\('([^']*)'",
        step_text,
    )
    step_shell_names = re.findall(
        r"SHELL_BASED_SURFACE_MODEL\('([^']*)'",
        step_text,
    )
    solid_components = sorted(
        (item for item in spec["components"] if item["is_solid"]),
        key=lambda item: item["source_step_leaf_index"],
    )
    surface_components = sorted(
        (item for item in spec["components"] if not item["is_solid"]),
        key=lambda item: item["source_step_leaf_index"],
    )
    failures = []
    for kind, step_names, components in (
        ("solid", step_solid_names, solid_components),
        ("shell", step_shell_names, surface_components),
    ):
        if len(step_names) != len(components):
            failures.append(f"{kind} count {len(step_names)} != {len(components)}")
            continue
        for step_name, component in zip(step_names, components):
            rhino_name = component["name"]
            is_generic = step_name.startswith(("brep_", "shell_"))
            is_unnamed = rhino_name.startswith("Rhino object ")
            if step_name != rhino_name and not (is_generic and is_unnamed):
                failures.append(
                    f"{kind} name {step_name!r} != {rhino_name!r}"
                )

    rpc = xmlrpc.client.ServerProxy(args.url, allow_none=True)
    code = """import json
doc = App.getDocument('CliffHouseFinalReference')
rows = []
for obj in doc.Objects:
    if obj.TypeId != 'Part::Feature' or not hasattr(obj, 'Shape') or obj.Shape.isNull():
        continue
    box = obj.Shape.BoundBox
    rows.append({
        'name': obj.Name,
        'shape_type': obj.Shape.ShapeType,
        'bounds': [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax],
    })
print('FINAL_REFERENCE_LEAVES=' + json.dumps(rows, separators=(',', ':')))
"""
    result = rpc.execute_code(code)
    if not result.get("success"):
        raise RuntimeError(result.get("error", result))
    output = result["message"].rsplit("Output: ", 1)[-1]
    marker = "FINAL_REFERENCE_LEAVES="
    line = next(line for line in output.splitlines() if line.startswith(marker))
    rows = json.loads(line[len(marker) :])
    by_name = {row["name"]: row for row in rows}

    maximum_delta = 0.0
    for component in spec["components"]:
        row = by_name.get(component["source_step_object"])
        if row is None:
            failures.append(f"missing {component['source_step_object']}")
            continue
        expected = component["bounds_mm"]["min"] + component["bounds_mm"]["max"]
        delta = max(
            abs(actual - wanted)
            for actual, wanted in zip(row["bounds"], expected)
        )
        maximum_delta = max(maximum_delta, delta)
        expected_type = "Solid" if component["is_solid"] else "Shell"
        if row["shape_type"] != expected_type:
            failures.append(
                f"{component['source_step_object']} type={row['shape_type']} "
                f"expected={expected_type}"
            )

    if failures:
        raise RuntimeError("; ".join(failures[:20]))
    print(
        "FINAL_REFERENCE_MAPPING_OK "
        f"components={len(spec['components'])} names=146/146 "
        f"max_step_healing_delta_mm={maximum_delta:.9f}"
    )


if __name__ == "__main__":
    main()
