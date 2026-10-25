# 体长误差评估 / Physical-length evaluation

该功能比较用户提供的**已配对**预测体长与真实体长，单位均为 cm，无需模型和相机。

```powershell
fish-length evaluate-lengths examples/length-evaluation.synthetic.json
fish-length evaluate-lengths C:/data/matched-lengths.json --output outputs/length-metrics.json
```

The shipped example is synthetic arithmetic data, not experimental evidence.
Provide one row per matched observation, retain failed observations with null
predictions, and review both errors and valid-measurement coverage.

## 输入

```json
{
  "samples": [
    {"sample_id": "session01-frame001-fish01", "true_length_cm": 25.0, "predicted_length_cm": 24.6, "group": "near"},
    {"sample_id": "session01-frame002-fish01", "true_length_cm": 25.0, "predicted_length_cm": null, "group": "near"}
  ]
}
```

这里的数字同样只是格式示例。每条记录需要唯一且非空的 sample_id、正数 true_length_cm、正数或 null 的 predicted_length_cm。必须显式包含 prediction 字段，失败时填 null；不能把失败样本整行丢掉。拒绝负数、0、布尔值、字符串数值及 NaN/Inf。

`group` 为可选非空字符串，例如距离档、姿态、采集场次或鱼种。省略时进入 group=null 的组。总体指标按每条有效观测加权，不是对各组均值做平均。

## 指标定义

误差 e = predicted_length_cm - true_length_cm。

- sample_count：全部观测数，包括预测失败的观测。
- valid_count / invalid_count：非空预测与空预测的数量。
- valid_rate：valid_count / sample_count；空输入时为 null。
- mae_cm：有效观测的平均绝对误差。
- rmse_cm：有效观测的均方根误差。
- bias_cm：有效观测的平均有符号误差；正值表示高估。
- median_absolute_error_cm：有效观测的绝对误差中位数。
- mape_percent：有效观测 abs(e)/true_length_cm 的平均值乘以 100。

输出包含 overall 与 by_group。没有有效预测时误差指标为 null，不输出虚假的零误差。除覆盖率及计数外，误差指标只针对成功预测；因此必须同时报告 valid_rate，不能跨失败率不同的方法只比较 MAE。

合成样例有 3 条观测、2 个有效预测，MAE=1.5 cm，RMSE=sqrt(2.5) cm，有效率=2/3。这些是测试算术的预期值，不能当成真实鱼体精度。

## 实验使用

工具不会自动配对鱼体、关联跨帧 ID 或从测量 JSON 中猜测对应关系。先用 sample_id 明确关联物理真值与同一条鱼的预测，再构造输入。保留失败观测并记录失败原因；不会用真实值填补缺失预测。

预测与真值必须使用相同的端点定义：全长、叉长和标准长不能混用；两端点弦长与弯曲中心线弧长也不能直接比较。记录真值测量方法、单位、深度/水质、测试集划分和校准条件。

同一鱼体多帧并非独立样本。当前汇总按观测计数，不提供独立鱼体加权、置信区间或显著性检验；论文评估需另行制定采样和统计协议。

该命令不证明模型或 ZED 实机可用，不会运行模型、训练或上传数据。公共仓库不包含真实测量结果。
