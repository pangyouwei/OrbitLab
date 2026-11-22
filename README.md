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

物理模拟时间与视频播放时间是两件事。前者通常等于 JSON 中的 `dt × steps`；`--duration` 可以临时覆盖 `steps`。后者由动画帧数除以 fps 决定，默认约为 `240 / 20 = 12` 秒。例如：

```bash
python -m orbitlab.run examples/forty_eight_body.json --duration 12 --max-frames 400 --fps 20
```

这会把 48 体系统模拟到 `t=12`，输出约 20 秒的 AVI/GIF。动画坐标范围只在首帧根据初始位置确定，播放期间不会缩放或平移；天体散开后可以自然跑出屏幕。4 体及以上的动画在首次超过半数天体离开画面时结束取样，因此此例视频会在模拟时间约 `t=2.45` 截止并以约 20 秒播完；完整的 `t=12` 数值结果仍保留在 CSV、静态图和摘要中。已有结果只需重做动画、保留 CSV 和摘要时可加 `--animation-only`；只想重新生成黑色静态图时可加 `--static-only`。

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

在示例的 `t=6` 模拟时间内，等边三角形解会近似保持三角形形状整体旋转；三组微扰案例延长到 `t=12`，可以比较扰动大小不同导致的轨迹分离。等质量三体的等边解本身是不稳定的，延长模拟时间后，即使没有人为扰动，数值误差也会逐渐放大。静态图和动画均使用黑色背景；动画从空轨道开始，天体运动时逐步绘制从起点到当前位置的完整轨迹，坐标范围保持固定。

每次运行还会计算总能量、总动量、二维角动量和质心漂移。`maximum_relative_energy_error` 越小，说明当前时间步长下的数值误差越小。动画默认最多取 240 个时间点显示天体位置，轨迹线使用截至当前帧的全部模拟点；轨迹 CSV 和诊断 CSV 保存全部计算结果。若想看到天体散出画面，使用初始位置较集中、后续速度较大的案例，并保持固定镜头。

微扰案例在较长时间内可能发生近距离掠过；固定步长遇到这种情况时能量误差会增大。因此比较混沌现象时，应同时查看轨迹图和 `*_summary.json` 中的守恒量误差。

## 更多天体与轨迹分离

中等三体扰动案例使用 `dt=0.00025`、`48000` 步，总模拟时间仍为 `12`。与原来的 `dt=0.001` 相比，近距离掠过时的最大相对能量误差从约 `1.38%` 降至 `0.087%`。

12 体案例从略有扰动的等质量圆环出发。`twelve_body_twin.json` 仅把两个天体的初始纵向速度分别加减 `10^-5`，使总动量不变。比较两次运行时对应天体的位置：

```bash
python -m orbitlab.run examples/twelve_body.json
python -m orbitlab.run examples/twelve_body_twin.json --skip-animation
python -m orbitlab.compare examples/twelve_body.json examples/twelve_body_twin.json --output-dir outputs/twelve_body_comparison
```

`outputs/twelve_body_comparison/separation.png` 的纵轴是 12 个对应天体位置差的均方根；初始位置相同，到 `t=12` 时该差距约为 `0.16`。这展示了对初始条件的敏感性，但单次有限时长的轨迹分离本身不是严格的 Lyapunov 指数测量。

生成更多天体的配置并运行，例如 48 体：

```bash
python -m orbitlab.generate --count 48 --seed 42 --dt 0.002 --duration 12 --softening 0.05 --output examples/forty_eight_body.json
python -m orbitlab.run examples/forty_eight_body.json
```

48 体案例现在也有 AVI/GIF。`--skip-animation` 仍可用于只要静态图、轨迹 CSV 和守恒量诊断的运行。生成器用固定随机种子保证复现，先按对称圆环的引力计算旋转速度，再加入小扰动，并把质心位置与总动量调至零。多体案例采用 `softening=0.05`，这是软化引力模型，可避免近距离接触处的数值奇点；它与理想点质量的 `softening=0` 模型有区别。直接两两计算的成本随天体数约按 `N^2` 增长，因此几十体适合普通笔记本，数千体需要更高效的算法。

## 如何修改 JSON，得到想要的运动

先复制一个 `examples/*.json` 并改名，再运行这个新文件。程序会把结果放进 `outputs/新文件名/`，便于保留原案例。JSON 的核心结构如下：

```json
{
  "G": 1.0,
  "dt": 0.001,
  "steps": 6000,
  "softening": 0.0,
  "bodies": [
    {"name": "A", "mass": 1.0, "position": [-0.5, 0.0], "velocity": [0.0, -0.70710678]},
    {"name": "B", "mass": 1.0, "position": [0.5, 0.0], "velocity": [0.0, 0.70710678]}
  ]
}
```

| 字段 | 控制什么 | 改动后的常见效果 |
| --- | --- | --- |
| `G` | 引力强度，示例采用无量纲 `G=1` | 增大后吸引更强；同样初速度下轨道会改变 |
| `mass` | 各天体质量，必须大于零 | 大质量天体更难被推动，也会更强地吸引其他天体 |
| `position: [x,y]` | 初始二维位置 | 改变相互距离和初始几何形状；过近会导致强烈掠过 |
| `velocity: [vx,vy]` | 初始二维速度 | 沿径向易接近/远离，沿切向更容易形成绕转 |
| `dt` | 每次积分走过的物理时间 | 越小通常越准，但相同总时长需要更多步，运行更慢 |
| `steps` | 积分次数 | `dt × steps` 决定模拟终点；增大它不会自动提高精度 |
| `softening` | 近距离引力软化长度 | 增大后近距离相互作用更平滑，但物理模型也随之改变 |

**想要稳定、近似圆形的二体轨道：**用 `two_body_1.json` 或 `two_body_2.json` 作起点。两个天体初始相距 `d`、质量为 `M` 和 `m` 时，相对圆轨道速度大小为 `sqrt(G × (M+m) / d)`。让位置在质心两侧，速度沿垂直于连线的方向且总动量为零。例如放在 x 轴上，位置可取 `[-m*d/(M+m), 0]` 与 `[M*d/(M+m), 0]`，纵向速度分别取 `-m*v/(M+m)` 与 `M*v/(M+m)`。只改质量而不重算速度，原本的圆轨道通常会变椭圆。

**想要椭圆、近距离掠过或逃逸：**从圆轨道案例复制一份，逐步改变一个天体的切向初速度。略低于圆轨道速度通常使轨道更扁，过高可能使它远离系统；也可调整初始距离。三体以上会相互扰动，二体的简单公式只能作为初始猜测。每次只改一个因素，才能看出原因。

**想要比较三体对初始条件的敏感性：**从 `three_body_lagrange.json` 复制一份，给第一个天体的 `vy` 加一个很小的量，例如 `0.001`，同时给另外两颗等质量天体的 `vy` 各减去 `0.0005`。这样总动量仍为零；现成的弱、中、强扰动配置可直接比较。若想用 `orbitlab.compare`，两份配置必须具有同样的天体顺序、质量、`G`、`softening`、`dt` 和 `steps`。

**想要 12、48 或更多天体：**使用 `python -m orbitlab.generate --count 12 --seed 42 --output examples/my_ring.json` 生成可复现的微扰圆环。`--position-jitter` 和 `--velocity-jitter` 控制初始扰动大小；设为 `0` 得到对称圆环，但对称构型仍可能不稳定。改 `--seed` 可生成另一套初始条件。也可以手动在 `bodies` 数组中增删对象，但每个对象都需要名称、正质量、二维位置和二维速度。

**调到满意且可信的结果：**先用短时长 `--duration 2` 试跑并看轨迹图；再逐步延长。遇到两体近距离擦过、轨迹突然折转时，检查 `*_summary.json` 的 `maximum_relative_energy_error`，把 `dt` 减半、`steps` 加倍，在相同总时长下重跑并比较误差。`softening` 可以防止数值奇点，但要在报告里注明它改变了引力模型。固定镜头只改变展示范围，不会改变物理计算或修复不准确的数值积分。

## 目录结构

```text
OrbitLab/
├── orbitlab/
│   ├── physics.py       # 引力和加速度
│   ├── diagnostics.py   # 能量、动量、角动量和质心漂移
│   ├── integrators.py   # Velocity Verlet
│   ├── generate.py      # 可复现的多体初始条件
│   ├── compare.py       # 邻近初始条件的轨迹差距
│   ├── visualize.py     # 轨迹图、AVI、GIF 和 CSV 输出
│   └── run.py           # 命令行入口和模拟流程
├── examples/
│   ├── two_body_1.json
│   ├── two_body_2.json
│   ├── three_body_lagrange.json
│   ├── three_body_perturbed_weak.json
│   ├── three_body_perturbed.json
│   ├── three_body_perturbed_strong.json
│   ├── twelve_body.json
│   ├── twelve_body_twin.json
│   └── forty_eight_body.json
├── outputs/
│   ├── two_body_1/      # two_body_1.json 的结果
│   ├── two_body_2/      # two_body_2.json 的结果
│   ├── three_body_lagrange/   # 等边三角形周期解
│   ├── three_body_perturbed_weak/    # 弱微扰
│   ├── three_body_perturbed/         # 中等微扰
│   ├── three_body_perturbed_strong/  # 强微扰
│   ├── twelve_body/                 # 12 体动画与数据
│   ├── twelve_body_twin/            # 12 体邻近初始状态
│   ├── twelve_body_comparison/      # 轨迹差距曲线
│   └── forty_eight_body/            # 48 体图、动画与数据
├── requirements.txt
└── README.md
```
