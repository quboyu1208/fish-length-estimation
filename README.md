# Fish Length Estimation

A small research toolkit for estimating the **straight-line 3D distance between two fish landmarks**, using pose keypoints and image-aligned XYZ measurements.

[中文说明](README.zh-CN.md) · [Data format](docs/data-format.md) · [Model notes](docs/model-card.md) · [Provenance](THIRD_PARTY_NOTICES.md)

**Status: early research MVP.** The dependency-free geometry path has automated tests. Fish checkpoint inference and live ZED integration require separate validation. No real-world accuracy, real-time performance, or improved YOLO architecture is claimed.

## Quick start (no model, camera, or third-party runtime required)

Use Python 3.10+ in a new virtual environment, from this project directory:

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e .
fish-length measure examples/synthetic.json
python -m unittest discover -s tests -v
```

The synthetic example returns two records: an invalid-depth record, then a 30 cm measurement. This is a geometry example, not a fish benchmark. Detection indices are preserved even when earlier measurements fail.

## Pose inference on one image

Install optional dependencies in the same environment. Install a suitable PyTorch build for your hardware if needed.

```sh
python -m pip install -e ".[vision]"
fish-length predict --weights /path/to/fish-pose.pt --image /path/to/fish.jpg --device cpu --output outputs/keypoints.json
```

Supply a **trusted local fish pose checkpoint** and verify its landmark order. Generic human pose models or detection-only fish weights do not establish the required endpoint semantics. Without XYZ data this command outputs 2D detections only; it cannot report physical length.

To measure with an aligned XYZ grid (see the data-format document):

```sh
fish-length predict --weights /path/to/fish-pose.pt --image /path/to/fish.jpg --xyz /path/to/aligned-xyz.json --endpoints 0 1 --output outputs/lengths.json
```

The vision extra pins Ultralytics 8.2.31 to the version declared by the source workspace. This is a compatibility starting point, not a recovered training environment or a validated inference matrix. No checkpoints or experimental images are distributed in the public package.

## Train and evaluate fish keypoints

Install the `vision` extra, prepare your own authorized YOLO Pose annotations and
edit the absolute dataset path in a copy of `configs/fish-pose.example.yaml`.
The supplied `configs/yolov8n-fish-pose.yaml` is a two-endpoint **baseline adapted
from Ultralytics**, not the missing historical CGA architecture.

```sh
# Dependency-free command plan only: no dataset scan, model loading or training.
fish-length train --model configs/yolov8n-fish-pose.yaml --data configs/fish-pose.example.yaml --dry-run
# Actual training: create and edit .local/fish-pose.yaml first.
fish-length train --model configs/yolov8n-fish-pose.yaml --data .local/fish-pose.yaml --device 0 --epochs 100 --name fish-baseline --output outputs/train-summary.json
# Explicit local .pt input can be used instead of model YAML for fine-tuning.
fish-length val --weights outputs/pose/fish-baseline/weights/best.pt --data .local/fish-pose.yaml --split val --device 0 --output outputs/val-summary.json
```

See the [training guide](docs/training.md) for label format, endpoint conventions,
finetuning, test splits and metric interpretation. Defaults use seed=0,
deterministic=True, workers=0 and AMP disabled. This is not a recovered environment
or experiment. Wrapper tests use mocked models; actual training has not been run.
Pose mAP is not centimetre-length accuracy.

## Check data and evaluate physical lengths

Both tools run with the dependency-free core:

```sh
# Read-only label/structure checks; set counts to match your own data config.
fish-length check-dataset /path/to/fish-pose --classes 1 --keypoints 2 --dimensions 3 --check-duplicates --output outputs/data-check.json
# Synthetic arithmetic example, not a measured fish benchmark.
fish-length evaluate-lengths examples/length-evaluation.synthetic.json
# Explicitly matched real observations supplied by you, in centimetres.
fish-length evaluate-lengths /path/to/matched-lengths.json --output outputs/length-metrics.json
```

The [dataset checker](docs/dataset-checks.md) reports file and line errors and
optional byte-identical images across splits; it cannot identify related video
frames or decode images. The [length evaluator](docs/length-evaluation.md) reports
MAE, RMSE, signed bias, median absolute error, MAPE and valid-measurement rate,
overall and per group. Failed predictions must remain as null rows so coverage is
visible. These tools validate supplied inputs; they do not establish real accuracy.

## Optional ZED camera

Install the matching ZED SDK and its Python API from Stereolabs separately. The project does not redistribute SDK wheels. Use a compatible GPU/driver/SDK environment.

```sh
fish-length zed --weights /path/to/fish-pose.pt --device 0 --max-frames 300 --show --output outputs/measurements.jsonl
```

Uses the rectified left image and the SDK's aligned XYZ point cloud in metres. Press Esc or q to stop the preview. Frame limits also work without a preview. Output is one JSON object per captured frame, with detection-local indices (not persistent tracking IDs). Camera cleanup runs on exit and errors.

## Measurement contract and limitations

- Input landmarks use original-image pixel coordinates; configurable endpoint indices default to 0 and 1.
- Input XYZ units must be explicit (`m`, `cm`, `mm`); outputs are centimetres.
- Confidence is checked when the third landmark component is available. Two-component landmarks contain no confidence information.
- Pixel coordinates are floored; each endpoint uses a single XYZ sample. Missing depth, non-finite values, nonpositive forward depth and invalid coordinates produce status fields and null lengths.
- This measures an endpoint chord, not a curved body centreline. Define whether your landmarks represent total, fork or standard length before scientific use.
- Underwater refraction, occlusion, stereo uncertainty and endpoint depth contamination remain unresolved sources of error. The SDK's depth is not a substitute for validation against physical ground truth.
- A training/validation CLI and an adapted two-endpoint YOLOv8 Pose model config are included. No training dataset, recovered CGA architecture, pretrained fish model, fish accuracy benchmark, speed estimation or individual identification is included.

## Development and release

Core tests require only Python. CI covers core functionality; it does not validate camera hardware or model accuracy.

```sh
python tools/build_public_bundle.py
```

This creates `dist/fish-length-estimation-0.3.0-source.zip` using an explicit public-file allowlist. Local weights, datasets, caches, outputs and virtual environments are excluded. See [release notes](docs/release.md) before publishing.

## License and provenance

AGPL-3.0; see [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Extracted and refactored from a fish measurement research workspace based on Ultralytics YOLO. This project is not an official Ultralytics or OpenAI project. No upstream popularity or benchmark claims are attributed to this project.

Local validation details: [verification record](docs/verification.md).
