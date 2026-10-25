import contextlib
import io
import json
import math
from pathlib import Path
import unittest

from fish_length.cli import main
from fish_length.evaluation import evaluate_lengths


class LengthEvaluationTests(unittest.TestCase):
    def samples(self):
        return {"samples": [
            {"sample_id": "a", "true_length_cm": 10, "predicted_length_cm": 11, "group": "near"},
            {"sample_id": "b", "true_length_cm": 20, "predicted_length_cm": 18, "group": "far"},
            {"sample_id": "c", "true_length_cm": 30, "predicted_length_cm": None, "group": "far"},
        ]}

    def test_known_errors_and_coverage(self):
        result = evaluate_lengths(self.samples())["overall"]
        self.assertEqual(result["sample_count"], 3)
        self.assertEqual(result["valid_count"], 2)
        self.assertEqual(result["invalid_count"], 1)
        self.assertAlmostEqual(result["valid_rate"], 2/3)
        self.assertEqual(result["mae_cm"], 1.5)
        self.assertAlmostEqual(result["rmse_cm"], math.sqrt(2.5))
        self.assertEqual(result["bias_cm"], -0.5)
        self.assertEqual(result["median_absolute_error_cm"], 1.5)
        self.assertAlmostEqual(result["mape_percent"], 10)

    def test_grouped_metrics_include_failed_predictions(self):
        groups = {r["group"]: r for r in evaluate_lengths(self.samples())["by_group"]}
        self.assertEqual(groups["near"]["mae_cm"], 1)
        self.assertEqual(groups["far"]["valid_rate"], 0.5)
        self.assertEqual(groups["far"]["mae_cm"], 2)

    def test_no_valid_predictions_have_null_errors(self):
        data = {"samples": [{"sample_id": "a", "true_length_cm": 10, "predicted_length_cm": None}]}
        result = evaluate_lengths(data)["overall"]
        self.assertEqual(result["valid_rate"], 0)
        self.assertIsNone(result["mae_cm"])
        self.assertIsNone(result["rmse_cm"])
        self.assertIsNone(evaluate_lengths({"samples": []})["overall"]["valid_rate"])

    def test_rejects_duplicate_ids_or_missing_prediction(self):
        data = self.samples()
        data["samples"][1]["sample_id"] = "a"
        with self.assertRaises(ValueError):
            evaluate_lengths(data)
        data = self.samples()
        del data["samples"][0]["predicted_length_cm"]
        with self.assertRaises(ValueError):
            evaluate_lengths(data)

    def test_rejects_invalid_numbers(self):
        for field in ("true_length_cm", "predicted_length_cm"):
            for value in (0, -1, float("nan"), float("inf"), True, "10"):
                with self.subTest(field=field, value=value):
                    data = self.samples()
                    data["samples"][0][field] = value
                    with self.assertRaises(ValueError):
                        evaluate_lengths(data)

    def test_rejects_malformed_documents(self):
        for data in ([], {}, {"samples": "bad"}, {"samples": [None]}):
            with self.assertRaises(ValueError):
                evaluate_lengths(data)

    def test_cli_synthetic_example(self):
        path = Path(__file__).resolve().parents[1] / "examples/length-evaluation.synthetic.json"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["evaluate-lengths", str(path)]), 0)
        self.assertEqual(json.loads(output.getvalue())["overall"]["valid_count"], 2)
