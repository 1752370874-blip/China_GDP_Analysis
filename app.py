# 中国各省 GDP 交互式数据分析平台（3.2）
# 重点：地图点击与现有筛选、指标卡、图表、表格同步。

import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
import streamlit as st

st.set_page_config(page_title="中国各省 GDP 数据分析平台", page_icon="📊", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "processed" / "gdp_analysis.csv"
MAP_FILE = BASE_DIR / "maps" / "china_provinces.geojson"
REGION_MAP = {
    "东部": ["北京", "天津", "河北", "上海", "江苏", "浙江", "福建", "山东", "广东", "海南"],
    "中部": ["山西", "安徽", "江西", "河南", "湖北", "湖南"],
    "西部": ["内蒙古", "广西", "重庆", "四川", "贵州", "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆"],
    "东北": ["辽宁", "吉林", "黑龙江"],
}
PROVINCE_TO_REGION = {province: region for region, provinces in REGION_MAP.items() for province in provinces}
STATUS_MAP = {True: "估算数据", False: "原始数据"}
STATUS_COLOR = {"原始数据": "#2563EB", "估算数据": "#F59E0B"}


def normalize_province(name):
    """把地图和数据中的全称统一为项目使用的简称。"""
    if pd.isna(name):
        return ""
    value = str(name).strip()
    for suffix in ("壮族自治区", "回族自治区", "维吾尔自治区", "特别行政区", "自治区", "省", "市"):
        if value.endswith(suffix):
            return value[:-len(suffix)]
    return value


def ring_to_svg_path(ring):
    """一个 GeoJSON 外环对应一个独立 SVG path。"""
    if not ring:
        return ""
    return " ".join(
        [f"M {ring[0][0]:.6f},{ring[0][1]:.6f}"]
        + [f"L {lon:.6f},{lat:.6f}" for lon, lat in ring[1:]]
        + ["Z"]
    )


def ring_center(ring):
    points = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring
    return (
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


@st.cache_data(show_spinner=False)
def load_map_features(file_path):
    """解析 Polygon/MultiPolygon；离散岛屿不会被合并到同一填充形状。"""
    with open(file_path, "r", encoding="utf-8") as file:
        geojson = json.load(file)
    features, all_x, all_y = {}, [], []
    for feature in geojson.get("features", []):
        name = normalize_province(feature.get("properties", {}).get("name", ""))
        geometry = feature.get("geometry") or {}
        geometry_type, coordinates = geometry.get("type"), geometry.get("coordinates")
        if not name or not coordinates or geometry_type not in {"Polygon", "MultiPolygon"}:
            continue
        polygons = [coordinates] if geometry_type == "Polygon" else coordinates
        paths, rings, centers = [], [], []
        for polygon in polygons:
            if not polygon or not polygon[0]:
                continue
            ring = polygon[0]
            path = ring_to_svg_path(ring)
            if path:
                paths.append(path)
                rings.append(ring)
                centers.append(ring_center(ring))
                all_x.extend(point[0] for point in ring)
                all_y.extend(point[1] for point in ring)
        if paths:
            features[name] = {"paths": paths, "rings": rings, "centers": centers}
    if not all_x:
        raise ValueError("地图文件中没有可绘制的 Polygon/MultiPolygon 边界。")
    return features, (min(all_x), min(all_y), max(all_x), max(all_y))


@st.cache_data(show_spinner="正在读取数据…")
def load_data(path):
    frame = pd.read_csv(path, encoding="utf-8-sig")
    required = {"省份", "GDP", "人口", "人均GDP", "GDP是否估算"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"分析结果缺少必要字段：{', '.join(missing)}")
    frame = frame.copy()
    frame["省份"] = frame["省份"].map(normalize_province)
    for column in ("GDP", "人口", "人均GDP"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["GDP是否估算"] = frame["GDP是否估算"].astype(str).str.lower().isin(["true", "1", "yes", "是"])
    frame = frame.dropna(subset=["省份", "GDP", "人口", "人均GDP"])
    frame["数据状态"] = frame["GDP是否估算"].map(STATUS_MAP)
    frame["区域"] = frame["省份"].map(PROVINCE_TO_REGION).fillna("其他")
    frame["地图省份"] = frame["省份"].map(normalize_province)
    return frame


def supports_plotly_selection():
    numbers = [int(number) for number in re.findall(r"\d+", getattr(st, "__version__", "0"))[:3]]
    numbers.extend([0] * (3 - len(numbers)))
    return tuple(numbers) >= (1, 35, 0)


def selected_province_from(event):
    """兼容 Streamlit PlotlyState / dict，安全读取图上选择。"""
    selection = getattr(event, "selection", None) if event else None
    if selection is None and isinstance(event, dict):
        selection = event.get("selection")
    points = getattr(selection, "points", None) if selection is not None else None
    if points is None and isinstance(selection, dict):
        points = selection.get("points", [])
    for point in points or []:
        customdata = point.get("customdata") if isinstance(point, dict) else getattr(point, "customdata", None)
        if isinstance(customdata, (list, tuple)):
            customdata = customdata[0] if customdata else None
        if customdata:
            return normalize_province(customdata)
    return None


def initialise_selection(all_provinces):
    """在 multiselect 创建前处理地图选择，避免 widget-state 异常。"""
    st.session_state.setdefault("province_filter", list(all_provinces))
    st.session_state.setdefault("province_filter_before_map", list(all_provinces))
    st.session_state.setdefault("selected_map_province", None)
    st.session_state.setdefault("map_selection_nonce", 0)
    pending = st.session_state.pop("pending_map_province", None)
    if pending:
        if st.session_state["selected_map_province"] is None:
            st.session_state["province_filter_before_map"] = list(st.session_state["province_filter"])
        st.session_state["province_filter"] = [pending]
        st.session_state["selected_map_province"] = pending


def clear_map_selection(all_provinces):
    """恢复点击前的省份多选项；其余筛选条件不改动。"""
    st.session_state["province_filter"] = list(
        st.session_state.get("province_filter_before_map", all_provinces)
    ) or list(all_provinces)
    st.session_state["selected_map_province"] = None
    st.session_state["map_selection_nonce"] += 1


def province_filter_changed():
    """用户手工改省份选择时，取消地图持久化选择。"""
    if st.session_state.get("selected_map_province") is not None:
        st.session_state["selected_map_province"] = None
        st.session_state["map_selection_nonce"] += 1
    st.session_state["province_filter_before_map"] = list(st.session_state["province_filter"])


def build_map(features, map_frame, full_frame, selected_province):
    """视觉层是独立 SVG shapes；透明 Scatter 层负责地图点击事件。"""
    fig = go.Figure()
    gdp_min, gdp_max = float(full_frame["GDP"].min()), float(full_frame["GDP"].max())
    gdp_span = max(gdp_max - gdp_min, 1.0)
    rows = {row["地图省份"]: row for _, row in map_frame.drop_duplicates("地图省份").iterrows()}

    shapes = []
    for province, feature in features.items():
        row = rows.get(province)
        if row is None:
            fill, border, width = "#E9EDF2", "#FFFFFF", 0.7
        else:
            ratio = max(0.0, min(1.0, (float(row["GDP"]) - gdp_min) / gdp_span))
            fill = sample_colorscale("Blues", [0.12 + 0.82 * ratio])[0]
            border = "#F59E0B" if bool(row["GDP是否估算"]) else "#FFFFFF"
            width = 1.4 if bool(row["GDP是否估算"]) else 0.8
        if province == selected_province:
            border, width = "#111827", 3.0
        shapes.extend(
            dict(type="path", path=path, fillcolor=fill, line=dict(color=border, width=width), layer="below")
            for path in feature["paths"]
        )
    fig.update_layout(shapes=shapes)

    # Shape 没有选择事件。每个有数据的省份新增透明命中多边形和中心兜底点。
    for province, row in rows.items():
        feature = features.get(province)
        if feature is None:
            continue
        hover = (
            f"<b>{province}</b><br>GDP：{row['GDP']:,.0f} 亿元<br>"
            f"人均 GDP：{row['人均GDP']:.2f} 万元/人<br>排名：{int(row['GDP排名'])}<br>"
            f"数据状态：{row['数据状态']}<br><i>单击选择该省份</i><extra></extra>"
        )
        for ring in feature["rings"]:
            fig.add_trace(go.Scatter(
                x=[point[0] for point in ring], y=[point[1] for point in ring],
                mode="lines", fill="toself", fillcolor="rgba(0,0,0,0.001)",
                line=dict(color="rgba(0,0,0,0.001)", width=1),
                customdata=[province] * len(ring), hoveron="fills", hovertemplate=hover,
                showlegend=False, name=province,
            ))
        fig.add_trace(go.Scatter(
            x=[center[0] for center in feature["centers"]],
            y=[center[1] for center in feature["centers"]], mode="markers",
            marker=dict(size=22, color="rgba(0,0,0,0.001)"),
            customdata=[province] * len(feature["centers"]), hovertemplate=hover,
            showlegend=False, name=province,
        ))

    # 色条基于完整样本，因此区域/GDP/TOP10 筛选不会改变颜色含义。
    fig.add_trace(go.Scatter(
        x=[None, None], y=[None, None], mode="markers",
        marker=dict(size=0, opacity=0, color=[gdp_min, gdp_max], colorscale="Blues",
                    cmin=gdp_min, cmax=gdp_max, showscale=True,
                    colorbar=dict(title="GDP（亿元）", thickness=14, len=0.65)),
        hoverinfo="skip", showlegend=False,
    ))
    fig.update_xaxes(visible=False, range=[73, 136], fixedrange=True)
    fig.update_yaxes(visible=False, range=[17, 54], scaleanchor="x", scaleratio=1, fixedrange=True)
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0),
                      paper_bgcolor="white", plot_bgcolor="white", showlegend=False,
                      clickmode="event+select")
    return fig


st.markdown("""<style>
.main-title {font-size:32px;font-weight:bold;color:#2563EB;}
.sub-title {color:#64748b;font-size:15px;}
</style>""", unsafe_allow_html=True)

if not DATA_FILE.exists():
    st.error("没有找到 data/processed/gdp_analysis.csv。请先在项目根目录运行 python main.py。")
    st.stop()
try:
    df = load_data(str(DATA_FILE))
except Exception as error:
    st.error(f"数据加载失败：{error}")
    st.stop()
if df.empty:
    st.error("没有可供分析的有效数据。")
    st.stop()

all_provinces = sorted(df["省份"].unique().tolist())
initialise_selection(all_provinces)
st.markdown('<div class="main-title">📊 中国各省 GDP 数据分析平台</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">教学示例数据，非官方统计结果 ｜ 3.2：地图点击联动</div>', unsafe_allow_html=True)
st.divider()

st.sidebar.header("筛选条件")
if st.session_state.get("selected_map_province"):
    st.sidebar.success(f"地图已选中：{st.session_state['selected_map_province']}")
    st.sidebar.button("清除地图选择（恢复原省份筛选）", on_click=clear_map_selection,
                      args=(all_provinces,), use_container_width=True)
selected = st.sidebar.multiselect("选择省份（可多选）", all_provinces,
                                  key="province_filter", on_change=province_filter_changed)
regions = [region for region in REGION_MAP if region in set(df["区域"])]
selected_regions = st.sidebar.multiselect("选择区域（可多选）", regions, default=regions)
gdp_min, gdp_max = int(df["GDP"].min()), int(df["GDP"].max())
gdp_range = st.sidebar.slider("GDP 区间（亿元）", gdp_min, gdp_max, (gdp_min, gdp_max), step=1000)
include_estimated = st.sidebar.checkbox("包含 GDP 估算值（中位数填补）", value=True)
top_n_only = st.sidebar.checkbox("只看 GDP 前 10 名", value=False)
st.sidebar.divider()
st.sidebar.caption("地图单击省份即可同步筛选；手工改变省份多选项会解除地图选择。")

# 地图保留区域/GDP/估算/TOP10 条件下的候选，便于在地图上直接换选；
# KPI、图表和表格继续严格叠加原有的省份多选条件。
map_view = df[df["区域"].isin(selected_regions) & df["GDP"].between(*gdp_range)].copy()
if not include_estimated:
    map_view = map_view[~map_view["GDP是否估算"]].copy()
if top_n_only:
    map_view = map_view.nlargest(10, "GDP").copy()
view = map_view[map_view["省份"].isin(selected)].copy()
if view.empty:
    st.warning("当前筛选条件没有数据。请调整侧边栏，或清除地图选择以恢复点击前的省份集合。")
    st.stop()

total_gdp, avg_gdp = view["GDP"].sum(), view["GDP"].mean()
avg_per_capita = view["人均GDP"].mean()
top_province = view.loc[view["GDP"].idxmax(), "省份"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("省份数量", f"{len(view)} 个")
c2.metric("GDP 总量", f"{total_gdp:,.0f} 亿元")
c3.metric("平均 GDP", f"{avg_gdp:,.0f} 亿元")
c4.metric("GDP 第一", top_province)
estimated_count = int(view["GDP是否估算"].sum())
if estimated_count:
    st.info(f"当前视图包含 {estimated_count} 条 GDP 估算记录；地图以橙色边框标出。")

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("各省 GDP 总量排名")
    fig_gdp = px.bar(view.sort_values("GDP"), x="GDP", y="省份", orientation="h",
                     color="数据状态", color_discrete_map=STATUS_COLOR, text="GDP",
                     labels={"GDP": "GDP（亿元）", "省份": "", "数据状态": "数据状态"})
    fig_gdp.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_gdp.update_layout(yaxis=dict(categoryorder="total ascending", title=None), height=460)
    st.plotly_chart(fig_gdp, width="stretch")
with right:
    st.subheader("各省人均 GDP 对比")
    fig_pc = px.bar(view.sort_values("人均GDP"), x="人均GDP", y="省份", orientation="h",
                    color="人均GDP", color_continuous_scale="Blues", text="人均GDP",
                    labels={"人均GDP": "人均 GDP（万元/人）", "省份": ""})
    fig_pc.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_pc.update_layout(yaxis=dict(categoryorder="total ascending", title=None),
                         coloraxis_showscale=False, height=460)
    st.plotly_chart(fig_pc, width="stretch")

st.divider()
st.subheader("四大区域 GDP 对比")
region_df = view.groupby("区域", as_index=False).agg(
    省份数量=("省份", "count"), GDP总量=("GDP", "sum"), 人均GDP均值=("人均GDP", "mean")
).sort_values("GDP总量", ascending=False)
region_df["GDP占比"] = region_df["GDP总量"] / region_df["GDP总量"].sum() * 100
rl, rr = st.columns([3, 2])
with rl:
    fig_region = px.bar(region_df.sort_values("GDP总量"), x="GDP总量", y="区域",
                        orientation="h", text="GDP总量", color="区域",
                        color_discrete_sequence=px.colors.qualitative.Set2)
    fig_region.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_region.update_layout(yaxis=dict(categoryorder="total ascending", title=None), height=380,
                             showlegend=False)
    st.plotly_chart(fig_region, width="stretch")
with rr:
    st.dataframe(region_df.rename(columns={"省份数量": "省份数", "GDP总量": "GDP 总量（亿元）",
                  "人均GDP均值": "人均均值（万元/人）", "GDP占比": "占比（%）"}),
                 width="stretch", hide_index=True)

st.divider()
left2, right2 = st.columns([3, 2])
with left2:
    st.subheader("GDP 与人口的关系")
    fig_scatter = px.scatter(view, x="人口", y="GDP", size="GDP", color="数据状态",
                             color_discrete_map=STATUS_COLOR, hover_name="省份")
    fig_scatter.update_layout(height=420)
    st.plotly_chart(fig_scatter, width="stretch")
with right2:
    st.subheader("GDP 占比")
    fig_pie = px.pie(view, names="省份", values="GDP", hole=0.45)
    fig_pie.update_traces(textinfo="percent+label")
    fig_pie.update_layout(height=420)
    st.plotly_chart(fig_pie, width="stretch")

st.divider()
st.subheader("中国各省 GDP 地理分布（点击选择）")
st.caption("GDP 色标按完整教学数据固定；橙色边框为估算值，灰色为当前候选集中没有数据，深色边框为选中省份。")
if not MAP_FILE.exists():
    st.warning("暂未找到 maps/china_provinces.geojson；地图与地图选择不可用，其余功能仍可使用。")
else:
    try:
        map_features, _ = load_map_features(str(MAP_FILE))
        manual_single = selected[0] if len(selected) == 1 else None
        highlight = st.session_state.get("selected_map_province") or manual_single
        figure = build_map(map_features, map_view, df, highlight)
        map_key = f"gdp_map_selection_{st.session_state['map_selection_nonce']}"
        if supports_plotly_selection():
            event = st.plotly_chart(figure, width="stretch", key=map_key,
                                    on_select="rerun", selection_mode="points")
            clicked = selected_province_from(event)
            # 相同选择不 rerun，因而不会出现无限刷新循环。
            if clicked and clicked != st.session_state.get("selected_map_province"):
                st.session_state["pending_map_province"] = clicked
                st.rerun()
        else:
            st.plotly_chart(figure, width="stretch", key=map_key)
            st.info("当前 Streamlit 版本不支持 Plotly 选择事件。地图仍可悬停；升级到 requirements.txt 指定版本后可点击筛选。")
    except Exception as error:
        st.warning(f"地图暂时无法显示或选择：{error}。其他分析功能不受影响。")

st.subheader("明细数据")
show_cols = ["省份", "区域", "GDP", "人口", "人均GDP", "GDP占比", "GDP排名", "数据状态"]
table_df = view.sort_values("GDP排名")[show_cols]
st.dataframe(table_df, width="stretch", hide_index=True,
             column_config={
                 "GDP": st.column_config.NumberColumn("GDP（亿元）", format="%,.0f"),
                 "人口": st.column_config.NumberColumn("人口（万人）", format="%,.0f"),
                 "人均GDP": st.column_config.NumberColumn("人均 GDP（万元/人）", format="%.2f"),
                 "GDP占比": st.column_config.NumberColumn("占比（%）", format="%.2f"),
                 "GDP排名": st.column_config.NumberColumn("排名", format="%d"),
             })
st.download_button("下载当前筛选结果（CSV）",
                   data=table_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                   file_name="gdp_view.csv", mime="text/csv")
st.divider()
st.caption("数据说明：本项目使用教学示例数据，缺失 GDP 由中位数填补并标记为估算值；所有结论仅用于演示数据分析流程。")
st.caption(f"数据文件：{DATA_FILE.relative_to(BASE_DIR)} ｜ 当前表格记录数：{len(view)} ｜ 如需更新数据，请重新运行 main.py 后刷新页面。")
