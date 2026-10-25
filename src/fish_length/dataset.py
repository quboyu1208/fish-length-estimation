"""Read-only checks for a directory-layout YOLO Pose dataset; no image decoding."""
import hashlib
import math
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def label_errors(text, classes, keypoints, dimensions):
    errors, objects = [], 0
    expected = 5 + keypoints * dimensions
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        tokens = line.split()
        if len(tokens) != expected:
            errors.append((line_number, f"expected {expected} values, got {len(tokens)}"))
            continue
        try:
            values = [float(token) for token in tokens]
        except ValueError:
            errors.append((line_number, "all annotation fields must be numeric"))
            continue
        if not all(math.isfinite(v) for v in values):
            errors.append((line_number, "non-finite annotation value"))
            continue
        class_id, x, y, w, h = values[:5]
        if not class_id.is_integer() or not 0 <= class_id < classes:
            errors.append((line_number, "class id is outside the configured integer class range"))
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
            errors.append((line_number, "box center must be in [0,1]; width and height in (0,1]"))
        for i in range(keypoints):
            point = values[5 + i * dimensions:5 + (i + 1) * dimensions]
            if not all(0 <= v <= 1 for v in point[:2]):
                errors.append((line_number, f"keypoint {i}: x/y must be in [0,1]"))
            if dimensions == 3 and point[2] not in (0, 1, 2):
                errors.append((line_number, f"keypoint {i}: visibility must be 0, 1 or 2"))
        objects += 1
    return errors, objects


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_dataset(root, *, classes=1, keypoints=2, dimensions=3,
                  splits=("train", "val"), check_duplicates=False):
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Dataset directory not found: {root}")
    if classes <= 0 or keypoints <= 0 or dimensions not in (2, 3):
        raise ValueError("classes/keypoints must be positive; dimensions must be 2 or 3")
    if not splits or len(set(splits)) != len(splits) or any(s not in ("train", "val", "test") for s in splits):
        raise ValueError("splits must be unique train/val/test names")
    issues, stats, hashes = [], {}, {}
    def issue(path, message, line=None):
        issues.append({"path": str(path.relative_to(root)), "line": line, "message": message})
    for split in splits:
        images_dir, labels_dir = root / "images" / split, root / "labels" / split
        images = sorted(p for p in images_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
        label_files = sorted(labels_dir.rglob("*.txt")) if labels_dir.is_dir() else []
        stats[split] = {"image_count": len(images), "label_count": len(label_files),
                        "parsed_object_rows": 0, "background_images": 0}
        if not images:
            issue(images_dir, "missing image directory or no supported image files")
        if not labels_dir.is_dir():
            issue(labels_dir, "missing label directory")
        expected_labels, owners = set(), {}
        for image in images:
            relative = image.relative_to(images_dir)
            label = labels_dir / relative.with_suffix(".txt")
            expected_labels.add(label)
            if label in owners:
                issue(image, f"multiple image extensions share one label: {owners[label].name}")
            owners[label] = image
            if not label.is_file():
                issue(label, "missing label; use an explicit empty file for a background image")
            else:
                try:
                    text = label.read_text(encoding="utf-8-sig")
                    errors, count = label_errors(text, classes, keypoints, dimensions)
                    stats[split]["parsed_object_rows"] += count
                    if not text.strip():
                        stats[split]["background_images"] += 1
                    for line, message in errors:
                        issue(label, message, line)
                except (OSError, UnicodeError) as exc:
                    issue(label, f"cannot read label: {type(exc).__name__}")
            if check_duplicates:
                digest = file_digest(image)
                previous = hashes.setdefault(digest, [])
                for other_split, other_image in previous:
                    if other_split != split:
                        issue(image, f"identical image bytes across splits: {other_image.relative_to(root)}")
                previous.append((split, image))
        for label in label_files:
            if label not in expected_labels:
                issue(label, "orphan label without matching supported image")
    return {"schema_version": 1, "ok": not issues, "classes": classes,
            "kpt_shape": [keypoints, dimensions], "splits": stats,
            "cross_split_byte_duplicates_checked": check_duplicates, "issues": issues,
            "limitations": ["Does not decode images or check anatomical landmark meaning.",
                            "Byte hashes do not detect related frames, fish identities or re-encoded duplicates.",
                            "This checker supports directory splits, not YAML manifests or image-list TXT files."]}
