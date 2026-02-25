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
    div[data-testid="stSidebar"] { background: #1e2d45; }
    div[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    /* 멀티셀렉트 태그 파스텔 블루 */
    span[data-baseweb="tag"] {
        background-color: #bfdbfe !important;
        border: 1px solid #93c5fd !important;
    }
    span[data-baseweb="tag"] span {
        color: #1e3a8a !important;
        font-weight: 600 !important;
    }
    span[data-baseweb="tag"] svg {
        fill: #1e3a8a !important;
    }
</style>
""", unsafe_allow_html=True)

PERIOD_ORDER = [1, 3, 6, 12, 24, 36]

# ─────────────────────────────────────────
# Supabase 연결
# ─────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# ─────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def load_comparison_data():
    response = supabase.rpc("get_better_than_woori_final", {}).execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=300)
def load_history_data():
    response = supabase.table("finance_data").select(
        "collected_at, kor_co_nm, fin_prdt_nm, save_trm, intr_rate, intr_rate2, spcl_cnd, product_type, rsrv_type_nm"
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
# 탭 구성
# ─────────────────────────────────────────
tabs = st.tabs([
    "🏠 종합 현황",
    "🗺️ 경쟁 구조",
    "📈 금리 변동 추이",
    "📋 전체 데이터",
])

# ══════════════════════════════════════════
# TAB 1: 종합 현황
# ══════════════════════════════════════════
with tabs[0]:
    st.markdown("### 🏠 종합 현황")
    st.markdown('<div class="desc-box">우리은행보다 금리가 높은 타행 상품을 금리차 순으로 확인합니다. 각 상품을 클릭하면 기간별 금리 변동 추이를 확인할 수 있습니다.</div>', unsafe_allow_html=True)

    # ── 핵심 지표 ──
    c1, c2, c3, c4 = st.columns(4)
    for col, (label, value, sub) in zip([c1,c2,c3,c4], [
        ("총 경쟁 상품",  f"{len(fdf)}개",         "우리은행보다 금리 높은 상품"),
        ("최대 금리차",   f"{max_diff:.2f}%p",      max_row[COL['bank']] if max_row is not None else "-"),
        ("고위험 상품",   f"{high_risk}개",         "금리차 0.3%p 이상"),
        ("비교 타행 수",  f"{fdf[COL['bank']].nunique()}개", "은행"),
    ]):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown("")

    import re

    def strip_deposit_type(name):
        """상품명에서 (자유적립식) / (정액적립식) 등 괄호 패턴 제거"""
        return re.sub(r"\s*\(자유적립식\)|\s*\(정액적립식\)", "", name).strip()

    def get_deposit_type(row):
        """적립 방식 추출 — 2가지 케이스 모두 처리
        케이스 A: fin_prdt_nm에 괄호로 포함된 경우
        케이스 B: rsrv_type_nm 별도 컬럼에 있는 경우
        """
        # 1순위: rsrv_type_nm 컬럼 (케이스 B)
        rsrv = row.get("rsrv_type_nm", None)
        if pd.notna(rsrv) and rsrv:
            if "자유" in str(rsrv):
                return "자유"
            elif "정액" in str(rsrv):
                return "정액"
        # 2순위: 상품명 괄호 파싱 (케이스 A)
        nm = str(row.get("fin_prdt_nm", ""))
        if "자유적립식" in nm:
            return "자유"
        elif "정액적립식" in nm:
            return "정액"
        return "일반"

    # ── 상품명 기준 중복 제거: 괄호 제거 후 금리차 가장 높은 기간 대표값으로 ──
    fdf_dedup = fdf.copy()
    fdf_dedup["_clean_prod"] = fdf_dedup[COL["bank_prod"]].apply(strip_deposit_type)

    dedup_df = (
        fdf_dedup.sort_values(COL["rate_diff"], ascending=False)
        .drop_duplicates(subset=[COL["bank"], "_clean_prod"], keep="first")
        .reset_index(drop=True)
    )

    # ── 세션 상태: 전체 보기 토글 ──
    if "show_all_products" not in st.session_state:
        st.session_state["show_all_products"] = False

    TOP_N = 5
    display_list = dedup_df if st.session_state["show_all_products"] else dedup_df.head(TOP_N)

    st.markdown('<div class="section-title">📋 금리차 높은 순 상품 랭킹</div>', unsafe_allow_html=True)

    # ── 색상 팔레트 ──
    # 자유적립식 or 일반: 파랑 계열 실선
    BLUE_COLORS = {
        1:  "#bfdbfe",
        3:  "#60a5fa",
        6:  "#3b82f6",
        12: "#1d4ed8",
        24: "#1e3a8a",
        36: "#172554",
    }
    # 정액적립식: 초록 계열 점선
    GREEN_COLORS = {
        1:  "#bbf7d0",
        3:  "#4ade80",
        6:  "#22c55e",
        12: "#16a34a",
        24: "#15803d",
        36: "#14532d",
    }

    for i, (_, row) in enumerate(display_list.iterrows()):
        bank_nm    = row[COL["bank"]]
        prod_nm_raw = row[COL["bank_prod"]]
        prod_nm    = strip_deposit_type(prod_nm_raw)   # 헤더엔 괄호 제거한 이름
        bank_max   = row[COL["bank_max"]]
        rate_diff  = row[COL["rate_diff"]]
        rank       = i + 1

        label = f"**{rank}위** · {bank_nm}  |  {prod_nm}  |  최고금리 **{bank_max:.2f}%**  |  금리차 **+{rate_diff:.2f}%p**"

        with st.expander(label, expanded=False):
            if hist_df.empty:
                st.info("추이 데이터를 불러올 수 없습니다.")
            else:
                # 괄호 포함된 원래 이름들 전부 매칭 (자유/정액 둘 다 포함)
                prod_hist = hist_df[
                    (hist_df["kor_co_nm"] == bank_nm) &
                    (hist_df["fin_prdt_nm"].apply(strip_deposit_type) == prod_nm)
                ].copy()
                prod_hist["_deposit_type"] = prod_hist.apply(get_deposit_type, axis=1)

                if prod_hist.empty:
                    st.info("해당 상품의 금리 추이 데이터가 없습니다.")
                else:
                    available_periods = sorted(prod_hist["save_trm"].dropna().unique().tolist())
                    deposit_types     = sorted(prod_hist["_deposit_type"].unique().tolist())

                    # ── 기간 × 적립방식 멀티라인 그래프 ──
                    fig_exp = go.Figure()
                    for dtype in deposit_types:
                        dtype_df = prod_hist[prod_hist["_deposit_type"] == dtype]
                        color_map  = GREEN_COLORS if dtype == "정액" else BLUE_COLORS
                        line_dash  = "dot" if dtype == "정액" else "solid"
                        type_label = f" ({dtype})" if len(deposit_types) > 1 else ""

                        for trm in available_periods:
                            trm_df = dtype_df[dtype_df["save_trm"] == trm].sort_values("collected_at")
                            if trm_df.empty:
                                continue
                            color = color_map.get(int(trm), "#64748b")
                            fig_exp.add_trace(go.Scatter(
                                x=trm_df["collected_at"],
                                y=trm_df["intr_rate2"],
                                mode="lines+markers",
                                name=f"{int(trm)}개월{type_label}",
                                line=dict(color=color, width=2, dash=line_dash),
                                marker=dict(size=5),
                            ))

                    # Y축 여유 계산 (25%로 확대 — 범례 공간 확보)
                    all_rates = prod_hist["intr_rate2"].dropna()
                    y_min = all_rates.min()
                    y_max = all_rates.max()
                    y_pad = (y_max - y_min) * 0.25 if y_max != y_min else 0.15

                    fig_exp.update_layout(
                        plot_bgcolor="white", paper_bgcolor="white",
                        legend=dict(orientation="h", y=1.18, x=1, xanchor="right", title_text="기간 · 방식"),
                        yaxis=dict(
                            ticksuffix="%", gridcolor="#f1f5f9", title="최대금리 (%)",
                            range=[y_min - y_pad, y_max + y_pad],
                        ),
                        xaxis=dict(title="수집 날짜", gridcolor="#f1f5f9"),
                        margin=dict(l=10, r=10, t=40, b=10),
                        height=360,
                        title=dict(text=f"{bank_nm} · {prod_nm} — 기간별 최대금리 추이", font=dict(size=13), x=0),
                    )
                    st.plotly_chart(fig_exp, use_container_width=True)

                    # ── 결과 요약 (st 기본 문법) ──
                    st.divider()

                    # 적립방식 × 기간 조합으로 컬럼 구성
                    summary_items = []
                    for dtype in deposit_types:
                        for trm in available_periods:
                            trm_df = prod_hist[
                                (prod_hist["_deposit_type"] == dtype) &
                                (prod_hist["save_trm"] == trm)
                            ].sort_values("collected_at")
                            if not trm_df.empty:
                                summary_items.append((dtype, trm, trm_df))

                    sum_cols = st.columns(len(summary_items)) if summary_items else st.columns(1)
                    for ci, (dtype, trm, trm_df) in enumerate(summary_items):
                        first_r  = trm_df["intr_rate2"].iloc[0]
                        latest_r = trm_df["intr_rate2"].iloc[-1]
                        delta    = latest_r - first_r
                        type_label = f" ({dtype})" if len(deposit_types) > 1 else ""
                        with sum_cols[ci]:
                            st.metric(
                                label=f"{int(trm)}개월{type_label}",
                                value=f"{latest_r:.2f}%",
                                delta=f"{delta:+.2f}%p",
                            )

                    # 데이터 수집 기간
                    date_min = prod_hist["collected_at"].min().strftime("%Y-%m-%d")
                    date_max = prod_hist["collected_at"].max().strftime("%Y-%m-%d")
                    deposit_label = " · ".join([f"{d}적립식" if d != "일반" else "일반" for d in deposit_types])
                    st.caption(f"📅 수집 기간: {date_min} ~ {date_max}  |  기간 수: {len(available_periods)}개  |  적립 방식: {deposit_label}")

    st.markdown("")

    # ── 전체 보기 / 접기 버튼 ──
    if len(dedup_df) > TOP_N:
        remaining = len(dedup_df) - TOP_N
        if not st.session_state["show_all_products"]:
            if st.button(f"📂 전체 보기 (나머지 {remaining}개 더 보기)"):
                st.session_state["show_all_products"] = True
                st.rerun()
        else:
            if st.button("🔼 접기 (상위 5개만 보기)"):
                st.session_state["show_all_products"] = False
                st.rerun()

# ══════════════════════════════════════════
# TAB 2: 경쟁 구조
# ══════════════════════════════════════════
with tabs[1]:
    st.markdown("### 🗺️ 경쟁 구조")
    st.markdown('<div class="desc-box">타행이 어느 저축 기간에 집중적으로 경쟁하는지 파악합니다. 히트맵으로 타행 × 기간 조합의 경쟁 강도를 확인하세요.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">타행 × 저축기간 금리차 히트맵</div>', unsafe_allow_html=True)
    pivot = fdf.groupby([COL["bank"], COL["period"]])[COL["rate_diff"]].max().reset_index()
    pivot_table = pivot.pivot(index=COL["bank"], columns=COL["period"], values=COL["rate_diff"]).fillna(0)
    # 저축 기간 순서 정렬
    pivot_table = pivot_table.reindex(columns=[p for p in PERIOD_ORDER if p in pivot_table.columns])

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
    # 저축 기간 순서 정렬
    vuln_pivot = vuln_pivot.reindex(columns=[p for p in PERIOD_ORDER if p in vuln_pivot.columns])

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
# TAB 3: 금리 변동 추이
# ══════════════════════════════════════════
with tabs[2]:
    st.markdown("### 📈 금리 변동 추이")
    st.markdown('<div class="desc-box">특정 상품의 날짜별 금리 변동을 추적합니다. 매일 수집된 데이터를 바탕으로 기본금리와 최대금리가 언제 어떻게 바뀌었는지 확인하세요.</div>', unsafe_allow_html=True)

    if hist_df.empty:
        st.warning("추이 데이터를 불러올 수 없습니다.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            all_banks_hist = sorted(hist_df["kor_co_nm"].dropna().unique().tolist())
            sel_bank_hist  = st.selectbox("은행 선택", all_banks_hist, key="hist_bank")
        with col2:
            products_of_bank = sorted(hist_df[hist_df["kor_co_nm"] == sel_bank_hist]["fin_prdt_nm"].dropna().unique().tolist())
            sel_prod_hist    = st.selectbox("상품 선택", products_of_bank, key="hist_prod")
        with col3:
            periods_of_prod = sorted(hist_df[
                (hist_df["kor_co_nm"] == sel_bank_hist) &
                (hist_df["fin_prdt_nm"] == sel_prod_hist)
            ]["save_trm"].dropna().unique().tolist())
            sel_trm_hist = st.selectbox("저축 기간(개월)", periods_of_prod, key="hist_trm")

        trend_df = hist_df[
            (hist_df["kor_co_nm"] == sel_bank_hist) &
            (hist_df["fin_prdt_nm"] == sel_prod_hist) &
            (hist_df["save_trm"] == sel_trm_hist)
        ].sort_values("collected_at").reset_index(drop=True)

        if trend_df.empty:
            st.info("해당 조건의 데이터가 없습니다.")
        else:
            trend_df["base_changed"] = trend_df["intr_rate"].diff().ne(0)
            trend_df["max_changed"]  = trend_df["intr_rate2"].diff().ne(0)
            trend_df["any_changed"]  = trend_df["base_changed"] | trend_df["max_changed"]
            changed_df = trend_df[trend_df["any_changed"] & (trend_df.index > 0)]

            st.markdown('<div class="section-title">날짜별 금리 추이</div>', unsafe_allow_html=True)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=trend_df["collected_at"], y=trend_df["intr_rate"],
                mode="lines+markers", name="기본금리",
                line=dict(color="#93c5fd", width=2), marker=dict(size=5),
            ))
            fig_trend.add_trace(go.Scatter(
                x=trend_df["collected_at"], y=trend_df["intr_rate2"],
                mode="lines+markers", name="최대금리",
                line=dict(color="#1d4ed8", width=2.5), marker=dict(size=5),
            ))
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

            # ── 금리 변동 이력 테이블 (이전 수치 → 현재 수치 포함) ──
            st.markdown('<div class="section-title">금리 변동 이력</div>', unsafe_allow_html=True)
            if len(changed_df) == 0:
                st.info("조회 기간 내 금리 변동 이력이 없습니다.")
            else:
                change_rows = []
                for idx in changed_df.index:
                    prev_idx = idx - 1
                    curr = trend_df.loc[idx]
                    prev = trend_df.loc[prev_idx]

                    base_diff = curr["intr_rate"]  - prev["intr_rate"]
                    max_diff  = curr["intr_rate2"] - prev["intr_rate2"]

                    change_rows.append({
                        "기준일 (이전)":    prev["collected_at"].strftime("%Y-%m-%d"),
                        "변동일 (현재)":    curr["collected_at"].strftime("%Y-%m-%d"),
                        "기본금리 이전(%)": f"{prev['intr_rate']:.2f}%",
                        "기본금리 현재(%)": f"{curr['intr_rate']:.2f}%",
                        "기본금리 변동":    f"{'+' if base_diff >= 0 else ''}{base_diff:.2f}%p",
                        "최대금리 이전(%)": f"{prev['intr_rate2']:.2f}%",
                        "최대금리 현재(%)": f"{curr['intr_rate2']:.2f}%",
                        "최대금리 변동":    f"{'+' if max_diff >= 0 else ''}{max_diff:.2f}%p",
                    })

                change_display = pd.DataFrame(change_rows)
                st.dataframe(change_display, use_container_width=True, height=250)

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
# TAB 4: 전체 데이터
# ══════════════════════════════════════════
with tabs[3]:
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
