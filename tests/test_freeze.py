"""Stage 3 freeze (audit 2026-10-31): the date gate, and predictions.csv carrying the simulation's probability and the terms
beside the flat-curve probability, so the graded record is the number the site showed. Unhappy paths first."""
from datetime import date
from pathlib import Path
import csv
import io
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
sys.path.insert(0, str(ROOT / 'scripts'))
import weight  # noqa: E402
import release_signals  # noqa: E402


def derived_fixture(with_sim=True):
    sig = {"adjusted_margin": 5.1787, "polling_margin": 2.3275, "delta_polling_error": 2.2023, "polling_error": {"state_adjustment": 0.2664},
           "delta_spending": 1.0221, "delta_early_vote": 0.0, "delta_partisan": -0.3731}
    d = {"section9_heat": {"races_with_defined_debate_gap": []}, "estimates": [],
         "races": {"2026-TX-SEN": {"weighted_margin": 2.3275, "retained_count": 9, "polling_read": {"rounds": "NA", "method": "v2"}, "averaging_stratum": None, "contrast_stratum": None}},
         "signals": {"per_race": {"2026-TX-SEN": sig, "2026-NO-POLLS-HOUSE": {"adjusted_margin": None}}}}
    if with_sim:
        d["simulation"] = {"per_seat": {"2026-TX-SEN": {"p_d": 0.8123, "center": 5.1787}}}
    return d


class FreezeGate(unittest.TestCase):
    def test_refused_before_november_2(self):
        self.assertFalse(release_signals.freeze_allowed(date(2026, 10, 31)))
        self.assertFalse(release_signals.freeze_allowed(date(2026, 11, 1)))

    def test_allowed_from_november_2_or_with_the_override(self):
        self.assertTrue(release_signals.freeze_allowed(date(2026, 11, 2)))
        self.assertTrue(release_signals.freeze_allowed(date(2026, 11, 3)))
        self.assertTrue(release_signals.freeze_allowed(date(2026, 10, 31), allow_early=True))


class PredictionsRecord(unittest.TestCase):
    def rows(self, derived):
        b = weight.Bundle.__new__(weight.Bundle)
        return weight.Bundle.predictions(b, derived, "2026-11-02T18:00:00-08:00")

    def test_header_carries_the_simulation_probability_and_the_terms(self):
        for col in ("p_d_slot", "p_d_simulation", "polling_margin", "polling_error_lean", "state_adjustment", "spending", "early_vote", "partisan", "frozen_at"):
            self.assertIn(col, weight.PREDICTIONS_HEADER)
        self.assertEqual(weight.CSV_SCHEMAS["predictions"], "1.1")

    def test_signal_row_freezes_the_shown_probability_and_each_term(self):
        rows = {(r["race"], r["vector"]): r for r in self.rows(derived_fixture())}
        s = rows[("2026-TX-SEN", "SIGNAL_ADJUSTED")]
        self.assertEqual(s["p_d_simulation"], "0.8123")
        self.assertEqual(s["p_d_slot"], f"{weight.stage3_probability(5.1787):.4f}")
        self.assertEqual((s["weighted_margin"], s["polling_margin"], s["polling_error_lean"], s["state_adjustment"], s["spending"], s["early_vote"], s["partisan"]),
                         ("5.18", "2.33", "2.20", "0.27", "1.02", "0.00", "-0.37"))
        self.assertAlmostEqual(float(s["polling_margin"]) + float(s["polling_error_lean"]) + float(s["spending"]) + float(s["early_vote"]) + float(s["partisan"]), float(s["weighted_margin"]), places=1)
        self.assertEqual(s["frozen_at"], "2026-11-02T18:00:00-08:00")
        self.assertNotIn(("2026-NO-POLLS-HOUSE", "SIGNAL_ADJUSTED"), rows)   # no reading, nothing frozen, nothing graded

    def test_polling_vector_rows_leave_the_reading_columns_na(self):
        rows = {(r["race"], r["vector"]): r for r in self.rows(derived_fixture())}
        p = rows[("2026-TX-SEN", "ALL_ELIGIBLE")]
        self.assertEqual((p["p_d_simulation"], p["polling_error_lean"], p["partisan"]), ("NA", "NA", "NA"))

    def test_without_a_simulation_the_column_is_na_not_a_guess(self):
        rows = {(r["race"], r["vector"]): r for r in self.rows(derived_fixture(with_sim=False))}
        self.assertEqual(rows[("2026-TX-SEN", "SIGNAL_ADJUSTED")]["p_d_simulation"], "NA")

    def test_every_row_fits_the_header_exactly(self):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=weight.PREDICTIONS_HEADER, extrasaction="raise")
        w.writeheader()
        for r in self.rows(derived_fixture()):
            w.writerow(r)   # raises on an unknown key; missing keys would be empty, so check them too
            self.assertEqual(set(r), set(weight.PREDICTIONS_HEADER))


if __name__ == "__main__":
    unittest.main()
