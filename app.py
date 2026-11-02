# ==========================================================
# 中国各省 GDP 交互式数据分析平台
# China GDP Analysis Dashboard
# 技术：Streamlit + Pandas + Plotly
# ==========================================================

import json

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ==========================================================
# 1. 页面基本配置
# ==========================================================

st.set_page_config(
    page_title="中国各省 GDP 数据分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# 2. 项目路径配置
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "gdp_analysis.csv"
)

# 中国省级行政区边界
# 来源：阿里云 DataV.GeoAtlas（100000_full.json），GCJ-02 坐标系，
# 仅用于省级区域着色展示，不作为测绘或导航用途。
MAP_FILE = (
    BASE_DIR
    / "maps"
    / "china_provinces.geojson"
)

# ==========================================================
# 3. 网页 CSS 样式
# ==========================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 32px;
        font-weight: bold;
        color: #2563EB;
    }
    .sub-title {
        color: #64748b;
        font-size: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================================
# 4. 常量：区域划分与数据状态
# ==========================================================

# 按国家统计局的四大区域划分（省级行政区）
REGION_MAP = {
    "东部": ["北京", "天津", "河北", "上海", "江苏", "浙江", "福建", "山东", "广东", "海南"],
    "中部": ["山西", "安徽", "江西", "河南", "湖北", "湖南"],
    "西部": ["内蒙古", "广西", "重庆", "四川", "贵州", "云南", "西藏",
             "陕西", "甘肃", "青海", "宁夏", "新疆"],
    "东北": ["辽宁", "吉林", "黑龙江"],
}

PROVINCE_TO_REGION = {
    province: region
    for region, provinces in REGION_MAP.items()
    for province in provinces
}

# 把 True / False 换成普通人看得懂的词
STATUS_MAP = {
    True: "估算数据",
    False: "原始数据",
}

STATUS_COLOR = {
    "原始数据": "#2563EB",
    "估算数据": "#F59E0B",
}

# ==========================================================
# 4.1 地图工具函数
# ==========================================================


def normalize_province(name) -> str:
    """把「广东省 / 广西壮族自治区」统一成「广东 / 广西」。"""
    if pd.isna(name):
        return ""

    name = str(name).strip()

    suffixes = [
        "壮族自治区",
        "回族自治区",
        "维吾尔自治区",
        "特别行政区",
        "自治区",
        "省",
        "市",
    ]

    for suffix in suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]

    return name


@st.cache_data(show_spinner=False)
def load_geojson(file_path: str) -> dict:
    """读取 GeoJSON，并给每个 feature 补一个 map_key，用于和 GDP 数据匹配。"""
    with open(file_path, "r", encoding="utf-8") as file:
        geojson = json.load(file)

    kept_features = []

    for feature in geojson["features"]:
        props = feature.get("properties", {})
        map_key = normalize_province(props.get("name", ""))

        # 没有名称的要素（例如九段线）不参与省份匹配
        if not map_key:
            continue

        props["map_key"] = map_key
        kept_features.append(feature)

    geojson["features"] = kept_features
    return geojson


# ==========================================================
# 5. 读取数据
# ==========================================================


@st.cache_data(show_spinner="正在读取数据…")
def load_data(path: Path) -> pd.DataFrame:
    """读取 main.py 生成的分析结果，并补充区域、数据状态两列。"""
    df = pd.read_csv(path, encoding="utf-8-sig")

    # 数据状态：True / False → 估算数据 / 原始数据
    df["数据状态"] = df["GDP是否估算"].map(STATUS_MAP)

    # 区域：省份 → 东部 / 中部 / 西部 / 东北
    df["区域"] = df["省份"].map(PROVINCE_TO_REGION).fillna("其他")

    return df


if not DATA_FILE.exists():
    st.error(
        "没有找到分析结果文件：`data/processed/gdp_analysis.csv`\n\n"
        "请先在项目根目录运行一次 `python main.py`，生成该文件后再刷新本页面。"
    )
    st.stop()

df = load_data(DATA_FILE)

# ==========================================================
# 6. 页面标题
# ==========================================================

st.markdown('<div class="main-title">📊 中国各省 GDP 数据分析平台</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">数据来源：main.py 生成的分析结果（教学示例数据，非官方统计）</div>',
    unsafe_allow_html=True
)
st.divider()

# ==========================================================
# 7. 侧边栏：筛选条件
# ==========================================================

st.sidebar.header("筛选条件")

all_provinces = sorted(df["省份"].unique().tolist())
selected = st.sidebar.multiselect(
    "选择省份（可多选）",
    options=all_provinces,
    default=all_provinces
)

all_regions = [r for r in REGION_MAP if r in set(df["区域"])]
selected_regions = st.sidebar.multiselect(
    "选择区域（可多选）",
    options=all_regions,
    default=all_regions,
    help="按国家统计局四大区域划分：东部、中部、西部、东北。"
)

gdp_min = int(df["GDP"].min())
gdp_max = int(df["GDP"].max())
gdp_range = st.sidebar.slider(
    "GDP 区间（亿元）",
    min_value=gdp_min,
    max_value=gdp_max,
    value=(gdp_min, gdp_max),
    step=1000
)

include_estimated = st.sidebar.checkbox(
    "包含 GDP 估算值（中位数填补）",
    value=True,
    help="取消勾选可排除 GDP 由中位数估算出来的省份，只看真实观测值。"
)

top_n_only = st.sidebar.checkbox(
    "只看 GDP 前 10 名",
    value=False
)

st.sidebar.divider()
st.sidebar.caption("提示：图表可鼠标悬停查看数值，也可用工具栏下载为图片。")

# ==========================================================
# 8. 应用筛选
# ==========================================================

view = df[
    df["省份"].isin(selected)
    & df["区域"].isin(selected_regions)
    & df["GDP"].between(gdp_range[0], gdp_range[1])
].copy()

if not include_estimated:
    view = view[view["GDP是否估算"] == False]

if top_n_only:
    view = view.nlargest(10, "GDP")

if view.empty:
    st.warning("当前筛选条件下没有数据，请在左侧调整省份、区域或 GDP 区间。")
    st.stop()

# ==========================================================
# 9. 关键指标卡片
# ==========================================================

total_gdp = view["GDP"].sum()
avg_gdp = view["GDP"].mean()
avg_per_capita = view["人均GDP"].mean()
top_province = view.loc[view["GDP"].idxmax(), "省份"]
estimated_count = int(view["GDP是否估算"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("省份数量", f"{len(view)} 个")
c2.metric("GDP 总量", f"{total_gdp:,.0f} 亿元")
c3.metric("平均 GDP", f"{avg_gdp:,.0f} 亿元")
c4.metric("GDP 第一", top_province)

if estimated_count:
    st.info(
        f"当前视图中有 {estimated_count} 个省份的 GDP 为中位数估算值"
        f"（标记列 `GDP是否估算 = True`），计算排名和统计时请注意这一点。"
    )

st.divider()

# ==========================================================
# 10. 图表区
# ==========================================================

left, right = st.columns(2)

with left:
    st.subheader("各省 GDP 总量排名")

    # 先按 GDP 升序排好（横向柱状图：靠下的数值小、靠上的数值大）
    gdp_chart_df = view.sort_values(by="GDP", ascending=True)

    fig_gdp = px.bar(
        gdp_chart_df,
        x="GDP",
        y="省份",
        orientation="h",
        color="数据状态",
        color_discrete_map=STATUS_COLOR,
        text="GDP",
        labels={"GDP": "GDP（亿元）", "省份": "", "数据状态": "数据状态"},
    )

    fig_gdp.update_traces(texttemplate="%{text:,.0f}", textposition="outside")

    # 关键：显式指定纵轴顺序，避免「按颜色分组」把排序打乱
    fig_gdp.update_layout(
        yaxis=dict(categoryorder="total ascending", title=None),
        height=460,
        margin=dict(l=10, r=30, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )

    st.plotly_chart(fig_gdp, width="stretch")

with right:
    st.subheader("各省人均 GDP 对比")

    capita_chart_df = view.sort_values(by="人均GDP", ascending=True)

    fig_pc = px.bar(
        capita_chart_df,
        x="人均GDP",
        y="省份",
        orientation="h",
        color="人均GDP",
        color_continuous_scale="Blues",
        text="人均GDP",
        labels={"人均GDP": "人均 GDP（万元/人）", "省份": ""},
    )

    fig_pc.update_traces(texttemplate="%{text:.2f}", textposition="outside")

    fig_pc.update_layout(
        yaxis=dict(categoryorder="total ascending", title=None),
        height=460,
        margin=dict(l=10, r=30, t=10, b=10),
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig_pc, width="stretch")

st.divider()

# ----------------------------------------------------------
# 区域分析
# ----------------------------------------------------------

st.subheader("四大区域 GDP 对比")
st.caption("区域划分依据国家统计局口径：东部、中部、西部、东北。")

region_df = (
    view.groupby("区域", as_index=False)
    .agg(
        省份数量=("省份", "count"),
        GDP总量=("GDP", "sum"),
        人均GDP均值=("人均GDP", "mean"),
    )
    .sort_values("GDP总量", ascending=False)
)

region_df["GDP占比"] = region_df["GDP总量"] / region_df["GDP总量"].sum() * 100

rl, rr = st.columns([3, 2])

with rl:
    fig_region = px.bar(
        region_df.sort_values("GDP总量", ascending=True),
        x="GDP总量",
        y="区域",
        orientation="h",
        text="GDP总量",
        color="区域",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"GDP总量": "GDP 总量（亿元）", "区域": ""},
    )
    fig_region.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_region.update_layout(
        yaxis=dict(categoryorder="total ascending", title=None),
        height=380,
        margin=dict(l=10, r=30, t=10, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_region, width="stretch")

with rr:
    st.dataframe(
        region_df.rename(columns={
            "省份数量": "省份数",
            "GDP总量": "GDP 总量（亿元）",
            "人均GDP均值": "人均均值（万元/人）",
            "GDP占比": "占比（%）",
        }),
        width="stretch",
        hide_index=True,
        column_config={
            "GDP 总量（亿元）": st.column_config.NumberColumn(format="%,.0f"),
            "人均均值（万元/人）": st.column_config.NumberColumn(format="%.2f"),
            "占比（%）": st.column_config.NumberColumn(format="%.1f"),
        },
    )

st.divider()

# ----------------------------------------------------------
# 散点图 + 占比图
# ----------------------------------------------------------

left2, right2 = st.columns([3, 2])

with left2:
    st.subheader("GDP 与人口的关系")
    fig_scatter = px.scatter(
        view,
        x="人口",
        y="GDP",
        size="GDP",
        color="数据状态",
        color_discrete_map=STATUS_COLOR,
        hover_name="省份",
        labels={"人口": "人口（万人）", "GDP": "GDP（亿元）", "数据状态": "数据状态"},
    )
    fig_scatter.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_scatter, width="stretch")

with right2:
    st.subheader("GDP 占比")
    fig_pie = px.pie(
        view,
        names="省份",
        values="GDP",
        hole=0.45,
        labels={"省份": "省份", "GDP": "GDP"},
    )
    fig_pie.update_traces(textinfo="percent+label")
    fig_pie.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_pie, width="stretch")

st.divider()

# ----------------------------------------------------------
# 中国各省 GDP 地理分布
# ----------------------------------------------------------

st.subheader("中国各省 GDP 地理分布")
st.caption(
    "地图颜色表示当前筛选样本中的 GDP 总量；"
    "灰色表示没有匹配到当前 GDP 数据，不代表 GDP 为零。"
)

if not MAP_FILE.exists():
    st.warning(
        "暂未找到中国省级地图文件，"
        "请将 china_provinces.geojson 放入 maps 文件夹。"
    )
else:
    geojson = load_geojson(str(MAP_FILE))

    all_map_keys = [
        feature["properties"]["map_key"]
        for feature in geojson["features"]
    ]

    matched = set(view["省份"]) & set(all_map_keys)
    unmatched = sorted(set(view["省份"]) - set(all_map_keys))

    fig_map = go.Figure()

    # 第一层：全国省份灰色底图
    # 目的：保证地图轮廓完整，同时不会把「没有数据」误读成「GDP 为零」
    fig_map.add_trace(
        go.Choropleth(
            geojson=geojson,
            locations=all_map_keys,
            z=[1] * len(all_map_keys),
            featureidkey="properties.map_key",
            colorscale=[[0, "#E9EDF2"], [1, "#E9EDF2"]],
            showscale=False,
            marker_line_color="#FFFFFF",
            marker_line_width=0.8,
            hoverinfo="skip",
            name="无数据",
        )
    )

    # 第二层：有数据的省份按 GDP 着色
    if matched:
        map_df = view[view["省份"].isin(matched)].sort_values("GDP")

        fig_map.add_trace(
            go.Choropleth(
                geojson=geojson,
                locations=map_df["省份"],
                z=map_df["GDP"],
                featureidkey="properties.map_key",
                colorscale="Blues",
                showscale=True,
                colorbar=dict(
                    title="GDP（亿元）",
                    thickness=14,
                    len=0.65,
                ),
                marker_line_color="#FFFFFF",
                marker_line_width=0.8,
                customdata=map_df[
                    ["省份", "人均GDP", "GDP排名", "数据状态"]
                ].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "GDP：%{z:,.0f} 亿元<br>"
                    "人均 GDP：%{customdata[1]:.2f} 万元/人<br>"
                    "排名：%{customdata[2]}<br>"
                    "数据状态：%{customdata[3]}"
                    "<extra></extra>"
                ),
            )
        )

    # 让地图自动适配边界范围，并隐藏经纬度坐标轴
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )

    st.plotly_chart(fig_map, width="stretch")

    if unmatched:
        st.caption(
            f"以下省份在当前地图文件中没有匹配到边界：{'、'.join(unmatched)}"
        )

st.divider()

# ==========================================================
# 11. 数据表格与导出
# ==========================================================

st.subheader("明细数据")

show_cols = ["省份", "区域", "GDP", "人口", "人均GDP", "GDP占比", "GDP排名", "数据状态"]
show_cols = [c for c in show_cols if c in view.columns]

table_df = view.sort_values("GDP排名")[show_cols]

st.dataframe(
    table_df,
    width="stretch",
    hide_index=True,
    column_config={
        "GDP": st.column_config.NumberColumn("GDP（亿元）", format="%,.0f"),
        "人口": st.column_config.NumberColumn("人口（万人）", format="%,.0f"),
        "人均GDP": st.column_config.NumberColumn("人均 GDP（万元/人）", format="%.2f"),
        "GDP占比": st.column_config.NumberColumn("占比（%）", format="%.2f"),
        "GDP排名": st.column_config.NumberColumn("排名", format="%d"),
    },
)

st.download_button(
    label="下载当前筛选结果（CSV）",
    data=table_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
    file_name="gdp_view.csv",
    mime="text/csv",
)

# ==========================================================
# 12. 页脚说明
# ==========================================================

st.divider()
st.caption(
    "数据说明：本项目使用教学示例数据，缺失 GDP 由中位数填补并标记为估算值；"
    "所有结论仅用于演示数据分析流程，不代表真实经济统计结果。"
)
st.caption(
    f"数据文件：{DATA_FILE.relative_to(BASE_DIR)}　｜　"
    f"记录数：{len(view)}　｜　"
    "如需更新数据，请重新运行 main.py 后刷新页面。"
)
