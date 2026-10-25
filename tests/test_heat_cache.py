"""Exercise the scorer entrypoint without network or paid model calls."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/heat"))
import score_units


class HeatCacheTests(unittest.TestCase):
    def test_same_unit_reuses_cache_and_changed_prompt_scores_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            units = base / "units.json"
            units.write_text(json.dumps([{"race": "2026-TX-SEN", "candidate": "Example", "slot": "D", "source_type": "AD", "unit_id": "one", "source_url": "https://example.org/ad", "sentences": ["A complete test sentence."]}]))
            config = base / "config.json"
            config.write_text('{}')
            state = base / "run-state.json"
            state.write_text(json.dumps({"budget_ledger": {"heat_spent_usd": 0, "heat_reserved_usd": 0, "heat_ceiling_usd": 3}}))
            result = {"lines": [{"status": "scored", "score": 3, "text": "A complete test sentence.", "heard": "A complete test sentence."}], "report": {"verdict": {"score": 3, "band": "test"}}, "cost_usd": 0.01}
            argv = ["score_units.py", "--units", str(units), "--bundle-dir", str(base), "--run-state", str(state), "--scorer-commit", "pinned", "--model", "test", "--config", str(config)]
            with patch.object(score_units, "Meter"), patch.object(score_units, "read_passcode", return_value="test"), patch.object(score_units, "score_unit", return_value=result.copy()) as call, contextlib.redirect_stdout(io.StringIO()):
                for prompt in ("one", "one", "two"):
                    with patch.object(sys, "argv", argv + ["--prompt-sha256", prompt]):
                        self.assertEqual(score_units.main(), 0)
            self.assertEqual(call.call_count, 2)
            self.assertEqual(len(list((base / "heat-cache").glob('*.json'))), 2)
            self.assertEqual(json.loads(state.read_text())["budget_ledger"]["heat_spent_usd"], 0.02)

    def test_dry_run_does_not_write_heat_or_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "units.json").write_text(json.dumps([{"race": "2026-TX-SEN", "candidate": "Example", "slot": "D", "source_type": "AD", "unit_id": "one", "sentences": ["A complete test sentence."]}]))
            (base / "config.json").write_text('{}')
            state = base / "run-state.json"
            state.write_text('{"budget_ledger": {"heat_spent_usd": 0, "heat_reserved_usd": 0}}')
            previous = state.read_bytes()
            argv = ["score_units.py", "--units", str(base / "units.json"), "--bundle-dir", str(base), "--run-state", str(state), "--scorer-commit", "pinned", "--model", "test", "--config", str(base / "config.json"), "--prompt-sha256", "one", "--dry-run"]
            with patch.object(sys, "argv", argv), patch.object(score_units, "Meter") as meter, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(score_units.main(), 0)
            meter.assert_not_called()
            self.assertEqual(state.read_bytes(), previous)
            self.assertFalse((base / "heat.csv").exists())

    def test_empty_reservation(self):
        self.assertEqual(score_units.reserve_upper_bound(None), 0)
        self.assertEqual(score_units.reserve_upper_bound([]), 0)


if __name__ == "__main__":
    unittest.main()
