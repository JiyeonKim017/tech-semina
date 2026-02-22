"""
우리은행 Rate Intelligence Dashboard v5
- 순수 Streamlit 컴포넌트만 사용 (CSS 없음)
- tech_semina.db 연동
- 더미 데이터: rate_changes, email_logs
"""
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import os

st.set_page_config(
    page_title="우리은행 Rate Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════
# DB 연결
# ══════════════════════════════════════════════════════════════════
DB_PATH = os.path.join(os.path.dirname(__file__), "tech_semina.db")

@st.cache_resource
def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}")

@st.cache_data(ttl=60)
def load_products():
    df = pd.read_sql("SELECT * FROM all_products", get_engine())
    df["save_trm"]   = df["save_trm"].astype(str)
    df["intr_rate"]  = pd.to_numeric(df["intr_rate"],  errors="coerce")
    df["intr_rate2"] = pd.to_numeric(df["intr_rate2"], errors="coerce")
    df["max_limit"]  = pd.to_numeric(df["max_limit"],  errors="coerce")
    return df

# 함수 인자에 woori_rate를 추가합니다.
def draw_comp_bar(name, rate, pct, is_woori=False, woori_rate=0.0):
    # 1. 색상 결정 로직 수정
    if is_woori:
        bar_color = "#0067ac" # 우리은행은 고유 파란색 유지
        text_style = "font-weight: bold; color: #0067ac;"
        label_prefix = "▶ "
    elif rate > woori_rate:
        # 우리은행보다 높은 경우: 상단 붉은색 그라데이션 (밝은 빨강 -> 진한 빨강)
        bar_color = "linear-gradient(90deg, #ff5f6d, #ff3131)" 
        text_style = "color: #ff3131;"
        label_prefix = ""
    else:
        # 우리은행보다 낮은 경우: 하단 회색
        bar_color = "#D1D8E0"
        text_style = ""
        label_prefix = ""

    st.markdown(f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 14px; {text_style}">{label_prefix}{name}</span>
                <span style="font-size: 14px; {text_style}">{rate:.2f}%</span>
            </div>
            <div style="background-color: #f0f2f6; border-radius: 4px; width: 100%; height: 8px;">
                <div style="background: {bar_color}; width: {pct*100}%; height: 100%; border-radius: 4px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 더미 데이터
# ══════════════════════════════════════════════════════════════════
DUMMY_CHANGES = [
    {"bank": "한국스탠다드차타드은행", "product": "e-그린세이브예금",
     "type": "금리인상", "from_rate": 2.95, "to_rate": 3.25, "trm": "12개월", "detected_at": "02-19 08:21"},
    {"bank": "아이엠뱅크", "product": "iM함께적금",
     "type": "금리인상", "from_rate": 3.30, "to_rate": 3.60, "trm": "12개월", "detected_at": "02-18 14:05"},
    {"bank": "부산은행", "product": "더(The) 특판 정기예금",
     "type": "신규출시", "from_rate": None, "to_rate": 2.70, "trm": "6개월", "detected_at": "02-17 09:00"},
    {"bank": "부산은행", "product": "저탄소 실천 적금",
     "type": "금리인하", "from_rate": 2.50, "to_rate": 2.20, "trm": "36개월", "detected_at": "02-17 07:30"},
    {"bank": "한국스탠다드차타드은행", "product": "퍼스트가계적금",
     "type": "금리인상", "from_rate": 2.50, "to_rate": 2.80, "trm": "36개월", "detected_at": "02-15 10:12"},
]

DUMMY_EMAILS = [
    {"subject": "[긴급] SC제일은행 금리 인상 감지 (3.25%)", "time": "08:21"},
    {"subject": "[알림] 아이엠뱅크 iM함께적금 금리 변동", "time": "02-18"},
    {"subject": "[알림] 부산은행 더(The) 특판 신규 출시", "time": "02-17"},
    {"subject": "[주간] 금리 동향 리포트 (2/10~2/16)", "time": "02-16"},
    {"subject": "[긴급] 아이엠뱅크 iM함께예금 신규 출시", "time": "02-10"},
]

DUMMY_DAG = [
    {"name": "fetch_fss_data",     "status": "success", "last": "09:00", "duration": "1m 42s", "next": "10:00"},
    {"name": "upsert_to_postgres", "status": "success", "last": "09:02", "duration": "0m 21s", "next": "10:02"},
    {"name": "send_gmail",         "status": "failed",  "last": "09:03", "duration": "—",      "next": "—",
     "error": "SMTPAuthenticationError: Gmail App Password expired"},
]

# ══════════════════════════════════════════════════════════════════
# 데이터 준비
# ══════════════════════════════════════════════════════════════════
df = load_products()
all_banks = sorted(df["kor_co_nm"].unique().tolist())

def get_woori_bench(ptype="예금", trm="12"):
    w = df[(df["kor_co_nm"] == "우리은행") & (df["product_type"] == ptype) & (df["save_trm"] == trm)]
    return (float(w["intr_rate2"].max()), w["fin_prdt_nm"].iloc[0]) if not w.empty else (None, None)

woori_rate_12, woori_prod_12 = get_woori_bench()

all12     = df[(df["product_type"] == "예금") & (df["save_trm"] == "12")]
top_rate  = float(all12["intr_rate2"].max()) if not all12.empty else 0
top_bank  = all12.loc[all12["intr_rate2"].idxmax(), "kor_co_nm"] if not all12.empty else "-"
w12       = all12[all12["kor_co_nm"] == "우리은행"]
woori_best = float(w12["intr_rate2"].max()) if not w12.empty else 0
gap_top   = round(top_rate - woori_best, 2)

rank_list  = all12.drop_duplicates("kor_co_nm").sort_values("intr_rate2", ascending=False)["kor_co_nm"].tolist()
woori_rank = rank_list.index("우리은행") + 1 if "우리은행" in rank_list else "-"
total_banks_cnt = len(rank_list)

change_cnt = len(DUMMY_CHANGES)
change_new = sum(1 for c in DUMMY_CHANGES if c["type"] == "신규출시")
change_up  = sum(1 for c in DUMMY_CHANGES if c["type"] == "금리인상")

# session_state 초기화
for k in ["show_changes_all", "show_email_all"]:
    if k not in st.session_state:
        st.session_state[k] = False

now = datetime.now()
weekdays = ["월", "화", "수", "목", "금", "토", "일"]


# ══════════════════════════════════════════════════════════════════
# ① 헤더
# ══════════════════════════════════════════════════════════════════
col_title, col_refresh = st.columns([6, 1])
with col_title:
    st.title("🏦 데일리 브리프")
    st.caption(f"{weekdays[now.weekday()]}요일 {now.strftime('%Y-%m-%d %H:%M')} 기준 · 오늘 수집 완료 ✓  |  DAG: 🟢 fetch · 🟢 upsert · 🔴 gmail")
with col_refresh:
    st.write("")  # 여백
    if st.button("↻ 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ══════════════════════════════════════════════════════════════════
# [추가] CSS 커스텀: 진행 바(st.progress) 색상 변경
# ══════════════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
        /* 진행 바의 높이 조절 및 배경색 */
        .stProgress > div > div {
            height: 12px;
            background-color: #f0f2f6;
        }
        /* 실제 채워지는 바의 색상 (우리은행 메인 블루 계열) */
        .stProgress > div > div > div > div {
            background-color: #0067ac; 
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ══════════════════════════════════════════════════════════════════
# ② 알림 배너
# ══════════════════════════════════════════════════════════════════
rivals = df[
    (df["kor_co_nm"] != "우리은행") & (df["save_trm"] == "12") &
    (df["product_type"] == "예금") & (df["intr_rate2"] > woori_rate_12)
] if woori_rate_12 else pd.DataFrame()

if not rivals.empty:
    top_r = rivals.sort_values("intr_rate2", ascending=False).iloc[0]
    diff  = round(top_r["intr_rate2"] - woori_rate_12, 2)
    st.error(
        f"🚨 **{top_r['kor_co_nm']} — {top_r['fin_prdt_nm']}** 금리 우위 감지  |  "
        f"연 **{top_r['intr_rate2']:.2f}%** (우리은행 대비 **+{diff:.2f}%p**)  |  "
        f"12개월 예금 기준 초과 상품 {len(rivals)}개 감지 · 담당자 메일 발송 완료 ✉️"
    )
else:
    st.success("✅ 우리은행이 12개월 예금 기준 경쟁력을 유지하고 있습니다 — 타행 대비 금리 우위 유지 중")


# ══════════════════════════════════════════════════════════════════
# ③ KPI 카드
# ══════════════════════════════════════════════════════════════════
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        label="🏆 업계 최고금리 (12개월 예금)",
        value=f"{top_rate:.2f}%",
        delta=f"{top_bank} 선두",
        delta_color="inverse"
    )
with k2:
    st.metric(
        label="🏦 우리은행 최고금리 (12개월)",
        value=f"{woori_best:.2f}%",
        delta=f"업계 {woori_rank}위 / {total_banks_cnt}개 은행",
        delta_color="inverse" if isinstance(woori_rank, int) and woori_rank > 3 else "normal"
    )
with k3:
    st.metric(
        label="📉 1위와의 금리 차이",
        value=f"-{gap_top:.2f}%p" if gap_top > 0 else "0.00%p",
        delta="격차 존재" if gap_top > 0 else "선두 유지",
        delta_color="inverse" if gap_top > 0 else "normal"
    )
with k4:
    st.metric(
        label="🔔 이번 주 감지된 변화",
        value=f"{change_cnt}건",
        delta=f"신규 {change_new}건 · 인상 {change_up}건",
        delta_color="off"
    )

st.divider()


# ══════════════════════════════════════════════════════════════════
# ④ 금리 비교 테이블 + 이번 주 변동 내역
# ══════════════════════════════════════════════════════════════════
col_tbl, col_log = st.columns([1.5, 1], gap="large")

# ── 금리 비교 테이블 ─────────────────────────────────────────
with col_tbl:
    st.subheader("📊 은행별 금리 비교")

    f1, f2 = st.columns(2)
    with f1:
        prod_sel = st.selectbox("상품 유형", ["예금", "적금"], key="prod_sel")
    with f2:
        trm_sel = st.selectbox("저축 기간", ["6개월", "12개월", "24개월"], index=1, key="trm_sel")

    trm_val = trm_sel.replace("개월", "")
    fdf = df[(df["product_type"] == prod_sel) & (df["save_trm"] == trm_val)]

    summary = (
        fdf.groupby("kor_co_nm")
        .agg(
            기본금리=("intr_rate", "max"),
            최고금리=("intr_rate2", "max"),
            대표상품=("fin_prdt_nm", "first"),
        )
        .reset_index()
        .sort_values("최고금리", ascending=False)
        .reset_index(drop=True)
    )
    summary.index = summary.index + 1
    summary.index.name = "순위"

    w_ref = float(summary[summary["kor_co_nm"] == "우리은행"]["최고금리"].values[0]) \
            if "우리은행" in summary["kor_co_nm"].values else 0

    summary["우리 대비"] = summary["최고금리"].apply(
        lambda x: "기준" if abs(x - w_ref) < 0.001 else f"+{x - w_ref:.2f}%p" if x > w_ref else f"{x - w_ref:.2f}%p"
    )
    summary["기본금리"] = summary["기본금리"].apply(lambda x: f"{x:.2f}%")
    summary["최고금리"] = summary["최고금리"].apply(lambda x: f"{x:.2f}%")
    summary = summary.rename(columns={"kor_co_nm": "은행"})
    summary = summary[["은행", "대표상품", "기본금리", "최고금리", "우리 대비"]]

    # 우리은행 행 하이라이트
    def highlight_woori(row):
        if row["은행"] == "우리은행":
            return ["background-color: #e8f1fb; font-weight: bold"] * len(row)
        return [""] * len(row)

    st.dataframe(
        summary.style.apply(highlight_woori, axis=1),
        use_container_width=True,
        hide_index=False,
    )

# ── 이번 주 변동 내역 ────────────────────────────────────────
with col_log:
    st.subheader("📰 이번 주 변동 내역")
    st.caption("🔴 신규출시 · 위협  🟡 금리인상  🟢 금리인하 · 안정")

    n = len(DUMMY_CHANGES) if st.session_state.show_changes_all else 4
    for c in DUMMY_CHANGES[:n]:
        if c["type"] == "신규출시":
            desc = f"신규 상품 출시 · 연 {c['to_rate']:.2f}%"
            fn = st.error
            icon = "🔴"
        elif c["type"] == "금리인상":
            desc = f"금리 인상: {c['from_rate']:.2f}% → {c['to_rate']:.2f}%"
            fn = st.warning
            icon = "🟡"
        else:
            desc = f"금리 인하: {c['from_rate']:.2f}% → {c['to_rate']:.2f}%"
            fn = st.success
            icon = "🟢"

        fn(
            f"{icon} **{c['bank']}** — {c['product']}  \n"
            f"{desc}  |  {c['trm']} · {c['detected_at']}"
        )

    if st.button(
        "▲ 접기" if st.session_state.show_changes_all else "전체 보기 ▼",
        key="btn_changes"
    ):
        st.session_state.show_changes_all = not st.session_state.show_changes_all
        st.rerun()

st.divider()


# ══════════════════════════════════════════════════════════════════
# ⑤ 경쟁력 분석 + Airflow + 이메일
# ══════════════════════════════════════════════════════════════════
col_comp, col_sys = st.columns([1.2, 1], gap="large")

# ── 경쟁력 분석 ─────────────────────────────────────────────
with col_comp:
    # 금리 비교 테이블 필터값 그대로 읽어오기
    comp_prod = st.session_state.get("prod_sel", "예금")
    comp_trm  = st.session_state.get("trm_sel",  "12개월").replace("개월", "")

    st.subheader("🎯 우리은행 경쟁력 분석")
    st.caption(f"{comp_trm}개월 정기{comp_prod} 기준")

    # 선택 기준으로 데이터 재집계
    comp_df   = df[(df["product_type"] == comp_prod) & (df["save_trm"] == comp_trm)]
    comp_best = comp_df.groupby("kor_co_nm")["intr_rate2"].max().reset_index()
    comp_best = comp_best.sort_values("intr_rate2", ascending=False).reset_index(drop=True)

    comp_top_rate  = float(comp_best["intr_rate2"].max()) if not comp_best.empty else 0
    comp_top_bank  = comp_best.iloc[0]["kor_co_nm"] if not comp_best.empty else "-"
    comp_woori_row = comp_best[comp_best["kor_co_nm"] == "우리은행"]
    comp_woori_best= float(comp_woori_row["intr_rate2"].values[0]) if not comp_woori_row.empty else 0
    comp_gap       = round(comp_top_rate - comp_woori_best, 2)

    if comp_gap > 0:
        st.warning(f"1위 달성에 필요한 금리 인상: **+{comp_gap:.2f}%p → {comp_top_rate:.2f}%**")
    elif comp_woori_best > 0:
        st.success(f"✅ 우리은행이 {comp_prod} {comp_trm}개월 기준 **1위**입니다!")

    max_val = comp_top_rate if comp_top_rate > 0 else 1
    
    for _, row in comp_best.iterrows():
        name = row["kor_co_nm"]
        rate = row["intr_rate2"]
        pct  = rate / max_val
        is_w = (name == "우리은행")
        
        # woori_rate 인자를 추가하여 기준점을 전달합니다.
        draw_comp_bar(name, rate, pct, is_woori=is_w, woori_rate=comp_woori_best)  

    # 현재 선택 기간 기준 순위 + 인접 기간 참고
    st.write("")
    def get_rank(ptype, trm_v):
        sub = df[(df["product_type"] == ptype) & (df["save_trm"] == trm_v)]
        rl  = sub.drop_duplicates("kor_co_nm").sort_values("intr_rate2", ascending=False)["kor_co_nm"].tolist()
        r   = rl.index("우리은행") + 1 if "우리은행" in rl else "-"
        return r, len(rl)

    # 현재 선택 기간 기준으로 인접 기간 3개 표시
    all_trms   = sorted(df["save_trm"].unique().tolist(), key=lambda x: int(x))
    cur_idx    = all_trms.index(comp_trm) if comp_trm in all_trms else 0
    show_trms  = all_trms[max(0, cur_idx-1) : cur_idx+2]   # 앞뒤 1개씩

    rank_cols = st.columns(len(show_trms))
    for col, t in zip(rank_cols, show_trms):
        r, total = get_rank(comp_prod, t)
        label_t  = f"{t}개월" + (" ◀" if t == comp_trm else "")
        with col:
            st.metric(label_t, f"{r}위", delta=f"/ {total}개 은행", delta_color="off")


# ── Airflow + 이메일 ─────────────────────────────────────────
with col_sys:
    # Airflow DAG
    st.subheader("⚙️ Airflow DAG 현황")

    for dag in DUMMY_DAG:
        if dag["status"] == "success":
            st.success(
                f"🟢 **{dag['name']}**  |  "
                f"마지막 실행: {dag['last']} · 소요: {dag['duration']} · 다음: {dag['next']}"
            )
        else:
            st.error(
                f"🔴 **{dag['name']}**  |  마지막 실행: {dag['last']}  \n"
                f"⚠️ `{dag.get('error', '알 수 없는 오류')}`"
            )

    st.divider()

    # 이메일 발송 내역
    st.subheader("✉️ 최근 알림 발송 내역")

    n_mail = len(DUMMY_EMAILS) if st.session_state.show_email_all else 3
    for m in DUMMY_EMAILS[:n_mail]:
        st.write(f"✉️ {m['subject']}  `{m['time']}`  ✅ 발송")

    if st.button(
        "▲ 접기" if st.session_state.show_email_all else "전체 보기 ▼",
        key="btn_email"
    ):
        st.session_state.show_email_all = not st.session_state.show_email_all
        st.rerun()

st.divider()


# ══════════════════════════════════════════════════════════════════
# ⑥ 상품 상세 우대조건
# ══════════════════════════════════════════════════════════════════
st.subheader("📋 상품별 우대조건 상세 분석")

f1, f2, f3 = st.columns([1, 1, 1])
with f1:
    dp_type = st.selectbox("상품 유형", ["예금", "적금"], key="dp_type")
with f2:
    dp_trm  = st.selectbox("저축 기간", ["6개월", "12개월", "24개월"], index=1, key="dp_trm")
with f3:
    dp_bank = st.selectbox("은행 선택", ["전체"] + all_banks, key="dp_bank")

dp_df = df[(df["product_type"] == dp_type) & (df["save_trm"] == dp_trm.replace("개월", ""))]
if dp_bank != "전체":
    dp_df = dp_df[dp_df["kor_co_nm"] == dp_bank]

detail = dp_df.drop_duplicates(subset=["fin_prdt_cd", "kor_co_nm"]).copy()
detail["_sort"] = detail["kor_co_nm"].apply(lambda x: 0 if x == "우리은행" else 1)
detail = detail.sort_values(["_sort", "intr_rate2"], ascending=[True, False])

if detail.empty:
    st.info("선택한 조건에 해당하는 상품이 없습니다.")
else:
    for _, row in detail.iterrows():
        is_w    = row["kor_co_nm"] == "우리은행"
        gap_val = round(row["intr_rate2"] - row["intr_rate"], 2)
        rdiff   = round(row["intr_rate2"] - woori_best, 2) if woori_best and not is_w else None

        label = f"{'🏦' if is_w else '🔍'} [{row['kor_co_nm']}] {row['fin_prdt_nm']}  |  최고 {row['intr_rate2']:.2f}%  ·  기본 {row['intr_rate']:.2f}%"
        if pd.notna(row.get("max_limit")):
            label += f"  ·  한도 {int(row['max_limit']):,}원"

        with st.expander(label):
            ca, cb = st.columns([1.2, 1])

            with ca:
                st.markdown("**📜 우대조건**")
                spcl = row.get("spcl_cnd", "")
                if pd.isna(spcl) or str(spcl).strip() in ["", "해당사항 없음", "없음"]:
                    st.caption("우대조건 없음 (단일금리 상품)")
                else:
                    st.text(spcl)
                if row.get("join_way"):
                    st.caption(f"🖥️ 가입 채널: {row['join_way']}")

            with cb:
                st.markdown("**💡 분석 인사이트**")

                # 우대 Gap
                if gap_val == 0:      label_g, dc = "우대조건 없음", "off"
                elif gap_val < 0.3:   label_g, dc = "달성 쉬움 🟢", "normal"
                elif gap_val < 0.8:   label_g, dc = "달성 보통 🟡", "off"
                else:                 label_g, dc = "달성 어려움 🔴", "inverse"

                st.metric("우대 Gap", f"+{gap_val:.2f}%p", delta=label_g, delta_color=dc)

                # 경쟁 위협
                if rdiff is not None:
                    if rdiff > 0:
                        st.warning(f"⚠️ 경쟁 위협: 우리은행 대비 **+{rdiff:.2f}%p**")
                    else:
                        st.success(f"✅ 경쟁력 우위: 우리은행 대비 **{rdiff:.2f}%p**")

                # 한도
                if pd.notna(row.get("max_limit")):
                    lure = row["max_limit"] < 1_000_000
                    if lure:
                        st.error(f"❗ 미끼형 상품 주의: 한도 {int(row['max_limit']):,}원")
                    else:
                        st.success(f"✅ 실질 경쟁 상품: 한도 {int(row['max_limit']):,}원")

# ══════════════════════════════════════════════════════════════════
# 푸터
# ══════════════════════════════════════════════════════════════════
st.divider()
st.caption("📡 데이터 출처: 금융감독원 금융상품 한눈에 API  ·  SQLite: tech_semina.db  ·  Airflow Pipeline 자동 수집  |  우리은행 상품기획팀 내부용")