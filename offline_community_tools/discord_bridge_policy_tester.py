"""Dry-run Discord/Minecraft bridge message policy without sending messages."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def preview(message: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    text = message.get("text", "")
    if not isinstance(text, str):
        raise ValueError("message.text must be a string")
    blocked_terms = policy.get("blocked_terms", [])
    if any(not isinstance(term, str) for term in blocked_terms):
        raise ValueError("blocked_terms must contain strings")
    matched = [term for term in blocked_terms if term.casefold() in text.casefold()]
    attachment_names = message.get("attachments", [])
    if not isinstance(attachment_names, list) or any(not isinstance(name, str) for name in attachment_names):
        raise ValueError("attachments must be an array of filenames")
    allowed_extensions = {ext.casefold() for ext in policy.get("allowed_attachment_extensions", [])}
    allowed_attachments = [
        name for name in attachment_names
        if Path(name).suffix.casefold() in allowed_extensions
    ]
    rejected_attachments = [name for name in attachment_names if name not in allowed_attachments]

    safe_text = re.sub(
        r"@(everyone|here)",
        lambda match: "@\u200b" + match.group(1),
        text,
        flags=re.I,
    )
    safe_text = re.sub(r"<@!?(\d+)>", r"@user-\1", safe_text)
    safe_text = re.sub(r"<@&(\d+)>", r"@role-\1", safe_text)
    blocked = bool(matched)
    return {
        "status": "blocked by policy" if blocked else "would relay",
        "policy_matches": matched,
        "discord_preview": None if blocked else safe_text,
        "minecraft_preview": None if blocked else safe_text,
        "allowed_attachments": [] if blocked else allowed_attachments,
        "rejected_attachments": rejected_attachments,
        "note": "Dry run only. Nothing was sent, uploaded, or modified.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--message", type=Path, required=True, help="JSON file with text and optional attachments.")
    args = parser.parse_args()
    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        message = json.loads(args.message.read_text(encoding="utf-8"))
        result = preview(message, policy)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
