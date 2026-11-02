# 中国各省 GDP 数据分析（教学项目）

一个用 Python + pandas + matplotlib 完成的入门级数据分析项目：读取省份 GDP 与人口数据，做基础清洗，计算排名、人均 GDP 和占比，输出三张图表和一份 Markdown 分析报告。

> **数据声明**：本项目使用的是**教学示例数据**，不是官方统计数据。缺失的 GDP 用中位数补全后会标记为「估算」；这些数值仅用于演示数据清洗与分析流程，不能当作真实 GDP、排名或结论引用。

---

## 1. 你将学到什么

- 用 `pandas` 读取 CSV，检查结构、缺失值和重复记录
- 用 `drop_duplicates()` 去重、用 `fillna(median)` 补缺失，并保留「是否估算」标记
- 计算 GDP 排名、人均 GDP、GDP 占比三类指标
- 用 `matplotlib` / `seaborn` 出图，并解决中文字体显示问题
- 自动导出一份 Markdown 分析报告

---

## 2. 项目结构

```
China_GDP_Analysis/
├── data/
│   ├── raw/
│   │   └── china_gdp.csv            # 原始数据（唯一的输入文件）
│   └── processed/                    # 清洗与分析后的结果（程序生成）
├── output/
│   ├── charts/                       # 图表（程序生成）
│   └── reports/                      # Markdown 报告（程序生成）
├── _archive/                         # 学习过程的中间脚本（只存档，见附录）
├── main.py                           # 主程序，五个阶段依次执行
├── requirements.txt                  # 依赖清单
├── .gitignore                        # 版本库忽略规则
└── README.md                         # 本文件
```

`.venv/`（虚拟环境）和 `.idea/`（PyCharm 配置）是本机文件，不需要提交到版本库。

---

## 3. 快速开始（Windows / PyCharm）

### 3.1 打开项目并确认解释器

1. **File → Open**，打开 `China_GDP_Analysis` 文件夹本身，而不是单独打开某个 `.py` 文件
2. **File → Settings → Project → Python Interpreter**，选择项目里的虚拟环境：

```text
C:\Users\17523\PyCharmProjects\China_GDP_Analysis\.venv\Scripts\python.exe
```

如果 `.venv` 不存在，在同一页面新建一个 Virtualenv（Python 3.10+ 均可，本项目在 3.12.10 上验证通过）。

### 3.2 安装依赖

在 PyCharm 底部 **Terminal** 里执行（注意提示符前应带 `(.venv)`）：

```powershell
python -m pip install -r requirements.txt
```

`requirements.txt` 内容为四个包：

```text
pandas
numpy
matplotlib
seaborn
```

判断终端是否用对了环境：

```powershell
python -c "import sys; print(sys.executable)"
```

输出里带 `China_GDP_Analysis\.venv\Scripts\python.exe` 才对；如果指向系统 Python，装完依赖 PyCharm 运行仍会报 `ModuleNotFoundError`。

### 3.3 准备数据

把符合格式的 CSV 放到 `data/raw/china_gdp.csv`。`main.py` 通过 `BASE_DIR` 拼接相对路径读取它，所以**与从哪个目录启动无关**，只要求路径和文件名一致。

如果该文件不存在，`main.py` 会自动生成一份教学数据并写入，方便首次运行。

### 3.4 运行

在项目树里右键 `main.py` → **Run 'main'**，或终端执行：

```powershell
python main.py
```

运行成功后，控制台会依次打印五个阶段的输出，并在 `data/processed/`、`output/charts/`、`output/reports/` 生成结果文件。

---

## 4. 数据格式与单位

CSV 表头必须包含三个中文列名（建议 UTF-8-SIG 编码，Excel 打开不乱码）：

```csv
省份,GDP,人口
广东,135000,12700
江苏,130000,8500
湖北,60000,5800
```

| 字段 | 含义 | 程序中的用途 |
| --- | --- | --- |
| `省份` | 省级地区名称 | 图表标签、报告文字、去重判断依据 |
| `GDP` | 地区生产总值（亿元） | 排名、占比、人均 GDP 的分子 |
| `人口` | 常住人口（万人） | 人均 GDP 的分母 |

### 单位：本项目算出来的是「万元/人」

`main.py` 里的公式是：

```python
df["人均GDP"] = df["GDP"] / df["人口"]
```

- GDP 单位是**亿元**（10⁸ 元），人口单位是**万人**（10⁴ 人）
- 亿元 ÷ 万人 = 10⁴ 元/人 = **万元/人**
- 例如广东：135000 ÷ 12700 ≈ 10.63，即 **10.63 万元/人**

> 代码里的单位约定和图表坐标轴标签（`人均 GDP（万元/人）`）是一致的。
> 如果你更习惯「元/人」，需要写成 `df["GDP"] * 10000 / df["人口"]`，并同时改掉图表标题和报告里的单位说明——**改了公式就必须改标签**，否则数字和标签对不上。

---

## 5. 处理流程（`main.py` 的五个阶段）

| 阶段 | 函数 | 做什么 |
| --- | --- | --- |
| 一、读取 | `load_data()` | 读 CSV，打印原始数据、`df.info()`、`df.describe()`、行列数 |
| 二、清洗 | `clean_data()` | 去重、处理缺失值、校验字段、保存 `cleaned_gdp.csv` |
| 三、分析 | `analyze_data()` | 计算排名/人均/占比，排序，打印统计量，保存 `gdp_analysis.csv` |
| 四、可视化 | `create_charts()` | 生成三张图，保存到 `output/charts/` |
| 五、报告 | `generate_report()` | 生成 Markdown 报告，保存到 `output/reports/` |

另外两个辅助函数：`setup_chinese_font()` 负责加载 `C:\Windows\Fonts\msyh.ttc`（微软雅黑）解决中文显示；`create_sample_data()` 在原始 CSV 缺失时自动生成教学数据。

---

## 6. 清洗规则详解

`clean_data()` 的执行顺序：

```python
# 1) 统计缺失值与重复行（先看清楚问题，再动手）
print(df.isnull().sum())
print(df[df.duplicated()])

# 2) 删除完全重复的记录
df = df.drop_duplicates()

# 3) 同一省份若存在多条不同记录，不擅自合并，直接报错提示人工核对
dup_prov = df[df.duplicated(subset=["省份"], keep=False)]
if not dup_prov.empty:
    raise ValueError("发现同一省份存在多条不同记录，请先核对数据。")

# 4) 补值之前先记录「哪些是估算的」
df["GDP是否估算"] = df["GDP"].isna()

# 5) 中位数补全 GDP 缺失值；人口缺失的行无法计算人均，直接删除
df["GDP"] = df["GDP"].fillna(df["GDP"].median())
df = df.dropna(subset=["人口"])
```

几个设计考虑：

- **先标记、后填补**：`GDP是否估算` 在 `fillna` 之前生成，否则补完就再也分不清哪个是真实值。
- **只删「完全重复」**：同一省份不同年份、不同口径的数据不能直接删，应先加年份/口径字段。
- **不自动合并**：同省多条不同记录时选择报错，把判断权交给人。
- **中位数而非均值**：中位数受极端值影响小，适合课堂演示；它不是任何官方补报方法。
- **`pd.to_numeric(..., errors="coerce")`**：把无法解析的值变成 `NaN` 而不是直接崩，便于统一处理。

---

## 7. 指标计算

```python
# 数值越大排名越靠前；method="min" 让并列值同名次，后面跳号
df["GDP排名"] = df["GDP"].rank(ascending=False, method="min").astype(int)

# 人均 GDP（万元/人）
df["人均GDP"] = df["GDP"] / df["人口"]

# 该省占「本样本」GDP 总量的比例（%）
df["GDP占比"] = df["GDP"] / df["GDP"].sum() * 100
```

注意三点：

1. `rank()` 默认是「小的排第 1」，求「第一名」必须写 `ascending=False`。
2. `method="min"` 下并列会占同一名次，下一名跳号。例如两个省并列第 5，下一个省是第 7。
3. `GDP占比` 的分母只是**当前 CSV 里的样本总和**，样本不全时不等于全国占比。

---

## 8. 输出文件

运行一次 `main.py` 后，会生成：

| 文件 | 内容 |
| --- | --- |
| `data/processed/cleaned_gdp.csv` | 清洗后的数据，含 `GDP是否估算` 标记列 |
| `data/processed/gdp_analysis.csv` | 分析结果，含排名、人均 GDP、占比 |
| `output/charts/gdp_ranking.png` | 各省 GDP 总量排名（横向柱状图） |
| `output/charts/gdp_per_capita.png` | 各省人均 GDP 对比（横向柱状图） |
| `output/charts/gdp_population.png` | GDP 与人口的关系（散点图） |
| `output/reports/GDP_analysis_report.md` | Markdown 分析报告，内含三张图的相对链接 |

报告用相对路径 `../charts/xxx.png` 引用图片，所以在 GitHub 或 PyCharm 的 Markdown 预览里能直接显示。

---

## 9. 一次实际运行的结果

用项目内的 `data/raw/china_gdp.csv`（11 行数据，刻意含 1 条重复记录和 1 个缺失 GDP）运行：

- 原始 **11 行** → 清洗后 **10 行**
  - 删除重复的广东 1 条
  - 湖南 GDP 缺失，用中位数 **65000** 补全，并标记 `GDP是否估算 = True`
- GDP 总量 **801000 亿元**，平均 **80100 亿元**
- GDP 排名第一：广东（135000 亿元）；最后一名：安徽（47000 亿元）
- 人均 GDP 最高：江苏 **15.29 万元/人**；广东总量第一但人均只有 10.63
- 因为补全值 65000 恰好等于四川的 GDP，湖南与四川**并列第 5**，下一名直接跳到第 7

最后一条特别值得留意：中位数填补会凭空造出一个「中等水平」的省，可能制造并列名次——写报告时要交代清楚，这也是保留 `GDP是否估算` 列的意义。

---

## 10. 结果解读与限制

- 中位数填补是演示方法，`GDP是否估算 = True` 的记录必须与真实观测值区分开。
- 样本只有 10 个省，且为教学数据，不足以支撑宏观结论。
- 人均 GDP 只反映产出与人口的关系，不能替代居民收入、生活成本或发展质量等指标。
- 不同统计年份、行政范围、核算口径（当年价 / 不变价）、人口口径（常住 / 户籍）不能直接混合比较。
- 图表只描述当前输入样本，不能证明因果关系。
- 使用公开数据时，应记录来源、发布日期、统计年份、单位和处理规则。

---

## 11. 发布到 GitHub

1. 在 GitHub 新建空仓库，例如 `China_GDP_Analysis`（不要勾选自动生成 README）
2. 项目根目录已经内置 `.gitignore`，它会自动排除虚拟环境、缓存、PyCharm 配置和运行产物
3. 在项目根目录执行：

```powershell
git init
git add -A
git commit -m "init: 中国各省 GDP 数据分析（教学项目）"
git remote add origin https://github.com/<你的用户名>/China_GDP_Analysis.git
git branch -M main
git push -u origin main
```

也可以用 PyCharm：**Git → GitHub → Share Project on GitHub**。

### `.gitignore` 保护了什么

会提交的只有源码和原始数据：

```text
.gitignore
README.md
main.py
requirements.txt
data/raw/china_gdp.csv
data/processed/.gitkeep
output/charts/.gitkeep
output/reports/.gitkeep
```

被排除的：`.venv/`（几百 MB）、`.idea/`、`*.iml`、`__pycache__/`、`*.pyc`、`Thumbs.db`，以及 `data/processed/`、`output/charts/`、`output/reports/` 里运行生成的文件（保留 `.gitkeep` 让空目录存在）。

这样别人克隆仓库后，`pip install -r requirements.txt` 再跑一次 `python main.py`，就能得到和你一样的图表和报告。

> 如果想让图表和报告也作为成果示例提交，用 `git add -f output/charts/*.png` 强制加入即可。


---

## 12. 下一步可以练什么

- 给数据加 `年份` 字段，做跨年份趋势分析
- 用 `groupby` 按区域（东/中/西部）分组聚合
- 把 `clean_data()`、`analyze_data()` 拆成独立模块，并为关键计算写测试
- 报告里补上数据来源、样本量、估算记录数和运行耗时
- 用命令行参数指定输入文件和输出目录，例如 `python main.py --input data/raw/xxx.csv`
- 换成真实、可追溯的公开统计数据（国家统计局或各省统计年鉴），并记录统计口径

---

## 附录：`_archive/` 里的学习过程脚本

这些是项目一步步长起来的中间版本，**只作存档，不参与运行**（`main.py` 不 import 它们）。

> ⚠️ 注意：其中部分脚本引用的是旧文件名 `data/raw/gdp_data.csv`（现已改名为 `china_gdp.csv`），照原样运行会报 `FileNotFoundError`。

| 文件 | 阶段 | 说明 |
| --- | --- | --- |
| `数据经济.py` | 第 1 天 | 最初版本：字典造数据 → 人均 GDP → 排名 → 排序 → `describe` + 变异系数 |
| `数据经济_新手版.py` | 第 1 天 | 同一份代码的注释加强版，每一步都有 `print` |
| `day2_csv.py` | 第 2 天 | `read_csv`、`head` / `shape` / `dtypes` / `info`、缺失值与重复值检查 |
| `day3_cleaning.py` | 第 3 天 | 清洗入门：去重、缺失值处理 |
| `data_cleaning.py` | 第 3–4 天 | 把清洗逻辑整理成函数 |
| `data_analysis.py` | 第 4 天 | 读取清洗结果，计算排名与人均 GDP |
| `visualization.py` | 第 4 天 | matplotlib + seaborn 出图、中文字体配置 |

这些逻辑后来都被合并进了 `main.py` 的五个阶段函数。保留它们的意义是能对比「同一个需求，代码是怎么从单文件长成工程结构的」；不需要的话，直接删除整个 `_archive/` 目录即可，不影响运行。
