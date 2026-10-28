"""Full-chamber projection: unhappy paths first, then the seat arithmetic and the control line."""
from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
import weight


def gpoll(pid, fe, d, r, pop='LV', n=1000, pollster='A'):
    return {'poll_id': pid, 'pollster': pollster, 'field_start': fe, 'field_end': fe, 'n': str(n), 'pop': pop, 'D': str(d), 'R': str(r), 'confirmed_at_source': 'YES'}


def seat(chamber, sid, state, up, holder, rating='Solid R', pres='-20.0', tracked='NA', district='NA', on_ballot=None):
    return {'chamber': chamber, 'seat': sid, 'state': state, 'district': district, 'up_2026': '1' if up else '0', 'special': '0', 'holder_party': holder,
            'incumbent_on_ballot': (on_ballot if on_ballot is not None else holder) if up else 'NA', 'cook_rating': rating if up else 'NA', 'cook_rating_date': '2026-10-20', 'pres2024_d_minus_r': pres,
            'tracked_race': tracked, 'source_sha256': 'x'}


def stub(seats, generic, ctx, early_vote=None):
    b = weight.Bundle.__new__(weight.Bundle)
    b.seats, b.generic_ballot, b._signal_ctx, b.as_of_date, b.early_vote = seats, generic, ctx, date(2026, 10, 27), early_vote
    return b


CTX = {'national': 2.0, 'national_sd': 1.0, 'leans': {'per_state': {'TX': {'state_adjustment': -0.5, 'lean': 1.5}}}, 'ev_model': None, 'witness': None,
       'fund': {weight.NATIONAL_FUNDAMENTALS_RACE: -1.5}, 'spend': {}}
GENERIC = [gpoll(f'p{i}', '2026-10-20', 50 + i % 2, 42, pollster=f'P{i}') for i in range(6)]   # mean D+8.5


class UnhappyPaths(unittest.TestCase):
    def test_no_seats_or_generic_or_national_means_no_block(self):
        self.assertIsNone(stub([], GENERIC, CTX).chambers_block({}, {'per_race': {}}))
        self.assertIsNone(stub([seat('SEN', 'SEN-AL-3', 'AL', False, 'R')], [], CTX).chambers_block({}, {'per_race': {}}))
        ctx = dict(CTX, fund={})
        self.assertIsNone(stub([seat('SEN', 'SEN-AL-3', 'AL', False, 'R')], GENERIC, ctx).chambers_block({}, {'per_race': {}}))

    def test_generic_needs_five_polls(self):
        self.assertIsNone(weight.generic_ballot_average(GENERIC[:4], date(2026, 10, 27)))


class Arithmetic(unittest.TestCase):
    def test_generic_average_is_the_weighted_margin(self):
        g = weight.generic_ballot_average(GENERIC, date(2026, 10, 27))
        self.assertEqual(g['polls'], 6)
        self.assertAlmostEqual(g['simple_mean'], 8.5, places=3)
        self.assertAlmostEqual(g['unadjusted_margin'], 8.5, places=3)   # equal weights: same dates, n, pop

    def test_house_effect_is_shrunk_toward_zero(self):
        rows = GENERIC + [gpoll('h1', '2026-10-20', 60, 40, pollster='H'), gpoll('h2', '2026-10-20', 60, 40, pollster='H')]
        g = weight.generic_ballot_average(rows, date(2026, 10, 27))
        self.assertGreater(g['house_adjustments']['H'], 0)
        self.assertLess(g['house_adjustments']['H'], 20 - g['unadjusted_margin'])   # shrunk, not the full deviation
        self.assertLess(g['margin'], g['unadjusted_margin'])

    def test_projection_is_base_plus_the_tracked_terms(self):
        seats = [seat('SEN', '2026-TX-SEN', 'TX', True, 'R', 'Solid R', '-13.7', on_ballot='R')]
        out = stub(seats, GENERIC, CTX).chambers_block({}, {'per_race': {}})
        item = out['chambers']['SEN']['items'][0]
        shift = out['generic']['margin'] - (-1.5)
        self.assertEqual(item['kind'], 'projection')
        self.assertAlmostEqual(item['base'], -13.7 + shift - 2.6, places=3)   # incumbent R on the ballot
        self.assertAlmostEqual(item['undertow'], item['base'] + 2.0 - 0.5, places=3)
        self.assertFalse(item['graded'])

    def test_open_seat_and_unknown_get_no_incumbency(self):
        for flag in ('NONE', 'UNKNOWN', 'VACANT', 'I'):
            seats = [seat('HOUSE', '2026-AL-01-HOUSE', 'AL', True, 'R', 'Solid R', '-30.0', district='01', on_ballot=flag)]
            item = stub(seats, GENERIC, CTX).chambers_block({}, {'per_race': {}})['chambers']['HOUSE']['items'][0]
            self.assertEqual(item['parts']['incumbency'], 0.0)

    def test_bonus_follows_the_incumbent_on_the_ballot_not_the_holder(self):
        seats = [seat('HOUSE', '2026-CA-06-HOUSE', 'CA', True, 'D', 'Solid D', '20.0', district='06', on_ballot='R')]   # a redistricted Republican runs here
        item = stub(seats, GENERIC, CTX).chambers_block({}, {'per_race': {}})['chambers']['HOUSE']['items'][0]
        self.assertEqual(item['parts']['incumbency'], -2.6)

    def test_tracked_reading_wins_over_the_swing(self):
        seats = [seat('SEN', '2026-TX-SEN', 'TX', True, 'R', 'Toss-up', '-13.7', tracked='2026-TX-SEN')]
        sig = {'2026-TX-SEN': {'adjusted_margin': 1.2, 'polling_margin': 0.5, 'delta_spending': 0.3, 'delta_early_vote': 0.0, 'polling_error': {'state_adjustment': -0.5}}}
        item = stub(seats, GENERIC, CTX).chambers_block({}, {'per_race': sig})['chambers']['SEN']['items'][0]
        self.assertEqual((item['kind'], item['undertow'], item['side'], item['graded']), ('reading', 1.2, 'D', True))

    def test_untracked_governor_is_rated_and_fixed(self):
        seats = [seat('GOV', '2026-VT-GOV', 'VT', True, 'R', 'Likely R', '32.0'), seat('GOV', '2026-KS-GOV', 'KS', True, 'D', 'Toss-up', '-16.0')]
        c = stub(seats, GENERIC, CTX).chambers_block({}, {'per_race': {}})['chambers']['GOV']
        self.assertEqual([i['kind'] for i in c['items']], ['rated', 'rated'])
        self.assertEqual([i['side'] for i in c['items']], ['R', None])
        self.assertEqual(c['at_bet'], {'D': 0, 'R': 1, 'undecided': 1})

    def test_senate_control_counts_seats_not_up_and_vance_breaks_a_tie(self):
        seats = [seat('SEN', f'SEN-X{i}-1', 'AL', False, 'D') for i in range(49)] + [seat('SEN', f'SEN-Y{i}-1', 'AL', False, 'R') for i in range(50)]
        seats.append(seat('SEN', '2026-WY-SEN', 'WY', True, 'D', 'Solid D', '40.0'))   # D projection: 50-50
        c = stub(seats, GENERIC, CTX).chambers_block({}, {'per_race': {}})['chambers']['SEN']
        self.assertEqual((c['at_bet']['D'], c['at_bet']['R'], c['control_at_bet']), (50, 50, 'R'))
        seats.append(seat('SEN', '2026-WV-SEN', 'WV', True, 'D', 'Solid D', '40.0'))
        c = stub(seats, GENERIC, CTX).chambers_block({}, {'per_race': {}})['chambers']['SEN']
        self.assertEqual((c['at_bet']['D'], c['control_at_bet']), (51, 'D'))



class ElectionNight(unittest.TestCase):
    SIG = {'2026-AA-SEN': {'polling_margin': 2.0, 'adjusted_margin': 4.0, 'delta_spending': 0.5, 'delta_early_vote': 0.0, 'polling_error': {'state_adjustment': -0.5}},
           '2026-BB-SEN': {'polling_margin': -3.0, 'adjusted_margin': -1.0, 'delta_spending': 0.0, 'delta_early_vote': 0.0, 'polling_error': {'state_adjustment': 0.0}},
           '2026-CC-SEN': {'polling_margin': 1.0, 'adjusted_margin': 3.0, 'delta_spending': 0.0, 'delta_early_vote': 0.0, 'polling_error': {'state_adjustment': 0.0}},
           '2026-DD-HOUSE': {'polling_margin': None, 'adjusted_margin': None}}
    slug = staticmethod(lambda r: r.replace('2026-', '').lower())

    def c(self, d, r, rep=100, called=None):
        return {'d_pct': d, 'r_pct': r, 'other_pct': 100 - d - r, 'reporting_pct': rep, 'called': called}

    def test_nothing_counted_means_no_dial(self):
        out = weight.live_miss(self.SIG, {}, self.slug)
        self.assertEqual((out['settled'], out['implied_miss'], out['dial_live']), (0, None, False))

    def test_unsettled_and_no_reading_races_do_not_count(self):
        out = weight.live_miss(self.SIG, {'aa-sen': self.c(55, 45, rep=60), 'dd-house': self.c(50, 50)}, self.slug)
        self.assertEqual(out['settled'], 0)

    def test_implied_miss_inverts_the_dial_arithmetic(self):
        # AA: count +10 = 2 + m - 0.5 + 0.5 -> m = 8; BB: count -1 = -3 + m -> m = 2; CC: called, count +4 = 1 + m -> m = 3
        live = {'aa-sen': self.c(55, 45), 'bb-sen': self.c(49.5, 50.5), 'cc-sen': self.c(52, 48, rep=40, called='D')}
        out = weight.live_miss(self.SIG, live, self.slug)
        self.assertEqual(out['settled'], 3)
        self.assertAlmostEqual(out['implied_miss'], (8 + 2 + 3) / 3, places=3)
        self.assertTrue(out['dial_live'])
        self.assertAlmostEqual(out['polls_mae'], (8 + 2 + 3) / 3, places=3)
        self.assertAlmostEqual(out['undertow_mae'], (6 + 0 + 1) / 3, places=3)
        self.assertEqual((out['undertow_closer'], out['polls_closer']), (3, 0))

    def test_two_races_do_not_set_the_dial(self):
        out = weight.live_miss(self.SIG, {'aa-sen': self.c(55, 45), 'bb-sen': self.c(49.5, 50.5)}, self.slug)
        self.assertFalse(out['dial_live'])


class WhatMoved(unittest.TestCase):
    def d(self, rid, per, n_est, at=None):
        return {'release_id': rid, 'analytical_as_of': '2026-10-30T12:00:00-07:00', 'signals': {'per_race': per},
                'estimates': [{'flags': {'principal': True}, 'quarantined': False}] * n_est,
                'chambers': {'chambers': {'SEN': {'at_bet': at or {'D': 55, 'R': 45}}}}}

    def test_no_prior_release(self):
        self.assertIsNone(weight.release_changes(None, self.d('b', {}, 0)))

    def test_moves_new_readings_polls_and_chambers(self):
        old = self.d('a', {'X': {'adjusted_margin': 1.0, 'polling_margin': 0.0}, 'Y': {'adjusted_margin': 2.0, 'polling_margin': 1.0}, 'Z': {'adjusted_margin': None}}, 10)
        new = self.d('b', {'X': {'adjusted_margin': 2.5, 'polling_margin': 1.0}, 'Y': {'adjusted_margin': 2.2, 'polling_margin': 1.1}, 'Z': {'adjusted_margin': 3.0, 'polling_margin': 2.0}}, 14, {'D': 56, 'R': 44})
        ch = weight.release_changes(old, new)
        self.assertEqual(ch['polls_added'], 4)
        self.assertEqual([m['race'] for m in ch['moved']], ['X'])       # Y moved 0.2, under the 0.3 floor
        self.assertEqual([m['race'] for m in ch['new_readings']], ['Z'])
        self.assertEqual(ch['chambers']['SEN']['to'], {'D': 56, 'R': 44})


if __name__ == '__main__':
    unittest.main()
