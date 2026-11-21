# OrbitLab: 二维二体引力模拟

这是 OrbitLab 的第一版最小可用程序：给定两个点质量天体的初始位置、速度和质量，用二维牛顿万有引力模拟它们的运动，并输出轨迹图和轨迹数据。

## 环境

- Python 3.10+
- NumPy
- Matplotlib

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

- `two_body_trajectory.png`：二维轨迹图；
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

这是第一阶段版本，暂时只支持两个天体和 Velocity Verlet。后续可以在此基础上加入 Euler、RK4、能量守恒检查、动画和 Barnes-Hut 四叉树。

## 目录结构

```text
OrbitLab/
├── orbitlab/
│   ├── physics.py       # 引力和加速度
│   ├── integrators.py   # Velocity Verlet
│   ├── visualize.py     # 轨迹图和 CSV 输出
│   └── run.py           # 命令行入口和模拟流程
├── examples/
│   └── two_body.json
├── outputs/
├── requirements.txt
└── README.md
```
