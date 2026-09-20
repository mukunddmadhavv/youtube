"""Verify the extracted Pitch catalog against its local source inventory.

Read-only provenance check; does not claim animation/render verification.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".opencode/skills/richard-system-design"


def check():
    catalog = json.loads((SKILL / "references/launch-video-catalog.json").read_text())
    source = Path(catalog["skill_root"])
    effects = Path(catalog["effects_root"])
    inventory = set(re.findall(r"^- ([a-z0-9-]+/[a-z0-9-]+)$",
                               (source / "SKILL.md").read_text(), re.MULTILINE))
    expected = catalog["catalog_size_at_inspection"]
    assert len(inventory) == expected["effects"], "Source inventory changed; refresh catalog counts"
    assert len({i.split('/')[0] for i in inventory}) == expected["families"]
    for relative in catalog["guidance_sources"]:
        assert (source / relative).is_file(), f"Missing guidance: {relative}"
    seen = set()
    for record in catalog["inspected"] + catalog["discovery_candidates"]:
        effect_id = record["effect_id"]
        assert effect_id in inventory, f"Unknown source ID: {effect_id}"
        assert effect_id not in seen, f"Duplicate source ID: {effect_id}"
        seen.add(effect_id)
        assert (effects / effect_id / "index.html").is_file(), f"Missing effect: {effect_id}"
        if "implementation" in record:
            implementation = effects / record["implementation"]
            assert implementation.is_file(), f"Missing implementation: {effect_id}"
            if "preset" in record:
                assert f"P==='{record['preset']}'" in implementation.read_text(), f"Missing preset: {effect_id}"
            if record.get("strip_inspected"):
                assert (effects / effect_id / "strip.jpg").is_file(), f"Missing strip: {effect_id}"
            if record.get("metadata_inspected"):
                assert (effects / effect_id / "meta.json").is_file(), f"Missing metadata: {effect_id}"
    skill_text = (SKILL / "SKILL.md").read_text()
    agent_text = (ROOT / ".opencode/agents/richardSystemDesign.md").read_text()
    for name in ("launch-video-motion.md", "launch-video-catalog.json"):
        assert name in skill_text and name in agent_text, f"Reference not wired: {name}"
    print(f"Verified {len(catalog['guidance_sources'])} guidance sources, "
          f"{len(catalog['inspected'])} inspected studies, "
          f"{len(catalog['discovery_candidates'])} discovery candidates, and agent/skill links.")
    print("This verifies provenance paths and IDs, not runtime animation quality.")


if __name__ == "__main__":
    check()
