"""Summarize differences between local Minecraft world snapshot JSON files."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    old_blocks = before.get("blocks", {})
    new_blocks = after.get("blocks", {})
    if not isinstance(old_blocks, dict) or not isinstance(new_blocks, dict):
        raise ValueError("blocks must be objects keyed by coordinates")
    block_changes = []
    for pos in sorted(old_blocks.keys() | new_blocks.keys()):
        old = old_blocks.get(pos)
        new = new_blocks.get(pos)
        if old != new:
            block_changes.append({"position": pos, "before": old, "after": new})

    old_inventory = before.get("inventories", {})
    new_inventory = after.get("inventories", {})
    inventory_changes = []
    for player in sorted(old_inventory.keys() | new_inventory.keys()):
        old_counts = old_inventory.get(player, {})
        new_counts = new_inventory.get(player, {})
        if not isinstance(old_counts, dict) or not isinstance(new_counts, dict):
            raise ValueError(f"inventory for {player} must be an object of item counts")
        for item in sorted(old_counts.keys() | new_counts.keys()):
            delta = new_counts.get(item, 0) - old_counts.get(item, 0)
            if not isinstance(delta, (int, float)):
                raise ValueError(f"inventory count for {player}/{item} must be numeric")
            if delta:
                inventory_changes.append({"player": player, "item": item, "delta": delta})

    before_owners = before.get("block_owners", {})
    after_owners = after.get("block_owners", {})
    builders: Counter[str] = Counter()
    for change in block_changes:
        owner = after_owners.get(change["position"]) or before_owners.get(change["position"]) or "unknown"
        builders[owner] += 1
    return {
        "block_change_count": len(block_changes),
        "block_changes": block_changes,
        "inventory_changes": inventory_changes,
        "changed_blocks_by_owner": dict(sorted(builders.items())),
        "note": "Snapshot comparison only; no Minecraft world was read or changed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    args = parser.parse_args()
    try:
        before = json.loads(args.before.read_text(encoding="utf-8"))
        after = json.loads(args.after.read_text(encoding="utf-8"))
        result = compare(before, after)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
