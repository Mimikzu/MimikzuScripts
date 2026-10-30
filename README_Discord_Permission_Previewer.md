# Discord Permission Change Previewer

An offline command-line prototype that previews which members and roles would gain or lose a permission if a Discord channel role-overwrite changed. **It does not connect to Discord or apply changes.**

## Requirements

Python 3.10 or later. No third-party packages are required.

## Try the sample

From this folder, run:

```powershell
python .\discord_permission_previewer.py --config .\discord_permissions.example.json --channel general --role member --permission view_channel --action allow
```

Actions are `allow`, `deny`, or `clear`. `clear` removes that permission from the role's channel overwrite, returning it to inherited permission behavior.

## Input format

Copy `discord_permissions.example.json` and edit the example roles, members, channels, and overwrites. IDs are local labels for this offline prototype; they are not fetched from Discord.

Role overwrites use `"type": "role"` and member-specific overwrites use `"type": "member"`. Permissions are listed in `allow` and `deny` arrays using names such as `view_channel` and `send_messages`.

The preview evaluates base role permissions, the Administrator permission, the `@everyone` overwrite, combined role overwrites, then member-specific overwrites. It reports only members whose effective permission changes and the roles held by those members.

## Tests

```powershell
python -m unittest -v .\test_discord_permission_previewer.py
```

This is a small planning aid, not a complete replacement for Discord's permissions UI or a live server audit. Review the real server state and the proposed change before applying it.
