"""Rehearse a block rollback against local snapshots without changing a world."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def rehearse(world: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    current = world.get("blocks", {})
    if not isinstance(current, dict):
        raise ValueError("world.blocks must be an object keyed by coordinates")
    changes = plan.get("changes", [])
    if not isinstance(changes, list):
        raise ValueError("plan.changes must be an array")
    proposed = dict(current)
    ready = []
    conflicts = []
    seen: set[str] = set()
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError("Each rollback change must be an object")
        pos = change.get("position")
        if not isinstance(pos, str) or not pos:
            raise ValueError("Every rollback change needs a position string")
        if pos in seen:
            raise ValueError(f"Duplicate rollback position: {pos}")
        seen.add(pos)
        expected = change.get("current")
        actual = current.get(pos)
        if actual != expected:
            conflicts.append({
                "position": pos,
                "expected_current": expected,
                "actual_current": actual,
                "restore_to": change.get("restore_to"),
            })
            continue
        ready.append({
            "position": pos,
            "from": actual,
            "to": change.get("restore_to"),
            "actor": change.get("actor", "unknown"),
        })
        if change.get("restore_to") is None:
            proposed.pop(pos, None)
        else:
            proposed[pos] = change["restore_to"]
    return {
        "ready_changes": ready,
        "conflicts": conflicts,
        "staged_blocks": proposed,
        "status": "review conflicts before approval" if conflicts else "all changes match snapshot",
        "note": "Rehearsal only. No Minecraft world was modified.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    try:
        world = json.loads(args.world.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        result = rehearse(world, plan)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
