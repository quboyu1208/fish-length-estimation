# YOLO 鱼类关键点训练与评估

本项目通过固定版本的 `ultralytics` Python 依赖提供网络、损失函数、训练循环和验证器；仓库中提供模型 YAML、数据模板及本项目的命令入口，不重复复制整套框架源码。

本页给出一个**新整理的双端点训练基线**，不是恢复原毕业设计全部实验。原 `coco8-fishpose.yaml` / `fish-pose.yaml` 及 CGA 模型配置未找到，因此原数据类别、端点解剖定义与改进结构不能从这些模板推断。

## 1. 安装训练依赖

从仓库根目录执行：

```powershell
python -m pip install -e ".[vision]"
```

请根据 GPU 和驱动安装匹配的 PyTorch。CPU 可用于检查流程，实际训练速度取决于硬件。固定的 Ultralytics 8.2.31 是从原工作区版本提取的兼容起点，不等于完整训练环境锁定；新环境仍需验证。

## 2. 准备并划分数据

自行准备具有训练及公开使用权限的图像和 YOLO Pose 标注。推荐目录：

```text
fish-pose/
  images/
    train/001.jpg
    val/101.jpg
    test/201.jpg
  labels/
    train/001.txt
    val/101.txt
    test/201.txt
```

同一图像对应同名 `.txt`，每条鱼一行。先按鱼体身份、视频或采集场次划分集合，再导出图像，避免把相邻帧随机分到训练和测试集。`test` 为可选独立测试集；不存在时不要配置或执行 test 评估。

双关键点、含可见性时每行 11 个数：

```text
class_id cx cy width height endpoint0_x endpoint0_y endpoint0_v endpoint1_x endpoint1_y endpoint1_v
```

- 类别从 0 开始；框中心、宽高和关键点 x/y 均相对于原图宽高归一化到 [0,1]。
- 可见性约定：0 未标注、1 已标注但遮挡、2 已标注且可见；缺失点使用 `0 0 0`，不是把可见点错误放到原点。
- 这个版本中 v=1 的位置仍参与关键点监督；不要为无法可靠定位的遮挡点编造坐标。
- 每一行的关键点顺序必须一致。例如你可以选择吻端和尾叉，但必须在数据说明中定义，不能把它自动当成原论文定义。
- 类别、关键点个数、维度和翻转映射必须与配置一致。

仅用于解释格式的一行合成数字（不是实验标注）：

```text
0 0.50 0.50 0.60 0.20 0.20 0.50 2 0.80 0.50 2
```

## 3. 编辑数据配置

复制 `configs/fish-pose.example.yaml` 为本地数据配置，例如 `.local/fish-pose.yaml`。将 `path` 改为你机器上的绝对路径：

```yaml
path: E:/datasets/fish-pose
train: images/train
val: images/val
test: images/test  # 仅在独立测试集存在时添加
kpt_shape: [2, 3]
flip_idx: [0, 1]
names:
  0: fish
```

`fish` 是示例单类别；多鱼种需按实际类别表修改。`flip_idx: [0,1]` 表示水平翻转不会交换解剖端点身份（如吻端/尾端）；如果你的定义是图像左端/右端，就需要重新设计标注和映射。

模型配置 `configs/yolov8n-fish-pose.yaml` 来自工作区内的 Ultralytics 基础 Pose 配置，仅将关键点数设为 2、明确 n 尺寸；保留上游 AGPL 标识。不是新架构或 CGA 模型。

## 4. 先检查命令计划

此命令不需要 vision 依赖，不会加载权重、扫描数据或启动训练：

```powershell
fish-length train --model configs/yolov8n-fish-pose.yaml --data configs/fish-pose.example.yaml --epochs 100 --device 0 --dry-run
```

dry-run 只检查本地输入文件是否存在、命令参数是否合法，然后打印计划。它不会证明 YAML、标注或数据划分正确；实际训练前必须编辑数据路径并核对标注。

## 5. 从配置训练双关键点基线

```powershell
fish-length train --model configs/yolov8n-fish-pose.yaml --data .local/fish-pose.yaml --epochs 100 --imgsz 640 --batch 8 --device 0 --workers 0 --seed 0 --project outputs/pose --name fish-baseline --output outputs/train-summary.json
```

使用 YAML 从头构建模型。默认关闭 AMP、`pretrained=False`；不主动指定下载预训练模型。训练框架仍可能做版本检查、可选依赖检查等网络操作，不能据此宣称完整离线运行。

默认 seed=0、deterministic=True，记录参数有助于复现，但不能保证不同 GPU/库版本逐位一致。`workers=0` 是兼顾 Windows 的起点。可用 `--amp` 显式开启混合精度，但上游 AMP 检查可能下载参考模型。

## 6. 从可信本地 Pose 权重微调

```powershell
fish-length train --model C:/models/trusted-pose.pt --data .local/fish-pose.yaml --epochs 100 --device 0 --name fish-finetune --output outputs/finetune-summary.json
```

当 `--model` 为本地 `.pt` 时，Ultralytics 8.2.31 会把该 checkpoint 中可匹配的模型参数用于初始化训练模型；数据配置会覆盖类别数和关键点形状。`pretrained=False` 不表示丢弃已经显式加载的 checkpoint；它避免额外指定远程预训练来源。

只加载可信 checkpoint，PyTorch 反序列化存在执行代码的可能。历史 train43 权重仅被本地保存，是否兼容及端点定义尚未确认，不在公共仓库提供。

## 7. 关键点评估

训练完成后，在实际运行目录中找到 `weights/best.pt`。若目录已存在，框架可能自动加数字后缀，请以命令输出或汇总中的 `save_dir` 为准。

```powershell
fish-length val --weights outputs/pose/fish-baseline/weights/best.pt --data .local/fish-pose.yaml --split val --device 0 --output outputs/val-summary.json
fish-length val --weights outputs/pose/fish-baseline/weights/best.pt --data .local/fish-pose.yaml --split test --device 0 --name independent-test --output outputs/test-summary.json
```

第二行仅用于已有独立测试集的情况。训练默认会验证并保存框架产物，独立 val 命令用于明确复评。

框架产物通常包括参数 YAML、results.csv、曲线、样例图及 best/last 权重。命令额外导出 metrics 汇总 JSON。产物可能包含原始图像，默认位于被 Git 忽略的 `outputs/`，不应未经审阅上传。

`metrics/*(B)` 为检测框指标，`metrics/*(P)` 为关键点指标；不能将这些值当作厘米体长误差。固定版本验证器对非 COCO17 任务使用均匀 `1/nkpt` sigma，本双点基线对应 0.5。论文比较应披露这一参数并补充逐点误差/PCK。

## 8. 接入体长估计

```powershell
fish-length predict --weights outputs/pose/fish-baseline/weights/best.pt --image C:/data/fish.jpg --xyz C:/data/aligned-xyz.json --endpoints 0 1 --output outputs/lengths.json
fish-length zed --weights outputs/pose/fish-baseline/weights/best.pt --device 0 --show --output outputs/live.jsonl
```

关键点训练本身不学习厘米长度。物理长度依赖正确的对齐三维信息、解剖端点定义和独立真值验证。至少报告长度 MAE、RMSE、相对误差、有效测量率，并按距离和姿态分组。

## 当前验证边界

命令分发、dry-run 不加载模型、参数校验和指标汇总通过模拟模型测试；模拟数值不代表任何真实实验结果。本次未实际训练、未运行真实验证集，也未证明基础模型和历史 checkpoint 的推理兼容性。下一步需要在有授权的数据上完成环境和真实训练检查。

## 训练前与测量后的检查

训练前建议运行只读标注检查：

```powershell
fish-length check-dataset E:/datasets/fish-pose --classes 1 --keypoints 2 --dimensions 3 --check-duplicates --output outputs/data-check.json
```

完成物理真值配对后，可运行 `fish-length evaluate-lengths` 报告厘米误差与有效率。详见 [数据检查](dataset-checks.md) 和 [体长误差评估](length-evaluation.md)。它们不取代 YOLO val，也不会自动恢复原数据集或测量真值。
