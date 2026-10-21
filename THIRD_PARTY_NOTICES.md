# Provenance and third-party notices

This repository was extracted from a local fish measurement research workspace.
The endpoint-distance workflow was refactored from `ultralytics/speed-id-length.py`,
particularly `xy2xyz` and `length_estimate`. The new implementation separates
geometry, optional inference and camera access, and adds explicit validity results.
The original workflow retrieved XYZ from ZED and calculated a Euclidean endpoint
distance. The original experimental script is not bundled.

The source workspace included Ultralytics YOLO, declared version 8.2.31 and
AGPL-3.0. This repository retains the AGPL-3.0 license text from that workspace.
No full Ultralytics source fork, README badges, upstream author metadata or
upstream performance tables are copied into this project.

Optional inference uses Ultralytics (https://github.com/ultralytics/ultralytics).
Its authors and applicable licenses remain those of the upstream project.
ZED SDK / Python API belong to Stereolabs
(https://github.com/stereolabs/zed-python-api); obtain the SDK separately under
its applicable terms. No SDK binaries are included.

No ArcFace code or weights, tracking code, experimental fish photos, videos,
training checkpoints or training-result images are included in the public bundle.
The included JSON example is synthetic and contains no experimental observations.

Before distributing any additional model or dataset, record its source, authors,
license/permission, landmark meanings and integrity hash separately. This license
file does not establish ownership or redistribution rights for external assets.
