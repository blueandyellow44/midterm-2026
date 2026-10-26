"""Ad unit building: bare name lines merge forward so the meter never scores an empty self-identification."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'heat'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
from build_ad_units import merge_name_lines


class NameLines(unittest.TestCase):
    def test_bare_name_merges_into_the_next_sentence(self):
        self.assertEqual(merge_name_lines(['We raised our daughters here.', "I'm Tom Tiffany.", 'I believe in Wisconsin.']),
                         ['We raised our daughters here.', "I'm Tom Tiffany. I believe in Wisconsin."])

    def test_trailing_name_merges_backward_and_content_lines_stay(self):
        self.assertEqual(merge_name_lines(['Lower costs now.', "I'm Jocelyn Benson."]), ["Lower costs now. I'm Jocelyn Benson."])
        self.assertEqual(merge_name_lines(["I'm David Crowley, and I'm running for governor."]), ["I'm David Crowley, and I'm running for governor."])
        self.assertEqual(merge_name_lines(["I'm Dr. Abdul El-Sayed.", 'I approve this message.']), ["I'm Dr. Abdul El-Sayed. I approve this message."])

    def test_empty_and_only_name(self):
        self.assertEqual(merge_name_lines([]), [])
        self.assertEqual(merge_name_lines(["I'm Ashley Hinson."]), ["I'm Ashley Hinson."])


if __name__ == '__main__':
    unittest.main()
