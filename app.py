import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="우리은행 금리 비교 대시보드",
    page_icon="🏦",
    layout="wide",
)

# ─────────────────────────────────────────
# 스타일
# ─────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .main { background-color: #f7f9fc; }

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        text-align: center;
    }
    .metric-label { font-size: 13px; color: #888; margin-bottom: 4px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #1a56db; }
    .metric-sub   { font-size: 12px; color: #aaa; margin-top: 4px; }

    .section-title {
        font-size: 16px;
        font-weight: 700;
        color: #1e293b;
        margin: 28px 0 12px;
        border-left: 4px solid #1a56db;
        padding-left: 10px;
    }
    div[data-testid="stSidebar"] {
        background: #1e2d45;
    }
    div[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    div[data-testid="stSidebar"] .stSelectbox label,
    div[data-testid="stSidebar"] .stMultiSelect label { color: #94a3b8 !important; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    supabase = create_client(supabase_url, supabase_key)
    response = supabase.rpc("get_better_than_woori_final", {}).execute()
    return pd.DataFrame(response.data)

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 로딩 실패: {e}")
    st.stop()

# 컬럼명 매핑 (실제 반환 컬럼에 맞게 조정)
# 예상 컬럼: product_type, woori_product, savings_period, bank_name, bank_product,
#           woori_base_rate, woori_max_rate, bank_base_rate, bank_max_rate,
#           max_rate_diff, benefit_difficulty, benefit_detail
COL = {
    "type":         df.columns[0],   # 상품 타입
    "woori_prod":   df.columns[1],   # 우리은행 상품명
    "period":       df.columns[2],   # 저축 기간
    "bank":         df.columns[3],   # 타행명
    "bank_prod":    df.columns[4],   # 타행 상품명
    "woori_base":   df.columns[5],   # 우리 기본금리
    "woori_max":    df.columns[6],   # 우리 최대금리
    "bank_base":    df.columns[7],   # 타행 기본금리
    "bank_max":     df.columns[8],   # 타행 최대금리
    "rate_diff":    df.columns[9],   # 최대 금리차
    "difficulty":   df.columns[10],  # 우대 난이도
    "benefit":      df.columns[11],  # 우대 조건
}

# ─────────────────────────────────────────
# 사이드바 필터
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 필터")
    st.markdown("---")

    # 상품 타입 필터
    all_types = sorted(df[COL["type"]].dropna().unique().tolist())
    sel_type = st.multiselect("상품 타입", all_types, default=all_types)

    # 저축 기간 필터
    all_periods = sorted(df[COL["period"]].dropna().unique().tolist())
    sel_period = st.multiselect("저축 기간 (개월)", all_periods, default=all_periods)

    # 타행명 필터
    all_banks = sorted(df[COL["bank"]].dropna().unique().tolist())
    sel_bank = st.multiselect("타행명", all_banks, default=all_banks)

    st.markdown("---")
    if st.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

# 필터 적용
mask = (
    df[COL["type"]].isin(sel_type) &
    df[COL["period"]].isin(sel_period) &
    df[COL["bank"]].isin(sel_bank)
)
fdf = df[mask].copy()

# ─────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────
st.markdown("# 🏦 우리은행 금리 경쟁력 대시보드")
st.markdown(f"<span style='color:#64748b;font-size:13px'>타행 대비 우리은행보다 금리가 높은 상품 분석 · 총 {len(fdf)}건</span>", unsafe_allow_html=True)
st.markdown("---")

# ─────────────────────────────────────────
# 요약 지표 카드
# ─────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">분석 상품 수</div>
        <div class="metric-value">{len(fdf)}</div>
        <div class="metric-sub">건</div>
    </div>""", unsafe_allow_html=True)

with c2:
    avg_diff = fdf[COL["rate_diff"]].mean() if len(fdf) > 0 else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">평균 최대 금리차</div>
        <div class="metric-value">{avg_diff:.2f}%</div>
        <div class="metric-sub">타행 - 우리은행</div>
    </div>""", unsafe_allow_html=True)

with c3:
    max_diff = fdf[COL["rate_diff"]].max() if len(fdf) > 0 else 0
    max_bank = fdf.loc[fdf[COL["rate_diff"]].idxmax(), COL["bank"]] if len(fdf) > 0 else "-"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">최대 금리차</div>
        <div class="metric-value">{max_diff:.2f}%</div>
        <div class="metric-sub">{max_bank}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    num_banks = fdf[COL["bank"]].nunique()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">비교 타행 수</div>
        <div class="metric-value">{num_banks}</div>
        <div class="metric-sub">개 은행</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 차트 1: 타행별 최대 금리차 (Bar Chart)
# ─────────────────────────────────────────
st.markdown('<div class="section-title">📊 타행별 최대 금리차 비교</div>', unsafe_allow_html=True)

bank_diff = (
    fdf.groupby(COL["bank"])[COL["rate_diff"]]
    .max()
    .reset_index()
    .sort_values(COL["rate_diff"], ascending=True)
)

fig1 = px.bar(
    bank_diff,
    x=COL["rate_diff"],
    y=COL["bank"],
    orientation="h",
    color=COL["rate_diff"],
    color_continuous_scale=["#93c5fd", "#1a56db", "#1e3a8a"],
    labels={COL["rate_diff"]: "최대 금리차 (%)", COL["bank"]: "타행명"},
    text=bank_diff[COL["rate_diff"]].apply(lambda x: f"{x:.2f}%"),
)
fig1.update_traces(textposition="outside")
fig1.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    coloraxis_showscale=False,
    margin=dict(l=10, r=40, t=10, b=10),
    height=max(300, len(bank_diff) * 40),
    xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
)
st.plotly_chart(fig1, use_container_width=True)

# ─────────────────────────────────────────
# 차트 2: 저축 기간별 금리 비교
# ─────────────────────────────────────────
st.markdown('<div class="section-title">📈 저축 기간별 평균 금리 비교</div>', unsafe_allow_html=True)

period_df = (
    fdf.groupby(COL["period"])[[COL["woori_max"], COL["bank_max"]]]
    .mean()
    .reset_index()
    .sort_values(COL["period"])
)

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    name="우리은행 최대금리",
    x=period_df[COL["period"]].astype(str) + "개월",
    y=period_df[COL["woori_max"]],
    marker_color="#93c5fd",
    text=period_df[COL["woori_max"]].apply(lambda x: f"{x:.2f}%"),
    textposition="outside",
))
fig2.add_trace(go.Bar(
    name="타행 최대금리",
    x=period_df[COL["period"]].astype(str) + "개월",
    y=period_df[COL["bank_max"]],
    marker_color="#1a56db",
    text=period_df[COL["bank_max"]].apply(lambda x: f"{x:.2f}%"),
    textposition="outside",
))
fig2.update_layout(
    barmode="group",
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis=dict(showgrid=True, gridcolor="#f1f5f9", ticksuffix="%"),
    margin=dict(l=10, r=10, t=30, b=10),
    height=380,
)
st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────
# 차트 3: 우리은행 vs 타행 금리 비교 (Scatter)
# ─────────────────────────────────────────
st.markdown('<div class="section-title">🔵 우리은행 vs 타행 최대금리 분포</div>', unsafe_allow_html=True)

fig3 = px.scatter(
    fdf,
    x=COL["woori_max"],
    y=COL["bank_max"],
    color=COL["bank"],
    size=COL["rate_diff"],
    hover_data=[COL["bank_prod"], COL["period"], COL["rate_diff"]],
    labels={
        COL["woori_max"]: "우리은행 최대금리 (%)",
        COL["bank_max"]: "타행 최대금리 (%)",
        COL["bank"]: "타행명",
    },
    size_max=25,
)

# 기준선 (우리은행 = 타행)
min_r = min(fdf[COL["woori_max"]].min(), fdf[COL["bank_max"]].min()) - 0.1
max_r = max(fdf[COL["woori_max"]].max(), fdf[COL["bank_max"]].max()) + 0.1
fig3.add_shape(type="line", x0=min_r, y0=min_r, x1=max_r, y1=max_r,
               line=dict(color="#e2e8f0", width=1.5, dash="dash"))
fig3.add_annotation(x=max_r, y=max_r, text="동일금리 기준선",
                    showarrow=False, font=dict(color="#94a3b8", size=11))

fig3.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=10, r=10, t=10, b=10),
    height=420,
)
st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────
# 상세 데이터 테이블
# ─────────────────────────────────────────
st.markdown('<div class="section-title">📋 상세 데이터</div>', unsafe_allow_html=True)

display_cols = list(COL.values())
rename_map = {v: k_kor for v, k_kor in zip(display_cols, [
    "상품타입", "우리은행상품", "저축기간(월)", "타행명", "타행상품명",
    "우리 기본금리", "우리 최대금리", "타행 기본금리", "타행 최대금리",
    "최대 금리차", "우대 난이도", "우대 조건"
])}

styled_df = (
    fdf[display_cols]
    .rename(columns=rename_map)
    .sort_values("최대 금리차", ascending=False)
    .reset_index(drop=True)
)

st.dataframe(
    styled_df.style
        .background_gradient(subset=["최대 금리차"], cmap="Blues")
        .format({"우리 기본금리": "{:.2f}%", "우리 최대금리": "{:.2f}%",
                 "타행 기본금리": "{:.2f}%", "타행 최대금리": "{:.2f}%",
                 "최대 금리차": "{:.2f}%"}),
    use_container_width=True,
    height=400,
)

# CSV 다운로드
csv = styled_df.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ CSV 다운로드", csv, "bank_rate_comparison.csv", "text/csv")
