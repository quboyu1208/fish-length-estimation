"""Measure straight-line 3D endpoint distances in aligned XYZ data.

Sampling is nearest-lower pixel (floor), without depth interpolation or smoothing.
Every input detection produces one result, including invalid detections.
"""
from dataclasses import asdict, dataclass
import math
from typing import Callable, Optional, Sequence


@dataclass(frozen=True)
class Measurement:
    detection_index: int
    status: str
    length_cm: Optional[float] = None
    pixels: Optional[tuple] = None
    points_m: Optional[tuple] = None

    def to_dict(self):
        return asdict(self)


def measure_endpoints(
    detections: Sequence,
    sample_xyz: Callable,
    width: int,
    height: int,
    *,
    unit: str,
    endpoint_indices=(0, 1),
    min_confidence=0.5,
):
    """Accept NxKx2 or NxKx3 keypoints in original-image pixels.

    Third component, when present, is confidence. XYZ must be in one camera
    coordinate system, aligned to the same image, with positive forward Z.
    sample_xyz(x, y) returns three coordinates, or None on invalid SDK status.
    Units must be supplied explicitly. Output lengths are centimetres.
    """
    factors = {"m": 1.0, "cm": 0.01, "mm": 0.001}
    if unit not in factors:
        raise ValueError("unit must be m, cm, or mm")
    if width <= 0 or height <= 0:
        raise ValueError("image dimensions must be positive")
    if len(endpoint_indices) != 2 or len(set(endpoint_indices)) != 2:
        raise ValueError("choose two different endpoint indices")
    if any(not isinstance(i, int) or i < 0 for i in endpoint_indices):
        raise ValueError("endpoint indices must be nonnegative integers")
    if not math.isfinite(min_confidence) or not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be between 0 and 1")
    results = []
    for index, keypoints in enumerate(detections):
        def invalid(status):
            return Measurement(index, status)
        try:
            endpoints = [keypoints[i] for i in endpoint_indices]
            if any(len(p) not in (2, 3) for p in endpoints):
                raise ValueError("invalid keypoint size")
            endpoints = [tuple(float(v) for v in p) for p in endpoints]
        except (TypeError, ValueError, IndexError, KeyError):
            results.append(invalid("invalid_keypoints"))
            continue
        if any(not math.isfinite(v) for p in endpoints for v in p):
            results.append(invalid("invalid_keypoints"))
            continue
        if any(len(p) == 3 and not 0 <= p[2] <= 1 for p in endpoints):
            results.append(invalid("invalid_keypoints"))
            continue
        if any(len(p) == 3 and p[2] < min_confidence for p in endpoints):
            results.append(invalid("low_confidence"))
            continue
        if any(not (0 <= p[0] < width and 0 <= p[1] < height) for p in endpoints):
            results.append(invalid("out_of_bounds"))
            continue
        pixels = tuple((math.floor(p[0]), math.floor(p[1])) for p in endpoints)
        if pixels[0] == pixels[1]:
            results.append(invalid("coincident_pixels"))
            continue
        points = []
        for x, y in pixels:
            value = sample_xyz(x, y)
            try:
                if value is None or len(value) != 3:
                    raise ValueError("missing XYZ")
                point = tuple(float(v) * factors[unit] for v in value)
                if any(not math.isfinite(v) for v in point) or point[2] <= 0:
                    raise ValueError("invalid XYZ")
            except (TypeError, ValueError):
                points = []
                break
            points.append(point)
        if len(points) != 2:
            results.append(invalid("invalid_depth"))
            continue
        length_cm = math.dist(*points) * 100.0
        if not math.isfinite(length_cm) or length_cm <= 0:
            results.append(invalid("invalid_distance"))
            continue
        results.append(Measurement(index, "ok", length_cm, pixels, tuple(points)))
    return results
