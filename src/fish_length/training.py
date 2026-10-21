"""Local YOLO Pose training/validation entry points, imported only on request."""
import math
from pathlib import Path


def local_file(value, suffixes, description):
    path = Path(value).expanduser().resolve()
    if path.suffix.lower() not in suffixes or not path.is_file():
        raise ValueError(f"{description} must be an existing local {'/'.join(suffixes)} file: {path}")
    return str(path)


def build_plan(args):
    data = local_file(args.data, (".yaml", ".yml"), "Dataset configuration")
    if args.imgsz <= 0 or args.batch <= 0 or args.workers < 0:
        raise ValueError("imgsz and batch must be positive; workers must be nonnegative")
    if not args.name or Path(args.name).name != args.name or args.name in (".", ".."):
        raise ValueError("name must be a single directory name")
    options = {"data": data, "imgsz": args.imgsz, "batch": args.batch,
               "device": args.device, "workers": args.workers,
               "project": str(Path(args.project).expanduser().resolve()),
               "name": args.name, "exist_ok": False, "plots": True}
    if args.command == "train":
        if args.epochs <= 0 or args.patience < 0 or args.seed < 0:
            raise ValueError("epochs must be positive; patience and seed must be nonnegative")
        model = local_file(args.model, (".yaml", ".yml", ".pt"), "Pose model")
        options.update(epochs=args.epochs, patience=args.patience, seed=args.seed,
                       deterministic=True, amp=args.amp, pretrained=False,
                       save=True, val=True)
    else:
        model = local_file(args.weights, (".pt",), "Pose checkpoint")
        options["split"] = args.split
    return {"command": args.command, "model": model, "options": options,
            "dry_run": args.dry_run}


def run(args):
    from .cli import write_json
    plan = build_plan(args)
    if args.dry_run:
        # No ML imports, checkpoint loading, dataset scanning or training here.
        write_json(plan, args.output)
        return
    from .inference import load_pose_model
    model = load_pose_model(plan["model"])
    method = model.train if args.command == "train" else model.val
    metrics = method(**plan["options"])
    values = getattr(metrics, "results_dict", {}) if metrics is not None else {}
    summary = {}
    for key, value in values.items():
        number = float(value)
        summary[key] = number if math.isfinite(number) else None
    # The framework may increment the directory name to avoid overwriting a run.
    runner = getattr(model, "trainer", None) if args.command == "train" else metrics
    save_dir = getattr(runner, "save_dir", None)
    write_json({"command": args.command, "model": plan["model"],
                "data": plan["options"]["data"], "arguments": plan["options"],
                "save_dir": str(save_dir) if save_dir is not None else None,
                "metrics": summary,
                "note": "YOLO box/pose metrics, not physical fish-length accuracy."}, args.output)
