import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight


class BacktestTests(unittest.TestCase):
    def test_gate_prevents_unpassed_backtest_output(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = weight._bundle(temp, [], [])
            bundle.backtest = [{"not": "validated"}]
            self.assertIsNone(bundle.backtest_block(False))

    def test_signed_error_uses_full_certified_denominator_and_separate_2025_method(self):
        with tempfile.TemporaryDirectory() as temp:
            current = weight._mkm("x", "YES")
            historical = dict(current, method_id="x-s-2025-VA", recall_weighted="NO", weighting_quote="age and sex", applicability="SURVEY")
            bundle = weight._bundle(temp, [], [current, historical])
            poll = weight._mk("backtest", "2025-VA-GOV", "x", "2025-10-20", "2025-10-21", "2025-10-22", 500, "LV", 50, 45, recall="NO", method=historical["method_id"])
            certified = weight.certified_vote_margin({"D_votes": 55, "R_votes": 40, "other_vote_counts": [5]})
            poll.update(certified_D=str(certified["D"]), certified_R=str(certified["R"]), certified_margin=str(certified["margin"]), result_url="https://example.org/results", result_locator="official totals", certification_date="2025-12-01", signed_error="NA")
            bundle.backtest = bundle.derive_rows([poll], backtest=True)
            self.assertTrue(bundle.validate(), bundle.problems)
            self.assertEqual(bundle.backtest[0]["signed_error"], "-10.0")
            self.assertEqual(bundle.backtest_block(True)["by_state"]["2025-VA-GOV"]["groups"]["NO"]["n"], 1)
            self.assertEqual(bundle.method_by_id[current["method_id"]]["recall_weighted"], "YES")
