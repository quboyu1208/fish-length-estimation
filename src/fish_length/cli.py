"""Command-line tools. JSON output is strict: invalid values become status fields."""
import argparse
import json
from pathlib import Path
import sys

from .measurement import measure_endpoints


def read_json(path):
    def reject(value):
        raise ValueError(f"Non-standard JSON number: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject)


def write_json(value, output=None):
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def measure_document(document, args):
    width, height = document["width"], document["height"]
    grid = document["xyz"]
    if len(grid) != height or any(len(row) != width for row in grid):
        raise ValueError("XYZ grid must match height x width exactly")
    detections = document["detections"]
    measurements = measure_endpoints(
        [d["keypoints"] for d in detections], lambda x, y: grid[y][x],
        width, height, unit=document["unit"], endpoint_indices=tuple(args.endpoints),
        min_confidence=args.keypoint_conf,
    )
    return {"schema_version": 1, "measurement": "straight_line_endpoint_distance",
            "length_unit": "cm", "detections": [
                {**d, "detection_index": i, "measurement": m.to_dict()}
                for i, (d, m) in enumerate(zip(detections, measurements))]}


def predict_image(args):
    import cv2
    from .inference import load_pose_model, predict_detections
    source = Path(args.image)
    if not source.is_file():
        raise ValueError(f"Image not found: {source}")
    image = cv2.imread(str(source))
    if image is None:
        raise ValueError("Cannot decode image")
    detections = predict_detections(load_pose_model(args.weights), image,
                                    confidence=args.conf, device=args.device)
    document = {"schema_version": 1, "width": image.shape[1], "height": image.shape[0],
                "detections": detections}
    if args.xyz:
        xyz = read_json(args.xyz)
        if (xyz["width"], xyz["height"]) != (document["width"], document["height"]):
            raise ValueError("XYZ must be aligned to the original image resolution")
        document.update({"xyz": xyz["xyz"], "unit": xyz["unit"]})
        document = measure_document(document, args)
    else:
        document["measurement_status"] = "not_measured_no_xyz"
    write_json(document, args.output)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fish pose and 3D endpoint length estimation")
    sub = parser.add_subparsers(dest="command", required=True)
    measure = sub.add_parser("measure", help="Measure keypoints with an aligned XYZ JSON grid")
    measure.add_argument("input")
    predict = sub.add_parser("predict", help="Run local pose weights on one image")
    predict.add_argument("--weights", required=True)
    predict.add_argument("--image", required=True)
    predict.add_argument("--xyz", help="Optional aligned XYZ JSON document")
    zed = sub.add_parser("zed", help="Optional live ZED measurement")
    zed.add_argument("--weights", required=True)
    zed.add_argument("--max-frames", type=int, default=300)
    zed.add_argument("--show", action="store_true")
    for command in (predict, zed):
        command.add_argument("--conf", type=float, default=0.25)
        command.add_argument("--device", default="cpu")
    for command in (measure, predict, zed):
        command.add_argument("--endpoints", nargs=2, type=int, default=[0, 1])
        command.add_argument("--keypoint-conf", type=float, default=0.5)
        command.add_argument("--output", help="Output JSON (ZED: JSONL), default stdout")
    train = sub.add_parser("train", help="Train a local YOLO Pose model on a local dataset")
    train.add_argument("--model", required=True, help="Local pose YAML or trusted .pt checkpoint")
    train.add_argument("--epochs", type=int, default=100)
    train.add_argument("--patience", type=int, default=50)
    train.add_argument("--seed", type=int, default=0)
    train.add_argument("--amp", action="store_true", help="Enable AMP (may trigger upstream checks/downloads)")
    val = sub.add_parser("val", help="Evaluate a local pose checkpoint")
    val.add_argument("--weights", required=True)
    val.add_argument("--split", choices=["val", "test"], default="val")
    for command in (train, val):
        command.add_argument("--data", required=True, help="Local dataset YAML")
        command.add_argument("--imgsz", type=int, default=640)
        command.add_argument("--batch", type=int, default=8)
        command.add_argument("--workers", type=int, default=0)
        command.add_argument("--device", default="cpu")
        command.add_argument("--project", default="outputs/pose")
        command.add_argument("--name", default="train" if command is train else "val")
        command.add_argument("--dry-run", action="store_true", help="Print plan without loading ML dependencies")
        command.add_argument("--output", help="Optional JSON plan or metric-summary file")
    check = sub.add_parser("check-dataset", help="Read-only checks of YOLO Pose directory splits")
    check.add_argument("root", help="Dataset root containing images/ and labels/")
    check.add_argument("--classes", type=int, default=1)
    check.add_argument("--keypoints", type=int, default=2)
    check.add_argument("--dimensions", type=int, choices=[2, 3], default=3)
    check.add_argument("--splits", nargs="+", choices=["train", "val", "test"], default=["train", "val"])
    check.add_argument("--check-duplicates", action="store_true", help="Hash images for exact cross-split duplicates")
    check.add_argument("--output", help="Optional JSON report")
    evaluate = sub.add_parser("evaluate-lengths", help="Compare matched physical lengths in centimetres")
    evaluate.add_argument("input", help="JSON object with samples list")
    evaluate.add_argument("--output", help="Optional JSON metric report")
    args = parser.parse_args(argv)
    try:
        if args.command == "measure":
            write_json(measure_document(read_json(args.input), args), args.output)
        elif args.command == "check-dataset":
            from .dataset import check_dataset
            report = check_dataset(args.root, classes=args.classes, keypoints=args.keypoints,
                                   dimensions=args.dimensions, splits=args.splits,
                                   check_duplicates=args.check_duplicates)
            write_json(report, args.output)
            return 0 if report["ok"] else 1
        elif args.command == "evaluate-lengths":
            from .evaluation import evaluate_lengths
            write_json(evaluate_lengths(read_json(args.input)), args.output)
        elif args.command == "predict":
            predict_image(args)
        elif args.command in ("train", "val"):
            from .training import run
            run(args)
        else:
            from .zed import run
            run(args)
    except (ValueError, KeyError, TypeError, OSError, ImportError) as exc:
        print(f"fish-length: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
