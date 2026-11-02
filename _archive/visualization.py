

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm


# =========================
# 1. 基础配置
# =========================

# 设置中文字体路径
font_path = r"C:\Windows\Fonts\msyh.ttc"

# 检查字体文件
if not os.path.exists(font_path):
    raise FileNotFoundError("没有找到微软雅黑字体文件！")

# 加载字体
my_font = fm.FontProperties(fname=font_path)

# 设置图表风格
sns.set_theme(style="whitegrid")

# 设置负号正常显示
plt.rcParams["axes.unicode_minus"] = False

print("当前使用字体：", my_font.get_name())


# =========================
# 2. 创建输出文件夹
# =========================

os.makedirs("output/charts", exist_ok=True)


# =========================
# 3. 读取数据
# =========================

df = pd.read_csv(
    "data/processed/gdp_analysis.csv"
)

print("数据读取成功！")
print(df.head())


# =========================
# 4. GDP 排名柱状图
# =========================

df_gdp = df.sort_values(
    by="GDP",
    ascending=True
)

plt.figure(figsize=(12, 7))

plt.barh(
    df_gdp["省份"],
    df_gdp["GDP"],
    color="steelblue"
)

plt.title(
    "中国各省 GDP 排名",
    fontsize=18,
    fontproperties=my_font
)

plt.xlabel(
    "GDP（亿元）",
    fontsize=12,
    fontproperties=my_font
)

plt.ylabel(
    "省份",
    fontsize=12,
    fontproperties=my_font
)

plt.xticks(fontproperties=my_font)
plt.yticks(fontproperties=my_font)

plt.tight_layout()

plt.savefig(
    "output/charts/gdp_ranking.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

plt.close()


# =========================
# 5. 人均 GDP 对比图
# =========================

df_capita = df.sort_values(
    by="人均GDP",
    ascending=True
)

plt.figure(figsize=(12, 7))

plt.barh(
    df_capita["省份"],
    df_capita["人均GDP"],
    color="orange"
)

plt.title(
    "中国各省人均 GDP 对比",
    fontsize=18,
    fontproperties=my_font
)

plt.xlabel(
    "人均 GDP（万元/人）",
    fontsize=12,
    fontproperties=my_font
)

plt.ylabel(
    "省份",
    fontsize=12,
    fontproperties=my_font
)

plt.xticks(fontproperties=my_font)
plt.yticks(fontproperties=my_font)

plt.tight_layout()

plt.savefig(
    "output/charts/gdp_per_capita.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

plt.close()


# =========================
# 6. GDP 与人口关系散点图
# =========================

plt.figure(figsize=(10, 7))

sns.scatterplot(
    data=df,
    x="人口",
    y="GDP",
    s=120
)

plt.title(
    "各省 GDP 与人口关系",
    fontsize=18,
    fontproperties=my_font
)

plt.xlabel(
    "人口（万人）",
    fontsize=12,
    fontproperties=my_font
)

plt.ylabel(
    "GDP（亿元）",
    fontsize=12,
    fontproperties=my_font
)

plt.xticks(fontproperties=my_font)
plt.yticks(fontproperties=my_font)

plt.tight_layout()

plt.savefig(
    "output/charts/gdp_population.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

plt.close()


# =========================
# 7. 完成提示
# =========================

print("\n所有图表生成完成！")

print("生成的文件：")
print("1. gdp_ranking.png")
print("2. gdp_per_capita.png")
print("3. gdp_population.png")