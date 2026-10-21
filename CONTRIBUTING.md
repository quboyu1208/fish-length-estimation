# Contributing

Use Python 3.10+. Install the core with `python -m pip install -e .`, then run
`python -m unittest discover -s tests -v`. Geometry changes should include tests
for units, invalid samples and detection association. Keep camera and ML imports
optional so core tests can run without hardware, Torch or internet access.

Describe the problem, expected/actual behavior and environment when reporting an
issue. Use synthetic or explicitly shareable inputs. Do not attach private fish
images, credentials, institutional datasets or unlicensed checkpoints.

Contributions should remain compatible with this project's AGPL-3.0 license.
Document provenance for third-party code. Do not claim model accuracy or hardware
support without a reproducible evaluation and clearly stated conditions.
