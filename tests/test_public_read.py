"""Public source facts must not silently become qualifying averages."""
from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
import weight

RACE = '2026-MI-GOV'
TODAY = date(2026, 10, 25)


def estimate(eid='one', **changes):
    row = weight._mk(eid, RACE, 'firm', '2026-10-15', '2026-10-18', '2026-10-19', None, 'LV', 51, 45)
    row.update(flag_principal=True, quarantined=False, margin_num=6.0, n_num=None, flag_reasons=['n missing'])
    row.update(changes)
    return row


class PublicReadTests(unittest.TestCase):
    def test_empty_and_missing_context_stay_unavailable(self):
        for rows in (None, [], [{}]):
            self.assertIsNone(weight.latest_published_poll(rows, RACE, TODAY))
        self.assertIsNone(weight.latest_published_poll([estimate()], RACE, None))

    def test_unverified_quarantined_future_alternate_and_wrong_round_cannot_supply_read(self):
        for changes in ({'primary_verified': 'UNVERIFIED'}, {'quarantined': True},
                        {'flag_principal': False}, {'round': 'UNVERIFIED'}, {'round': 'FINAL'},
                        {'field_end': '2026-10-26'}, {'release_date': '2026-10-26'},
                        {'window': 'HOUSE_ONLY'}, {'source_url': 'javascript:bad'},
                        {'margin_num': None}, {'pop': 'UNVERIFIED'}):
            with self.subTest(changes=changes):
                self.assertIsNone(weight.latest_published_poll([estimate(**changes)], RACE, TODAY))

    def test_malformed_numeric_and_date_raise_instead_of_becoming_evidence(self):
        for changes in ({'margin_num': float('nan')}, {'field_end': 'not a date'}):
            with self.assertRaises(ValueError):
                weight.latest_published_poll([estimate(**changes)], RACE, TODAY)

    def test_missing_sample_and_unknown_sponsor_are_source_context_only(self):
        with tempfile.TemporaryDirectory() as temp:
            poll = weight._mk('one', RACE, 'firm', '2026-10-15', '2026-10-18', '2026-10-19', None, 'LV', 51, 45, sponsor='UNKNOWN')
            bundle = weight._bundle(temp, [poll], [weight._mkm('firm')])
            block = bundle.race_block(RACE, bundle.estimates(), True)
            self.assertIsNone(block['weighted_margin'])
            self.assertEqual(block['averaging_estimate_ids'], [])
            read = block['polling_read']
            self.assertEqual((read['kind'], read['margin'], read['age_days']), ('LATEST_POLL', 6, 7))
            self.assertIsNone(read['latest_poll']['n'])

    def test_rcv_final_precedes_newer_first_and_unsupported_never_substitutes(self):
        race = '2026-AK-SEN'
        final = estimate('final', race=race, round='FINAL', field_end='2026-10-16')
        first = estimate('first', race=race, round='FIRST', field_end='2026-10-20', release_date='2026-10-21')
        unknown = estimate('unknown', race=race, round='UNVERIFIED', field_end='2026-10-22')
        self.assertEqual(weight.latest_published_poll([first, unknown, final], race, TODAY)['estimate_id'], 'final')
        self.assertEqual(weight.latest_published_poll([unknown, first], race, TODAY)['round'], 'FIRST')

    def test_latest_date_then_release_then_stratum_then_id_is_order_independent(self):
        rows = [estimate('z'), estimate('a'), estimate('old', field_end='2026-10-17'),
                estimate('earlier-release', release_date='2026-10-18'), estimate('adult', pop='A')]
        for pool in (rows, list(reversed(rows)), rows * 1000):
            self.assertEqual(weight.latest_published_poll(pool, RACE, TODAY)['estimate_id'], 'a')

    def test_qualifying_average_always_precedes_latest_context(self):
        with tempfile.TemporaryDirectory() as temp:
            poll = weight._mk('one', RACE, 'firm', '2026-10-23', '2026-10-24', '2026-10-25', 1000, 'LV', 51, 45)
            bundle = weight._bundle(temp, [poll], [weight._mkm('firm')])
            block = bundle.race_block(RACE, bundle.estimates(), True)
            self.assertEqual(block['polling_read']['kind'], 'WEIGHTED_AVERAGE')
            self.assertEqual(block['polling_read']['margin'], block['weighted_margin'])
            self.assertIsNone(block['polling_read']['latest_poll'])


if __name__ == '__main__':
    unittest.main()
