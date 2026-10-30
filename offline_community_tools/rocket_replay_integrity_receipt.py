"""Create a local SHA-256 integrity receipt for a Rocket League replay file."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOL_VERSION = "0.1.0"


def create_receipt(replay_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    if not replay_path.is_file():
        raise FileNotFoundError(f"Replay file not found: {replay_path}")
    digest = hashlib.sha256()
    with replay_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "receipt_version": 1,
        "file_name": replay_path.name,
        "file_size_bytes": replay_path.stat().st_size,
        "sha256": digest.hexdigest(),
        "metadata_supplied_by_user": metadata,
        "analysis_tool": "Mimikzu Replay Integrity Receipt",
        "analysis_version": TOOL_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Hash identifies these exact file bytes; supplied match metadata is not independently verified.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, help="Optional JSON file with user-supplied match metadata.")
    parser.add_argument("--output", type=Path, help="Optional receipt output path.")
    args = parser.parse_args()
    try:
        metadata = json.loads(args.metadata.read_text(encoding="utf-8")) if args.metadata else {}
        receipt = create_receipt(args.replay, metadata)
        rendered = json.dumps(receipt, indent=2)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
