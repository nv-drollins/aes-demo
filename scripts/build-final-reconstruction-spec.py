#!/usr/bin/env python3
"""Build a staged FreeCAD reconstruction manifest from the final Rhino audit."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FINISH_PREFIX = "House_02_finish::H02_finishes"


def freecad_leaf_name(index: int) -> str:
    return "Part__Feature" if index == 0 else f"Part__Feature{index:03d}"


def phase_for(layer: str, name: str) -> str:
    value = f"{layer}::{name}".lower()
    if "new_pool::new_deck" in value or "new_pool::new_retaining_wall" in value:
        return "00_site_support"
    if "l1_floors" in value:
        return "01_level_1_floors"
    if "l1_finish::l1_walls" in value:
        return "02_level_1_walls"
    if "l1_windows" in value or "l1_fristed_glass" in value:
        return "03_level_1_glazing"
    if "l2_floors" in value:
        return "04_level_2_floors"
    if "l2_finish::l2_walls" in value:
        return "05_level_2_walls"
    if "l2_windows" in value or "l2_frosted_glass" in value:
        return "06_level_2_glazing"
    if "l2_balconies" in value or "l2_roof" in value:
        return "07_level_2_balconies_roof"
    if "l3_floors" in value:
        return "08_level_3_floors"
    if "l3_finish::l3_walls" in value:
        return "09_level_3_walls"
    if "l3_finish::glazing" in value or "l3_frosted_glass" in value or "garage_north_window" in value:
        return "10_level_3_glazing"
    if "l3_balconies" in value or "l3_roof" in value:
        return "11_level_3_balconies_roof"
    if "l1_cladding" in value or "::entry" in value or "wood_door" in value:
        return "12_entry_cladding"
    if "new_pool" in value:
        return "13_infinity_pool"
    return "12_entry_cladding"


def material_role_for(layer: str, name: str) -> str:
    value = f"{layer}::{name}".lower()
    if "glass" in value or "glazing" in value or "frost" in value:
        return "glazing"
    if any(word in value for word in ("mullion", "rail", "track", "stile")):
        return "metal_frame"
    if "wood_door" in value or "door_slat" in value or "wood_panel" in value:
        return "wood_door"
    if "pool" in value or "infinity_weir" in value:
        return "pool"
    if "cladding_dark" in value:
        return "cladding_dark"
    if "cladding_light" in value:
        return "cladding_light"
    if "roof" in value:
        return "roof"
    if "floor" in value or "balcon" in value:
        return "concrete_slab"
    if "wall" in value or "reveal" in value or "entry" in value:
        return "wall"
    return "architectural"


def safe_name(value: str, fallback: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    if not result:
        result = fallback
    if result[0].isdigit():
        result = "Object_" + result
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    components = [
        item
        for item in inventory["objects"]
        if item["layer_path"].startswith(FINISH_PREFIX)
        and item["type"] in {"Brep", "Extrusion"}
    ]
    solids = [item for item in reversed(components) if item.get("is_solid")]
    surfaces = [item for item in reversed(components) if not item.get("is_solid")]
    if len(solids) != 136 or len(surfaces) != 10:
        raise RuntimeError(
            f"Unexpected final object split: solids={len(solids)} surfaces={len(surfaces)}"
        )

    mapping = {}
    for leaf_index, item in enumerate(solids + surfaces):
        mapping[item["index"]] = (leaf_index, freecad_leaf_name(leaf_index))

    phase_names = sorted(
        {
            phase_for(item["layer_path"], item["name"])
            for item in components
        }
    )
    phase_order = {name: index for index, name in enumerate(phase_names)}
    result = []
    for item in components:
        leaf_index, leaf_name = mapping[item["index"]]
        phase = phase_for(item["layer_path"], item["name"])
        display_name = item["name"] or f"Rhino object {item['index']}"
        result.append(
            {
                "order": phase_order[phase] * 1000 + item["index"],
                "phase": phase,
                "name": display_name,
                "freecad_name": safe_name(
                    f"R{item['index']:03d}_{display_name}",
                    f"R{item['index']:03d}",
                ),
                "source_step_leaf_index": leaf_index,
                "source_step_object": leaf_name,
                "source_rhino_index": item["index"],
                "source_rhino_id": item["id"],
                "source_rhino_layer": item["layer_path"],
                "source_rhino_type": item["type"],
                "is_solid": bool(item.get("is_solid")),
                "material_role": material_role_for(item["layer_path"], item["name"]),
                "bounds_mm": {
                    "min": [
                        round(value * 1000.0, 6)
                        for value in item["bounds_source_units"]["min"]
                    ],
                    "max": [
                        round(value * 1000.0, 6)
                        for value in item["bounds_source_units"]["max"]
                    ],
                },
            }
        )

    result.sort(key=lambda item: item["order"])
    spec = {
        "format": "aec-demo-final-reconstruction-v1",
        "id": "cliff-house-final-reconstruction-v1",
        "source_rhino": inventory["source"],
        "source_step": {
            "path": "/home/nvidia/aec-demo/cliff_house_exp.stp",
            "sha256": "54a92968a8dd3273c074ca3426de64f907211b1815c3f74dc29b0093ea0fdd41",
            "freecad_reference": "CliffHouseFinalReference",
        },
        "phases": phase_names,
        "expected": {
            "components": 146,
            "solid_components": 136,
            "surface_components": 10,
        },
        "components": result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(
        f"FINAL_RECONSTRUCTION_SPEC_OK={args.output.resolve()} "
        f"components={len(result)} solids={len(solids)} surfaces={len(surfaces)} "
        f"phases={len(phase_names)}"
    )


if __name__ == "__main__":
    main()
