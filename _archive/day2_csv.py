import pandas as pd

# 读取CSV
df = pd.read_csv("data/raw/gdp_data.csv")

# 查看前五行
print("数据预览：")
print(df.head())

# 查看数据规模
print("\n数据规模：")
print(df.shape)

# 查看数据类型
print("\n数据类型：")
print(df.dtypes)

# 查看数据基本信息
print("\n数据基本信息：")
df.info()
# 检查缺失值
print("\n缺失值：")
print(df.isnull().sum())

# 检查重复记录
print("\n重复记录数量：")
print(df.duplicated().sum())

# 检查省份数量
print("\n省份数量：")
print(df["省份"].nunique())

# GDP从高到低排序
df = df.sort_values(
    by="GDP",
    ascending=False
)

print("\n排序后的数据：")
print(df)