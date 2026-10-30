"""Check local Rocket League league proposals against explicit JSON rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def evaluate(rules: dict[str, Any], state: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    violations: list[str] = []
    roster = state.get("roster", {})
    if not isinstance(roster, dict):
        raise ValueError("state.roster must map team names to player arrays")
    action = proposal.get("action")

    if action == "roster_move":
        team = proposal.get("team")
        player = proposal.get("player")
        destination = proposal.get("destination")
        if team not in roster or destination not in roster:
            raise ValueError("Proposal team and destination must exist in state.roster")
        source_players = list(roster[team])
        dest_players = list(roster[destination])
        if player not in source_players:
            violations.append(f"{player} is not currently on {team}.")
        else:
            source_players.remove(player)
            dest_players.append(player)
        max_size = rules.get("max_roster_size")
        if isinstance(max_size, int) and len(dest_players) > max_size:
            violations.append(f"{destination} would exceed the maximum roster size of {max_size}.")
        eligible = set(rules.get("eligible_players", []))
        if eligible and player not in eligible:
            violations.append(f"{player} is not listed as eligible.")
        if player in set(rules.get("locked_players", [])):
            violations.append(f"{player} is locked and cannot be moved.")
    elif action == "schedule_match":
        match = proposal.get("match")
        if not isinstance(match, dict):
            raise ValueError("schedule_match proposal needs a match object")
        existing = state.get("matches", [])
        if not isinstance(existing, list):
            raise ValueError("state.matches must be an array")
        for scheduled in existing:
            if scheduled.get("time") == match.get("time") and (
                scheduled.get("team_a") in {match.get("team_a"), match.get("team_b")}
                or scheduled.get("team_b") in {match.get("team_a"), match.get("team_b")}
            ):
                violations.append(
                    f"{scheduled.get('team_a')} or {scheduled.get('team_b')} already has a match at {match.get('time')}."
                )
        allowed_teams = set(roster)
        if match.get("team_a") not in allowed_teams or match.get("team_b") not in allowed_teams:
            violations.append("Both scheduled teams must exist in the roster.")
        if match.get("team_a") == match.get("team_b"):
            violations.append("A team cannot play itself.")
    else:
        raise ValueError("action must be 'roster_move' or 'schedule_match'")

    return {
        "proposal": proposal,
        "result": "passes configured checks" if not violations else "fails configured checks",
        "reasons": violations,
        "note": "Local rules simulation only. An authorized league admin makes the final decision.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    args = parser.parse_args()
    try:
        rules = json.loads(args.rules.read_text(encoding="utf-8"))
        state = json.loads(args.state.read_text(encoding="utf-8"))
        proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
        result = evaluate(rules, state, proposal)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
