"""Offline preview of Discord channel permission-overwrite changes.

This tool reads a local JSON snapshot and never connects to or modifies Discord.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when the preview configuration is malformed."""


def _require_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ConfigError(f"{label} must be a JSON array of objects.")
    return value


def _identifier(obj: dict[str, Any], label: str) -> str:
    value = obj.get("id")
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label} entries need a non-empty string 'id'.")
    return value


def _permission_list(value: Any, label: str) -> set[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ConfigError(f"{label} must be an array of permission names.")
    return {item.strip().casefold() for item in value}


def _index_unique(items: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = _identifier(item, label)
        if item_id in indexed:
            raise ConfigError(f"Duplicate {label} id: {item_id}")
        indexed[item_id] = item
    return indexed


def validate_config(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ConfigError("The config root must be a JSON object.")

    roles = _index_unique(_require_list(raw.get("roles"), "roles"), "role")
    members = _index_unique(_require_list(raw.get("members"), "members"), "member")
    channels = _index_unique(_require_list(raw.get("channels"), "channels"), "channel")

    everyone_id = raw.get("everyone_role_id")
    if not isinstance(everyone_id, str) or everyone_id not in roles:
        raise ConfigError("'everyone_role_id' must identify a role in 'roles'.")

    for role_id, role in roles.items():
        role["permissions"] = _permission_list(role.get("permissions", []), f"role {role_id} permissions")

    for member_id, member in members.items():
        role_ids = member.get("roles", [])
        if not isinstance(role_ids, list) or any(not isinstance(role_id, str) for role_id in role_ids):
            raise ConfigError(f"Member {member_id} roles must be an array of role ids.")
        unknown = set(role_ids) - roles.keys()
        if unknown:
            raise ConfigError(f"Member {member_id} refers to unknown role(s): {', '.join(sorted(unknown))}")
        member["roles"] = set(role_ids) | {everyone_id}

    for channel_id, channel in channels.items():
        overwrites = _require_list(channel.get("overwrites", []), f"channel {channel_id} overwrites")
        for overwrite in overwrites:
            target_type = overwrite.get("type", "role")
            target_id = overwrite.get("target_id")
            if target_type not in {"role", "member"}:
                raise ConfigError(f"Channel {channel_id} overwrite type must be 'role' or 'member'.")
            known_targets = roles if target_type == "role" else members
            if not isinstance(target_id, str) or target_id not in known_targets:
                raise ConfigError(f"Channel {channel_id} overwrite refers to an unknown {target_type}.")
            overwrite["type"] = target_type
            overwrite["allow"] = _permission_list(
                overwrite.get("allow", []), f"channel {channel_id} overwrite allow"
            )
            overwrite["deny"] = _permission_list(
                overwrite.get("deny", []), f"channel {channel_id} overwrite deny"
            )
            if overwrite["allow"] & overwrite["deny"]:
                raise ConfigError(
                    f"Channel {channel_id} overwrite for {target_id} both allows and denies a permission."
                )
        channel["overwrites"] = overwrites

    return {
        "everyone_role_id": everyone_id,
        "roles": roles,
        "members": members,
        "channels": channels,
    }


def effective_permission(
    config: dict[str, Any],
    channel: dict[str, Any],
    member: dict[str, Any],
    permission: str,
) -> bool:
    """Apply guild permissions and channel overwrites in Discord precedence order."""
    roles = config["roles"]
    member_roles = member["roles"]

    base_permissions: set[str] = set()
    for role_id in member_roles:
        base_permissions.update(roles[role_id]["permissions"])
    if "administrator" in base_permissions:
        return True

    has_permission = permission in base_permissions
    overwrites = channel["overwrites"]
    everyone_id = config["everyone_role_id"]

    everyone = next(
        (overwrite for overwrite in overwrites
         if overwrite["type"] == "role" and overwrite["target_id"] == everyone_id),
        None,
    )
    if everyone:
        if permission in everyone["deny"]:
            has_permission = False
        if permission in everyone["allow"]:
            has_permission = True

    role_denied = False
    role_allowed = False
    for overwrite in overwrites:
        if (
            overwrite["type"] == "role"
            and overwrite["target_id"] != everyone_id
            and overwrite["target_id"] in member_roles
        ):
            role_denied |= permission in overwrite["deny"]
            role_allowed |= permission in overwrite["allow"]
    if role_denied:
        has_permission = False
    if role_allowed:
        has_permission = True

    member_overwrite = next(
        (overwrite for overwrite in overwrites
         if overwrite["type"] == "member" and overwrite["target_id"] == member["id"]),
        None,
    )
    if member_overwrite:
        if permission in member_overwrite["deny"]:
            has_permission = False
        if permission in member_overwrite["allow"]:
            has_permission = True

    return has_permission


def proposed_overwrites(
    overwrites: list[dict[str, Any]],
    role_id: str,
    permission: str,
    action: str,
) -> list[dict[str, Any]]:
    """Return a modified copy without mutating the loaded configuration."""
    result = [
        {
            **overwrite,
            "allow": set(overwrite["allow"]),
            "deny": set(overwrite["deny"]),
        }
        for overwrite in overwrites
    ]
    target = next(
        (
            overwrite for overwrite in result
            if overwrite["type"] == "role" and overwrite["target_id"] == role_id
        ),
        None,
    )

    if action == "clear":
        if target:
            target["allow"].discard(permission)
            target["deny"].discard(permission)
            if not target["allow"] and not target["deny"]:
                result.remove(target)
        return result

    if target is None:
        target = {
            "type": "role",
            "target_id": role_id,
            "allow": set(),
            "deny": set(),
        }
        result.append(target)
    target["allow"].discard(permission)
    target["deny"].discard(permission)
    target["allow" if action == "allow" else "deny"].add(permission)
    return result


def make_preview(
    config: dict[str, Any],
    channel_id: str,
    role_id: str,
    permission: str,
    action: str,
) -> dict[str, Any]:
    if channel_id not in config["channels"]:
        raise ConfigError(f"Unknown channel id: {channel_id}")
    if role_id not in config["roles"]:
        raise ConfigError(f"Unknown role id: {role_id}")
    if action not in {"allow", "deny", "clear"}:
        raise ConfigError("Action must be 'allow', 'deny', or 'clear'.")
    if not permission or permission != permission.strip():
        raise ConfigError("Permission must be a non-empty permission name.")

    channel = config["channels"][channel_id]
    proposed_channel = {
        **channel,
        "overwrites": proposed_overwrites(channel["overwrites"], role_id, permission, action),
    }
    affected: list[dict[str, str]] = []
    role_name = config["roles"][role_id].get("name", role_id)

    for member_id, member in config["members"].items():
        before = effective_permission(config, channel, member, permission)
        after = effective_permission(config, proposed_channel, member, permission)
        if before != after:
            affected.append(
                {
                    "member_id": member_id,
                    "member_name": member.get("name", member_id),
                    "change": "gains access" if after else "loses access",
                }
            )

    # Identify every role whose holders are among the affected members.
    affected_member_ids = {entry["member_id"] for entry in affected}
    affected_roles = []
    for candidate_id, candidate in config["roles"].items():
        holders = [
            member_id
            for member_id, member in config["members"].items()
            if candidate_id in member["roles"] and member_id in affected_member_ids
        ]
        if holders:
            affected_roles.append(
                {
                    "role_id": candidate_id,
                    "role_name": candidate.get("name", candidate_id),
                    "affected_members": len(holders),
                }
            )

    return {
        "channel": channel.get("name", channel_id),
        "permission": permission,
        "target_role": role_name,
        "proposed_action": action,
        "affected_members": affected,
        "affected_roles": affected_roles,
        "note": "Preview only. No Discord API calls or server changes were made.",
    }


def load_config(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as file:
            return validate_config(json.load(file))
    except OSError as error:
        raise ConfigError(f"Could not read config file '{path}': {error}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"Invalid JSON in '{path}' at line {error.lineno}, column {error.colno}.") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview Discord channel permission changes offline.")
    parser.add_argument("--config", type=Path, required=True, help="Path to a local JSON server snapshot.")
    parser.add_argument("--channel", required=True, help="Channel id from the JSON snapshot.")
    parser.add_argument("--role", required=True, help="Role id whose channel overwrite would change.")
    parser.add_argument("--permission", required=True, help="Permission name, for example view_channel.")
    parser.add_argument("--action", required=True, choices=("allow", "deny", "clear"))
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        preview = make_preview(
            config,
            args.channel,
            args.role,
            args.permission.casefold(),
            args.action,
        )
    except ConfigError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(json.dumps(preview, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
