
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from datetime import datetime


# ==================================================
# 1. 项目路径配置
# ==================================================

# 获取当前 Python 文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 设置数据文件路径
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# 设置输出文件路径
CHART_DIR = os.path.join(BASE_DIR, "output", "charts")
REPORT_DIR = os.path.join(BASE_DIR, "output", "reports")

RAW_FILE = os.path.join(RAW_DIR, "china_gdp.csv")

# 自动创建文件夹
for folder in [
    RAW_DIR,
    PROCESSED_DIR,
    CHART_DIR,
    REPORT_DIR
]:
    os.makedirs(folder, exist_ok=True)


# ==================================================
# 2. 中文字体配置
# ==================================================

def setup_chinese_font():

    font_candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc"
    ]

    for font_path in font_candidates:

        if os.path.exists(font_path):

            font = fm.FontProperties(
                fname=font_path
            )

            plt.rcParams["axes.unicode_minus"] = False

            print("中文字体加载成功：", font.get_name())

            return font

    raise RuntimeError(
        "没有找到中文字体，请检查系统字体文件。"
    )


# ==================================================
# 3. 创建教学数据
# ==================================================

def create_sample_data():

    if os.path.exists(RAW_FILE):

        print("发现原始数据文件，直接读取。")

        return

    print("没有找到原始数据，正在创建教学数据...")

    data = {
        "省份": [
            "广东", "江苏", "湖北", "四川",
            "浙江", "河南", "山东", "广东",
            "湖南", "安徽", "福建"
        ],

        "GDP": [
            135000, 130000, 60000, 65000,
            90000, 59000, 95000, 135000,
            np.nan, 47000, 55000
        ],

        "人口": [
            12700, 8500, 5800, 8300,
            6600, 9800, 10100, 12700,
            6600, 6100, 4200
        ]
    }

    df = pd.DataFrame(data)

    df.to_csv(
        RAW_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("教学数据创建完成！")


# ==================================================
# 4. 数据读取与初步检查
# ==================================================

def load_data():

    print("\n" + "=" * 50)
    print("第一阶段：数据读取")
    print("=" * 50)

    df = pd.read_csv(RAW_FILE)

    print("\n原始数据：")
    print(df)

    print("\n数据基本信息：")
    df.info()

    print("\n数据统计信息：")
    print(df.describe())

    print("\n数据行列数：")
    print(df.shape)

    return df


# ==================================================
# 5. 数据清洗
# ==================================================

def clean_data(df):

    print("\n" + "=" * 50)
    print("第二阶段：数据清洗")
    print("=" * 50)

    # 复制数据，避免修改原始数据
    df = df.copy()

    # 检查必要字段
    required_columns = ["省份", "GDP", "人口"]

    if not all(
        column in df.columns
        for column in required_columns
    ):
        raise ValueError("原始数据缺少必要字段！")

    # 统一省份名称格式
    df["省份"] = df["省份"].astype("string").str.strip()

    # 将 GDP 和人口转换为数字
    df["GDP"] = pd.to_numeric(
        df["GDP"],
        errors="coerce"
    )

    df["人口"] = pd.to_numeric(
        df["人口"],
        errors="coerce"
    )

    # 删除省份名称缺失的记录
    df = df.dropna(subset=["省份"])

    # 删除空省份名称
    df = df[df["省份"] != ""]

    # 删除无效的 GDP 和人口数值
    df.loc[df["GDP"] < 0, "GDP"] = np.nan
    df.loc[df["人口"] <= 0, "人口"] = np.nan

    # 检查缺失值
    print("\n缺失值统计：")
    print(df.isnull().sum())

    # 检查重复记录
    print("\n重复记录：")
    print(df[df.duplicated()])

    # 删除完全重复的数据
    df = df.drop_duplicates()

    # 如果同一省份存在多条不同记录，暂不擅自合并
    duplicated_provinces = df[
        df.duplicated(subset=["省份"], keep=False)
    ]

    if not duplicated_provinces.empty:
        raise ValueError(
            "发现同一省份存在多条不同记录，请先核对数据。"
        )

    # 记录 GDP 是否经过估算
    df["GDP是否估算"] = df["GDP"].isna()

    # 使用中位数填补 GDP 缺失值（仅供教学演示）
    if df["GDP"].isna().any():

        median_gdp = df["GDP"].median()

        if pd.isna(median_gdp):
            raise ValueError("GDP 全部缺失，无法计算中位数。")

        df["GDP"] = df["GDP"].fillna(median_gdp)

        print("\n已使用 GDP 中位数填补缺失值：", median_gdp)

    # 删除人口缺失记录
    df = df.dropna(subset=["人口"])

    # 再次检查数据
    print("\n清洗后的数据：")
    print(df)

    # 保存清洗结果
    clean_file = os.path.join(
        PROCESSED_DIR,
        "cleaned_gdp.csv"
    )

    df.to_csv(
        clean_file,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n数据清洗完成！")
    print("保存位置：", clean_file)

    return df


# ==================================================
# 6. GDP 数据分析
# ==================================================

def analyze_data(df):

    print("\n" + "=" * 50)
    print("第三阶段：GDP 数据分析")
    print("=" * 50)

    df = df.copy()

    # GDP 排名
    df["GDP排名"] = df["GDP"].rank(
        ascending=False,
        method="min"
    ).astype(int)

    # 人均 GDP
    # GDP 单位：亿元
    # 人口单位：万人
    # 结果单位：万元/人
    df["人均GDP"] = (
        df["GDP"] / df["人口"]
    )

    # GDP 总量
    total_gdp = df["GDP"].sum()

    # GDP 占比
    df["GDP占比"] = (
        df["GDP"] / total_gdp * 100
    )

    # 按 GDP 排序
    df = df.sort_values(
        by=["GDP", "省份"],
        ascending=[False, True]
    )

    # 计算统计指标
    average_gdp = df["GDP"].mean()

    max_gdp = df["GDP"].max()

    min_gdp = df["GDP"].min()

    average_per_capita = df["人均GDP"].mean()

    # 输出结果
    print("\n各省 GDP 排名：")

    print(
        df[["省份", "GDP", "GDP排名"]].to_string(
            index=False
        )
    )

    print("\n各省人均 GDP：")

    print(
        df[["省份", "人均GDP"]].to_string(
            index=False
        )
    )

    print("\n各省 GDP 占比：")

    print(
        df[["省份", "GDP占比"]].to_string(
            index=False
        )
    )

    print("\nGDP 总量：", total_gdp)

    print("平均 GDP：", average_gdp)

    print("最高 GDP：", max_gdp)

    print("最低 GDP：", min_gdp)

    print("平均人均 GDP：", average_per_capita)

    # 保存分析结果
    analysis_file = os.path.join(
        PROCESSED_DIR,
        "gdp_analysis.csv"
    )

    df.to_csv(
        analysis_file,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n分析结果已保存！")

    statistics = {
        "total_gdp": total_gdp,
        "average_gdp": average_gdp,
        "max_gdp": max_gdp,
        "min_gdp": min_gdp,
        "average_per_capita": average_per_capita
    }

    return df, statistics


# ==================================================
# 7. 数据可视化
# ==================================================

def create_charts(df, font):

    print("\n" + "=" * 50)
    print("第四阶段：数据可视化")
    print("=" * 50)

    sns.set_theme(style="whitegrid")

    plt.rcParams["axes.unicode_minus"] = False

    # ----------------------------------------------
    # 图表一：GDP 排名柱状图
    # ----------------------------------------------

    df_gdp = df.sort_values(
        by="GDP",
        ascending=True
    )

    fig, ax = plt.subplots(
        figsize=(12, 7)
    )

    ax.barh(
        df_gdp["省份"],
        df_gdp["GDP"],
        color="steelblue"
    )

    ax.set_title(
        "中国各省 GDP 排名",
        fontsize=18,
        fontproperties=font
    )

    ax.set_xlabel(
        "GDP（亿元）",
        fontproperties=font
    )

    ax.set_ylabel(
        "省份",
        fontproperties=font
    )

    for label in ax.get_xticklabels():
        label.set_fontproperties(font)

    for label in ax.get_yticklabels():
        label.set_fontproperties(font)

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            CHART_DIR,
            "gdp_ranking.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    print("GDP 排名图生成成功！")

    # ----------------------------------------------
    # 图表二：人均 GDP 对比图
    # ----------------------------------------------

    df_capita = df.sort_values(
        by="人均GDP",
        ascending=True
    )

    fig, ax = plt.subplots(
        figsize=(12, 7)
    )

    ax.barh(
        df_capita["省份"],
        df_capita["人均GDP"],
        color="orange"
    )

    ax.set_title(
        "中国各省人均 GDP 对比",
        fontsize=18,
        fontproperties=font
    )

    ax.set_xlabel(
        "人均 GDP（万元/人）",
        fontproperties=font
    )

    ax.set_ylabel(
        "省份",
        fontproperties=font
    )

    for label in ax.get_xticklabels():
        label.set_fontproperties(font)

    for label in ax.get_yticklabels():
        label.set_fontproperties(font)

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            CHART_DIR,
            "gdp_per_capita.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    print("人均 GDP 图生成成功！")

    # ----------------------------------------------
    # 图表三：GDP 与人口关系散点图
    # ----------------------------------------------

    fig, ax = plt.subplots(
        figsize=(10, 7)
    )

    sns.scatterplot(
        data=df,
        x="人口",
        y="GDP",
        s=120,
        ax=ax
    )

    ax.set_title(
        "各省 GDP 与人口关系",
        fontsize=18,
        fontproperties=font
    )

    ax.set_xlabel(
        "人口（万人）",
        fontproperties=font
    )

    ax.set_ylabel(
        "GDP（亿元）",
        fontproperties=font
    )

    for label in ax.get_xticklabels():
        label.set_fontproperties(font)

    for label in ax.get_yticklabels():
        label.set_fontproperties(font)

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            CHART_DIR,
            "gdp_population.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    print("GDP 与人口关系图生成成功！")

    print("\n所有图表生成完成！")


# ==================================================
# 8. 自动生成 Markdown 分析报告
# ==================================================

def generate_report(df, statistics):

    print("\n" + "=" * 50)
    print("第五阶段：生成分析报告")
    print("=" * 50)

    # 找出 GDP 排名第一的省份
    top_province = df.iloc[0]

    # 找出人均 GDP 最高的省份
    top_per_capita = df.loc[
        df["人均GDP"].idxmax()
    ]

    # 找出 GDP 排名最后的省份
    bottom_province = df.loc[
        df["GDP"].idxmin()
    ]

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    report = f"""
# 中国各省 GDP 数据分析报告

## 一、项目简介

本项目使用 Python 对中国部分省份的 GDP 和人口数据进行处理、统计和可视化。

报告生成时间：{current_time}

注意：当前教学数据为模拟数据，仅用于学习 Python 数据分析方法，
不代表真实年度统计结果。

## 二、数据基本情况

- 分析省份数量：{len(df)}
- GDP 总量：{statistics['total_gdp']:.2f} 亿元
- 平均 GDP：{statistics['average_gdp']:.2f} 亿元
- 最高 GDP：{statistics['max_gdp']:.2f} 亿元
- 最低 GDP：{statistics['min_gdp']:.2f} 亿元
- 平均人均 GDP：{statistics['average_per_capita']:.2f} 万元/人

## 三、GDP 排名分析

GDP 排名第一的省份：{top_province['省份']}

GDP 数值：{top_province['GDP']:.2f} 亿元

GDP 排名最后的省份：{bottom_province['省份']}

GDP 数值：{bottom_province['GDP']:.2f} 亿元

## 四、人均 GDP 分析

人均 GDP 最高的省份：{top_per_capita['省份']}

人均 GDP：{top_per_capita['人均GDP']:.2f} 万元/人

## 五、图表展示

### 1. 各省 GDP 排名

![GDP排名](../charts/gdp_ranking.png)

### 2. 各省人均 GDP 对比

![人均GDP](../charts/gdp_per_capita.png)

### 3. GDP 与人口关系

![GDP与人口](../charts/gdp_population.png)

## 六、数据分析结论

1. 不同省份的 GDP 总量存在差异。
2. GDP 总量和人均 GDP 是两个不同的统计指标。
3. 人口规模与 GDP 总量之间可以进行相关性探索。
4. 进一步研究需要使用同一统计年度的真实官方数据。

## 七、项目技术

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn

## 八、数据局限性

本报告使用的教学数据为模拟数据。
其中缺失 GDP 使用中位数填补，仅用于演示数据清洗操作。

正式研究应使用同一年度、统一口径的官方统计数据，
并记录数据来源、单位和估算情况。
"""

    report_file = os.path.join(
        REPORT_DIR,
        "GDP_analysis_report.md"
    )

    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report)

    print("分析报告生成成功！")
    print("报告位置：", report_file)


# ==================================================
# 9. 主程序：一键运行所有功能
# ==================================================

def main():

    print("\n")
    print("=" * 60)
    print("       中国各省 GDP 数据分析系统")
    print("=" * 60)

    try:

        # 第一步：加载中文字体
        font = setup_chinese_font()

        # 第二步：创建教学数据（若不存在）
        create_sample_data()

        # 第三步：读取原始数据
        df = load_data()

        # 第四步：数据清洗
        clean_df = clean_data(df)

        # 第五步：数据分析
        analysis_df, statistics = analyze_data(
            clean_df
        )

        # 第六步：生成图表
        create_charts(
            analysis_df,
            font
        )

        # 第七步：生成报告
        generate_report(
            analysis_df,
            statistics
        )

        print("\n" + "=" * 60)
        print("       所有数据分析任务执行完成！")
        print("=" * 60)

        print("\n结果保存位置：")

        print("清洗数据：", PROCESSED_DIR)

        print("图表文件：", CHART_DIR)

        print("分析报告：", REPORT_DIR)

    except Exception as error:

        print("\n程序运行出现错误！")

        print("错误原因：", error)

        raise


# ==================================================
# 10. 程序入口
# ==================================================

if __name__ == "__main__":

    main()
