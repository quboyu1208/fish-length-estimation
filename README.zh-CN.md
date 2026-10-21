# 鱼体长度估计 Fish Length Estimation

从鱼类 Pose 关键点与对齐的三维 XYZ 数据计算两个端点之间的直线距离。

这是从毕业设计研究目录中提取、重构的最小开源版本。**当前可独立验证的是几何计算链路；鱼类权重推理和 ZED 实机尚未验证。** 不宣称测量精度、实时帧率或改进模型效果。

## 最快运行：无需模型与相机

在本项目目录使用 Python 3.10 或更新版本：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
fish-length measure examples/synthetic.json
python -m unittest discover -s tests -v
```

合成样例包含两个目标：第一个返回无效深度，第二个返回 30 cm。样例用于验证单位、几何和目标对应关系，不是鱼类精度实验。

## 图片关键点检测

```powershell
python -m pip install -e ".[vision]"
fish-length predict --weights C:/models/fish-pose.pt --image C:/data/fish.jpg --device cpu --output outputs/keypoints.json
```

必须提供可信的本地 Pose 权重，并自行核实关键点顺序。仅有普通图片时只输出二维关键点，不输出厘米数。

如有与原图逐像素对齐、来自同一时刻的三维数据：

```powershell
fish-length predict --weights C:/models/fish-pose.pt --image C:/data/fish.jpg --xyz C:/data/aligned-xyz.json --endpoints 0 1 --output outputs/lengths.json
```

数据格式见 [data-format.md](docs/data-format.md)。这里需要 XYZ 三维坐标，不能直接把单通道深度数值当成 XYZ 使用；从深度反投影需要正确的相机内参及坐标约定。

## ZED 实时测量（待实机验证）

自行通过官方渠道安装匹配的 ZED SDK、Python API、GPU 驱动和依赖。项目不包含 SDK wheel。

```powershell
fish-length zed --weights C:/models/fish-pose.pt --device 0 --max-frames 300 --show --output outputs/measurements.jsonl
```

使用 SDK 校正左图和米制对齐点云；Esc/q 退出。每帧结果保留每个检测的测量状态；检测索引只在当前帧有效，不是跨帧鱼体 ID。

## 本次提取与修复

- 将长度计算从速度、ArcFace 个体识别、旧 YOLO 工具和硬编码路径中拆出。
- 无效目标保留原始检测索引，防止过滤后与其他鱼的框错配。
- 显式单位换算，检查关键点置信度、坐标边界、点云有限值和正向深度。
- 原图边界的零坐标可以有效；同一像素的两个端点拒绝测量。
- ZED 入口检查采集状态，异常及退出时释放相机。
- 提供合成样例、核心测试、最小 CI 和白名单发布压缩包脚本。

## 科研边界

当前结果是两个指定端点的三维弦长，不能直接称为弯曲鱼体中心线长度。端点是否代表吻端、尾叉或尾鳍末端必须结合标注协议确认。

尚未解决：水下折射校正、邻域稳健深度采样、深度不确定度、遮挡、端点背景污染及真实体长误差评估。当前单点深度采样仅作为可解释基线。

公开包不包含实验图片、数据集、研究权重或训练指标；不包含缺失的 CGA 模型结构。`vision` 依赖固定为原工作区声明的 Ultralytics 8.2.31，但未证明它能直接加载历史权重。

## 上传准备

```powershell
python tools/build_public_bundle.py
```

生成 `dist/fish-length-estimation-0.1.0-source.zip`。该压缩包仅收录明确列出的公开源码、文档和合成数据，不包含 `.local`、权重、环境或输出。请优先使用它创建公开仓库，避免把原毕业设计目录一起上传。

本地提取时额外复制的参考权重位于 `.local/weights`，被 Git 和发布包排除；其来源记录也只保存在 `.local`。权重未加载、未验证、尚未确认公开授权。

许可证为 AGPL-3.0，来源说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。上线前待办与后续研究计划见 [release.md](docs/release.md)。

本地实际验证及未验证范围见 [验证记录](docs/verification.md)。
