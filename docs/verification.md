# Verification record

Date: 2026-10-21. Local platform: Windows, Python 3.10.5.

Completed:

- 9 standard-library unittest tests passed against source.
- Synthetic CLI returned invalid_depth for detection 0 and 30.0 cm for detection 1.
- Standard isolated wheel build succeeded with project name fish-length-estimation
  and version 0.1.0. A preliminary no-build-isolation attempt with the host's old
  setuptools generated UNKNOWN metadata; that artifact is excluded from release.
- Correct wheel installed into a separate virtual environment with no runtime
  dependencies; installed fish-length command ran the synthetic example.
- All 9 tests passed against the installed wheel in that environment.
- Source upload archive was inspected for membership and ZIP integrity; it includes
  no checkpoints, experimental images/videos, SDK wheels, caches or local settings.

Not performed:

- Loading the historical fish checkpoint or running actual image inference.
- Installing/testing the optional vision dependencies as a complete environment.
- Connecting a ZED camera, validating SDK compatibility or measuring real fish.
- Training, evaluating research metrics, or verifying dataset/model redistribution rights.
- Running GitHub Actions remotely; the included workflow has only been authored.

Core tests validate geometry and result association, not scientific accuracy.

## v0.2.0 training/validation addition (2026-10-21)

- 14 unittest tests passed against source and the installed v0.2.0 wheel in the
  separate virtual environment. Training/validation tests use mocked model calls.
- Both YAML configs parsed successfully; model and dataset specify kpt_shape [2,3].
- CLI train dry-run succeeded without vision dependencies or model loading.
- v0.2.0 wheel built and installed successfully.
- Updated source ZIP has 26 allowlisted files; no checkpoints or research media.
- No actual training, fish checkpoint loading, dataset validation run, camera test
  or real model construction was performed. No research metrics were produced.
