import json
import random
import re
from datetime import date, timedelta
import google.generativeai as genai
import pandas as pd
import streamlit as st

st.set_page_config(page_title="육군 인사 및 의무교육 관제", layout="wide")

st.markdown("""
<style>
    .main-title {
        font-size: 24px !important;
        font-weight: bold;
        color: #1E3A8A;
        border-bottom: 2px solid #1E3A8A;
        padding-bottom: 8px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

USER_DB = {
    "6bde": {
        "password": "1234",
        "name": "김지휘 대위 (6여단)",
        "unit": "6여단",
        "accessible_units": [
            "6여단 본부", "6여단 101대대 본부", "6여단 101대대 1중대", 
            "6여단 101대대 2중대", "6여단 102대대", "6여단 103대대", 
            "6여단 포병대대", "6여단 수송대대", "6여단 정비대대"
        ]
    },
    "101bn": {
        "password": "1234",
        "name": "강우진 중사 (101대대)",
        "unit": "6여단 101대대",
        "accessible_units": [
            "6여단 101대대 본부", "6여단 101대대 1중대", "6여단 101대대 2중대"
        ]
    },
    "HQ": {
        "password": "1234",
        "name": "박군수 소령 (상급부대)",
        "unit": "군수사령부",
        "accessible_units": ["ALL"]
    }
}

if not st.session_state["logged_in"]:
    st.markdown('<div class="main-title">🛡️ 육군 관제 시스템 - 로그인</div>', unsafe_allow_html=True)
    st.info("💡 계정: 6bde / 101bn / HQ (비밀번호: 1234)")
    with st.form("login_form"):
        u = st.text_input("아이디")
        p = st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인", type="primary", use_container_width=True):
            if u in USER_DB and USER_DB[u]["password"] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.rerun()
            else:
                st.error("❌ 비밀번호 오류")
    st.stop()

current_user = USER_DB[st.session_state["username"]]

gemini_api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    try:
        genai.configure(api_key=gemini_api_key)
    except Exception:
        pass

with st.sidebar:
    st.markdown("### 🎖️ 접속 프로필")
    st.write("성명:", current_user["name"])
    st.write("소속:", current_user["unit"])
    st.divider()
    st.markdown("### 🔑 AI 참모 연동")
    if gemini_api_key:
        st.success("🟢 Gemini AI 연동 완료")
    else:
        st.warning("🔴 API Key 설정 필요")
    st.divider()
    if st.button("🚪 로그아웃", type="secondary", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

st.markdown('<div class="main-title">🛡️ [' + str(current_user["unit"]) + '] Gemini LLM 관제 대시보드</div>', unsafe_allow_html=True)

@st.cache_data
def generate_personnel_db():
    random.seed(42)
    today = date(2026, 8, 30)

    u_6bde = [
        "6여단 본부", "6여단 101대대 본부", "6여단 101대대 1중대", 
        "6여단 101대대 2중대", "6여단 102대대", "6여단 103대대", 
        "6여단 포병대대", "6여단 수송대대", "6여단 정비대대"
    ]
    u_oth = ["군수사령부 직할대", "작전사령부 본부", "1군단 사령부", "5사단 본부"]

    ln = ["김", "이", "박", "최", "정", "강", "조", "윤"]
    fn = ["민준", "서준", "도현", "우진", "지후", "하준"]
    rk = ["하사", "중사", "상사", "원사", "소위", "중위", "대위"]
    br = ["통신", "병기", "수송", "보급", "보병", "포병"]
    cp = ["대형운전면허", "특수운전면허", "구난차운전면허", "정보처리기사", "없음"]
    ep = ["수송안전교육(이수)", "구난차량운용교육(이수)", "안전관리교육(이수)"]
    ap = ["즉시 가용", "2026-08-31", "임무 수행 중"]
    rt = ["S", "A+", "A", "B+", "B"]
    cs = ["자살예방교육", "성폭력 예방교육", "보안 및 정보보호교육", "군대윤리교육"]

    data = []
    for i in range(1, 301):
        name = random.choice(ln) + random.choice(fn)
        sn = str(random.randint(15, 25)) + "-" + str(10000 + i)
        rank = random.choice(rk)
        branch = random.choice(br)
        unit = random.choice(u_6bde) if i <= 240 else random.choice(u_oth)

        if i % 10 == 0:
            branch = "수송"
            cert = "특수운전면허, 구난차운전면허"
            edu = "구난차량운용교육(이수), 수송안전교육(이수)"
        else:
            cert = random.choice(cp)
            edu = random.choice(ep)

        exp = str(random.randint(1, 15)) + "년"
        avail = random.choice(ap)
        rating = random.choice(rt)
        course = random.choice(cs)
        status = random.choices(["이수완료", "미이수"], weights=[0.7, 0.3])[0]

        days = random.choice([-3, -1, 2, 4, 6, 10, 18, 25])
        due = today + timedelta(days=days)

        data.append({
            "소속부대": unit,
            "군번": sn,
            "성명": name,
            "계급": rank,
            "병과": branch,
            "보유자격증": cert,
            "교육이수현황": edu,
            "관련경력": exp,
            "투입가용일": avail,
            "최종평정": rating,
            "필수의무교육": course,
            "이수상태": status,
            "교육마감일": due.strftime("%Y-%m-%d"),
            "D_Day": (due - today).days
        })

    return pd.DataFrame(data)

raw_df = generate_personnel_db()

if current_user["accessible_units"] == ["ALL"]:
    df = raw_df.copy()
else:
    df = raw_df[raw_df["소속부대"].isin(current_user["accessible_units"])].copy()

tab1, tab2 = st.tabs(["🤖 1. 적합자 분석", "🚨 2. 의무교육 관제"])

with tab1:
    st.subheader("🤖 Gemini AI 인사 추론")
    st.write("📊 관할 부대 인원: **총", len(df), "명**")

    user_prompt = st.text_input(
        "💡 임무 요구사항:",
        value="내일 바로 구난차 끌고 출동할 수 있는 숙련된 간부 찾아줘"
    )
    top_n = st.slider("🎯 추출 인원 수:", min_value=1, max_value=5, value=3)

    if st.button("🚀 AI 분석 실행", type="primary"):
        if not user_prompt.strip():
            st.warning("요구사항을 입력하세요.")
        else:
            with st.spinner("🤖 심사 진행 중..."):
                if gemini_api_key:
                    try:
                        kw = [w for w in ["구난", "운전", "드론", "통신", "위험물", "보급"] if w in user_prompt.lower()]
                        if kw:
                            pat = "|".join(kw)
                            fc = df[df["보유자격증"].str.contains(pat, na=False) | df["교육이수현황"].str.contains(pat, na=False) | df["병과"].str.contains(pat, na=False)]
                            if len(fc) < 5:
                                fc = df.head(20)
                        else:
                            fc = df.head(20)

                        cols = ["소속부대", "성명", "계급", "병과", "보유자격증", "교육이수현황", "관련경력", "투입가용일", "최종평정"]
                        db_j = fc.head(15)[cols].to_json(orient="records", force_ascii=False)

                        p_txt = "육군 인사참모 AI다. DB에서 상위 " + str(top_n) + "명을 추천해라.\n요구:" + user_prompt + "\nDB:" + db_j + '\nJSON만 응답:[{"성명":"이름","계급":"계급","소속부대":"부대","적합도점수":95,"추천사유":"사유"}]'

                        m = genai.GenerativeModel("gemini-3.6-flash")
                        res = m.generate_content(p_txt)
                        c_txt = re.sub(r"```(?:json)?", "", res.text).strip()
                        items = json.loads(c_txt)

                        st.success(f"🎯 최적격자 {len(items)}명 심사 완료")
                        for r, it in enumerate(items, 1):
                            t = f"🏅 {r}순위: [{it['소속부대']}] {it['성명']} {it['계급']} ({it['적합도점수']}점)"
                            with st.expander(t, expanded=True):
                                st.write("🤖 **판단 사유:**")
                                st.info(it["추천사유"])
                    except Exception as e:
                        st.error(f"연동 오류: {e}")
                else:
                    st.error("API 키 설정이 필요합니다.")

    st.divider()
    st.subheader("📋 관할 부대 간부 인사자력 현황")
    d_cols = ["소속부대", "군번", "성명", "계급", "병과", "보유자격증", "교육이수현황", "관련경력", "투입가용일", "최종평정"]
    st.dataframe(df[d_cols], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("📢 필수 의무교육 이수 관제")
    st.write("접속 권한: **[" + str(current_user["unit"]) + "]**")

    u_opts = ["관할 부대 전체"] + list(df["소속부대"].unique())
    sel_u = st.selectbox("📌 조회 부대 선택:", u_opts)

    edf = df if sel_u == "관할 부대 전체" else df[df["소속부대"] == sel_u].copy()
    un_df = edf[edf["이수상태"] == "미이수"]
    urg_df = un_df[un_df["D_Day"] <= 7]
    comp = len(edf[edf["이수상태"] == "이수완료"])
    rate = round((comp / len(edf)) * 100, 1) if len(edf) > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 대상 인원", f"{len(edf)}명")
    c2.metric("✅ 평균 이수율", f"{rate}%")
    c3.metric("❌ 미이수 인원", f"{len(un_df)}명")
    c4.metric("🚨 마감 임박(D-7)", f"{len(urg_df)}명")

    st.divider()
    st.subheader("🚨 독려 대상자 목록")

    if len(urg_df) == 0:
        st.success("🎉 마감 임박 미이수자가 없습니다.")
    else:
        for idx, row in urg_df.sort_values(by="D_Day").head(15).iterrows():
            d_str = f"D-{row['D_Day']}일" if row["D_Day"] >= 0 else f"마감 {abs(row['D_Day'])}
