import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from football_predictor.post_world_cup_update import (
    apply_goal_weights,
    calculate_ratings,
    name_maps,
    prepare_confederations,
    prepare_prior,
    simulate_spi,
)


class PostWorldCupUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dictionary = pd.DataFrame(
            {
                "original": ["Alpha", "Beta", "Gamma"],
                "corrected": ["Alpha", "Beta", "Gamma"],
            }
        )
        cls.prior = prepare_prior(
            pd.DataFrame(
                {
                    "rank": [1, 2, 3],
                    "name": ["Alpha", "Beta", "Gamma"],
                    "confed": ["UEFA", "UEFA", "AFC"],
                    "off": [2.0, 1.0, 0.5],
                    "def": [0.5, 1.0, 1.5],
                    "spi": [70.0, 50.0, 30.0],
                }
            ),
            cls.dictionary,
        )
        cls.confeds = prepare_confederations(
            pd.DataFrame({"team": ["Alpha", "Beta", "Gamma"], "confed": ["UEFA", "UEFA", "AFC"]}),
            cls.dictionary,
        )

    def test_friendly_goals_are_halved_before_metrics(self):
        matches = pd.DataFrame(
            {
                "tournament": ["Friendly", "League"],
                "home_score": [2, 2],
                "away_score": [4, 4],
            }
        )
        weighted = apply_goal_weights(matches)
        np.testing.assert_allclose(weighted.loc[0, ["home_score", "away_score"]].astype(float), [1.0, 2.0])
        np.testing.assert_allclose(weighted.loc[1, ["home_score", "away_score"]].astype(float), [2.0, 4.0])

    def test_missing_name_is_not_silently_mapped(self):
        original_to_corrected, corrected_to_original = name_maps(self.dictionary)
        self.assertNotIn("Unknown", original_to_corrected)
        self.assertNotIn("Unknown", corrected_to_original)

    def test_prior_carry_forward_preserves_unobserved_team(self):
        matches = pd.DataFrame(
            {
                "date": ["2026-01-27", "2026-01-28"],
                "home_team": ["Alpha", "Beta"],
                "away_team": ["Beta", "Alpha"],
                "home_score": [1, 0],
                "away_score": [0, 1],
                "tournament": ["League", "League"],
            }
        )
        run = calculate_ratings(matches, self.prior, self.confeds, 0.07)
        gamma = run.ratings.loc[run.ratings.team == "Gamma"].iloc[0]
        self.assertEqual(gamma.matches, 0.0)
        self.assertEqual(gamma.xG, 0.25)
        self.assertEqual(gamma.xGA, 0.75)

    def test_empty_sample_carries_prior_metrics(self):
        empty = pd.DataFrame(columns=["date", "home_team", "away_team", "home_score", "away_score", "tournament"])
        run = calculate_ratings(empty, self.prior, self.confeds, 0.07)
        self.assertEqual(len(run.ratings), 3)
        pd.testing.assert_series_equal(
            run.ratings.sort_values("team").xG.reset_index(drop=True),
            pd.Series([2.0, 1.0, 0.5], name="xG"),
            check_names=True,
        )

    def test_seeded_simulation_is_reproducible(self):
        matches = pd.DataFrame(
            {
                "date": ["2026-01-27", "2026-01-28", "2026-01-29"],
                "home_team": ["Alpha", "Beta", "Gamma"],
                "away_team": ["Beta", "Gamma", "Alpha"],
                "home_score": [1, 2, 0],
                "away_score": [0, 1, 1],
                "tournament": ["League", "League", "League"],
            }
        )
        run = calculate_ratings(matches, self.prior, self.confeds, 0.07)
        first = simulate_spi(run.ratings, self.dictionary, n_simulations=100, seed=42)
        second = simulate_spi(run.ratings, self.dictionary, n_simulations=100, seed=42)
        pd.testing.assert_frame_equal(first, second)


if __name__ == "__main__":
    unittest.main()
