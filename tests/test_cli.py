import contextlib
import io
import json
from pathlib import Path
import unittest
from fish_length.cli import main, measure_document
from argparse import Namespace


class CliTests(unittest.TestCase):
    def test_synthetic_cli(self):
        output = io.StringIO()
        fixture = Path(__file__).resolve().parents[1] / "examples/synthetic.json"
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["measure", str(fixture)]), 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["detections"][0]["measurement"]["status"], "invalid_depth")
        self.assertEqual(data["detections"][1]["label"], "synthetic_30_cm")
        self.assertAlmostEqual(data["detections"][1]["measurement"]["length_cm"], 30)

    def test_misaligned_grid_rejected(self):
        with self.assertRaises(ValueError):
            measure_document({"width": 3, "height": 1, "xyz": [[]], "detections": [], "unit": "m"},
                             Namespace(endpoints=[0, 1], keypoint_conf=0.5))
