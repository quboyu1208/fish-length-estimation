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
