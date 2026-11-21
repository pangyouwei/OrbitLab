# OrbitLab: 二维二体引力模拟

这是 OrbitLab 的第一版最小可用程序：给定两个点质量天体的初始位置、速度和质量，用二维牛顿万有引力模拟它们的运动，并输出轨迹图、动画和轨迹数据。

## 环境

- Python 3.10+
- NumPy
- Matplotlib
- imageio-ffmpeg（编码 AVI 和 GIF）

安装依赖：

```bash
python -m pip install -r requirements.txt
```

## 运行

在项目根目录执行：

```bash
python -m orbitlab.run examples/two_body_2.json
```

程序会根据配置文件名自动创建输出子目录。例如：

- `examples/two_body_1.json` → `outputs/two_body_1/`；
- `examples/two_body_2.json` → `outputs/two_body_2/`。

`two_body_1.json` 使用质量比 `1000:1` 的圆轨道初始条件：两体间距为 `1`，共同质心在原点，行星初速度约为 `31.607`。由于质量比很大，恒星的轨道半径约为 `0.001`，行星会近似绕恒星运动。

仓库中也可以保留多套已生成结果：

- 每个配置对应的输出目录都包含轨迹 PNG、SVG、CSV、AVI、GIF 和运行摘要 JSON。

`--output-dir` 指定的是输出根目录，程序仍会在其下追加配置文件名：

```bash
python -m orbitlab.run examples/two_body_2.json --output-dir outputs
```

## 模型说明

程序使用二维牛顿引力。第 `i` 个天体的加速度为：

\[
\mathbf a_i = G \sum_{j \ne i} m_j
\frac{\mathbf r_j-\mathbf r_i}
{(|\mathbf r_j-\mathbf r_i|^2+\epsilon^2)^{3/2}}
\]

时间推进使用 Velocity Verlet。示例采用无量纲单位 `G=1`，现在模拟两个质量相等的天体。

示例初始条件将共同质心放在原点，两个天体相距 `1`，质量均为 `1`。相对圆轨道速度为 `sqrt(2)`，因此每个天体的速度大小为 `1/sqrt(2)`；两个天体都以半径 `0.5` 绕共同质心运动。程序还会把初始和最终质心位置、质心速度写入摘要，用来检查质心是否保持不动。

示例的 `8886` 步约等于四个等质量双星轨道周期，因此 GIF 循环播放时天体会回到起点附近。动画中的轨道线始终显示，天体标记随模拟时间移动。

这是第一阶段版本，暂时只支持两个天体和 Velocity Verlet。动画最多取 180 个时间点显示天体位置，轨道线使用全部模拟点；CSV 保存全部计算结果。后续可以在此基础上加入 Euler、RK4、能量守恒检查和 Barnes-Hut 四叉树。

## 目录结构

```text
OrbitLab/
├── orbitlab/
│   ├── physics.py       # 引力和加速度
│   ├── integrators.py   # Velocity Verlet
│   ├── visualize.py     # 轨迹图、AVI、GIF 和 CSV 输出
│   └── run.py           # 命令行入口和模拟流程
├── examples/
│   ├── two_body_1.json
│   └── two_body_2.json
├── outputs/
│   ├── two_body_1/      # two_body_1.json 的结果
│   └── two_body_2/      # two_body_2.json 的结果
├── requirements.txt
└── README.md
```
