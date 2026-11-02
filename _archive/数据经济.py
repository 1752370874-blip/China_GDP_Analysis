import numpy as np
import pandas as pd

# 1. 创建模拟数据
data = {
    "省份": ["广东", "江苏", "湖北", "四川", "浙江"],
    "GDP": [135000, 130000, 60000, 65000, 90000],
    "人口": [12700, 8500, 5800, 8300, 6700]
}

df = pd.DataFrame(data)

# 2. 计算人均GDP
df["人均GDP"] = df["GDP"] / df["人口"] * 10000

# 3. 计算GDP排名
df["GDP排名"] = df["GDP"].rank(
    ascending=False,
    method="min"
)

# 4. 计算人均GDP排名
df["人均GDP排名"] = df["人均GDP"].rank(
    ascending=False,
    method="min"
)

# 5. 按GDP从高到低排序
df = df.sort_values(
    by="GDP",
    ascending=False
)

# 6. 输出结果
print("\n各省经济数据：")
print(df.to_string(index=False))

# 7. 描述性统计
print("\nGDP描述性统计：")
print(df["GDP"].describe())

# 8. 计算GDP变异系数
cv = df["GDP"].std() / df["GDP"].mean()

print("\nGDP变异系数：", cv)