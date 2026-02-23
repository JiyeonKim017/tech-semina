import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="우리은행 금리 경쟁력 모니터",
    page_icon="🏦",
    layout="wide",
)

# ─────────────────────────────────────────
# 스타일
# ─────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

    /* 상단 요약 배너 */
    .summary-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
        border-radius: 14px;
        padding: 22px 28px;
        color: white;
        margin-bottom: 24px;
    }
    .summary-banner .date { font-size: 12px; opacity: .7; margin-bottom: 6px; }
    .summary-banner .headline { font-size: 20px; font-weight: 800; line-height: 1.4; }
    .summary-banner .sub { font-size: 13px; opacity: .85; margin-top: 8px; }

    /* 위험 카드 */
    .danger-card {
        background: #fff1f2;
        border: 1.5px solid #fca5a5;
        border-left: 5px solid #ef4444;
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 10px;
    }
    .danger-card .bank { font-size: 11px; color: #ef4444; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
    .danger-card .product { font-size: 15px; font-weight: 700; color: #1e293b; margin: 3px 0; }
    .danger-card .rate-diff { font-size: 22px; font-weight: 800; color: #ef4444; }
    .danger-card .meta { font-size: 12px; color: #64748b; margin-top: 6px; }
    .danger-card .condition { font-size: 11px; color: #475569; background: #fee2e2; border-radius: 4px; padding: 4px 8px; margin-top: 8px; }

    /* 주의 카드 */
    .warning-card {
        background: #fffbeb;
        border: 1.5px solid #fcd34d;
        border-left: 5px solid #f59e0b;
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 10px;
    }
    .warning-card .bank { font-size: 11px; color: #d97706; font-weight: 700; }
    .warning-card .product { font-size: 15px; font-weight: 700; color: #1e293b; margin: 3px 0; }
    .warning-card .rate-diff { font-size: 22px; font-weight: 800; color: #d97706; }
    .warning-card .meta { font-size: 12px; color: #64748b; margin-top: 6px; }
    .warning-card .condition { font-size: 11px; color: #475569; background: #fef3c7; border-radius: 4px; padding: 4px 8px; margin-top: 8px; }

    /* 일반 카드 */
    .normal-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #94a3b8;
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 10px;
    }
    .normal-card .bank { font-size: 11px; color: #64748b; font-weight: 700; }
    .normal-card .product { font-size: 15px; font-weight: 700; color: #1e293b; margin: 3px 0; }
    .normal-card .rate-diff { font-size: 22px; font-weight: 800; color: #64748b; }
    .normal-card .meta { font-size: 12px; color: #94a3b8; margin-top: 6px; }
    .normal-card .condition { font-size: 11px; color: #475569; background: #f1f5f9; border-radius: 4px; padding: 4px 8px; margin-top: 8px; }

    /* 메트릭 카드 */
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-label { font-size: 11px; color: #94a3b8; margin-bottom: 6px; font-weight: 600; }
    .metric-value { font-size: 26px; font-weight: 800; color: #1d4ed8; }
    .metric-sub { font-size: 11px; color: #94a3b8; margin-top: 3px; }

    .section-title {
        font-size: 15px; font-weight: 700; color: #1e293b;
        margin: 28px 0 14px;
        border-left: 4px solid #1d4ed8;
        padding-left: 10px;
    }

    div[data-testid="stSidebar"] { background: #1e2d45; }
    div[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

    .badge-easy { background: #dcfce7; color: #16a34a; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
    .badge-hard { background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
    .badge-mid  { background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(supabase_url, supabase_key)
    response = supabase.rpc("get_better_than_woori_final", {}).execute()
    return pd.DataFrame(response.data)

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 로딩 실패: {e}")
    st.stop()

COL = {
    "type":       df.columns[0],
    "woori_prod": df.columns[1],
    "period":     df.columns[2],
    "bank":       df.columns[3],
    "bank_prod":  df.columns[4],
    "woori_base": df.columns[5],
    "woori_max":  df.columns[6],
    "bank_base":  df.columns[7],
    "bank_max":   df.columns[8],
    "rate_diff":  df.columns[9],
    "difficulty": df.columns[10],
    "benefit":    df.columns[11],
}

# ─────────────────────────────────────────
# 사이드바 필터
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 필터")
    st.markdown("---")
    all_types   = sorted(df[COL["type"]].dropna().unique().tolist())
    all_periods = sorted(df[COL["period"]].dropna().unique().tolist())
    all_banks   = sorted(df[COL["bank"]].dropna().unique().tolist())

    sel_type   = st.multiselect("상품 타입",      all_types,   default=all_types)
    sel_period = st.multiselect("저축 기간 (개월)", all_periods, default=all_periods)
    sel_bank   = st.multiselect("타행명",          all_banks,   default=all_banks)

    st.markdown("---")
    top_n = st.slider("주목 상품 표시 개수", 3, 10, 5)
    if st.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

mask = (
    df[COL["type"]].isin(sel_type) &
    df[COL["period"]].isin(sel_period) &
    df[COL["bank"]].isin(sel_bank)
)
fdf = df[mask].copy()
fdf_sorted = fdf.sort_values(COL["rate_diff"], ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────
# 1. 오늘의 핵심 요약 배너
# ─────────────────────────────────────────
today = datetime.now().strftime("%Y년 %m월 %d일 기준")
max_diff  = fdf[COL["rate_diff"]].max() if len(fdf) > 0 else 0
max_row   = fdf.loc[fdf[COL["rate_diff"]].idxmax()] if len(fdf) > 0 else None
high_risk = len(fdf[fdf[COL["rate_diff"]] >= 0.3])  # 금리차 0.3% 이상

headline = ""
sub = ""
if max_row is not None:
    headline = f"우리은행 {max_row[COL['woori_prod']]}({int(max_row[COL['period']])}개월) 대비 최대 {max_diff:.2f}%p 높은 타행 상품 {len(fdf)}개 발견"
    sub = f"이 중 금리차 0.3%p 이상 고위험 상품 {high_risk}개 · 가장 위협적: {max_row[COL['bank']]} '{max_row[COL['bank_prod']]}'"

st.markdown(f"""
<div class="summary-banner">
    <div class="date">📅 {today}</div>
    <div class="headline">🚨 {headline}</div>
    <div class="sub">{sub}</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 2. 요약 지표
# ─────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
metrics = [
    ("총 경쟁 상품", f"{len(fdf)}개", "우리은행보다 금리 높은 상품"),
    ("평균 금리차",  f"{fdf[COL['rate_diff']].mean():.2f}%p", "타행 최대금리 - 우리 최대금리"),
    ("최대 금리차",  f"{max_diff:.2f}%p", max_row[COL['bank']] if max_row is not None else "-"),
    ("고위험 상품",  f"{high_risk}개", "금리차 0.3%p 이상"),
    ("비교 타행 수", f"{fdf[COL['bank']].nunique()}개", "은행"),
]
for col, (label, value, sub) in zip([c1, c2, c3, c4, c5], metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 3. 주목할 상품 (위험도별 카드)
# ─────────────────────────────────────────
st.markdown('<div class="section-title">🚨 지금 당장 주목해야 할 상품</div>', unsafe_allow_html=True)
st.caption("금리차가 크고 우대조건이 쉬울수록 경쟁력 위협이 큽니다.")

top_df = fdf_sorted.head(top_n)

cols = st.columns(min(len(top_df), 3))
for i, (_, row) in enumerate(top_df.iterrows()):
    diff = row[COL["rate_diff"]]
    difficulty = row[COL["difficulty"]]
    benefit_text = str(row[COL["benefit"]])[:120] + "..." if len(str(row[COL["benefit"]])) > 120 else str(row[COL["benefit"]])

    # 위험도 분류: 금리차 크고 난이도 낮을수록 위험
    if diff >= 0.3 and difficulty <= 0.2:
        card_class = "danger-card"
        risk_label = "🔴 고위험"
    elif diff >= 0.15:
        card_class = "warning-card"
        risk_label = "🟡 주의"
    else:
        card_class = "normal-card"
        risk_label = "⚪ 모니터링"

    if difficulty <= 0.1:
        diff_badge = '<span class="badge-easy">우대조건 쉬움</span>'
    elif difficulty <= 0.3:
        diff_badge = '<span class="badge-mid">우대조건 보통</span>'
    else:
        diff_badge = '<span class="badge-hard">우대조건 어려움</span>'

    with cols[i % 3]:
        st.markdown(f"""
        <div class="{card_class}">
            <div class="bank">{risk_label} · {row[COL['bank']]}</div>
            <div class="product">{row[COL['bank_prod']]}</div>
            <div class="rate-diff">+{diff:.2f}%p</div>
            <div class="meta">
                저축기간 {int(row[COL['period']])}개월 &nbsp;|&nbsp;
                타행 최대금리 {row[COL['bank_max']]:.2f}% vs 우리 {row[COL['woori_max']]:.2f}%
                &nbsp;|&nbsp; {diff_badge}
            </div>
            <div class="condition">📋 우대조건: {benefit_text}</div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# 4. 차트
# ─────────────────────────────────────────
st.markdown('<div class="section-title">📊 타행별 최대 금리차</div>', unsafe_allow_html=True)

bank_diff = (
    fdf.groupby(COL["bank"])[COL["rate_diff"]]
    .max().reset_index()
    .sort_values(COL["rate_diff"], ascending=True)
)
fig1 = px.bar(
    bank_diff, x=COL["rate_diff"], y=COL["bank"], orientation="h",
    color=COL["rate_diff"],
    color_continuous_scale=["#93c5fd", "#1d4ed8", "#1e3a8a"],
    text=bank_diff[COL["rate_diff"]].apply(lambda x: f"{x:.2f}%p"),
)
fig1.update_traces(textposition="outside")
fig1.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    coloraxis_showscale=False,
    margin=dict(l=10, r=40, t=10, b=10),
    height=max(280, len(bank_diff) * 42),
    xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
)
st.plotly_chart(fig1, use_container_width=True)

col_a, col_b = st.columns(2)

with col_a:
    st.markdown('<div class="section-title">📈 저축 기간별 금리 비교</div>', unsafe_allow_html=True)
    period_df = (
        fdf.groupby(COL["period"])[[COL["woori_max"], COL["bank_max"]]]
        .mean().reset_index().sort_values(COL["period"])
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
        marker_color="#1d4ed8",
        text=period_df[COL["bank_max"]].apply(lambda x: f"{x:.2f}%"),
        textposition="outside",
    ))
    fig2.update_layout(
        barmode="group", plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", ticksuffix="%"),
        margin=dict(l=10, r=10, t=30, b=10), height=320,
    )
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    st.markdown('<div class="section-title">🔵 금리차 분포 (우대난이도별)</div>', unsafe_allow_html=True)
    fig3 = px.scatter(
        fdf,
        x=COL["difficulty"],
        y=COL["rate_diff"],
        color=COL["bank"],
        size=COL["rate_diff"],
        hover_data=[COL["bank_prod"], COL["period"], COL["woori_max"], COL["bank_max"]],
        labels={
            COL["difficulty"]: "우대 난이도 (낮을수록 쉬움)",
            COL["rate_diff"]: "금리차 (%p)",
            COL["bank"]: "타행명",
        },
        size_max=20,
    )
    # 위험 구역 표시 (난이도 낮고 금리차 높음)
    fig3.add_shape(type="rect", x0=-0.05, y0=0.3, x1=0.25, y1=fdf[COL["rate_diff"]].max()+0.1,
                   fillcolor="rgba(239,68,68,0.08)", line=dict(color="rgba(239,68,68,0.3)", width=1))
    fig3.add_annotation(x=0.1, y=fdf[COL["rate_diff"]].max()+0.05,
                        text="⚠️ 고위험 구역", showarrow=False,
                        font=dict(color="#ef4444", size=11))
    fig3.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10), height=320,
    )
    st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────
# 5. 상세 데이터 테이블
# ─────────────────────────────────────────
st.markdown('<div class="section-title">📋 전체 상세 데이터</div>', unsafe_allow_html=True)

display_cols = list(COL.values())
rename_map = {v: k for v, k in zip(display_cols, [
    "상품타입", "우리은행상품", "저축기간(월)", "타행명", "타행상품명",
    "우리 기본금리", "우리 최대금리", "타행 기본금리", "타행 최대금리",
    "금리차(%p)", "우대난이도", "우대조건"
])}

styled_df = (
    fdf[display_cols]
    .rename(columns=rename_map)
    .sort_values("금리차(%p)", ascending=False)
    .reset_index(drop=True)
)

st.dataframe(
    styled_df.style.format({
        "우리 기본금리": "{:.2f}%", "우리 최대금리": "{:.2f}%",
        "타행 기본금리": "{:.2f}%", "타행 최대금리": "{:.2f}%",
        "금리차(%p)": "+{:.2f}%p",
    }),
    use_container_width=True,
    height=420,
)

csv = styled_df.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ CSV 다운로드", csv, "bank_rate_comparison.csv", "text/csv")
