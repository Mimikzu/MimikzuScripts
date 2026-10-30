"""Offline Discord onboarding visibility simulator; never connects to Discord."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def simulate(config: dict[str, Any], role_ids: list[str], verified: bool) -> dict[str, Any]:
    roles = {role["id"]: role for role in config["roles"]}
    unknown = set(role_ids) - roles.keys()
    if unknown:
        raise ValueError(f"Unknown role(s): {', '.join(sorted(unknown))}")

    assigned = set(role_ids) | {config["everyone_role_id"]}
    if verified:
        assigned.update(config.get("verified_role_ids", []))
    else:
        assigned.update(config.get("unverified_role_ids", []))
    if assigned - roles.keys():
        raise ValueError(f"Onboarding config refers to unknown role(s): {', '.join(sorted(assigned - roles.keys()))}")

    visible = []
    hidden = []
    for channel in config["channels"]:
        allowed = set(channel.get("visible_to_roles", []))
        denied = set(channel.get("hidden_from_roles", []))
        if assigned & denied:
            is_visible = False
            reason = f"hidden from role(s): {', '.join(sorted(assigned & denied))}"
        elif not allowed or assigned & allowed:
            is_visible = True
            reason = "matches the channel's visibility rule"
        else:
            is_visible = False
            reason = f"requires role(s): {', '.join(sorted(allowed))}"
        record = {"channel": channel["name"], "visible": is_visible, "reason": reason}
        (visible if is_visible else hidden).append(record)

    return {
        "mode": "verified" if verified else "unverified",
        "assigned_role_names": [roles[role_id]["name"] for role_id in sorted(assigned)],
        "visible_channels": visible,
        "hidden_channels": hidden,
        "note": "Local simulation only; visibility rules are supplied by the example config.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--roles", default="", help="Comma-separated local role ids.")
    parser.add_argument("--verified", action="store_true")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        result = simulate(config, [item.strip() for item in args.roles.split(",") if item.strip()], args.verified)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
