import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="우리은행 금리 경쟁력 모니터", page_icon="🏦", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .summary-banner { background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%); border-radius: 14px; padding: 22px 28px; color: white; margin-bottom: 24px; }
    .summary-banner .date { font-size: 12px; opacity: .7; margin-bottom: 6px; }
    .summary-banner .headline { font-size: 20px; font-weight: 800; line-height: 1.4; }
    .summary-banner .sub { font-size: 13px; opacity: .85; margin-top: 8px; }
    .insight-box { background: #f0f7ff; border-left: 4px solid #1d4ed8; border-radius: 8px; padding: 14px 18px; margin-top: 16px; font-size: 13px; color: #1e293b; line-height: 1.8; }
    .insight-box b { color: #1d4ed8; }
    .desc-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; font-size: 13px; color: #475569; line-height: 1.7; }
    .section-title { font-size: 15px; font-weight: 700; color: #1e293b; margin: 20px 0 10px; border-left: 4px solid #1d4ed8; padding-left: 10px; }
    .metric-card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 20px; text-align: center; }
    .metric-label { font-size: 11px; color: #94a3b8; margin-bottom: 6px; font-weight: 600; }
    .metric-value { font-size: 26px; font-weight: 800; color: #1d4ed8; }
    .metric-sub { font-size: 11px; color: #94a3b8; margin-top: 3px; }
    .danger-card { background: #fff1f2; border: 1.5px solid #fca5a5; border-left: 5px solid #ef4444; border-radius: 10px; padding: 16px 18px; margin-bottom: 10px; }
    .danger-card .bank { font-size: 11px; color: #ef4444; font-weight: 700; }
    .danger-card .product { font-size: 15px; font-weight: 700; color: #1e293b; margin: 3px 0; }
    .danger-card .rate-diff { font-size: 22px; font-weight: 800; color: #ef4444; }
    .danger-card .meta { font-size: 12px; color: #64748b; margin-top: 6px; }
    .danger-card .condition { font-size: 11px; color: #475569; background: #fee2e2; border-radius: 4px; padding: 4px 8px; margin-top: 8px; }
    .warning-card { background: #fffbeb; border: 1.5px solid #fcd34d; border-left: 5px solid #f59e0b; border-radius: 10px; padding: 16px 18px; margin-bottom: 10px; }
    .warning-card .bank { font-size: 11px; color: #d97706; font-weight: 700; }
    .warning-card .product { font-size: 15px; font-weight: 700; color: #1e293b; margin: 3px 0; }
    .warning-card .rate-diff { font-size: 22px; font-weight: 800; color: #d97706; }
    .warning-card .meta { font-size: 12px; color: #64748b; margin-top: 6px; }
    .warning-card .condition { font-size: 11px; color: #475569; background: #fef3c7; border-radius: 4px; padding: 4px 8px; margin-top: 8px; }
    .normal-card { background: #f8fafc; border: 1px solid #e2e8f0; border-left: 5px solid #94a3b8; border-radius: 10px; padding: 16px 18px; margin-bottom: 10px; }
    .normal-card .bank { font-size: 11px; color: #64748b; font-weight: 700; }
    .normal-card .product { font-size: 15px; font-weight: 700; color: #1e293b; margin: 3px 0; }
    .normal-card .rate-diff { font-size: 22px; font-weight: 800; color: #64748b; }
    .normal-card .meta { font-size: 12px; color: #94a3b8; margin-top: 6px; }
    .normal-card .condition { font-size: 11px; color: #475569; background: #f1f5f9; border-radius: 4px; padding: 4px 8px; margin-top: 8px; }
    div[data-testid="stSidebar"] { background: #1e2d45; }
    div[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    .badge-easy { background: #dcfce7; color: #16a34a; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
    .badge-hard { background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
    .badge-mid  { background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# Supabase 연결
# ─────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# ─────────────────────────────────────────
# 데이터 로드 - 프로시저 (현황 분석용)
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def load_comparison_data():
    response = supabase.rpc("get_better_than_woori_final", {}).execute()
    return pd.DataFrame(response.data)

# ─────────────────────────────────────────
# 데이터 로드 - finance_data 직접 조회 (추이 분석용)
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def load_history_data():
    response = supabase.table("finance_data").select(
        "collected_at, kor_co_nm, fin_prdt_nm, save_trm, intr_rate, intr_rate2, spcl_cnd, product_type"
    ).execute()
    df = pd.DataFrame(response.data)
    df["collected_at"] = pd.to_datetime(df["collected_at"])
    return df

try:
    df = load_comparison_data()
except Exception as e:
    st.error(f"데이터 로딩 실패: {e}")
    st.stop()

try:
    hist_df = load_history_data()
except Exception as e:
    st.warning(f"추이 데이터 로딩 실패: {e}")
    hist_df = pd.DataFrame()

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
    sel_type   = st.multiselect("상품 타입",       sorted(df[COL["type"]].dropna().unique()),   default=sorted(df[COL["type"]].dropna().unique()))
    sel_period = st.multiselect("저축 기간 (개월)", sorted(df[COL["period"]].dropna().unique()), default=sorted(df[COL["period"]].dropna().unique()))
    sel_bank   = st.multiselect("타행명",           sorted(df[COL["bank"]].dropna().unique()),   default=sorted(df[COL["bank"]].dropna().unique()))
    st.markdown("---")
    top_n = st.slider("주목 상품 표시 개수", 3, 10, 5)
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()

mask = (
    df[COL["type"]].isin(sel_type) &
    df[COL["period"]].isin(sel_period) &
    df[COL["bank"]].isin(sel_bank)
)
fdf = df[mask].copy()
fdf_sorted = fdf.sort_values(COL["rate_diff"], ascending=False).reset_index(drop=True)

today     = datetime.now().strftime("%Y년 %m월 %d일")
max_diff  = fdf[COL["rate_diff"]].max() if len(fdf) > 0 else 0
max_row   = fdf.loc[fdf[COL["rate_diff"]].idxmax()] if len(fdf) > 0 else None
high_risk = len(fdf[fdf[COL["rate_diff"]] >= 0.3])

# ─────────────────────────────────────────
# 상단 배너
# ─────────────────────────────────────────
if max_row is not None:
    st.markdown(f"""
    <div class="summary-banner">
        <div class="date">📅 {today} 기준</div>
        <div class="headline">🚨 우리은행 대비 최대 {max_diff:.2f}%p 높은 타행 상품 {len(fdf)}개 발견</div>
        <div class="sub">고위험 상품(금리차 0.3%p↑) {high_risk}개 · 가장 위협적: {max_row[COL['bank']]} '{max_row[COL['bank_prod']]}'</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# 탭
# ─────────────────────────────────────────
tabs = st.tabs([
    "🏠 종합 현황",
    "🚨 주목 상품",
    "📊 금리 비교",
    "🗺️ 경쟁 구조",
    "⭐ 우대조건 분석",
    "⚠️ 위험 매트릭스",
    "📈 금리 변동 추이",
    "📋 전체 데이터",
])

# ══════════════════════════════════════════
# TAB 1: 종합 현황
# ══════════════════════════════════════════
with tabs[0]:
    st.markdown("### 🏠 종합 현황")
    st.markdown('<div class="desc-box">우리은행보다 금리가 높은 타행 상품 전체를 한눈에 파악합니다. 핵심 지표와 타행별 금리차를 통해 현재 경쟁 상황을 빠르게 확인하세요.</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, (label, value, sub) in zip([c1,c2,c3,c4,c5], [
        ("총 경쟁 상품", f"{len(fdf)}개",                          "우리은행보다 금리 높은 상품"),
        ("평균 금리차",  f"{fdf[COL['rate_diff']].mean():.2f}%p", "타행 최대 - 우리 최대"),
        ("최대 금리차",  f"{max_diff:.2f}%p",                      max_row[COL['bank']] if max_row is not None else "-"),
        ("고위험 상품",  f"{high_risk}개",                         "금리차 0.3%p 이상"),
        ("비교 타행 수", f"{fdf[COL['bank']].nunique()}개",        "은행"),
    ]):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="section-title">타행별 최대 금리차</div>', unsafe_allow_html=True)
    bank_diff = fdf.groupby(COL["bank"])[COL["rate_diff"]].max().reset_index().sort_values(COL["rate_diff"], ascending=True)
    fig = px.bar(bank_diff, x=COL["rate_diff"], y=COL["bank"], orientation="h",
                 color=COL["rate_diff"], color_continuous_scale=["#93c5fd","#1d4ed8","#1e3a8a"],
                 text=bank_diff[COL["rate_diff"]].apply(lambda x: f"{x:.2f}%p"))
    fig.update_traces(textposition="outside")
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", coloraxis_showscale=False,
                      margin=dict(l=10,r=40,t=10,b=10), height=max(280, len(bank_diff)*42),
                      xaxis=dict(showgrid=True, gridcolor="#f1f5f9"))
    st.plotly_chart(fig, use_container_width=True)

    top_bank    = bank_diff.iloc[-1]
    bottom_bank = bank_diff.iloc[0]
    st.markdown(f"""
    <div class="insight-box">
        📌 <b>결과 요약</b><br>
        현재 <b>{top_bank[COL['bank']]}</b>이 최대 <b>{top_bank[COL['rate_diff']]:.2f}%p</b>로 가장 높은 금리차를 보이며 우리은행 대비 경쟁력 위협이 가장 큰 타행입니다.<br>
        반면 <b>{bottom_bank[COL['bank']]}</b>은 {bottom_bank[COL['rate_diff']]:.2f}%p로 상대적으로 위협 수준이 낮습니다.<br>
        총 <b>{fdf[COL['bank']].nunique()}개 타행</b> 중 금리차 0.3%p 이상인 고위험 타행은 <b>{len(bank_diff[bank_diff[COL['rate_diff']] >= 0.3])}곳</b>입니다.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 2: 주목 상품
# ══════════════════════════════════════════
with tabs[1]:
    st.markdown("### 🚨 주목 상품")
    st.markdown('<div class="desc-box">금리차가 크고 우대조건이 쉬운 상품일수록 고객 이탈 위험이 높습니다. 위험도(🔴 고위험 / 🟡 주의 / ⚪ 모니터링)로 분류해 빠르게 파악하세요.</div>', unsafe_allow_html=True)

    top_df = fdf_sorted.head(top_n)
    cols   = st.columns(min(len(top_df), 3))

    for i, (_, row) in enumerate(top_df.iterrows()):
        diff         = row[COL["rate_diff"]]
        difficulty   = row[COL["difficulty"]]
        benefit_text = str(row[COL["benefit"]])
        benefit_short = benefit_text[:120] + "..." if len(benefit_text) > 120 else benefit_text

        if diff >= 0.3 and difficulty <= 0.2:
            card_class, risk_label = "danger-card",  "🔴 고위험"
        elif diff >= 0.15:
            card_class, risk_label = "warning-card", "🟡 주의"
        else:
            card_class, risk_label = "normal-card",  "⚪ 모니터링"

        if difficulty <= 0.1:
            badge = '<span class="badge-easy">우대조건 쉬움</span>'
        elif difficulty <= 0.3:
            badge = '<span class="badge-mid">우대조건 보통</span>'
        else:
            badge = '<span class="badge-hard">우대조건 어려움</span>'

        with cols[i % 3]:
            st.markdown(f"""
            <div class="{card_class}">
                <div class="bank">{risk_label} · {row[COL['bank']]}</div>
                <div class="product">{row[COL['bank_prod']]}</div>
                <div class="rate-diff">+{diff:.2f}%p</div>
                <div class="meta">{int(row[COL['period']])}개월 | 타행 {row[COL['bank_max']]:.2f}% vs 우리 {row[COL['woori_max']]:.2f}% | {badge}</div>
                <div class="condition">📋 {benefit_short}</div>
            </div>
            """, unsafe_allow_html=True)

    danger_count  = sum(1 for _, r in top_df.iterrows() if r[COL["rate_diff"]] >= 0.3 and r[COL["difficulty"]] <= 0.2)
    warning_count = sum(1 for _, r in top_df.iterrows() if r[COL["rate_diff"]] >= 0.15)
    st.markdown(f"""
    <div class="insight-box">
        📌 <b>결과 요약</b><br>
        상위 {top_n}개 상품 중 <b>고위험 {danger_count}개, 주의 {warning_count}개</b>가 확인됩니다.<br>
        우대조건이 쉬우면서 금리차가 큰 상품은 고객이 별다른 노력 없이 갈아탈 수 있어 <b>이탈 위험이 가장 높습니다.</b>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 3: 금리 비교
# ══════════════════════════════════════════
with tabs[2]:
    st.markdown("### 📊 금리 비교")
    st.markdown('<div class="desc-box">저축 기간별로 우리은행과 타행의 평균 금리를 비교합니다. 어느 기간에서 경쟁력이 부족한지 파악할 수 있습니다.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">저축 기간별 평균 금리 비교</div>', unsafe_allow_html=True)
    period_df = fdf.groupby(COL["period"])[[COL["woori_max"], COL["bank_max"]]].mean().reset_index().sort_values(COL["period"])
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="우리은행 최대금리", x=period_df[COL["period"]].astype(str)+"개월",
                          y=period_df[COL["woori_max"]], marker_color="#93c5fd",
                          text=period_df[COL["woori_max"]].apply(lambda x: f"{x:.2f}%"), textposition="outside"))
    fig2.add_trace(go.Bar(name="타행 최대금리", x=period_df[COL["period"]].astype(str)+"개월",
                          y=period_df[COL["bank_max"]], marker_color="#1d4ed8",
                          text=period_df[COL["bank_max"]].apply(lambda x: f"{x:.2f}%"), textposition="outside"))
    fig2.update_layout(barmode="group", plot_bgcolor="white", paper_bgcolor="white",
                       legend=dict(orientation="h", y=1.1, x=1, xanchor="right"),
                       yaxis=dict(ticksuffix="%", gridcolor="#f1f5f9"),
                       height=380, margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig2, use_container_width=True)

    worst_period = period_df.copy()
    worst_period["diff"] = worst_period[COL["bank_max"]] - worst_period[COL["woori_max"]]
    worst = worst_period.loc[worst_period["diff"].idxmax()]
    st.markdown(f"""
    <div class="insight-box">
        📌 <b>결과 요약</b><br>
        특히 <b>{int(worst[COL['period']])}개월 구간</b>에서 평균 금리차가 <b>{worst['diff']:.2f}%p</b>로 가장 크며, 이 구간에서의 경쟁력 개선이 시급합니다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">기본금리 vs 최대금리 — 우대 효과 크기 비교</div>', unsafe_allow_html=True)
    fdf2 = fdf.copy()
    fdf2["우리 우대폭"] = fdf2[COL["woori_max"]] - fdf2[COL["woori_base"]]
    fdf2["타행 우대폭"] = fdf2[COL["bank_max"]]  - fdf2[COL["bank_base"]]
    benefit_df = fdf2.groupby(COL["bank"])[["우리 우대폭","타행 우대폭"]].mean().reset_index().sort_values("타행 우대폭", ascending=False)
    fig_b = go.Figure()
    fig_b.add_trace(go.Bar(name="우리은행 우대폭", x=benefit_df[COL["bank"]], y=benefit_df["우리 우대폭"], marker_color="#bfdbfe"))
    fig_b.add_trace(go.Bar(name="타행 우대폭",     x=benefit_df[COL["bank"]], y=benefit_df["타행 우대폭"], marker_color="#1d4ed8"))
    fig_b.update_layout(barmode="group", plot_bgcolor="white", paper_bgcolor="white",
                        yaxis=dict(ticksuffix="%p", gridcolor="#f1f5f9"),
                        legend=dict(orientation="h", y=1.1), height=340, margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig_b, use_container_width=True)

# ══════════════════════════════════════════
# TAB 4: 경쟁 구조
# ══════════════════════════════════════════
with tabs[3]:
    st.markdown("### 🗺️ 경쟁 구조")
    st.markdown('<div class="desc-box">타행이 어느 저축 기간에 집중적으로 경쟁하는지 파악합니다. 히트맵으로 타행 × 기간 조합의 경쟁 강도를 확인하세요.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">타행 × 저축기간 금리차 히트맵</div>', unsafe_allow_html=True)
    pivot = fdf.groupby([COL["bank"], COL["period"]])[COL["rate_diff"]].max().reset_index()
    pivot_table = pivot.pivot(index=COL["bank"], columns=COL["period"], values=COL["rate_diff"]).fillna(0)
    fig_h = px.imshow(pivot_table, color_continuous_scale="Blues",
                      labels=dict(x="저축 기간(개월)", y="타행명", color="최대 금리차(%p)"),
                      text_auto=".2f", aspect="auto")
    fig_h.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=360)
    st.plotly_chart(fig_h, use_container_width=True)

    max_combo = pivot.loc[pivot[COL["rate_diff"]].idxmax()]
    st.markdown(f"""
    <div class="insight-box">
        📌 <b>결과 요약</b><br>
        현재 <b>{max_combo[COL['bank']]}</b>의 <b>{int(max_combo[COL['period']])}개월</b> 상품이 금리차 <b>{max_combo[COL['rate_diff']]:.2f}%p</b>로 가장 위협적인 조합입니다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">우리은행 상품별 경쟁 상품 수</div>', unsafe_allow_html=True)
    vuln = fdf.groupby([COL["woori_prod"], COL["period"]]).size().reset_index(name="경쟁 상품 수")
    vuln_pivot = vuln.pivot(index=COL["woori_prod"], columns=COL["period"], values="경쟁 상품 수").fillna(0)
    fig_v = px.imshow(vuln_pivot, color_continuous_scale="Reds",
                      labels=dict(x="저축 기간(개월)", y="우리은행 상품", color="경쟁 상품 수"),
                      text_auto=True, aspect="auto")
    fig_v.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=300)
    st.plotly_chart(fig_v, use_container_width=True)

    worst_prod = vuln.loc[vuln["경쟁 상품 수"].idxmax()]
    st.markdown(f"""
    <div class="insight-box">
        📌 <b>결과 요약</b><br>
        <b>{worst_prod[COL['woori_prod']]}</b> <b>{int(worst_prod[COL['period']])}개월</b> 상품이 <b>{int(worst_prod['경쟁 상품 수'])}개</b> 타행 상품에 밀리며 가장 취약한 구간입니다.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 5: 우대조건 분석
# ══════════════════════════════════════════
with tabs[4]:
    st.markdown("### ⭐ 우대조건 분석")
    st.markdown('<div class="desc-box">우대조건의 난이도와 금리의 관계를 분석합니다. 조건이 쉬우면서 금리가 높은 상품이 실질적으로 가장 위협적입니다.</div>', unsafe_allow_html=True)

    fdf3 = fdf.copy()
    fdf3["난이도 구분"] = fdf3[COL["difficulty"]].apply(
        lambda x: "쉬움 (0~0.1)" if x <= 0.1 else ("보통 (0.1~0.3)" if x <= 0.3 else "어려움 (0.3↑)")
    )
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">우대 난이도 분포</div>', unsafe_allow_html=True)
        diff_count = fdf3["난이도 구분"].value_counts().reset_index()
        diff_count.columns = ["난이도", "상품 수"]
        fig_pie = px.pie(diff_count, names="난이도", values="상품 수",
                         color_discrete_sequence=["#4ade80","#fbbf24","#f87171"], hole=0.4)
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(showlegend=False, margin=dict(l=10,r=10,t=10,b=10), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_b:
        st.markdown('<div class="section-title">난이도별 평균 금리차</div>', unsafe_allow_html=True)
        diff_rate = fdf3.groupby("난이도 구분")[COL["rate_diff"]].mean().reset_index()
        fig_dr = px.bar(diff_rate, x="난이도 구분", y=COL["rate_diff"],
                        color="난이도 구분",
                        color_discrete_map={"쉬움 (0~0.1)":"#4ade80","보통 (0.1~0.3)":"#fbbf24","어려움 (0.3↑)":"#f87171"},
                        text=diff_rate[COL["rate_diff"]].apply(lambda x: f"{x:.2f}%p"))
        fig_dr.update_traces(textposition="outside")
        fig_dr.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
                             yaxis=dict(ticksuffix="%p", gridcolor="#f1f5f9"),
                             margin=dict(l=10,r=10,t=10,b=10), height=300)
        st.plotly_chart(fig_dr, use_container_width=True)

    easy_pct  = len(fdf3[fdf3["난이도 구분"]=="쉬움 (0~0.1)"]) / len(fdf3) * 100 if len(fdf3) > 0 else 0
    easy_rate = fdf3[fdf3["난이도 구분"]=="쉬움 (0~0.1)"][COL["rate_diff"]].mean() if len(fdf3) > 0 else 0
    st.markdown(f"""
    <div class="insight-box">
        📌 <b>결과 요약</b><br>
        전체 경쟁 상품 중 <b>우대조건이 쉬운 상품이 {easy_pct:.0f}%</b>를 차지하며 평균 금리차는 <b>{easy_rate:.2f}%p</b>입니다.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 6: 위험 매트릭스
# ══════════════════════════════════════════
with tabs[5]:
    st.markdown("### ⚠️ 위험 매트릭스")
    st.markdown('<div class="desc-box">X축은 우대조건 난이도(낮을수록 쉬움), Y축은 금리차(높을수록 위협적)입니다. 왼쪽 위 구역이 가장 위험한 상품입니다.</div>', unsafe_allow_html=True)

    fig_m = px.scatter(fdf, x=COL["difficulty"], y=COL["rate_diff"],
                       color=COL["bank"], size=COL["bank_max"],
                       hover_data=[COL["bank_prod"], COL["period"], COL["woori_max"], COL["bank_max"], COL["benefit"]],
                       labels={COL["difficulty"]: "우대 난이도 (낮을수록 쉬움 →)", COL["rate_diff"]: "금리차 (%p) ↑", COL["bank"]: "타행명"},
                       size_max=22)
    fig_m.add_shape(type="rect", x0=-0.02, y0=0.3, x1=0.22, y1=fdf[COL["rate_diff"]].max()+0.1,
                    fillcolor="rgba(239,68,68,0.07)", line=dict(color="rgba(239,68,68,0.4)", width=1.5, dash="dot"))
    fig_m.add_annotation(x=0.1, y=fdf[COL["rate_diff"]].max()+0.07, text="🔴 고위험 구역",
                         showarrow=False, font=dict(color="#ef4444", size=12))
    fig_m.add_hline(y=0.3, line_dash="dash", line_color="#fca5a5", line_width=1)
    fig_m.add_vline(x=0.2, line_dash="dash", line_color="#94a3b8", line_width=1)
    fig_m.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=10,r=10,t=20,b=10), height=480)
    st.plotly_chart(fig_m, use_container_width=True)

    danger_products = fdf[(fdf[COL["rate_diff"]] >= 0.3) & (fdf[COL["difficulty"]] <= 0.2)]
    st.markdown(f"""
    <div class="insight-box">
        📌 <b>결과 요약</b><br>
        고위험 구역에 포함된 상품은 총 <b>{len(danger_products)}개</b>입니다. 이 상품들은 고객이 손쉽게 갈아탈 수 있는 가장 위협적인 상품입니다.
    </div>
    """, unsafe_allow_html=True)

    if len(danger_products) > 0:
        st.markdown('<div class="section-title">🔴 고위험 구역 상품 목록</div>', unsafe_allow_html=True)
        show_cols = [COL["bank"], COL["bank_prod"], COL["period"], COL["woori_max"], COL["bank_max"], COL["rate_diff"], COL["difficulty"], COL["benefit"]]
        rename = {COL["bank"]: "타행명", COL["bank_prod"]: "타행 상품명", COL["period"]: "기간(월)",
                  COL["woori_max"]: "우리 최대금리", COL["bank_max"]: "타행 최대금리",
                  COL["rate_diff"]: "금리차(%p)", COL["difficulty"]: "우대난이도", COL["benefit"]: "우대조건"}
        st.dataframe(danger_products[show_cols].rename(columns=rename).reset_index(drop=True),
                     use_container_width=True, height=250)

# ══════════════════════════════════════════
# TAB 7: 금리 변동 추이 (NEW)
# ══════════════════════════════════════════
with tabs[6]:
    st.markdown("### 📈 금리 변동 추이")
    st.markdown('<div class="desc-box">특정 상품의 날짜별 금리 변동을 추적합니다. 매일 수집된 데이터를 바탕으로 기본금리와 최대금리가 언제 어떻게 바뀌었는지 확인하세요.</div>', unsafe_allow_html=True)

    if hist_df.empty:
        st.warning("추이 데이터를 불러올 수 없습니다.")
    else:
        # 필터 선택
        col1, col2, col3 = st.columns(3)

        with col1:
            all_banks_hist = sorted(hist_df["kor_co_nm"].dropna().unique().tolist())
            sel_bank_hist  = st.selectbox("은행 선택", all_banks_hist)

        with col2:
            products_of_bank = sorted(hist_df[hist_df["kor_co_nm"] == sel_bank_hist]["fin_prdt_nm"].dropna().unique().tolist())
            sel_prod_hist    = st.selectbox("상품 선택", products_of_bank)

        with col3:
            periods_of_prod = sorted(hist_df[
                (hist_df["kor_co_nm"] == sel_bank_hist) &
                (hist_df["fin_prdt_nm"] == sel_prod_hist)
            ]["save_trm"].dropna().unique().tolist())
            sel_trm_hist = st.selectbox("저축 기간(개월)", periods_of_prod)

        # 필터 적용
        trend_df = hist_df[
            (hist_df["kor_co_nm"] == sel_bank_hist) &
            (hist_df["fin_prdt_nm"] == sel_prod_hist) &
            (hist_df["save_trm"] == sel_trm_hist)
        ].sort_values("collected_at").reset_index(drop=True)

        if trend_df.empty:
            st.info("해당 조건의 데이터가 없습니다.")
        else:
            # 금리 변동 시점 감지
            trend_df["base_changed"] = trend_df["intr_rate"].diff().ne(0)
            trend_df["max_changed"]  = trend_df["intr_rate2"].diff().ne(0)
            trend_df["any_changed"]  = trend_df["base_changed"] | trend_df["max_changed"]
            changed_df = trend_df[trend_df["any_changed"] & (trend_df.index > 0)]

            # 라인 차트
            st.markdown('<div class="section-title">날짜별 금리 추이</div>', unsafe_allow_html=True)
            fig_trend = go.Figure()

            fig_trend.add_trace(go.Scatter(
                x=trend_df["collected_at"], y=trend_df["intr_rate"],
                mode="lines+markers", name="기본금리",
                line=dict(color="#93c5fd", width=2),
                marker=dict(size=5),
            ))
            fig_trend.add_trace(go.Scatter(
                x=trend_df["collected_at"], y=trend_df["intr_rate2"],
                mode="lines+markers", name="최대금리",
                line=dict(color="#1d4ed8", width=2.5),
                marker=dict(size=5),
            ))

            # 변동 시점 마커 강조
            if len(changed_df) > 0:
                fig_trend.add_trace(go.Scatter(
                    x=changed_df["collected_at"], y=changed_df["intr_rate2"],
                    mode="markers", name="금리 변동 시점",
                    marker=dict(color="#ef4444", size=12, symbol="star"),
                ))

            fig_trend.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", y=1.1, x=1, xanchor="right"),
                yaxis=dict(ticksuffix="%", gridcolor="#f1f5f9", title="금리 (%)"),
                xaxis=dict(title="수집 날짜", gridcolor="#f1f5f9"),
                margin=dict(l=10,r=10,t=30,b=10), height=400,
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            # 변동 이력 테이블
            st.markdown('<div class="section-title">금리 변동 이력</div>', unsafe_allow_html=True)
            if len(changed_df) == 0:
                st.info("조회 기간 내 금리 변동 이력이 없습니다.")
            else:
                change_display = changed_df[["collected_at","intr_rate","intr_rate2"]].copy()
                change_display.columns = ["변동 날짜", "기본금리(%)", "최대금리(%)"]
                change_display["변동 날짜"] = change_display["변동 날짜"].dt.strftime("%Y-%m-%d")
                st.dataframe(change_display.reset_index(drop=True), use_container_width=True, height=250)

            # 자동 요약
            first_max  = trend_df["intr_rate2"].iloc[0]
            latest_max = trend_df["intr_rate2"].iloc[-1]
            rate_delta = latest_max - first_max
            direction  = "상승" if rate_delta > 0 else ("하락" if rate_delta < 0 else "변동 없음")
            date_range = f"{trend_df['collected_at'].min().strftime('%Y-%m-%d')} ~ {trend_df['collected_at'].max().strftime('%Y-%m-%d')}"

            st.markdown(f"""
            <div class="insight-box">
                📌 <b>결과 요약</b><br>
                <b>{sel_bank_hist} · {sel_prod_hist} ({sel_trm_hist}개월)</b><br>
                조회 기간: <b>{date_range}</b> (총 {len(trend_df)}일 수집)<br>
                최대금리: <b>{first_max:.2f}%</b> → <b>{latest_max:.2f}%</b>
                (<b>{'+' if rate_delta >= 0 else ''}{rate_delta:.2f}%p {direction}</b>)<br>
                금리 변동 횟수: <b>{len(changed_df)}회</b>
                {"· ⚠️ 최근 금리가 상승 중이므로 경쟁력 모니터링이 필요합니다." if rate_delta > 0 else ""}
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 8: 전체 데이터
# ══════════════════════════════════════════
with tabs[7]:
    st.markdown("### 📋 전체 데이터")
    st.markdown('<div class="desc-box">필터가 적용된 전체 데이터를 확인하고 CSV로 다운로드할 수 있습니다.</div>', unsafe_allow_html=True)

    display_cols = list(COL.values())
    rename_map = {v: k for v, k in zip(display_cols, [
        "상품타입", "우리은행상품", "저축기간(월)", "타행명", "타행상품명",
        "우리 기본금리", "우리 최대금리", "타행 기본금리", "타행 최대금리",
        "금리차(%p)", "우대난이도", "우대조건"
    ])}
    styled_df = (
        fdf[display_cols].rename(columns=rename_map)
        .sort_values("금리차(%p)", ascending=False)
        .reset_index(drop=True)
    )
    st.dataframe(
        styled_df.style.format({
            "우리 기본금리": "{:.2f}%", "우리 최대금리": "{:.2f}%",
            "타행 기본금리": "{:.2f}%", "타행 최대금리": "{:.2f}%",
            "금리차(%p)": "+{:.2f}%p",
        }),
        use_container_width=True, height=500,
    )
    csv = styled_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ CSV 다운로드", csv, "bank_rate_comparison.csv", "text/csv")
