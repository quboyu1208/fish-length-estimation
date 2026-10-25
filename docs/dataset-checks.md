# 训练前的数据检查 / Dataset checks

`check-dataset` 只读取数据，不创建或修改图像、标签、划分文件。无需 Torch、相机或 vision 依赖。

```powershell
fish-length check-dataset E:/datasets/fish-pose --classes 1 --keypoints 2 --dimensions 3 --splits train val --check-duplicates --output outputs/dataset-check.json
```

支持目录布局 `images/<split>/...` 和对应的 `labels/<split>/...`，保留子目录结构。支持 train、val、test；默认只检查 train 和 val。参数必须与实际数据 YAML 的类别数及 kpt_shape 一致；此工具不读取 YAML。

For directory-layout datasets, check before training:

```sh
fish-length check-dataset /path/to/fish-pose --classes 1 --keypoints 2 --dimensions 3 --check-duplicates
```

## 检查内容

- 每个划分是否存在支持的图像文件以及标签目录。
- 图像与同名标签是否配对，是否存在无对应图像的孤立标签。
- 不同图片扩展名是否错误地共用一个标签路径。
- 每行字段数是否为 `5 + keypoints * dimensions`。
- 所有值是否为有限数值，类别是否是合法范围内的整数。
- 框中心是否位于 [0,1]，宽高是否位于 (0,1]。
- 关键点坐标是否归一化，三维标签中的 visibility 是否为 0/1/2。
- 启用 `--check-duplicates` 后，按 SHA256 检查跨划分图片字节完全相同的情况，按块读取图像，不需要一次载入全部数据。

空标签文件是合法背景图像。缺失标签作为错误报告，避免漏标被当成背景。对于确认属于背景的图片，请由数据负责人显式创建空标签；工具本身不修复数据。

报告包含相对于数据根目录的文件路径、行号、错误原因以及每个划分的图像/标签/背景数量。`parsed_object_rows` 是能解析出预期数值结构的行数，可能包含范围错误，不能当作有效鱼体数量。

退出码：0 表示未发现所列格式问题；1 表示检查发现问题；2 表示命令参数或文件读取等执行错误。使用 `--output` 时只写指定报告文件；不指定时输出到终端。

## 边界

不解码图片，因此不能证明图像完整、可读或内容确为鱼类。支持 jpg/jpeg/png/bmp/tif/tiff/webp。仅扫描小写 `.txt` 标签。此工具不支持图像列表 TXT、任意 YAML 划分路径或 ZIP 数据集。

归一化范围检查不验证解剖关键点顺序、框与关键点是否贴合鱼体，也不保证所有点都在框内。字节哈希不能发现相邻视频帧、同一鱼体、改编码或裁剪后的重复图像。没有发现重复并不等于排除了数据泄漏，仍需按采集场次/鱼体分组划分。

检查通过不等于可以公开数据，或保证模型训练成功。本项目不上传被检查数据。报告可能包含数据文件名，请审阅后再分享。
