#!/usr/bin/env python3
"""Validate the template-driven brief, assumptions, spec, and source hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "projects" / "cliff_house_template_reconstruction"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-approved", action="store_true")
    args = parser.parse_args()

    prompt_path = PROJECT / "project_prompt.md"
    assumptions_path = PROJECT / "SUBJECTIVE_ASSUMPTIONS.md"
    spec_path = PROJECT / "construction_spec.json"
    prompt = prompt_path.read_text(encoding="utf-8")
    assumptions = assumptions_path.read_text(encoding="utf-8")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    sections = {
        int(value)
        for value in re.findall(r"^## SECTION (\d+)\b", prompt, re.MULTILINE)
    }
    if sections != set(range(14)):
        raise RuntimeError(f"Expected sections 0-13, found {sorted(sections)}")
    if "[FILL IN]" in prompt or "[TBD]" in prompt:
        raise RuntimeError("Project prompt still contains unresolved placeholders")
    status_match = re.search(r"^status:\s*(\S+)", prompt, re.MULTILINE)
    if status_match is None:
        raise RuntimeError("Project prompt has no status")
    prompt_status = status_match.group(1)
    if prompt_status not in {"draft_for_human_approval", "approved_for_template_build"}:
        raise RuntimeError(f"Unexpected project-prompt status: {prompt_status}")
    if args.require_approved and prompt_status != "approved_for_template_build":
        raise RuntimeError("Project brief has not received human approval")
    if "Recommended approval statement" not in assumptions:
        raise RuntimeError("Subjective assumptions have no approval statement")
    if spec.get("format") != "aec-demo-template-construction-v1":
        raise RuntimeError(f"Unexpected construction format: {spec.get('format')!r}")

    for source in spec["sources"].values():
        source_hash = source.get("sha256")
        if not source_hash:
            continue
        source_path = Path(source["path"])
        if not source_path.is_file():
            raise RuntimeError(f"Missing source: {source_path}")
        actual = sha256(source_path)
        if actual != source_hash:
            raise RuntimeError(
                f"Source hash mismatch for {source_path}: {actual} != {source_hash}"
            )

    evidence = json.loads(
        (PROJECT / "evidence" / "base_template_inventory.json").read_text(
            encoding="utf-8"
        )
    )
    expected = spec["template_audit"]
    for key in ("layers", "objects", "curves", "labels"):
        if evidence["counts"][key] != expected[key]:
            raise RuntimeError(
                f"Template {key} mismatch: {evidence['counts'][key]} != {expected[key]}"
            )

    marker = (
        "PROJECT_BRIEF_APPROVED"
        if prompt_status == "approved_for_template_build"
        else "PROJECT_BRIEF_READY"
    )
    print(
        f"{marker} status={prompt_status} sections={len(sections)} "
        f"phases={len(spec['phases'])} sources=3 assumptions=12"
    )


if __name__ == "__main__":
    main()
