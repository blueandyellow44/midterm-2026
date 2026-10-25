"""Metric identity, malformed import, and an empty retained-pool sensitivity."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "analysis"), str(ROOT / "scripts")]
import weight
from import_ratings import import_rows


class RatingsTests(unittest.TestCase):
    def source(self):
        return {"name": "Silver Bulletin", "version_label": "Jan 2026", "cohort": "Silver Bulletin database, all race types and years in the file", "mapping": {"x": {"registry_name": "x", "rating_id": 8, "expected_rating_name": "x", "reason": "exact identity"}}}

    def test_wrong_identity_and_empty_registry_stop(self):
        for rows, profiles in [([], {}), ([weight._mkm("x")], {8: {"name": "different"}})]:
            with self.assertRaises(weight.ValidationError):
                import_rows(rows, self.source(), profiles)

    def test_missing_metric_is_provisional_and_boundaries_are_exact(self):
        for sae, factor, status in [(None, "1.0", "PROVISIONAL"), (3, "1.0", "RATED"), (3.01, "0.8", "RATED"), (5, "0.8", "RATED"), (5.01, "0.5", "RATED"), (float("nan"), "1.0", "PROVISIONAL")]:
            r = import_rows([weight._mkm("x")], self.source(), {8: {"name": "x", "n": 10, "sae": sae, "bias": .2, "banned": "no"}})[0]
            self.assertEqual((r["f_track"], r["track_status"]), (factor, status))

    def test_wrong_metric_or_factor_rejected(self):
        rated = import_rows([weight._mkm("x")], self.source(), {8: {"name": "x", "n": 10, "sae": 4, "bias": .2, "banned": "no"}})[0]
        for key, value in [("rating_metric", "Predictive Plus-Minus"), ("f_track", "1.0"), ("rating_poll_count", "0")]:
            bad = dict(rated, **{key: value})
            with tempfile.TemporaryDirectory() as temp:
                bundle = weight._bundle(temp, [], [bad])
                self.assertFalse(bundle.validate())

    def test_sensitivity_survives_all_polls_below_cutoff(self):
        poll = weight._mk("old", "2026-TX-SEN", "x", "2026-10-01", "2026-10-01", "2026-10-02", 100, "LV", 47, 43)
        with tempfile.TemporaryDirectory() as temp:
            bundle = weight._bundle(temp, [poll], [weight._mkm("x")])
            block = bundle.race_block("2026-TX-SEN", bundle.estimates(), True)
            self.assertEqual(block["retained_count"], 0)
            self.assertIsNone(block["weighted_margin"])
            self.assertEqual(block["no_cutoff_margin"], 4.0)
            self.assertEqual(block["no_cutoff_stratum"]["pop"], "LV")
            self.assertIsNone(block["newest_poll_age_days"])


if __name__ == "__main__":
    unittest.main()
