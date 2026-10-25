"""Physical-length error metrics for explicitly matched, user-supplied pairs."""
import math
from statistics import median


def positive_number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a JSON number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{field} is too large") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be finite and positive")
    return number


def summarize(rows):
    valid = [row for row in rows if row["predicted_length_cm"] is not None]
    errors = [row["predicted_length_cm"] - row["true_length_cm"] for row in valid]
    count = len(valid)
    result = {"sample_count": len(rows), "valid_count": count,
              "invalid_count": len(rows) - count,
              "valid_rate": count / len(rows) if rows else None,
              "mae_cm": None, "rmse_cm": None, "bias_cm": None,
              "median_absolute_error_cm": None, "mape_percent": None}
    if count:
        result.update(
            mae_cm=math.fsum(abs(e) / count for e in errors),
            rmse_cm=math.hypot(*errors) / math.sqrt(count),
            bias_cm=math.fsum(e / count for e in errors),
            median_absolute_error_cm=median(abs(e) for e in errors),
            mape_percent=math.fsum((abs(e) / row["true_length_cm"]) / count * 100
                                   for e, row in zip(errors, valid)),
        )
        if any(not math.isfinite(value) for value in result.values() if value is not None):
            raise ValueError("Metric overflow; check the length units and numeric range")
    return result


def evaluate_lengths(document):
    """No automatic fish matching, unit guessing, or missing-prediction imputation."""
    if not isinstance(document, dict) or not isinstance(document.get("samples"), list):
        raise ValueError("Expected an object with a samples list")
    rows, seen, groups = [], set(), {}
    for index, sample in enumerate(document["samples"]):
        if not isinstance(sample, dict):
            raise ValueError(f"sample {index} must be an object")
        sample_id = sample.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id.strip() or sample_id in seen:
            raise ValueError(f"sample {index} requires a unique nonempty sample_id")
        if "predicted_length_cm" not in sample:
            raise ValueError(f"{sample_id}: include predicted_length_cm, using null for failed measurements")
        truth = positive_number(sample.get("true_length_cm"), f"{sample_id}.true_length_cm")
        prediction = sample["predicted_length_cm"]
        if prediction is not None:
            prediction = positive_number(prediction, f"{sample_id}.predicted_length_cm")
        group = sample.get("group")
        if group is not None and (not isinstance(group, str) or not group.strip()):
            raise ValueError(f"{sample_id}: group must be a nonempty string or null")
        row = {"sample_id": sample_id, "true_length_cm": truth,
               "predicted_length_cm": prediction, "group": group}
        rows.append(row)
        seen.add(sample_id)
        groups.setdefault(group, []).append(row)
    return {"schema_version": 1, "length_unit": "cm",
            "error_definition": "predicted_length_cm - true_length_cm",
            "overall": summarize(rows),
            "by_group": [{"group": key, **summarize(value)} for key, value in groups.items()],
            "note": "Errors use valid predictions only; report valid_rate and counts alongside errors."}
