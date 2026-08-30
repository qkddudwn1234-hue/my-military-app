import json
import random
import re
from datetime import date, timedelta
import google.generativeai as genai
import pandas as pd
import streamlit as st

st.set_page_config(page_title="육군 인사 및 의무교육 관제 시스템", layout="wide")

# 1. 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# 관리자 커스텀 세션 상태 (컬러 및 차트 형태)
if "title_color" not in st.session_state:
    st.session_state["title_color"] = "#1E3A8A"
if "header_color" not in st.session_state:
    st.session_state["header_color"] = "#0F172A"
if "accent_color" not in st.session_state:
    st.session_state["accent_color"] = "#2563EB"
if "bg_color" not in st.session_state:
    st.session_state["bg_color"] = "#F8FAFC"
if "chart_type" not in st.session_state:
    st.session_state["chart_type"] = "세로 막대 차트"
if "unit_icon" not in st.session_state:
    st.session_state["unit_icon"] = "🛡️"
if "title_align" not in st.session_state:
    st.session_state["title_align"] = "left"
if "custom_title" not in st.session_state:
    st.session_state["custom_title"] = "LLM 인사 자력 & 의무교육 통합 관제 대시보드"

# Dynamic CSS
st.markdown(
    '<style>'
    'body, .stApp { background-color: ' + st.session_state["bg_color"] + ' !important; }'
    '.main-title {'
    '    font-size: 26px !important;'
    '    font-weight: 900 !important;'
    '    color: ' + st.session_state["title_color"] + ';'
    '    text-align: ' + st.session_state["title_align"] + ';'
    '    border-bottom: 3px solid ' + st.session_state["title_color"] + ';'
    '    padding-bottom: 10px;'
    '    margin-bottom: 20px;'
    '}'
    'h2, h3, h4 {'
    '    color: ' + st.session_state["header_color"] + ' !important;'
    '}'
    '.accent-text {'
    '    color: ' + st.session_state["accent_color"] + ' !important;'
    '    font-weight: bold;'
    '}'
    '</style>',
    unsafe_allow_html=True
)

# 계정 DB (admin 비공개)
USER_DB = {
    "admin": {
        "password": "1234",
        "name": "최고관리자",
        "unit": "국방부/합참",
        "role": "ADMIN",
        "accessible_units": ["ALL"]
    },
    "6bde": {
        "password": "1234",
        "name": "김지휘 대위 (6여단)",
        "unit": "6여단",
        "role": "USER",
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
        "role": "USER",
        "accessible_units": [
            "6여단 101대대 본부", "6여단 101대대 1중대", "6여단 101대대 2중대"
        ]
    },
    "HQ": {
        "password": "1234",
        "name": "박군수 소령 (상급부대)",
        "unit": "군수사령부",
        "role": "USER",
        "accessible_units": ["ALL"]
    }
}

# 로그인 UI (admin 화면 노출 안 됨)
if not st.session_state["logged_in"]:
    st.markdown('<div class="main-title">🛡️ 대한민국 육군 통합 관제 시스템</div>', unsafe_allow_html=True)
    st.info("💡 **부대별 계정 정보:** 6여단 (`6bde`) | 101대대 (`101bn`) | 상급부대 (`HQ`) - 비밀번호: `1234`")
    
    with st.form("login_form"):
        u = st.text_input("아이디 (ID)")
        p = st.text_input("비밀번호 (PW)", type="password")
        if st.form_submit_button("로그인", type="primary", use_container_width=True):
            if u in USER_DB and USER_DB[u]["password"] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.rerun()
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다.")
    st.stop()

current_user = USER_DB[st.session_state["username"]]

gemini_api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    try:
        genai.configure(api_key=gemini_api_key)
    except Exception:
        pass

# 사이드바 설정
with st.sidebar:
    st.markdown("### " + st.session_state["unit_icon"] + " 접속 프로필")
    st.write("성명:", current_user["name"])
    st.write("소속:", current_user["unit"])
    st.divider()
    
    st.markdown("### 🔑 AI 참모 연동")
    if gemini_api_key:
        st.success("🟢 Gemini 3.6 Flash 연동")
    else:
        st.warning("🔴 API Key 설정 필요")
    st.divider()

    # 관리자 비밀 디자인 & 차트 컨트롤러
    if current_user.get("role") == "ADMIN":
        st.markdown("### 🎨 Admin 디자인 & 차트 커스텀")
        
        c_title_color = st.color_picker("메인 타이틀 텍스트 색상", st.session_state["title_color"])
        c_header_color = st.color_picker("서브 헤더 텍스트 색상", st.session_state["header_color"])
        c_accent_color = st.color_picker("강조 텍스트 색상", st.session_state["accent_color"])
        c_bg = st.color_picker("대시보드 배경 색상", st.session_state["bg_color"])
        
        c_chart = st.selectbox(
            "시각화 차트 형태 선택:",
            ["세로 막대 차트", "영역 차트"],
            index=["세로 막대 차트", "영역 차트"].index(st.session_state["chart_type"]) if st.session_state["chart_type"] in ["세로 막대 차트", "영역 차트"] else 0
        )
        
        c_align = st.radio("타이틀 정렬:", ["left", "center"], format_func=lambda x: "좌측 정렬" if x == "left" else "중앙 정렬")
        c_icon = st.selectbox("부대 아이콘:", ["🛡️", "🎖️", "⚔️", "🦅"])
        c_title = st.text_input("메인 타이틀 문구:", value=st.session_state["custom_title"])
        
        if st.button("🎨 설정 저장 및 즉시 적용", type="primary", use_container_width=True):
            st.session_state["title_color"] = c_title_color
            st.session_state["header_color"] = c_header_color
            st.session_state["accent_color"] = c_accent_color
            st.session_state["bg_color"] = c_bg
            st.session_state["chart_type"] = c_chart
            st.session_state["title_align"] = c_align
            st.session_state["unit_icon"] = c_icon
            st.session_state["custom_title"] = c_title
            st.rerun()
        st.divider()

    if st.button("🚪 로그아웃", type="secondary", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

# 헤더
header_txt = st.session_state["unit_icon"] + " [" + str(current_user["unit"]) + "] " + st.session_state["custom_title"]
st.markdown('<div class="main-title">' + header_txt + '</div>', unsafe_allow_html=True)

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

tab1, tab2 = st.tabs(["🤖 1. Gemini AI 인사 적합자 분석", "🚨 2. 예하부대 의무교육 관제 & 차트"])

# TAB 1
with tab1:
    st.subheader("🤖 Gemini 참모 AI 적합자 분석")
    st.write("📊 관할 부대 인원: **총", len(df), "명**")

    user_prompt = st.text_input(
        "💡 임무 요구사항 (자연어로 입력):",
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

                        st.success("🎯 최적격자 " + str(len(items)) + "명 심사 완료")
                        for r, it in enumerate(items, 1):
                            t = "🏅 " + str(r) + "순위: [" + str(it['소속부대']) + "] " + str(it['성명']) + " " + str(it['계급']) + " (" + str(it['적합도점수']) + "점)"
                            with st.expander(t, expanded=True):
                                st.write("🤖 **판단 사유:**")
                                st.markdown('<p class="accent-text">' + str(it["추천사유"]) + '</p>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error("연동 오류: " + str(e))
                else:
                    st.error("API 키 설정이 필요합니다.")

    st.divider()
    st.subheader("📋 관할 부대 간부 인사자력 현황")
    d_cols = ["소속부대", "군번", "성명", "계급", "병과", "보유자격증", "교육이수현황", "관련경력", "투입가용일", "최종평정"]
    st.dataframe(df[d_cols], use_container_width=True, hide_index=True)

# TAB 2
with tab2:
    st.subheader("📢 필수 의무교육 관제 및 차트")
    st.write("접속 권한: **[" + str(current_user["unit"]) + "]** | 선택된 차트 스타일: **" + st.session_state["chart_type"] + "**")

    u_opts = ["관할 부대 전체"] + list(df["소속부대"].unique())
    sel_u = st.selectbox("📌 조회 부대 선택:", u_opts)

    edf = df if sel_u == "관
