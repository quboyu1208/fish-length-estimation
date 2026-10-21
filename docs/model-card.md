# Model and evaluation status

## Distributed model

None. The public release contains no checkpoint or dataset. Users supply a trusted
local fish pose checkpoint and verify both its format and landmark meanings.
Loading a checkpoint may execute deserialization code; use only trusted files.

## Endpoint semantics

Default indices are 0 and 1, an API convention only. Their anatomical meaning has
not been recovered from the original training data configuration. Specify your
own indices and document the anatomical definitions before interpreting output
as total length, fork length or standard length.

## Historical research artifacts

The source workspace contains fish training artifacts, but its fish dataset
configurations and a referenced CGA model configuration were missing during
extraction. This release cannot reproduce those experiments, identify their data
splits, or validate their historical scores. A generic YOLO Pose backbone must not
be advertised as a recovered YOLO-Fishpose improvement.

## Evaluation to perform

1. Verify a chosen checkpoint on consented fish images with documented landmarks.
2. Define split units by fish identity / acquisition session / video, avoiding
   adjacent-frame leakage.
3. Report landmark pixel/normalized errors, PCK and any OKS sigma used.
4. Compare estimated lengths with physical ground truth: sample count, MAE, RMSE,
   relative error and valid-measurement rate, stratified by depth and posture.
5. Record hardware, package versions, latency methodology and failure cases.

Synthetic geometry tests establish arithmetic and validity handling only. They do
not establish underwater measurement accuracy or camera/model compatibility.

## Included training baseline (v0.2.0)

A two-endpoint YOLOv8n Pose architecture YAML, dataset template, train and val
commands are now included. These are an adapted baseline and wrapper around
Ultralytics, not recovered historical experiment configs. No actual training
or checkpoint compatibility check was performed for this addition. See training.md.
