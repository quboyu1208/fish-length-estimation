"""Optional YOLO pose adapter; importing the core never imports Torch or ZED."""
from pathlib import Path


def load_pose_model(weights):
    path = Path(weights).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"Local pose weights not found: {path}")
    from ultralytics import YOLO
    model = YOLO(str(path), task="pose")
    if model.task != "pose":
        raise ValueError("A pose checkpoint is required, not detection-only weights")
    return model


def predict_detections(model, image, *, confidence=0.25, device=None):
    import numpy as np
    results = model.predict(source=image, conf=confidence, device=device,
                            save=False, verbose=False)
    result = results[0]
    if result.keypoints is None:
        raise ValueError("The model returned no pose output")
    keypoints = result.keypoints.data.cpu().numpy()
    boxes = result.boxes.xyxy.cpu().numpy()
    scores = result.boxes.conf.cpu().numpy()
    classes = result.boxes.cls.cpu().numpy()
    if len(keypoints) != len(boxes):
        raise ValueError("Keypoints and boxes have inconsistent detection counts")
    detections = []
    for i, (points, box, score, cls) in enumerate(zip(keypoints, boxes, scores, classes)):
        if not np.isfinite(points).all():
            raise ValueError("Non-finite model keypoints")
        detections.append({"detection_index": i, "bbox_xyxy": box.tolist(),
                           "confidence": float(score), "class_id": int(cls),
                           "keypoints": points.tolist()})
    return detections
