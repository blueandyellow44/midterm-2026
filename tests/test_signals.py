"""Signal-adjusted reading: unhappy paths first, then the alignment rule and the arithmetic."""
from pathlib import Path
import math
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
import weight

BETA = (1.0, 0.5)
GAMMA = (1.5, 1.0)


def heat(race, slot, score, status='SCORED'):
    return {'race': race, 'slot': slot, 'ph_score': str(score), 'status': status}


def bundle_stub(spending, fundamentals, heat_rows=(), history=()):
    b = weight.Bundle.__new__(weight.Bundle)
    b.spending, b.fundamentals, b.heat, b.spend_history = list(spending), list(fundamentals), list(heat_rows), list(history)
    return b


def spend_row(race, d, r, coverage='FEC_SCHEDULE_E'):
    return {'race': race, 'fec_coverage': coverage, 'window_end': '2026-10-25', 'd_fav_recent': str(d), 'r_fav_recent': str(r),
            'd_fav_prior': '0', 'r_fav_prior': '0'}


class UnhappyPaths(unittest.TestCase):
    def test_missing_inputs_return_no_block(self):
        self.assertIsNone(bundle_stub([], []).signals_block({}))

    def test_no_polling_read_never_invents_a_margin(self):
        out = weight.signal_adjusted(None, 2.0, 1.0, BETA, GAMMA)
        self.assertEqual(out['status'], 'NO_POLLING_READ')
        self.assertIsNone(out['adjusted_margin'])

    def test_no_signal_leaves_the_polling_read_unchanged(self):
        out = weight.signal_adjusted(3.0, None, None, BETA, GAMMA)
        self.assertEqual((out['status'], out['adjusted_margin'], out['delta_total'], out['lagging_side']), ('NO_SIGNAL', 3.0, 0.0, None))

    def test_tiny_signals_carry_no_direction(self):
        self.assertEqual(weight.alignment_weights(0.1, 0.05)[2], 'NO_SIGNAL')
        self.assertEqual(weight.alignment_weights(0.3, 0.05)[2], 'SPENDING_ONLY')

    def test_rhetoric_needs_two_scored_units_per_candidate(self):
        rows = [heat('X', 'D', 3), heat('X', 'R', 4), heat('X', 'R', 4), heat('X', 'D', 5, status='FAILED')]
        self.assertIsNone(weight.rhetoric_gap(rows, 'X')['gap'])
        self.assertIsNone(weight.rhetoric_gap([], 'X')['gap'])

    def test_unknown_fundamentals_give_no_spending_direction(self):
        self.assertEqual(weight.underdog_sign(None), 0)
        self.assertEqual(weight.underdog_sign(0.0), 0)

    def test_undefined_excess_fit(self):
        self.assertIsNone(weight.excess_spend_z([1.0, 1.0, 1.0], [2.0, 2.0, 2.0]))
        self.assertIsNone(weight.excess_spend_z([1.0, 2.0], [1.0, 2.0]))

    def test_thin_history_keeps_the_prior(self):
        est = weight.spending_history_estimate([{'year': '2020', 'poll_margin': '1', 'result_margin': '2', 'log_recent_spend_m': '1', 'pres_d_minus_r': '-3'}])
        self.assertEqual(est['status'], 'insufficient history')
        self.assertEqual(weight.normal_posterior((1.5, 1.0), est['slope'], est['se']), (1.5, 1.0))

    def test_governors_without_fec_coverage_stay_unadjusted(self):
        races = weight.SENATE_RACES + weight.GOVERNOR_RACES
        spending = [spend_row(r, 1e6 * (i + 1), 2e6) for i, r in enumerate(weight.SENATE_RACES)] + [spend_row(r, 'NA', 'NA', 'NOT_FEDERAL') for r in weight.GOVERNOR_RACES]
        fundamentals = [{'race': r, 'pres_d_minus_r': '-5'} for r in races]
        blocks = {r: {'polling_read': {'margin': 1.0 + i}} for i, r in enumerate(races)}
        out = bundle_stub(spending, fundamentals).signals_block(blocks)
        gov = out['per_race']['2026-OH-GOV']
        base = blocks['2026-OH-GOV']['polling_read']['margin']
        self.assertEqual((gov['alignment'], gov['spending']['status']), ('NO_SIGNAL', 'not federal: no FEC coverage'))
        self.assertAlmostEqual(gov['adjusted_margin'], base + weight.SIGNAL_POLL_ERROR_TOWARD_D)
        self.assertAlmostEqual(gov['delta_polling_error'], weight.SIGNAL_POLL_ERROR_TOWARD_D)
        self.assertEqual(len(out['rules']['excess_fit_races']), len(weight.SENATE_RACES))


class PollingError(unittest.TestCase):
    def test_polling_error_adds_to_every_reading_and_counts_in_the_total(self):
        out = weight.signal_adjusted(1.0, None, None, BETA, GAMMA, 3.3)
        self.assertEqual((out['status'], out['alignment']), ('ADJUSTED', 'NO_SIGNAL'))
        self.assertAlmostEqual(out['adjusted_margin'], 4.3)
        self.assertAlmostEqual(out['delta_total'], out['delta_spending'] + out['delta_rhetoric'] + out['delta_polling_error'])

    def test_no_polling_read_gets_no_polling_error(self):
        self.assertIsNone(weight.signal_adjusted(None, 1.0, 1.0, BETA, GAMMA, 3.3)['adjusted_margin'])


class AlignmentRule(unittest.TestCase):
    def test_aligned_signals_apply_at_full_weight(self):
        out = weight.signal_adjusted(2.0, 1.0, 1.0, BETA, GAMMA)
        self.assertEqual(out['alignment'], 'ALIGNED')
        self.assertAlmostEqual(out['adjusted_margin'], 2.0 + 1.0 + 1.5)
        self.assertEqual(out['lagging_side'], 'R')

    def test_opposed_signals_apply_at_a_quarter(self):
        out = weight.signal_adjusted(2.0, 1.0, -1.0, BETA, GAMMA)
        self.assertEqual(out['alignment'], 'OPPOSED')
        self.assertAlmostEqual(out['delta_total'], 0.25 * 1.0 - 0.25 * 1.5)

    def test_single_signal_applies_at_half(self):
        self.assertAlmostEqual(weight.signal_adjusted(0.0, -2.0, None, BETA, GAMMA)['delta_total'], -1.0)
        self.assertAlmostEqual(weight.signal_adjusted(0.0, None, 1.0, BETA, GAMMA)['delta_total'], 0.75)

    def test_rhetoric_contribution_is_capped(self):
        out = weight.signal_adjusted(0.0, None, 4.0, BETA, GAMMA)
        self.assertTrue(out['rhetoric_capped'])
        self.assertAlmostEqual(out['delta_rhetoric'], 0.5 * weight.SIGNAL_RHETORIC_CAP)


class Arithmetic(unittest.TestCase):
    def test_hotter_republican_reads_as_lagging(self):
        rows = [heat('X', 'D', 3), heat('X', 'D', 3), heat('X', 'R', 4), heat('X', 'R', 4)]
        self.assertEqual(weight.rhetoric_gap(rows, 'X')['gap'], 1.0)

    def test_missing_money_points_to_the_poll_leader_not_the_favorite(self):
        # Georgia-style: R is the fundamentals favorite (underdog D, +1) but D leads the polls and money dries up.
        self.assertEqual(weight.spend_direction(-1.2, 1, 7.1), 1)
        self.assertEqual(weight.spend_direction(-1.2, -1, -3.0), -1)
        self.assertEqual(weight.spend_direction(-1.2, 1, 0.0), 0)

    def test_extra_money_points_to_the_fundamentals_underdog(self):
        self.assertEqual(weight.spend_direction(1.1, 1, -2.0), 1)
        self.assertEqual(weight.spend_direction(1.1, -1, 5.0), -1)

    def test_underdog_sign_follows_the_presidential_loser(self):
        self.assertEqual(weight.underdog_sign(-13.7), 1)
        self.assertEqual(weight.underdog_sign(6.9), -1)

    def test_posterior_is_precision_weighted(self):
        m, s = weight.normal_posterior((1.5, 1.0), 0.5, 1.0)
        self.assertAlmostEqual(m, 1.0)
        self.assertAlmostEqual(s, math.sqrt(0.5))

    def test_excess_spending_is_residual_on_poll_closeness(self):
        z = weight.excess_spend_z([1.0, 2.0, 3.0, 10.0], [3.0, 2.0, 1.0, 0.5])
        self.assertEqual(max(range(4), key=lambda i: z[i]), 3)
        self.assertAlmostEqual(sum(z), 0.0, places=9)


if __name__ == '__main__':
    unittest.main()


class FreezeRecordsOurReading(unittest.TestCase):
    def test_signal_adjusted_row_frozen_beside_polls(self):
        b = weight.Bundle.__new__(weight.Bundle)
        derived = {"section9_heat": {"races_with_defined_debate_gap": []}, "estimates": [],
                   "races": {"2026-TX-SEN": {"weighted_margin": None, "averaging_stratum": None, "retained_count": 3}},
                   "signals": {"per_race": {"2026-TX-SEN": {"adjusted_margin": 7.2}, "2026-IA-SEN": {"adjusted_margin": None}}}}
        rows = weight.Bundle.predictions(b, derived, "2026-11-02T00:00:00-07:00")
        self.assertEqual([r["vector"] for r in rows], ["SIGNAL_ADJUSTED"])
        self.assertEqual(rows[0]["weighted_margin"], "7.20")
        self.assertEqual(rows[0]["n_retained"], 3)


class StateLean(unittest.TestCase):
    def rows(self):
        out = []
        for y in range(2000, 2026, 2):
            out += [{"year": str(y), "state": "AA", "state_bias": "3.0"}, {"year": str(y), "state": "BB", "state_bias": "-1.0"},
                    {"year": str(y), "state": "CC", "state_bias": "1.0"}]
        return out

    def test_persistent_overstatement_shrinks_lean(self):
        l = weight.state_poll_error_leans(self.rows(), 3.3)
        self.assertEqual(l["target_year"], 2026)
        self.assertAlmostEqual(l["slope"], 1.0, places=3)
        self.assertAlmostEqual(l["per_state"]["AA"]["lean"], 1.3, places=3)   # polls overstate D by 2 more than national
        self.assertAlmostEqual(l["per_state"]["BB"]["lean"], 5.3, places=3)
        self.assertAlmostEqual(l["per_state"]["CC"]["lean"], 3.3, places=3)

    def test_thin_history_gets_national(self):
        rows = self.rows() + [{"year": "2024", "state": "DD", "state_bias": "9.0"}]
        self.assertEqual(weight.state_poll_error_leans(rows, 3.3)["per_state"]["DD"]["lean"], 3.3)

    def test_no_rows(self):
        self.assertEqual(weight.state_poll_error_leans([], 3.3)["per_state"], {})


class LeanUncertainty(unittest.TestCase):
    def test_range_includes_poll_error_sd(self):
        out = weight.signal_adjusted(2.0, None, None, (1.5, 1.0), (0.75, 0.5), 2.5, 1.8)
        self.assertAlmostEqual(out["delta_sd"], 1.8, places=4)
        sd = (1.8 ** 2 + 4.06 ** 2) ** 0.5
        self.assertAlmostEqual(out["range_sd"], sd, places=3)
        self.assertEqual(out["range"], [weight.r4(4.5 - sd), weight.r4(4.5 + sd)])

    def test_lean_constants_match_refit(self):
        self.assertAlmostEqual(weight.SIGNAL_POLL_ERROR_TOWARD_D, 2.48, places=2)
        self.assertAlmostEqual(weight.SIGNAL_POLL_ERROR_SD, 1.82, places=2)


class PollErrorModel(unittest.TestCase):
    def hist(self):
        rows = []
        for y in range(1999, 2026):
            miss = 2.0 if y % 2 else 1.0   # off-year overstated D by 2, next year by 1 -> share 0.5
            for st in ("AA", "BB", "CC"):
                rows.append({"year": str(y), "state": st, "race": f"{y}_Sen-G_{st}", "type": "Sen-G", "n_polls": "5",
                             "poll_margin": str(miss), "actual_margin": "0", "bias": str(miss)})
        return rows

    def test_carryover_and_lean_from_history(self):
        m = weight.poll_error_model(self.hist(), 2026)
        self.assertAlmostEqual(m["carryover_share"], 0.5, places=3)
        self.assertAlmostEqual(m["offyear_miss_toward_d"], -2.0, places=3)
        self.assertAlmostEqual(m["lean_toward_d"], -1.0, places=3)
        self.assertEqual(m["backtest"]["years"], 8)
        self.assertAlmostEqual(m["backtest"]["mae_with_lean"], 0.0, places=3)   # lean exactly removes the 1-point miss

    def test_no_history(self):
        self.assertIsNone(weight.poll_error_model([], 2026))


class AbandonmentDeadZone(unittest.TestCase):
    def test_near_tie_gives_no_direction(self):
        self.assertEqual(weight.spend_direction(-1.3, 1, 0.2), 0)
        self.assertEqual(weight.spend_direction(-1.3, 1, -1.99), 0)
        self.assertEqual(weight.spend_direction(-1.3, 1, 2.0), 1)

    def test_extra_money_unaffected(self):
        self.assertEqual(weight.spend_direction(1.3, -1, 0.2), -1)


class EarlyVoteContext(unittest.TestCase):
    def test_block_found_and_never_counted(self):
        rows = [{"state": "TX", "shift_vs_2022": "3.1", "d_margin_2026": "-8.0", "d_margin_2022_same_day": "-11.1", "as_of": "2026-10-26", "party_basis": "modeled", "source_url": "https://x"}]
        b = weight.early_vote_block(rows, "TX")
        self.assertFalse(b["in_reading"])
        self.assertAlmostEqual(b["shift_vs_2022_toward_d"], 3.1)
        self.assertIsNone(weight.early_vote_block(rows, "IA"))
        self.assertIsNone(weight.early_vote_block(None, "TX"))


class PollingAverageV2(unittest.TestCase):
    def est(self, race, pid, D, R, fe, n=800, pop="LV", den="FULL"):
        return {"race": race, "pollster_id": pid, "D": D, "R": R, "field_start": fe, "field_end": fe, "n": n, "pop": pop,
                "denominator_class": den, "round": "NA", "window": "BOTH", "flags": {"principal": True}, "quarantined": False,
                "primary_verified": "YES", "sample_id": f"{pid}-{fe}-{race}", "estimate_id": f"{pid}-{fe}-{race}-{pop}", "margin": D - R, "factors": {"f_track": 1.0}}

    def test_uses_every_poll_and_removes_house_lean(self):
        from datetime import date
        ests = [self.est("X", "a", 50, 45, "2026-10-25"), self.est("X", "b", 48, 47, "2026-10-20"), self.est("X", "c", 47, 47, "2026-10-10"),
                self.est("Y", "a", 52, 44, "2026-10-25"), self.est("Y", "b", 49, 47, "2026-10-25")]
        v = weight.polling_average_v2(ests, date(2026, 10, 27))
        self.assertEqual(v["per_race"]["X"]["polls"], 3)
        self.assertIn("a", v["per_race"]["X"]["house_adjustments"])   # a runs D-ward in Y, so it is adjusted in X
        self.assertLess(v["per_race"]["X"]["two_party_margin"], 100 * (50 - 45) / 95)

    def test_unverified_and_quarantined_excluded(self):
        from datetime import date
        a = self.est("X", "a", 50, 45, "2026-10-25"); b = dict(self.est("X", "b", 40, 55, "2026-10-25"), primary_verified="UNVERIFIED")
        c = dict(self.est("X", "c", 40, 55, "2026-10-25"), quarantined=True)
        self.assertEqual(weight.polling_average_v2([a, b, c], date(2026, 10, 27))["per_race"]["X"]["polls"], 1)


class RegularGeneralsOnly(unittest.TestCase):
    def test_specials_and_la_primaries_excluded(self):
        self.assertTrue(weight.regular_general("2025_Gov-G_NJ"))
        self.assertFalse(weight.regular_general("2017_Sen-GS_AL"))
        self.assertFalse(weight.regular_general("2019_Gov-O_LA"))
        self.assertFalse(weight.regular_general("2015_Gov-GR_LA"))


class AuditFixes(unittest.TestCase):
    def est(self, sample, rnd, D, R, pop="LV", den="FULL", verified="YES"):
        return {"race": "2026-AK-SEN", "pollster_id": sample, "D": D, "R": R, "field_start": "2026-10-20", "field_end": "2026-10-20", "n": 800,
                "pop": pop, "denominator_class": den, "round": rnd, "window": "BOTH", "flags": {"principal": True}, "quarantined": False,
                "primary_verified": verified, "sample_id": sample, "estimate_id": f"{sample}-{rnd}-{pop}-{den}", "margin": D - R, "factors": {"f_track": 1.0}}

    def test_rcv_race_uses_first_round_only_one_per_survey(self):
        from datetime import date
        v = weight.polling_average_v2([self.est("s1", "FIRST", 45, 44), self.est("s1", "FINAL", 51, 49), self.est("s2", "FINAL", 52, 48),
                                       self.est("s1", "FIRST", 46, 44, pop="RV")], date(2026, 10, 27))
        x = v["per_race"]["2026-AK-SEN"]
        self.assertEqual(x["polls"], 1)
        self.assertEqual(x["rounds"], "FIRST")

    def test_unverified_round_excluded(self):
        from datetime import date
        v = weight.polling_average_v2([self.est("s1", "UNVERIFIED", 45, 44), self.est("s2", "FIRST", 46, 44)], date(2026, 10, 27))
        self.assertEqual(v["per_race"]["2026-AK-SEN"]["polls"], 1)

    def test_lv_rv_gap_ignores_unverified_pairs(self):
        from datetime import date
        ests = [self.est("a", "NA", 50, 45, pop="LV"), self.est("a", "NA", 52, 44, pop="RV"),
                self.est("b", "NA", 40, 55, pop="LV", verified="UNVERIFIED"), self.est("b", "NA", 60, 30, pop="RV", verified="UNVERIFIED")]
        self.assertEqual(weight.polling_average_v2(ests, date(2026, 10, 27))["lv_rv_pairs"], 1)


class UncertaintyAndSpendingReplay(unittest.TestCase):
    def test_lean_sd_includes_residual(self):
        rows = []
        for y in range(1999, 2026):
            miss = (2.0 if y % 2 else 1.0) + (0.5 if y % 4 == 1 else 0.0)
            rows.append({"year": str(y), "state": "AA", "race": f"{y}_Sen-G_AA", "type": "Sen-G", "n_polls": "5", "poll_margin": str(miss), "actual_margin": "0", "bias": str(miss)})
        m = weight.poll_error_model(rows, 2026)
        self.assertGreater(m["lean_residual_sd"], 0)
        self.assertAlmostEqual(m["lean_sd"] ** 2, m["lean_coefficient_sd"] ** 2 + m["lean_residual_sd"] ** 2, places=3)

    def test_spending_replay_uses_only_earlier_years(self):
        rows = [{"year": y, "state": s, "poll_margin": str(p), "result_margin": str(p - 1), "log_recent_spend_m": str(ls), "pres_d_minus_r": str(pr)}
                for y in ("2020", "2022") for s, p, ls, pr in (("A", 2, 1.0, -5), ("B", 5, 3.0, -8), ("C", -3, 0.5, 4), ("D", 8, 2.0, 10), ("E", 1, 2.5, -2), ("F", -6, 1.5, -9))]
        b = weight.spending_backtest(rows)
        self.assertEqual(b["by_year"]["2020"]["trained_on"], [])
        self.assertEqual(b["by_year"]["2022"]["trained_on"], ["2020"])
        self.assertEqual(b["by_year"]["2020"]["beta"], weight.SIGNAL_PRIOR_BETA[0])
