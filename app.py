# ==========================================================
# 中国各省 GDP 交互式数据分析平台
# China GDP Analysis Dashboard
# 技术：Streamlit + Pandas + Plotly
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
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
# 4. 读取数据
# ==========================================================

@st.cache_data(show_spinner="正在读取数据…")
def load_data(path: Path) -> pd.DataFrame:
    """读取 main.py 生成的分析结果，不做任何清洗。"""
    return pd.read_csv(path, encoding="utf-8-sig")


if not DATA_FILE.exists():
    st.error(
        "没有找到分析结果文件：`data/processed/gdp_analysis.csv`\n\n"
        "请先在项目根目录运行一次 `python main.py`，生成该文件后再刷新本页面。"
    )
    st.stop()

df = load_data(DATA_FILE)

# ==========================================================
# 5. 页面标题
# ==========================================================

st.markdown('<div class="main-title">📊 中国各省 GDP 数据分析平台</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">数据来源：main.py 生成的分析结果（教学示例数据，非官方统计）</div>',
    unsafe_allow_html=True
)
st.divider()

# ==========================================================
# 6. 侧边栏：筛选条件
# ==========================================================

st.sidebar.header("筛选条件")

all_provinces = sorted(df["省份"].unique().tolist())
selected = st.sidebar.multiselect(
    "选择省份（可多选）",
    options=all_provinces,
    default=all_provinces
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

st.sidebar.divider()
st.sidebar.caption(
    "提示：图表可鼠标悬停查看数值，也可用工具栏下载为图片。"
)

# ==========================================================
# 7. 应用筛选
# ==========================================================

view = df[
    df["省份"].isin(selected)
    & df["GDP"].between(gdp_range[0], gdp_range[1])
].copy()

if not include_estimated:
    view = view[view["GDP是否估算"] == False]

if view.empty:
    st.warning("当前筛选条件下没有数据，请在左侧调整省份或 GDP 区间。")
    st.stop()

# ==========================================================
# 8. 关键指标卡片
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
# 9. 图表区
# ==========================================================

COLOR_MAP = {False: "#2563EB", True: "#F59E0B"}

left, right = st.columns(2)

with left:
    st.subheader("各省 GDP 总量排名")
    fig_gdp = px.bar(
        view.sort_values("GDP", ascending=True),
        x="GDP",
        y="省份",
        orientation="h",
        color="GDP是否估算",
        color_discrete_map=COLOR_MAP,
        text="GDP",
        labels={"GDP": "GDP（亿元）", "省份": "", "GDP是否估算": "是否估算"},
    )
    fig_gdp.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_gdp.update_layout(
        height=460,
        margin=dict(l=10, r=30, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(fig_gdp, width="stretch")

with right:
    st.subheader("各省人均 GDP 对比")
    fig_pc = px.bar(
        view.sort_values("人均GDP", ascending=True),
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
        height=460,
        margin=dict(l=10, r=30, t=10, b=10),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_pc, width="stretch")

st.divider()
left2, right2 = st.columns([3, 2])

with left2:
    st.subheader("GDP 与人口的关系")
    fig_scatter = px.scatter(
        view,
        x="人口",
        y="GDP",
        size="GDP",
        color="省份",
        hover_name="省份",
        labels={"人口": "人口（万人）", "GDP": "GDP（亿元）"},
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

# ==========================================================
# 10. 数据表格与导出
# ==========================================================

st.subheader("明细数据")

show_cols = ["省份", "GDP", "人口", "人均GDP", "GDP占比", "GDP排名", "GDP是否估算"]
show_cols = [c for c in show_cols if c in view.columns]

st.dataframe(
    view.sort_values("GDP排名")[show_cols],
    width="stretch",
    hide_index=True,
    column_config={
        "GDP": st.column_config.NumberColumn("GDP（亿元）", format="%,.0f"),
        "人口": st.column_config.NumberColumn("人口（万人）", format="%,.0f"),
        "人均GDP": st.column_config.NumberColumn("人均 GDP（万元/人）", format="%.2f"),
        "GDP占比": st.column_config.NumberColumn("占比（%）", format="%.2f"),
        "GDP排名": st.column_config.NumberColumn("排名", format="%d"),
        "GDP是否估算": st.column_config.CheckboxColumn("是否估算"),
    },
)

st.download_button(
    label="下载当前筛选结果（CSV）",
    data=view.sort_values("GDP排名")[show_cols].to_csv(
        index=False, encoding="utf-8-sig"
    ).encode("utf-8-sig"),
    file_name="gdp_view.csv",
    mime="text/csv",
)

# ==========================================================
# 11. 页脚说明
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
