# Mimikzu Offline Community Tools

Small, local-only prototypes for Discord, Minecraft, and Rocket League workflows.
They use Python's standard library and local input files only—no bot tokens, API
keys, network calls, or account access.

These are prototypes, not replacements for live server validation or official
moderation/admin interfaces. Review every preview before making a real change.

## Tools

| Tool | Purpose | Input |
|---|---|---|
| `discord_onboarding_simulator.py` | Preview a member's channel visibility and verification gate | Local roles/channels JSON |
| `discord_scam_explainer.py` | Explain heuristic signals in a suspicious message | Text supplied locally |
| `discord_bridge_policy_tester.py` | Dry-run bridge filtering and mention/attachment transforms | Local policy JSON and message |
| `minecraft_world_impact_preview.py` | Compare world snapshots and summarize block/inventory deltas | Before/after JSON snapshots |
| `minecraft_log_to_fix_assistant.py` | Compare performance metrics and suggest areas to inspect | Local metric JSON files |
| `minecraft_rollback_rehearsal.py` | Simulate proposed block restoration against a snapshot | Local world and rollback JSON |
| `rocket_replay_integrity_receipt.py` | Hash a replay and create a metadata receipt | Local replay file and metadata JSON |
| `rocket_league_rules_referee.py` | Check roster/schedule proposals against local rules | Local league/rules JSON |

## Run tests

From the parent folder:

```powershell
python -m unittest -v offline_community_tools.test_offline_tools
```

Each script supports `--help` for its command-line options. Examples and formats
are described in the script docstrings. The tools do not apply changes to any
Discord server, Minecraft world, or Rocket League league.

## Try the included examples

Run these commands from the parent folder:

```powershell
python .\offline_community_tools\discord_onboarding_simulator.py --config .\offline_community_tools\examples\discord_onboarding.example.json --roles member
python .\offline_community_tools\discord_onboarding_simulator.py --config .\offline_community_tools\examples\discord_onboarding.example.json --roles member --verified
python .\offline_community_tools\discord_bridge_policy_tester.py --policy .\offline_community_tools\examples\discord_bridge_policy.example.json --message .\offline_community_tools\examples\discord_bridge_message.example.json
python .\offline_community_tools\minecraft_world_impact_preview.py --before .\offline_community_tools\examples\minecraft_before.example.json --after .\offline_community_tools\examples\minecraft_after.example.json
python .\offline_community_tools\minecraft_log_to_fix_assistant.py --before .\offline_community_tools\examples\minecraft_metrics_before.example.json --after .\offline_community_tools\examples\minecraft_metrics_after.example.json
python .\offline_community_tools\minecraft_rollback_rehearsal.py --world .\offline_community_tools\examples\minecraft_rollback_world.example.json --plan .\offline_community_tools\examples\minecraft_rollback_plan.example.json
python .\offline_community_tools\rocket_replay_integrity_receipt.py --replay .\some-match.replay --metadata .\offline_community_tools\examples\rocket_metadata.example.json
python .\offline_community_tools\rocket_league_rules_referee.py --rules .\offline_community_tools\examples\rocket_rules.example.json --state .\offline_community_tools\examples\rocket_state.example.json --proposal .\offline_community_tools\examples\rocket_roster_proposal.example.json
```

The replay example expects a replay file you provide locally. It hashes the file
but does not parse or verify match metadata.
