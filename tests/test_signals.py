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
                rows.append({"year": str(y), "state": st, "race": f"{y}{st}", "type": "Sen-G", "n_polls": "5",
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
