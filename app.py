import streamlit as st
import pandas as pd
import random
import json
from datetime import datetime, date, timedelta
import google.generativeai as genai

# 1. 페이지 레이아웃 및 기본 설정
st.set_page_config(
    page_title="LLM 기반 대규모 군 인사 & 의무교육 관제 시스템",
    page_icon="🎖️",
    layout="wide"
)

# 2. 커스텀 CSS 디자인
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif !important;
    }
    
    .main-header {
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #1E3A8A !important;
        padding-bottom: 10px;
        border-bottom: 3px solid #1E3A8A;
        margin-bottom: 20px;
    }
    
    .card-box {
        background-color: #F8FAFC;
        border-left: 5px solid #1E3A8A;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }

    .warning-box {
        background-color: #FEF2F2;
        border-left: 5px solid #DC2626;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 로그인 및 부대 권한 세션 관리
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# 부대별 테스트 계정
USER_DB = {
    "6bde": {
        "password": "1234", 
        "name": "김지휘 대위 (6여단 인사실무자)", 
        "unit": "6여단",
        "accessible_units": [
            "6여단 본부", "6여단 101대대 본부", "6여단 101대대 1중대", "6여단 101대대 2중대",
            "6여단 102대대", "6여단 103대대", "6여단 포병대대", "6여단 수송대대", "6여단 정비대대"
        ]
    },
    "101bn": {
        "password": "1234", 
        "name": "강우진 중사 (101대대 인사담당관)", 
        "unit": "6여단 101대대",
        "accessible_units": ["6여단 101대대 본부", "6여단 101대대 1중대", "6여단 101대대 2중대"]
    },
    "HQ": {
        "password": "1234", 
        "name": "박군수 소령 (상급부대 인사처장)", 
        "unit": "군수사령부",
        "accessible_units": ["ALL"]
    }
}

# --- 로그인 화면 UI ---
if not st.session_state["logged_in"]:
    st.markdown('<div class="main-header">🔒 대규모 부대 인사 & 의무교육 관제 시스템 - 로그인</div>', unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.info(
            "💡 **부대 권한별 테스트 로그인 계정 (총 5,000명 DB 관제)**\n"
            "- **6여단 인사실무자:** ID `6bde` / PW `1234` (6여단 본부 및 예하 대대/중대 관제)\n"
            "- **101대대 인사담당관:** ID `101bn` / PW `1234` (101대대 본부 및 중대 전용 관제)\n"
            "- **상급부대 지휘관:** ID `HQ` / PW `1234` (전체 5,000명 부대 총괄)"
        )
        
        with st.form("login_form"):
            input_user = st.text_input("아이디 (ID)")
            input_pw = st.text_input("비밀번호 (Password)", type="password")
            submit_button = st.form_submit_button("로그인", type="primary", use_container_width=True)
            
            if submit_button:
                if input_user in USER_DB and USER_DB[input_user]["password"] == input_pw:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = input_user
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")
    st.stop()

# --- 로그인 후 메인 화면 ---
current_user = USER_DB[st.session_state["username"]]

# Streamlit Secrets 자동 연결
gemini_api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    try:
        genai.configure(api_key=gemini_api_key)
    except Exception:
        pass

with st.sidebar:
    st.write(f"👤 **접속자:** {current_user['name']}")
    st.write(f"🎖️ **소속:** {current_user['unit']}")
    st.divider()
    
    st.subheader("🔑 Gemini LLM 연동 상태")
    if gemini_api_key:
        st.caption("🟢 Gemini 3.6 Flash AI 초고속 연동 중")
    else:
        st.caption("🔴 Secrets 설정 필요 (Streamlit Cloud Settings 확인)")
            
    st.divider()
    if st.button("🚪 로그아웃", type="secondary"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

st.markdown(f'<div class="main-header">🤖 [{current_user["unit"]}] Gemini LLM 대규모 인사 & 의무교육 통합 관제</div>', unsafe_allow_html=True)

# 4. 5,000명 대규모 간부 DB 고속 생성 및 캐싱
@st.cache_data
def generate_5000_personnel():
    random.seed(42)
    today = date(2026, 8, 30)
    
    units_pool_6bde = [
        "6여단 본부", "6여단 101대대 본부", "6여단 101대대 1중대", "6여단 101대대 2중대",
        "6여단 102대대", "6여단 103대대", "6여단 포병대대", "6여단 수송대대", "6여단 정비대대"
    ]
    units_pool_others = ["군수사령부 직할대", "작전사령부 본부", "1군단 사령부", "5사단 본부"]
    
    last_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"]
    first_names = ["민준", "서준", "도현", "우진", "지후", "하준", "도윤", "시우", "유진", "소희", "지민", "서연", "하은", "지아", "수아", "예은", "지원", "현우", "건우", "성민"]
    ranks = ["하사", "중사", "상사", "원사", "소위", "중위", "대위", "소령", "중령"]
    branches = ["통신", "병기", "수송", "보급", "보병", "포병", "공병", "정보통신", "기갑", "항공"]
    
    cert_pool = [
        "대형운전면허", "특수운전면허", "구난차운전면허", "초경량비행장치 지도조종자", "초경량비행장치 조종자", 
        "무선통신산업기사", "정보처리기사", "위험물산업기사", "물류관리사", "자원관리사", "위험물관리자", "없음"
    ]
    
    edu_pool = [
        "수송안전교육(이수)", "구난차량운용교육(이수)", "드론전문교관과정(이수)", "드론기초조종과정(이수)", "군수재정교육(이수)",
        "자원관리교육(이수)", "보급기획과정(이수)", "안전관리교육(이수)", "지휘관과정(이수)"
    ]
    
    avail_pool = ["즉시 가용", "2026-08-31", "2026-09-01", "2026-09-05", "2026-09-10", "임무 수행 중(불가)"]
    ratings = ["S", "A+", "A", "B+", "B"]
    mandatory_courses = ["자살예방교육", "성폭력 예방교육", "보안 및 정보보호교육", "군대윤리교육"]
    
    data = []
    for i in range(1, 5001):
        name = random.choice(last_names) + random.choice(first_names)
        year = random.randint(15, 25)
        sn = f"{year}-{10000 + (i % 9000)}"
        rank = random.choice(ranks)
        branch = random.choice(branches)
        
        assigned_unit = random.choice(units_pool_6bde) if i <= 4000 else random.choice(units_pool_others)
            
        if i % 10 == 0:
            branch = "수송"
            cert = "특수운전면허, 구난차운전면허"
            edu = "구난차량운용교육(이수), 수송안전교육(이수)"
        elif i % 7 == 0:
            branch = "병기"
            cert = "위험물산업기사, 위험물관리자"
            edu = "안전관리교육(이수), 자원관리교육(이수)"
        elif i % 6 == 0:
            branch = "보급"
            cert = "물류관리사, 자원관리사"
            edu = "보급기획과정(이수), 군수재정교육(이수)"
        elif i % 4 == 0:
            branch = "수송"
            cert = random.choice(["대형운전면허", "특수운전면허"]) + ", " + random.choice(cert_pool[:4])
            edu = "수송안전교육(이수), " + random.choice(edu_pool)
        elif i % 3 == 0:
            cert = random.choice(["초경량비행장치 지도조종자", "초경량비행장치 조종자"]) + ", " + random.choice(cert_pool[4:])
            edu = "드론전문교관과정(이수), " + random.choice(edu_pool)
        else:
            cert = random.choice(cert_pool) + ", " + random.choice(cert_pool)
            edu = random.choice(edu_pool)
            
        exp = f"{random.randint(1, 15)}년"
        avail = random.choice(avail_pool)
        rating = random.choice(ratings)
        
        course_target = random.choice(mandatory_courses)
        status = random.choices(["이수완료", "미이수"], weights=[0.70, 0.30])[0]
        
        days_offset = random.choice([-3, -1, 2, 4, 6, 10, 18, 25])
        due_date = today + timedelta(days=days_offset)
        d_day_val = (due_date - today).days
        
        data.append({
            "소속부대": assigned_unit,
            "군번": sn,
            "성명": name,
            "계급": rank,
            "병과": branch,
            "보유자격증": cert,
            "교육이수현황": edu,
            "관련경력": exp,
            "투입가용일": avail,
            "최종평정": rating,
            "필수의무교육": course_target,
            "이수상태": status,
            "교육마감일": due_date.strftime("%Y-%m-%d"),
            "D_Day": d_day_val
        })
        
    return pd.DataFrame(data)

raw_df = generate_5000_personnel()

# 권한 기반 부대 데이터 필터링
if current_user["accessible_units"] == ["ALL"]:
    df = raw_df.copy()
else:
    df = raw_df[raw_df["소속부대"].isin(current_user["accessible_units"])].copy()

# 5. 대시보드 탭 구성을 위한 렌더링
tab1, tab2 = st.tabs(["🤖 1. Gemini LLM 기반 대규모 적합자 분석", "🚨 2. 예하 부대 의무교육 관제 대시보드"])

# ==========================================
# TAB 1: Gemini LLM 기반 초고속 적합자 추론
# ==========================================
with tab1:
    st.subheader("🤖 Gemini LLM 대규모 인사 자력 지능형 추론")
    st.write(f"현재 권한 관할 부대 DB 인원: **총 {len(df):,}명** (초고속 필터링 연동)")

    user_prompt = st.text_input(
        "임무 요구사항 (자연어로 자유롭게 입력):",
        value="내일 바로 구난차 끌고 현장 출동할 수 있는 숙련된 간부 찾아줘"
    )

    top_n = st.slider("최대 추출 인원 수 선택:", min_value=1, max_value=5, value=3)

    if st.button("🚀 Gemini LLM 실시간 분석 및 추천 실행", type="primary"):
        if not user_prompt.strip():
            st.warning("⚠️ 요구사항을 입력해 주세요.")
        else:
            with st.spinner("🤖 Python 초고속 스캔 후 Gemini AI가 핵심 적합자를 최종 심사 중입니다..."):
                if gemini_api_key:
                    try:
                        # [초고속 연동 핵심 알고리즘]
                        # 1차: Python으로 관련 조건자 25~30명 빠르게 1차 추출 (0.01초 소요)
                        prompt_lower = user_prompt.lower()
                        keywords = [w for w in ["구난", "운전", "드론", "통신", "위험물", "안전", "물류", "보급", "비행", "특수"] if w in prompt_lower]
                        
                        if keywords:
                            # 키워드 포함 인원 1차 필터링
                            pattern = "|".join(keywords)
                            filtered_candidates = df[
                                df["보유자격증"].str.contains(pattern, na=False) | 
                                df["교육이수현황"].str.contains(pattern, na=False) |
                                df["병과"].str.contains(pattern, na=False)
                            ]
                            if len(filtered_candidates) < 10:
                                filtered_candidates = df.head(30)
                        else:
                            filtered_candidates = df.head(30)
                            
                        # 상위 최대 25명만 LLM에 전달하여 처리 속도를 1~2초대로 단축
                        target_df = filtered_candidates.head(25)
                        db_json = target_df[["소속부대", "성명", "계급", "병과", "보유자격증", "교육이수현황", "관련경력", "투입가용일", "최종평정"]].to_json(orient="records", force_ascii=False)
                        
                        prompt_text = f"""
                        너는 대한민국 육군 인사참모 AI 보조관이다.
                        주어진 [부대 간부 1차 후보 DB]를 종합 분석해서 사용자의 [요구사항]에 가장 완벽히 부합하는 간부를 상위 {top_n}명 선발해라.
                        자격증, 가용일, 병과, 경력, 평정 등을 종합 판단하여 자연스러운 군 인사 참모 문체로 추천 사유를 작성해라.

                        [요구사항]: {user_prompt}
                        [부대 간부 1차 후보 DB]: {db_json}

                        반드시 아래 JSON 배열 형식으로만 응답해라. 다른 설명 텍스트나 코드블록 표시는 생략해라.
                        [
                          {{
                            "성명": "이름",
                            "계급": "계급",
                            "소속부대": "부대명",
                            "적합도점수": 95,
                            "추천사유": "상세 추천 사유"
                          }}
                        ]
                        """
                        
                        model = genai.GenerativeModel('gemini-3.6-flash')
                        response = model.generate_content(prompt_text)
                        
                        clean_json = response.text.replace("```json", "").replace("
