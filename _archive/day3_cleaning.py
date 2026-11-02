import pandas as pd

# 1. 读取数据
df = pd.read_csv("data/raw/gdp_data.csv")

# 2. 检查数据
print("原始数据规模：", df.shape)
print("缺失值：")
print(df.isnull().sum())

# 3. 删除完全重复的记录
df = df.drop_duplicates()

# 4. 删除关键指标缺失的记录
df = df.dropna(subset=["GDP", "人口"])

# 5. 检查异常值
df = df[
    (df["GDP"] > 0) &
    (df["人口"] > 0)
].copy()

# 6. 重新设置索引
df = df.reset_index(drop=True)

# 7. 计算人均GDP
df["人均GDP"] = (
    df["GDP"] / df["人口"] * 10000
)

# 8. 计算排名
df["GDP排名"] = df["GDP"].rank(
    ascending=False,
    method="min"
)

df["人均GDP排名"] = df["人均GDP"].rank(
    ascending=False,
    method="min"
)

# 9. 按GDP排序
df = df.sort_values(
    "GDP",
    ascending=False
).reset_index(drop=True)

# 10. 保存清洗结果
df.to_csv(
    "data/processed/gdp_cleaned.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n最终清洗结果：")
print(df.to_string(index=False))

# 按省份GDP计算总体统计指标
print("GDP平均值：")
print(df["GDP"].mean())

print("\nGDP中位数：")
print(df["GDP"].median())

print("\nGDP标准差：")
print(df["GDP"].std())

print("\nGDP最高的省份：")
print(df.loc[df["GDP"].idxmax(), "省份"])