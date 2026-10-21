"""Live adapter for ZED SDK. Hardware integration is not yet validated."""
import json
from pathlib import Path
import sys
import time

from .measurement import measure_endpoints


def run(args):
    import cv2
    import pyzed.sl as sl
    from .inference import load_pose_model, predict_detections
    if args.max_frames <= 0:
        raise ValueError("max-frames must be positive")
    model = load_pose_model(args.weights)
    camera = sl.Camera()
    image, cloud = sl.Mat(), sl.Mat()
    stream = None
    opened = False
    try:
        init = sl.InitParameters()
        init.camera_resolution = sl.RESOLUTION.HD720
        init.coordinate_units = sl.UNIT.METER
        init.coordinate_system = sl.COORDINATE_SYSTEM.IMAGE
        init.depth_mode = sl.DEPTH_MODE.QUALITY
        status = camera.open(init)
        if status != sl.ERROR_CODE.SUCCESS:
            raise ValueError(f"ZED open failed: {status}")
        opened = True
        runtime = sl.RuntimeParameters()
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            stream = output.open("w", encoding="utf-8")
        for frame_index in range(args.max_frames):
            status = camera.grab(runtime)
            if status != sl.ERROR_CODE.SUCCESS:
                raise ValueError(f"ZED grab failed: {status}")
            if camera.retrieve_image(image, sl.VIEW.LEFT) != sl.ERROR_CODE.SUCCESS:
                raise ValueError("ZED image retrieval failed")
            if camera.retrieve_measure(cloud, sl.MEASURE.XYZRGBA) != sl.ERROR_CODE.SUCCESS:
                raise ValueError("ZED point-cloud retrieval failed")
            frame = cv2.cvtColor(image.get_data(), cv2.COLOR_BGRA2BGR)
            detections = predict_detections(model, frame, confidence=args.conf, device=args.device)
            def sample(x, y):
                error, value = cloud.get_value(x, y)
                return value[:3] if error == sl.ERROR_CODE.SUCCESS else None
            measurements = measure_endpoints(
                [d["keypoints"] for d in detections], sample, frame.shape[1], frame.shape[0],
                unit="m", endpoint_indices=tuple(args.endpoints),
                min_confidence=args.keypoint_conf,
            )
            record = {"schema_version": 1, "frame_index": frame_index,
                      "recorded_at_unix_s": time.time(), "length_unit": "cm",
                      "measurement": "straight_line_endpoint_distance", "detections": [
                          {**d, "measurement": m.to_dict()} for d, m in zip(detections, measurements)]}
            print(json.dumps(record, allow_nan=False), file=stream or sys.stdout, flush=True)
            if args.show:
                for detection, measurement in zip(detections, measurements):
                    if measurement.status != "ok":
                        continue
                    p, q = measurement.pixels
                    cv2.line(frame, p, q, (0, 255, 0), 2)
                    cv2.putText(frame, f"{measurement.length_cm:.1f} cm", p,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.imshow("Fish endpoint length", frame)
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    break
    finally:
        if opened:
            camera.close()
        if stream:
            stream.close()
        if args.show:
            cv2.destroyAllWindows()
