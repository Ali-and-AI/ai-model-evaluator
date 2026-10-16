"""Tests for the judge guard. No API key needed."""
import unittest

from judge import parse_verdict
from run_eval import cost_usd


class TestParseVerdict(unittest.TestCase):

    def test_valid_verdict(self):
        v = parse_verdict('{"accuracy": 5, "completeness": 4, "tone": 5, "hallucination": false, "reason": "ok"}')
        self.assertEqual(v["average"], 4.67)
        self.assertFalse(v["hallucination"])

    def test_json_inside_text(self):
        v = parse_verdict('Here you go: {"accuracy": 3, "completeness": 3, "tone": 3, "hallucination": true, "reason": "x"}')
        self.assertTrue(v["hallucination"])

    def test_garbage_is_rejected(self):
        self.assertIsNone(parse_verdict("I can't grade this"))

    def test_missing_field_is_rejected(self):
        self.assertIsNone(parse_verdict('{"accuracy": 5, "tone": 5, "hallucination": false}'))

    def test_score_out_of_range_is_rejected(self):
        self.assertIsNone(parse_verdict('{"accuracy": 9, "completeness": 4, "tone": 5, "hallucination": false}'))

    def test_hallucination_must_be_boolean(self):
        self.assertIsNone(parse_verdict('{"accuracy": 5, "completeness": 5, "tone": 5, "hallucination": "no"}'))


class TestCost(unittest.TestCase):

    def test_cost_per_million(self):
        self.assertAlmostEqual(cost_usd("claude-haiku-5-5", 1_000_000, 0), 0.10)

    def test_unknown_price_returns_none(self):
        self.assertIsNone(cost_usd("gemini-3.8-flash", 100, 100))


if __name__ == "__main__":
    unittest.main()
