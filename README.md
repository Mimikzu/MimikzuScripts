# 🎮 Mimikzu Scripts

**Gaming utilities and community tools by Mimikzu**  
Minecraft · Rocket League · Modrinth · Discord

This repository-style collection groups small scripts by what they do. Most
utilities run locally and use sample files. The voice agent needs Python
packages and downloads its speech model on first launch. The Modrinth stats
tool contacts Modrinth's public API; it uses no Discord login or API token.

## 📁 What's inside

### Discord

- `discord_permission_previewer.py` — offline preview of who gains or loses a
  channel permission; never connects to Discord.
- `offline_community_tools/discord_onboarding_simulator.py` — local role and
  verification visibility simulation.
- `offline_community_tools/discord_scam_explainer.py` — explains heuristic
  message signals for human review; no automatic moderation.
- `offline_community_tools/discord_bridge_policy_tester.py` — dry-run message
  and attachment policy preview; sends nothing.

### Minecraft

- `voice_game_agent.py` — local voice-to-keyboard controls with a Minecraft
  profile. Use `start_minecraft.bat`.
- `donutsmp_tools.py` — offline coordinate conversion, spawner-cost math, and
  supplied rate estimates.
- `offline_community_tools/minecraft_world_impact_preview.py` — compare local
  before/after block and inventory snapshots.
- `offline_community_tools/minecraft_log_to_fix_assistant.py` — compare local
  performance metric reports.
- `offline_community_tools/minecraft_rollback_rehearsal.py` — rehearse
  proposed block changes against a local snapshot without modifying a world.

### Rocket League

- `voice_game_agent.py` — local voice controls with a Rocket League profile.
  Use `start_rocket_league.bat`.
- `offline_community_tools/rocket_replay_integrity_receipt.py` — SHA-256
  receipt for a local replay file. It does not independently verify match
  metadata.
- `offline_community_tools/rocket_league_rules_referee.py` — simulate a
  roster or schedule proposal using local rules and league state.

### Modrinth

- `modrinth_stats.py` — retrieve public user or project statistics from
  Modrinth's public API. This one needs internet access, but no API key or
  Discord credentials.

## 🚀 Getting started

Install Python 3.10 or later. To install the voice agent's dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the voice agent by double-clicking `start_minecraft.bat` or
`start_rocket_league.bat`. Press **F12** to stop it.

Examples for the other local tools are in `offline_community_tools/README.md`.
For standalone utilities, run `python .\donutsmp_tools.py --help` or
`python .\modrinth_stats.py --help`.

## 🧪 Tests

```powershell
python -m unittest -v
python -m unittest -v offline_community_tools.test_offline_tools
```

## 🔐 Privacy and scope

- No Discord bot token, user token, API key, or account login is needed by the
  included tools.
- Discord and Minecraft preview tools work from local sample/configuration
  files and do not change live servers or worlds.
- `modrinth_stats.py` makes read-only requests to the public Modrinth API.
- The replay receipt hashes the exact local file; user-supplied metadata is
  labeled as unverified.
- This collection intentionally excludes channel-spam and Nighty Selfbot
  scripts that require an authenticated Discord client. No local Nighty
  settings, token files, or account data are included.
- Check game/server rules before using automated input in multiplayer.

## ✨ Credits

Built and organized as Mimikzu's scripts collection. The included tools are
original implementations, not copied from the linked script collection.
