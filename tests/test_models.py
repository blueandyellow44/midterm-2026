"""Alternative models (2026-10-29): unhappy paths first, then the centers, the counts and the backtest on a toy archive."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
import models, simulate

BANDS = ((1, 2), (3, 5), (6, 10), (11, 10 ** 6))
BONUS = {'D': 2.3, 'R': 1.61}
RATED = simulate.RATED_CENTER


def hist():
    """A toy archive: presidential margins for two states, Senate and governor races every even year 2002-2024 with a
    known swing against the president's party and polls that miss by a fixed amount."""
    rows = []
    for y in range(2000, 2025, 4):
        for st, pm in (('AA', 10.0), ('BB', -10.0)):
            rows.append({'year': str(y), 'state': st, 'type': 'Pres-G', 'n_polls': '5', 'poll_margin': str(pm), 'actual_margin': str(pm)})
    for y in range(2002, 2025, 2):
        pres_party = models.PRESIDENT_PARTY.get(y, 'R')
        swing = 4.0 if pres_party == 'R' else -4.0   # toward the out party
        for i, st in enumerate(['AA'] * 6 + ['BB'] * 6):
            pm = (10.0 if st == 'AA' else -10.0)
            act = pm + swing + (1.0 if i % 2 else -1.0)
            rows.append({'year': str(y), 'state': st, 'type': 'Sen-G' if i % 3 else 'Gov-G', 'n_polls': str(1 + i % 4), 'poll_margin': str(act - 2.0), 'actual_margin': str(act)})
    return rows


def chambers():
    items_sen = [
        {'seat': 'S1', 'state': 'AA', 'kind': 'not_up', 'side': 'D'},
        {'seat': 'S2', 'state': 'BB', 'kind': 'reading', 'race': '2026-BB-SEN', 'polls': 1.0, 'undertow': 3.0, 'rating': 'Toss-up', 'pres2024_d_minus_r': -10.0, 'incumbent_on_ballot': 'R'},
        {'seat': 'S3', 'state': 'AA', 'kind': 'projection', 'base': 12.0, 'undertow': 14.0, 'rating': 'Solid D', 'pres2024_d_minus_r': 10.0, 'incumbent_on_ballot': 'D'},
    ]
    items_gov = [{'seat': 'G1', 'state': 'BB', 'kind': 'rated', 'rating': 'Likely R', 'pres2024_d_minus_r': -10.0, 'incumbent_on_ballot': 'NONE'}]
    items_house = [{'seat': 'H1', 'state': 'AA', 'kind': 'projection', 'base': 5.0, 'undertow': 7.0, 'rating': 'Lean D', 'pres2024_d_minus_r': 3.0, 'incumbent_on_ballot': 'NONE'}]
    return {'shift_toward_d': 2.0, 'tie_breaker': 'R', 'majority': {'SEN': 2, 'HOUSE': 1},
            'chambers': {'SEN': {'items': items_sen}, 'GOV': {'items': items_gov}, 'HOUSE': {'items': items_house}}}


FIT = {'division_sd': 1.0, 'state_sd': 2.0, 'shared_sd_measured': 2.5}
PARTISAN = {'v_prior': 16.0, 'v_polls': {'1-2': 16.0, '3-5': 9.0, '6-10': 4.0, '11-1000000': 4.0}}


def run_model(specs, fit, nsd, meta, tracked):
    return simulate.run_model(specs, fit, nsd, meta, tracked, n=400, seed=1)


class Unhappy(unittest.TestCase):
    def test_no_chambers_or_fit_or_history(self):
        for ch, fit, h in ((None, FIT, hist()), (chambers(), None, hist()), (chambers(), FIT, None), (chambers(), FIT, [])):
            self.assertIsNone(models.build(ch, {}, h, 2026, {}, fit, PARTISAN, BANDS, BONUS, RATED, 5.0, 5.7, 1.0, run_model))

    def test_swing_needs_two_years(self):
        self.assertIsNone(models.midterm_swing([], 2026))


class Centers(unittest.TestCase):
    def setUp(self):
        self.out = models.build(chambers(), {}, hist(), 2026, {'2026-BB-SEN': 3}, FIT, PARTISAN, BANDS, BONUS, RATED, 5.0, 5.7, 1.0, run_model)

    def test_every_model_covers_every_seat_up(self):
        for k in models.KEYS:
            self.assertEqual(set(self.out['models'][k]['centers']), {'2026-BB-SEN', 'S3', 'G1', 'H1'}, k)

    def test_polls_model(self):
        c = self.out['models']['polls']['centers']
        self.assertEqual(c['2026-BB-SEN'], 1.0)      # the polling average, no lean
        self.assertEqual(c['S3'], 12.0)              # projection base, no Undertow terms
        self.assertEqual(c['G1'], RATED['Likely R'])  # untracked governor keeps Cook

    def test_fundamentals_has_no_polls(self):
        swing = self.out['fundamentals_env']['swing_against_president']
        self.assertAlmostEqual(swing, 4.0, places=6)
        c = self.out['models']['fundamentals']['centers']
        self.assertAlmostEqual(c['2026-BB-SEN'], -10.0 + 4.0 - BONUS['R'], places=4)
        self.assertAlmostEqual(c['G1'], -10.0 + 4.0, places=4)

    def test_blend_sits_between_polls_and_prior(self):
        c = self.out['models']['blend']['centers']['2026-BB-SEN']
        prior = -10.0 + 2.0 - BONUS['R']
        self.assertTrue(prior < c < 1.0)
        w = models.blend_weight(PARTISAN, 3, BANDS)
        self.assertAlmostEqual(c, w * 1.0 + (1 - w) * prior, places=4)

    def test_ratings_model(self):
        c = self.out['models']['ratings']['centers']
        self.assertEqual(c['2026-BB-SEN'], 0.0)
        self.assertEqual(c['H1'], RATED['Lean D'])
        self.assertEqual(self.out['models']['ratings']['up_at_default']['SEN'], {'D': 1, 'R': 0, 'undecided': 1})

    def test_odds_and_dial(self):
        m = self.out['models']['polls']['simulation']
        self.assertEqual(len(m['dial']['chambers']['SEN']), len(m['dial']['values']))
        self.assertIn('2026-BB-SEN', m['per_seat'])
        self.assertTrue(0 <= m['chambers']['HOUSE']['p_control_d'] <= 1)

    def test_backtest_scores_each_model(self):
        bt = self.out['backtest']
        self.assertGreater(bt['midterms']['fundamentals']['races'], 0)
        self.assertLess(bt['midterms']['fundamentals']['mae'], bt['midterms']['polls']['mae'])   # toy polls miss by 2, the swing is exact
        self.assertIsNone(bt['ratings'])


if __name__ == '__main__':
    unittest.main()
