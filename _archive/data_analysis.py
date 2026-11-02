import pandas as pd

# 读取清洗后的数据
df = pd.read_csv(
    "data/processed/cleaned_gdp.csv"
)

print("清洗后的数据：")
print(df)
# GDP 排名
df["GDP排名"] = df["GDP"].rank(
    ascending=False,
    method="min"
)

# 排序
df = df.sort_values(
    by="GDP",
    ascending=False
)

print("\n各省 GDP 排名：")
print(df[["省份", "GDP", "GDP排名"]])
# 计算人均 GDP
df["人均GDP"] = df["GDP"] / df["人口"]

print("\n人均 GDP：")
print(df[["省份", "人均GDP"]])
# 计算 GDP 总量
total_gdp = df["GDP"].sum()

# 计算各省 GDP 占比
df["GDP占比"] = (
    df["GDP"] / total_gdp * 100
)

print("\nGDP 总量：")
print(total_gdp)

print("\n各省 GDP 占比：")
print(df[["省份", "GDP占比"]])
# 保存分析结果
df.to_csv(
    "data/processed/gdp_analysis.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n数据分析完成！")
print("分析结果已保存。")