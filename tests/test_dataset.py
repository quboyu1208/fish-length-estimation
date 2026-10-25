import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from fish_length.cli import main
from fish_length.dataset import check_dataset, label_errors

LABEL = "0 0.5 0.5 0.6 0.2 0.2 0.5 2 0.8 0.5 2\n"


class DatasetTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for split in ("train", "val"):
            (self.root / "images" / split).mkdir(parents=True)
            (self.root / "labels" / split).mkdir(parents=True)
            # Synthetic bytes, not valid encoded images: checker never decodes images.
            (self.root / "images" / split / "fish.jpg").write_bytes(split.encode())
            (self.root / "labels" / split / "fish.txt").write_text(LABEL, encoding="utf-8")

    def test_valid_directory_and_no_modifications(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        report = check_dataset(self.root)
        self.assertTrue(report["ok"])
        self.assertEqual(report["splits"]["train"]["parsed_object_rows"], 1)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_empty_label_is_background(self):
        (self.root / "labels/train/fish.txt").write_text("", encoding="utf-8")
        report = check_dataset(self.root)
        self.assertTrue(report["ok"])
        self.assertEqual(report["splits"]["train"]["background_images"], 1)

    def test_missing_and_orphan_labels_are_errors(self):
        (self.root / "labels/train/fish.txt").rename(self.root / "labels/train/orphan.txt")
        issues = check_dataset(self.root)["issues"]
        self.assertTrue(any("missing label;" in r["message"] for r in issues))
        self.assertTrue(any("orphan label" in r["message"] for r in issues))

    def test_cross_split_duplicate_bytes(self):
        (self.root / "images/val/fish.jpg").write_bytes(b"train")
        self.assertTrue(check_dataset(self.root)["ok"])
        report = check_dataset(self.root, check_duplicates=True)
        self.assertFalse(report["ok"])
        self.assertTrue(any("identical image bytes" in r["message"] for r in report["issues"]))

    def test_image_extension_collision(self):
        (self.root / "images/train/fish.png").write_bytes(b"other")
        self.assertTrue(any("multiple image extensions" in r["message"]
                            for r in check_dataset(self.root)["issues"]))

    def test_missing_split_and_invalid_options(self):
        report = check_dataset(self.root, splits=("test",))
        self.assertFalse(report["ok"])
        for kwargs in ({"classes": 0}, {"keypoints": 0}, {"dimensions": 4},
                       {"splits": ("train", "train")}, {"splits": ("../escape",)}):
            with self.assertRaises(ValueError):
                check_dataset(self.root, **kwargs)

    def test_annotation_validation(self):
        invalid = ["0 1", LABEL.replace("0.5", "NaN", 1),
                   LABEL.replace("0 0.5", "2 0.5", 1),
                   LABEL.replace("0.6", "0", 1), LABEL.replace("0.2", "1.2", 1),
                   LABEL.rstrip().rsplit(" ", 1)[0] + " 3", "word " * 11]
        for line in invalid:
            with self.subTest(line=line):
                errors, _ = label_errors(line, 1, 2, 3)
                self.assertTrue(errors)
        self.assertEqual(label_errors("0 0.5 0.5 0.2 0.2 0.1 0.1 0.9 0.9", 1, 2, 2)[0], [])

    def test_errors_include_line_numbers_and_cli_exit_status(self):
        (self.root / "labels/train/fish.txt").write_text(LABEL + "bad\n", encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["check-dataset", str(self.root)])
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(output.getvalue())["issues"][0]["line"], 2)
