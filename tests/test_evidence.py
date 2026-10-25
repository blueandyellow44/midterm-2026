"""Regression cases from real primary-source and connector discrepancies."""
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))
import weight
import build_polls

spec = importlib.util.spec_from_file_location("find_stories", ROOT / "scripts/coverage/find_stories.py")
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)


class EvidenceTests(unittest.TestCase):
    def test_joint_partner_does_not_inherit_fox_identity(self):
        self.assertEqual(build_polls.pollster_slug("Cygnal", "Beacon Research"), "cygnal-beacon")
        self.assertEqual(build_polls.pollster_slug("Fox News", "Beacon Research / Shaw & Company"), "fox-beacon-shaw")

    def coverage_call(self, result):
        with tempfile.TemporaryDirectory() as temp:
            args = ["find_stories.py", "--bundle-dir", temp, "--expected-edition", "2026-10-25", "--races", "2026-MI-GOV"]
            with patch.object(sys, "argv", args), patch.object(coverage, "rpc", side_effect=[({}, "session"), ({}, None), ({"result": result}, None)]), redirect_stdout(io.StringIO()):
                self.assertEqual(coverage.main(), 0)
            return weight.read_csv(str(Path(temp) / "coverage.csv"), weight.COVERAGE_HEADER)[0]

    def test_actual_connector_shape_and_candidate_partial(self):
        # The October8 edition returns a story mentioning Benson, not James.
        r = self.coverage_call({"structuredContent": {"edition": "2026-10-08", "stale": True, "total": 1, "stories": [{"story_id": "obama-rally", "headline": "Obama to rally for El-Sayed in Michigan", "summary": "Jocelyn Benson will attend", "outletCount": 7, "low": {"score": 1.3}, "high": {"score": 2.5}, "calmest": {"outlet": "The Hill"}, "hottest": {"outlet": "Daily Wire"}}]}})
        self.assertEqual((r["edition_status"], r["match_status"]), ("STALE_FLAG", "PARTIAL"))
        self.assertEqual((r["story_count"], r["outlet_count"], r["spread"]), ("1", "7", "1.2"))

    def test_error_and_missing_edition_are_unknown_not_zero(self):
        for result in [{"isError": True, "content": [{"type": "text", "text": "access failed"}]}, {"structuredContent": {"stories": []}}]:
            r = self.coverage_call(result)
            self.assertEqual((r["edition_status"], r["match_status"], r["story_count"], r["outlet_count"]), ("ACCESS_FAILED", "ERROR", "UNVERIFIED", "UNVERIFIED"))

    def test_confirmed_empty_reply_is_zero(self):
        r = self.coverage_call({"structuredContent": {"edition": "2026-10-25", "stories": [], "total": 0}})
        self.assertEqual((r["edition_status"], r["match_status"], r["story_count"]), ("OK", "ZERO", "0"))

    def test_full_valid_vote_denominator_includes_other_candidates(self):
        result = weight.certified_vote_margin({"D_votes": 45, "R_votes": 50, "other_vote_counts": [3, 2]})
        self.assertEqual(result, {"D": 45.0, "R": 50.0, "margin": -5.0, "valid_votes": 100})
        for bad in [None, {}, {"D_votes": 0, "R_votes": 0}, {"D_votes": 45, "R_votes": 50, "other_vote_counts": ["*"]}]:
            self.assertIsNone(weight.certified_vote_margin(bad))


if __name__ == "__main__":
    unittest.main()
