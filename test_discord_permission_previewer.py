import unittest

from discord_permission_previewer import ConfigError, make_preview, validate_config


def sample_config():
    return validate_config(
        {
            "everyone_role_id": "everyone",
            "roles": [
                {"id": "everyone", "name": "@everyone", "permissions": ["view_channel"]},
                {"id": "staff", "name": "Staff", "permissions": ["view_channel"]},
                {"id": "member", "name": "Member", "permissions": ["view_channel"]},
            ],
            "members": [
                {"id": "a", "name": "Alex", "roles": ["staff"]},
                {"id": "b", "name": "Blair", "roles": ["member"]},
                {"id": "c", "name": "Casey", "roles": ["staff", "member"]},
            ],
            "channels": [
                {
                    "id": "private",
                    "name": "#private",
                    "overwrites": [
                        {
                            "type": "role",
                            "target_id": "everyone",
                            "allow": [],
                            "deny": ["view_channel"],
                        },
                        {
                            "type": "role",
                            "target_id": "staff",
                            "allow": ["view_channel"],
                            "deny": [],
                        },
                        {
                            "type": "member",
                            "target_id": "c",
                            "allow": [],
                            "deny": ["view_channel"],
                        },
                    ],
                }
            ],
        }
    )


class PermissionPreviewTests(unittest.TestCase):
    def test_denial_preview_lists_only_affected_members(self):
        preview = make_preview(sample_config(), "private", "staff", "view_channel", "deny")
        self.assertEqual(preview["affected_members"], [
            {"member_id": "a", "member_name": "Alex", "change": "loses access"}
        ])
        affected_role_ids = {role["role_id"] for role in preview["affected_roles"]}
        self.assertIn("staff", affected_role_ids)

    def test_role_allow_overrides_everyone_deny(self):
        preview = make_preview(sample_config(), "private", "member", "view_channel", "allow")
        changed_ids = {entry["member_id"] for entry in preview["affected_members"]}
        self.assertEqual(changed_ids, {"b"})
        self.assertEqual(preview["affected_members"][0]["change"], "gains access")

    def test_member_deny_has_precedence_over_role_allow(self):
        config = sample_config()
        preview = make_preview(config, "private", "staff", "view_channel", "deny")
        self.assertNotIn(
            "c",
            {entry["member_id"] for entry in preview["affected_members"]},
        )

    def test_invalid_overwrite_target_is_rejected(self):
        config = {
            "everyone_role_id": "everyone",
            "roles": [{"id": "everyone", "permissions": []}],
            "members": [],
            "channels": [{
                "id": "general",
                "overwrites": [{
                    "type": "role",
                    "target_id": "missing",
                    "allow": [],
                    "deny": [],
                }],
            }],
        }
        with self.assertRaises(ConfigError):
            validate_config(config)

    def test_preview_does_not_mutate_input_config(self):
        config = sample_config()
        previous = [
            set(item["allow"])
            for item in config["channels"]["private"]["overwrites"]
        ]
        make_preview(config, "private", "staff", "view_channel", "deny")
        current = [
            item["allow"]
            for item in config["channels"]["private"]["overwrites"]
        ]
        self.assertEqual(current, previous)


if __name__ == "__main__":
    unittest.main()
