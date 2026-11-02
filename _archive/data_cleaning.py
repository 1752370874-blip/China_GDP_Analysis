import pandas as pd
import numpy as np

# 1. 读取数据
df = pd.read_csv("data/raw/china_gdp.csv")

# 2. 查看前五行
print("原始数据：")
print(df.head())

# 3. 查看数据基本信息
print("\n数据基本信息：")
print(df.info())

# 4. 查看数据统计信息
print("\n数据统计信息：")
print(df.describe())

# 5. 查看数据形状
print("\n数据行列数：")
print(df.shape)

# 6. 缺失值统计
print("\n缺失值统计：")
print(df.isnull().sum())


# 7. 检查重复记录
print("\n重复记录：")
print(df[df.duplicated()])


# 8. 查看缺失数据
print("\n缺失数据：")
print(df[df.isnull().any(axis=1)])


# 9. 删除重复记录
df = df.drop_duplicates()


# 10. 处理缺失值
df["GDP"] = df["GDP"].fillna(df["GDP"].median())


# 11. 删除无效数据
df = df.dropna(subset=["省份", "人口"])


# 12. 检查数据类型
df["GDP"] = pd.to_numeric(df["GDP"], errors="coerce")
df["人口"] = pd.to_numeric(df["人口"], errors="coerce")

# 删除无法转换为有效数字的记录
df = df.dropna(subset=["GDP", "人口"])

# 13. 保存清洗结果
df.to_csv(
    "data/processed/cleaned_gdp.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n清洗后的数据：")
print(df)