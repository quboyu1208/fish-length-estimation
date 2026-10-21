"""Command routing and safety checks; no real training, datasets or ML imports."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fish_length.cli import main


class TrainingCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "fish.yaml"
        self.model = self.root / "pose.yaml"
        self.weights = self.root / "pose.pt"
        self.data.write_text("# fixture only", encoding="utf-8")
        self.model.write_text("# fixture only", encoding="utf-8")
        self.weights.write_bytes(b"not a real checkpoint")

    def invoke(self, command, *extra):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main([command, "--data", str(self.data), *extra])
        return status, output.getvalue()

    def test_dry_run_never_loads_model(self):
        with patch("fish_length.inference.load_pose_model") as loader:
            status, text = self.invoke("train", "--model", str(self.model), "--dry-run")
        self.assertEqual(status, 0)
        loader.assert_not_called()
        plan = json.loads(text)
        self.assertFalse(plan["options"]["amp"])
        self.assertEqual(plan["options"]["seed"], 0)
        self.assertEqual(plan["options"]["data"], str(self.data.resolve()))

    def test_missing_model_rejected_before_loading(self):
        with patch("fish_length.inference.load_pose_model") as loader:
            with contextlib.redirect_stderr(io.StringIO()):
                status, _ = self.invoke("train", "--model", str(self.root / "missing.pt"))
        self.assertEqual(status, 2)
        loader.assert_not_called()

    def test_train_and_metric_export(self):
        model = Mock()
        model.train.return_value = SimpleNamespace(results_dict={"metrics/mAP50(P)": 0.25})
        model.trainer.save_dir = self.root / "run"
        target = self.root / "report.json"
        with patch("fish_length.inference.load_pose_model", return_value=model):
            status, _ = self.invoke("train", "--model", str(self.model), "--epochs", "7",
                                    "--output", str(target))
        self.assertEqual(status, 0)
        self.assertEqual(model.train.call_args.kwargs["epochs"], 7)
        model.val.assert_not_called()
        report = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(report["save_dir"], str(self.root / "run"))
        self.assertEqual(report["metrics"]["metrics/mAP50(P)"], 0.25)

    def test_validation_uses_requested_split_and_preserves_nan_as_null(self):
        model = Mock()
        model.val.return_value = SimpleNamespace(results_dict={"test_metric": float("nan")},
                                                  save_dir=self.root / "val")
        with patch("fish_length.inference.load_pose_model", return_value=model):
            status, text = self.invoke("val", "--weights", str(self.weights), "--split", "test")
        self.assertEqual(status, 0)
        self.assertEqual(model.val.call_args.kwargs["split"], "test")
        model.train.assert_not_called()
        self.assertIsNone(json.loads(text)["metrics"]["test_metric"])

    def test_invalid_hyperparameters(self):
        for option, value in (("--epochs", "0"), ("--batch", "0"),
                              ("--workers", "-1"), ("--name", "../escape")):
            with self.subTest(option=option):
                with contextlib.redirect_stderr(io.StringIO()):
                    status, _ = self.invoke("train", "--model", str(self.model), option, value)
                self.assertEqual(status, 2)
