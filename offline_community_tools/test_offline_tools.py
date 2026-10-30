import tempfile
import unittest
from pathlib import Path

from .discord_bridge_policy_tester import preview as bridge_preview
from .discord_onboarding_simulator import simulate
from .discord_scam_explainer import explain
from .minecraft_log_to_fix_assistant import compare_metrics
from .minecraft_rollback_rehearsal import rehearse
from .minecraft_world_impact_preview import compare as compare_worlds
from .rocket_league_rules_referee import evaluate
from .rocket_replay_integrity_receipt import create_receipt


class OfflineToolTests(unittest.TestCase):
    def test_onboarding_visibility_depends_on_verification(self):
        config = {
            "everyone_role_id": "everyone",
            "roles": [{"id": "everyone", "name": "@everyone"}, {"id": "verified", "name": "Verified"}],
            "verified_role_ids": ["verified"],
            "channels": [{"name": "#members", "visible_to_roles": ["verified"]}],
        }
        self.assertFalse(simulate(config, [], False)["visible_channels"])
        self.assertTrue(simulate(config, [], True)["visible_channels"])

    def test_scam_explainer_reports_signal_without_punishment(self):
        result = explain("Urgent! Claim your prize at https://bit.ly/example and send password")
        self.assertGreaterEqual(len(result["signals"]), 3)
        self.assertIn("Human review only", result["action"])

    def test_bridge_dry_run_neutralizes_mass_mention_and_filters_attachment(self):
        result = bridge_preview(
            {"text": "Hi @everyone <@&123>", "attachments": ["photo.png", "tool.exe"]},
            {"blocked_terms": [], "allowed_attachment_extensions": [".png"]},
        )
        self.assertIn("@\u200beveryone", result["discord_preview"])
        self.assertEqual(result["allowed_attachments"], ["photo.png"])
        self.assertEqual(result["rejected_attachments"], ["tool.exe"])

    def test_world_compare_reports_block_and_inventory_delta(self):
        result = compare_worlds(
            {"blocks": {"0,1,0": "stone"}, "inventories": {"Alex": {"stone": 2}}},
            {"blocks": {"0,1,0": "air"}, "inventories": {"Alex": {"stone": 1}}},
        )
        self.assertEqual(result["block_change_count"], 1)
        self.assertEqual(result["inventory_changes"][0]["delta"], -1)

    def test_metric_comparison_calculates_change(self):
        result = compare_metrics({"metrics": {"tps": 20}}, {"metrics": {"tps": 18}})
        self.assertEqual(result["comparisons"][0]["percent_change"], -10.0)

    def test_rollback_rehearsal_detects_conflict_without_mutation(self):
        world = {"blocks": {"0,0,0": "dirt"}}
        result = rehearse(
            world,
            {"changes": [{"position": "0,0,0", "current": "stone", "restore_to": "air"}]},
        )
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertEqual(world["blocks"]["0,0,0"], "dirt")

    def test_replay_receipt_hashes_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            replay = Path(temp_dir) / "match.replay"
            replay.write_bytes(b"replay sample")
            receipt = create_receipt(replay, {"teams": ["A", "B"]})
        self.assertEqual(len(receipt["sha256"]), 64)
        self.assertIn("not independently verified", receipt["note"])

    def test_rules_referee_explains_roster_violation(self):
        result = evaluate(
            {"max_roster_size": 1, "eligible_players": ["Alex", "Blair"]},
            {"roster": {"A": ["Alex"], "B": ["Blair"]}},
            {"action": "roster_move", "team": "B", "destination": "A", "player": "Blair"},
        )
        self.assertEqual(result["result"], "fails configured checks")
        self.assertTrue(result["reasons"])


if __name__ == "__main__":
    unittest.main()
