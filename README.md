# OrbitLab: 二维 N 体引力模拟

OrbitLab 用二维牛顿万有引力模拟点质量天体的运动。程序支持两个及以上天体，并输出轨迹图、渐进轨迹动画、轨迹数据和守恒量诊断。

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
python -m orbitlab.run examples/three_body_lagrange.json
```

比较三组扰动：

```bash
python -m orbitlab.run examples/three_body_perturbed_weak.json
python -m orbitlab.run examples/three_body_perturbed.json
python -m orbitlab.run examples/three_body_perturbed_strong.json
```

程序会根据配置文件名自动创建输出子目录。例如：

- `examples/two_body_1.json` → `outputs/two_body_1/`；
- `examples/two_body_2.json` → `outputs/two_body_2/`。

`two_body_1.json` 使用质量比 `1000:1` 的圆轨道初始条件；`three_body_lagrange.json` 使用三个相同质量天体组成的等边三角形周期解；`three_body_perturbed_weak.json`、`three_body_perturbed.json` 和 `three_body_perturbed_strong.json` 分别加入大小为 `10^-4`、`10^-3`、`10^-2` 的速度扰动，同时补偿另外两个天体的速度以保持总动量为零。

仓库中也可以保留多套已生成结果：

- 每个配置对应的输出目录都包含轨迹 PNG、SVG、轨迹 CSV、诊断 CSV、AVI、GIF 和运行摘要 JSON。

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

时间推进使用 Velocity Verlet。示例采用无量纲单位 `G=1`。Velocity Verlet 不依赖天体数量，因此同一套推进器可以处理三体系统。

示例初始条件将共同质心放在原点，两个天体相距 `1`，质量均为 `1`。相对圆轨道速度为 `sqrt(2)`，因此每个天体的速度大小为 `1/sqrt(2)`；两个天体都以半径 `0.5` 绕共同质心运动。程序还会把初始和最终质心位置、质心速度写入摘要，用来检查质心是否保持不动。

在示例的 `t=6` 模拟时间内，等边三角形解会近似保持三角形形状整体旋转；三组微扰案例延长到 `t=12`，可以比较扰动大小不同导致的轨迹分离。等质量三体的等边解本身是不稳定的，延长模拟时间后，即使没有人为扰动，数值误差也会逐渐放大。动画从空轨道开始，天体运动时逐步绘制从起点到当前位置的完整轨迹。

每次运行还会计算总能量、总动量、二维角动量和质心漂移。`maximum_relative_energy_error` 越小，说明当前时间步长下的数值误差越小。动画最多取 180 个时间点显示天体位置，轨迹线使用全部模拟点；轨迹 CSV 和诊断 CSV 保存全部计算结果。

微扰案例在较长时间内可能发生近距离掠过；固定步长遇到这种情况时能量误差会增大。因此比较混沌现象时，应同时查看轨迹图和 `*_summary.json` 中的守恒量误差。

## 目录结构

```text
OrbitLab/
├── orbitlab/
│   ├── physics.py       # 引力和加速度
│   ├── diagnostics.py   # 能量、动量、角动量和质心漂移
│   ├── integrators.py   # Velocity Verlet
│   ├── visualize.py     # 轨迹图、AVI、GIF 和 CSV 输出
│   └── run.py           # 命令行入口和模拟流程
├── examples/
│   ├── two_body_1.json
│   ├── two_body_2.json
│   ├── three_body_lagrange.json
│   ├── three_body_perturbed_weak.json
│   ├── three_body_perturbed.json
│   └── three_body_perturbed_strong.json
├── outputs/
│   ├── two_body_1/      # two_body_1.json 的结果
│   ├── two_body_2/      # two_body_2.json 的结果
│   ├── three_body_lagrange/   # 等边三角形周期解
│   ├── three_body_perturbed_weak/    # 弱微扰
│   ├── three_body_perturbed/         # 中等微扰
│   └── three_body_perturbed_strong/  # 强微扰
├── requirements.txt
└── README.md
```
