import unittest

from donutsmp_tools import calculate_spawners, convert_coordinates, parse_price, spawner_rate
from modrinth_stats import project_stats, user_stats


class DonutSMPTests(unittest.TestCase):
    def test_coordinate_conversion_both_directions(self):
        nether = convert_coordinates("overworld-to-nether", "1200", "64", "-800")
        self.assertEqual(nether["output"], ["150", "64", "-100"])
        overworld = convert_coordinates("nether-to-overworld", "150", "64", "-100")
        self.assertEqual(overworld["output"], ["1200", "64", "-800"])

    def test_price_shortcuts_and_total(self):
        self.assertEqual(parse_price("$1.25m"), 1_250_000)
        self.assertEqual(calculate_spawners(12, "1.25m")["total"], "$15,000,000.00")

    def test_rate_lookup_marks_estimate(self):
        result = spawner_rate("iron golem")
        self.assertEqual(result["spawner"], "Iron Golem")
        self.assertIn("not verified live", result["note"])

    def test_invalid_prices_and_quantities_rejected(self):
        with self.assertRaises(ValueError):
            parse_price("NaN")
        with self.assertRaises(ValueError):
            calculate_spawners(0, "10k")


class ModrinthStatsTests(unittest.TestCase):
    def test_user_stats_uses_public_api_and_sorts_projects(self):
        import modrinth_stats

        original = modrinth_stats.fetch_json
        responses = {
            "/user/Test": {"username": "Test"},
            "/user/Test/projects": [
                {"id": "a", "slug": "a", "title": "A", "downloads": 10, "followers": 2, "project_type": "mod"},
                {"id": "b", "slug": "b", "title": "B", "downloads": 20, "followers": 3, "project_type": "mod"},
            ],
        }
        try:
            modrinth_stats.fetch_json = lambda path: responses[path]
            result = user_stats("Test")
        finally:
            modrinth_stats.fetch_json = original
        self.assertEqual(result["total_downloads"], 30)
        self.assertEqual(result["projects"][0]["slug"], "b")
        self.assertIn("no Discord login", result["source"])

    def test_project_stats_uses_api_response(self):
        import modrinth_stats

        original = modrinth_stats.fetch_json
        try:
            modrinth_stats.fetch_json = lambda path: {
                "id": "id", "slug": "slug", "title": "Project",
                "downloads": 7, "followers": 4, "project_type": "mod",
            }
            result = project_stats("slug")
        finally:
            modrinth_stats.fetch_json = original
        self.assertEqual(result["downloads"], 7)
        self.assertEqual(result["url"], "https://modrinth.com/mod/slug")


if __name__ == "__main__":
    unittest.main()
