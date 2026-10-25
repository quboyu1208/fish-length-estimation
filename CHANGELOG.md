# Changelog

## 0.3.0 — 2026-10-25

- Add read-only YOLO Pose directory-dataset checks, annotation diagnostics and optional exact cross-split image hashing.
- Add physical-length MAE, RMSE, bias, median absolute error, MAPE and coverage metrics with optional grouping.
- Preserve failed measurements in coverage statistics; reject duplicate sample IDs and malformed length values.
- Add synthetic evaluation example, command documentation and regression tests.
- No experimental data, model weights or real accuracy claims added.

## 0.2.0 — 2026-10-21

- Add local YOLO Pose train/val commands, a two-endpoint baseline model YAML, dataset template and training guide.
- Add command-plan dry-run and mocked model dispatch tests; no actual training performed.

## 0.1.0 — 2026-10-21

- Extract endpoint geometry from the research workspace.
- Add optional local pose inference and ZED adapter, synthetic geometry example and core tests.
- Keep research media and checkpoints outside the public source package.
