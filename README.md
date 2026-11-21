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
python -m orbitlab.run examples/two_body.json
```

默认输出到 `outputs/`：

- `two_body_trajectory.png`：1600 × 1600 像素的二维轨迹图，恒星标记较大、行星标记较小；
- `two_body_trajectory.svg`：可放大查看的矢量轨迹图；
- `two_body_animation.avi`：MJPEG 编码的视频，适合兼容性较差的本地播放器；
- `two_body_animation.gif`：960 × 960 像素、30 帧/秒的循环预览；
- `two_body_trajectory.csv`：每个时间步的位置和速度；
- `two_body_summary.json`：本次运行的参数和基本结果。

也可以指定输出目录：

```bash
python -m orbitlab.run examples/two_body.json --output-dir outputs/demo
```

## 模型说明

程序使用二维牛顿引力。第 `i` 个天体的加速度为：

\[
\mathbf a_i = G \sum_{j \ne i} m_j
\frac{\mathbf r_j-\mathbf r_i}
{(|\mathbf r_j-\mathbf r_i|^2+\epsilon^2)^{3/2}}
\]

时间推进使用 Velocity Verlet。示例采用无量纲单位 `G=1`、中心天体质量 `1`、轨道半径约 `1`，因此行星初速度约为 `1` 时会形成近似圆轨道。

示例初始条件将共同质心放在原点，两个天体相距 `1`。相对圆轨道速度取 `sqrt(G * (m_star + m_planet) / r)`，再按质量比分配给两者，所以两个天体都绕共同质心运动：恒星的小轨道半径约为 `0.001`，行星的轨道半径约为 `0.999`。程序还会把初始和最终质心位置、质心速度写入摘要，用来检查质心是否保持不动。

示例的 `9420` 步约等于三个轨道周期，因此 GIF 循环播放时天体会回到起点附近。动画中的轨道线始终显示，天体标记随模拟时间移动。

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
│   └── two_body.json
├── outputs/
├── requirements.txt
└── README.md
```
