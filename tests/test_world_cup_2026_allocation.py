import importlib.util
import itertools
from pathlib import Path
from unittest.mock import patch
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "simulate_world_cup_2026.py"

spec = importlib.util.spec_from_file_location("simulate_world_cup_2026", SCRIPT_PATH)
wc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wc)


def fake_standings(qualified_third_groups):
    standings = {}
    for group in wc.GROUPS:
        third_qualifies = group in qualified_third_groups
        standings[group] = [
            {"team": f"W{group}", "group": group, "points": 9, "gd": 5, "gf": 8, "spi": 90},
            {"team": f"R{group}", "group": group, "points": 6, "gd": 2, "gf": 5, "spi": 80},
            {"team": f"T{group}", "group": group, "points": 4 if third_qualifies else 1, "gd": 0, "gf": 3, "spi": 70},
            {"team": f"X{group}", "group": group, "points": 0, "gd": -7, "gf": 1, "spi": 60},
        ]
    return standings


def fake_predict_match(team_a, team_b, rankings, n_simulations, venue_country, use_home_advantage, home_multiplier):
    return {
        "team_a": team_a,
        "team_b": team_b,
        "score_a": 1,
        "score_b": 0,
        "winner": team_a,
        "forecast": "team_a",
        "wins_a": 1,
        "wins_b": 0,
        "draws": 0,
        "home_advantage_team": None,
    }


class WorldCup2026AllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = wc.load_third_place_allocation_table()

    def test_qualification_count(self):
        standings = fake_standings("ABCDEFGH")
        qualifiers = []
        for rows in standings.values():
            qualifiers.extend([rows[0], rows[1]])
        qualifiers.extend(wc.best_thirds(standings))

        self.assertEqual(len(qualifiers), 32)
        self.assertEqual(len(wc.best_thirds(standings)), 8)
        self.assertEqual(wc.third_place_allocation_key(wc.best_thirds(standings)), "ABCDEFGH")

    def test_third_place_allocation_table_completeness(self):
        expected_keys = {"".join(groups) for groups in itertools.combinations("ABCDEFGHIJKL", 8)}

        self.assertEqual(len(self.table), 495)
        self.assertEqual(set(self.table), expected_keys)

        for key, row in self.table.items():
            self.assertEqual(len(key), 8)
            self.assertEqual(len(set(key)), 8)
            self.assertTrue(set(key).issubset(set("ABCDEFGHIJKL")))
            self.assertEqual(set(row), set(wc.THIRD_PLACE_WINNER_SLOTS))

            assigned_groups = [third_slot.removeprefix("3") for third_slot in row.values()]
            self.assertEqual(sorted(assigned_groups), sorted(key))
            self.assertEqual(len(set(assigned_groups)), 8)

    def test_fixed_round_of_32_winner_slots(self):
        third_place_winners = {
            slot_a
            for _, slot_a, slot_b, _ in wc.ROUND_OF_32
            if slot_b.startswith("3")
        }
        runner_up_winners = {
            slot_a
            for _, slot_a, slot_b, _ in wc.ROUND_OF_32
            if slot_a.startswith("1") and slot_b.startswith("2")
        }
        runner_up_matches = {
            slot_a: slot_b
            for _, slot_a, slot_b, _ in wc.ROUND_OF_32
            if slot_a.startswith("1") and slot_b.startswith("2")
        }

        self.assertEqual(third_place_winners, {"1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"})
        self.assertEqual(runner_up_winners, {"1C", "1F", "1H", "1J"})
        self.assertEqual(runner_up_matches, {"1C": "2F", "1F": "2C", "1H": "2J", "1J": "2H"})

    def test_no_same_group_round_of_32_rematches_in_table(self):
        for key, row in self.table.items():
            for winner_slot, third_slot in row.items():
                self.assertNotEqual(
                    winner_slot.removeprefix("1"),
                    third_slot.removeprefix("3"),
                    f"{key}: {winner_slot} received {third_slot}",
                )

    def test_known_official_rows(self):
        self.assertEqual(
            self.table["ABCDEFGH"],
            {
                "1A": "3H",
                "1B": "3G",
                "1D": "3B",
                "1E": "3C",
                "1G": "3A",
                "1I": "3F",
                "1K": "3D",
                "1L": "3E",
            },
        )
        self.assertEqual(
            self.table["ABCEFIKL"],
            {
                "1A": "3E",
                "1B": "3I",
                "1D": "3B",
                "1E": "3C",
                "1G": "3A",
                "1I": "3F",
                "1K": "3L",
                "1L": "3K",
            },
        )

    def test_round_of_32_generation_uses_official_allocation(self):
        standings = fake_standings("ABCDEFGH")

        with patch.object(wc, "predict_match", side_effect=fake_predict_match):
            matches, _ = wc.build_round_of_32_matches(
                standings,
                rankings={},
                n_simulations=1,
                use_home_advantage=False,
                home_multiplier=1.0,
                allocation_table=self.table,
            )

        self.assertEqual(len(matches), 16)
        third_matches = {
            match_no: match
            for match_no, match in matches.items()
            if match["team_b"].startswith("T")
        }
        self.assertEqual(len(third_matches), 8)

        expected_by_match = {
            74: ("WE", "TC"),
            77: ("WI", "TF"),
            79: ("WA", "TH"),
            80: ("WL", "TE"),
            81: ("WD", "TB"),
            82: ("WG", "TA"),
            85: ("WB", "TG"),
            87: ("WK", "TD"),
        }
        for match_no, (team_a, team_b) in expected_by_match.items():
            self.assertEqual((matches[match_no]["team_a"], matches[match_no]["team_b"]), (team_a, team_b))
            self.assertNotEqual(team_a[-1], team_b[-1])


if __name__ == "__main__":
    unittest.main()
