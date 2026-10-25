import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import weight


class TurnoutTests(unittest.TestCase):
    def row(self, **values):
        return dict({"election_dt": "11/03/2026", "ballot_rtn_status": "ACCEPTED", "ballot_req_type": "EARLY VOTING", "voter_party_code": "UNA", "ncid": "private1", "ballot_rtn_dt": "10/24/2026"}, **values)

    def test_empty_single_duplicate_and_no_identifiers(self):
        self.assertEqual(weight.nc_absentee_summary([], "11/03/2026")["accepted_unique"], 0)
        result = weight.nc_absentee_summary([self.row(), self.row()], "11/03/2026")
        self.assertEqual((result["accepted_unique"], result["duplicate_accepted_rows_removed"]), (1, 1))
        self.assertEqual(result["methods"]["EARLY_IN_PERSON"]["parties"]["UNA"]["share_pct"], 100)
        self.assertNotIn("private1", str(result))

    def test_conflicting_duplicate_and_unknown_method_stop(self):
        for rows in ([self.row(), self.row(voter_party_code="DEM")], [self.row(ballot_req_type="UNRECOGNIZED")], [self.row(ncid="")]):
            with self.assertRaises(weight.ValidationError):
                weight.nc_absentee_summary(rows, "11/03/2026")

    def test_unaccepted_are_excluded_and_county_keys_do_not_collide(self):
        rows = [self.row(ballot_rtn_status="REJECTED")]
        rows += [self.row(ncid="", county_desc=county, voter_reg_num="1", ballot_req_type="MAIL") for county in ("A", "B")]
        result = weight.nc_absentee_summary(rows, "11/03/2026")
        self.assertEqual((result["accepted_unique"], result["not_accepted_rows"]), (2, 1))
        self.assertEqual(result["methods"]["RETURNED_MAIL"]["accepted_ballots"], 2)

    def test_conflicts_are_missing_in_both_methods_when_explicitly_quarantined(self):
        result = weight.nc_absentee_summary([self.row(), self.row(ballot_req_type="MAIL")], "11/03/2026", quarantine_conflicts=True)
        self.assertEqual((result["accepted_unique"], result["conflicting_accepted_identities_excluded"]), (0, 1))
        self.assertEqual(sum(x["accepted_ballots"] for x in result["methods"].values()), 0)
