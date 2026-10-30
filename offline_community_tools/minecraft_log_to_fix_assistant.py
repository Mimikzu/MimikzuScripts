"""Compare local Minecraft performance metric snapshots and suggest review areas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def compare_metrics(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    old = before.get("metrics", before)
    new = after.get("metrics", after)
    if not isinstance(old, dict) or not isinstance(new, dict):
        raise ValueError("Each report must contain a metrics object.")
    comparisons = []
    for key in sorted(old.keys() | new.keys()):
        if key not in old or key not in new:
            comparisons.append({"metric": key, "status": "missing from one report"})
            continue
        old_value, new_value = old[key], new[key]
        if not isinstance(old_value, (int, float)) or not isinstance(new_value, (int, float)):
            comparisons.append({"metric": key, "status": "not numeric; not compared"})
            continue
        delta = new_value - old_value
        percent = None if old_value == 0 else round((delta / abs(old_value)) * 100, 2)
        comparisons.append({
            "metric": key,
            "before": old_value,
            "after": new_value,
            "delta": delta,
            "percent_change": percent,
        })
    hints = [
        "Compare reports from similar player counts, worlds, and time windows.",
        "Treat changed metrics as investigation leads, not proof of a cause or fix.",
        "Record software versions and server conditions alongside each report.",
    ]
    return {"comparisons": comparisons, "review_hints": hints, "note": "Local report comparison; no server changes made."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    args = parser.parse_args()
    try:
        before = json.loads(args.before.read_text(encoding="utf-8"))
        after = json.loads(args.after.read_text(encoding="utf-8"))
        result = compare_metrics(before, after)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
