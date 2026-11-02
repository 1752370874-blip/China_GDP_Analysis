import pandas as pd

# 第一步：把数据装进字典。键 = 列名，列表 = 这一列的内容
data = {
    "省份": ["广东", "江苏", "湖北", "四川", "浙江"],
    "GDP": [135000, 130000, 60000, 65000, 90000],
    "人口": [12700, 8500, 5800, 8300, 6700],
}

# 第二步：变成一张表
df = pd.DataFrame(data)
print("原始数据：")
print(df)

# 第三步：新加一列「人均GDP」，保留两位小数
# 亿元 ÷ 万人 = 万元/人，所以还要 ×10000 才变成 元/人
df["人均GDP"] = (df["GDP"] / df["人口"] * 10000).round(2)
print("\n加上人均GDP：")
print(df)

# 第四步：算名次（1 = 第一名）。ascending=False 表示"数大的排前面"
df["GDP排名"] = df["GDP"].rank(ascending=False, method="min").astype(int)
df["人均GDP排名"] = df["人均GDP"].rank(ascending=False, method="min").astype(int)
print("\n加上两个排名：")
print(df)

# 第五步：按 GDP 从高到低排序，并让行号重新从 0 开始
df = df.sort_values("GDP", ascending=False, ignore_index=True)
print("\n按 GDP 从高到低排序：")
print(df)

# 第六步：看一眼 GDP 的分布
print("\nGDP 的描述性统计：")
print(df["GDP"].describe())

# 第七步：变异系数 = 标准差 ÷ 均值，用来衡量"差距大不大"
cv = df["GDP"].std() / df["GDP"].mean()
print("\nGDP 变异系数：", round(cv, 4))
