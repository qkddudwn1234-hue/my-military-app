import streamlit as st
import pandas as pd
import random
import json
import re
from datetime import datetime, date, timedelta
import google.generativeai as genai

# 1. 페이지 레이아웃 설정
st.set_page_config(
    page_title="LLM 기반 부대별 인사 & 의무교육 관제 시스템",
    page_icon="🎖️",
    layout="wide"
)

# 2. 세션 초기화
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

USER_DB = {
    "6bde": {
        "password": "1234", 
        "name": "김지휘 대위 (6여단 인사실무자)", 
        "unit": "6여단",
        "accessible_units": [
            "6여단 본부", "6여단 101대대 본부", 
            "6여단 101대대 1중대", "6여단 101대대 2중대",
            "6여단 102대대", "6여단 103대대", 
            "6여단 포병대대", "6여단 수송대대", "6여단 정비대대"
        ]
    },
    "101bn": {
        "password": "1234", 
        "name": "강우진 중사 (101대대 인사담당관)", 
        "unit": "6여단 101대대",
        "accessible_units": [
            "6여단 101대대 본부", 
            "6여단 101대대 1중대", 
            "6여단 101대대 2중대"
        ]
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
    st.title("🔒 부대별 인사 & 의무교육 관제 시스템 - 로그인")
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.info(
            "💡 부대 권한별 테스트 로그인 계정\n"
            "- 6여단 인사실무자: ID 6bde / PW 1234\n"
            "- 101대대 인사담당관: ID 101bn / PW 1234\n"
            "- 상급부대 지휘관: ID HQ / PW 1234"
        )
        
        with st.form("login_form"):
            input_user = st.text_input("아이디 (ID)")
            input_pw = st.text_input("비밀번호 (Password)", type="password")
            submit_button = st.form_submit_button(
                "로그인", type="primary", use_container_width=True
            )
            
            if submit_button:
                if input_user in USER_DB and USER_DB[input_user]["password"] == input_pw:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = input_user
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")
    st.stop()

# --- 로그인 완료 후 메인 화면 ---
current_user = USER_DB[st.session_state["username"]]

gemini_api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    try:
        genai.configure(api_key=gemini_api_key)
    except Exception:
        pass

with st.sidebar:
    st.write("👤 접속자:", current_user['name'])
    st.write("🎖️ 소속:", current_user['unit'])
    st.divider()
    
    st.subheader("🔑 Gemini LLM 연동 상태")
    if gemini_api_key:
        st.caption("🟢 Gemini 3.6 Flash AI 연동 완료")
    else:
        st.caption("🔴 Secrets 설정 필요")
            
    st.divider()
    if st.button("🚪 로그아웃", type="secondary"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

st.title("🤖 [" + current_user["unit"] + "] Gemini LLM 인사 & 의무교육 관제")

# 3. 데이터베이스 생성 (300명)
@st.cache_data
def generate_personnel_db():
    random.seed(42)
    today = date(2026, 8, 30)
    
    units_pool_6bde = [
        "6여단 본부", "6여단 101대대 본부", 
        "6여단 101대대 1중대", "6여단 101대대 2중대",
        "6여단 102대대", "6여단 103대대", 
        "6여단 포병대대", "6여단 수송대대", "6여단 정비대대"
    ]
    units_pool_others = [
        "군수사령부 직할대", "작전사령부 본부", 
        "1군단 사령부", "5사단 본부"
    ]
    
    last_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
    first_names = ["민준", "서준", "도현", "우진", "지후", "하준", "도윤", "시우"]
    ranks = ["하사", "중사", "상사", "원사", "소위", "중위", "대위", "소령"]
    branches = ["통신", "병기", "수송", "보급", "보병", "포병", "공병"]
    
    cert_pool = [
        "대형운전면허", "특수운전면허", "구난차운전면허", 
        "초경량비행장치 조종자", "정보처리기사", "위험물산업기사", "없음"
    ]
    
    edu_pool = [
        "수송안전교육(이수)", "구난차량운용교육(이수)", 
        "드론기초조종과정(이수)", "군수재정교육(이수)", "안전관리교육(이수)"
    ]
    
    avail_pool = ["즉시 가용", "2026-08-31", "2026-09-01", "임무 수행 중(불가)"]
    ratings = ["S", "A+", "A", "B+", "B"]
    mandatory_courses = ["자살예방교육", "성폭력 예방교육", "보안 및 정보보호교육", "군대윤리교육"]
    
    data = []
    for i in range(1, 301):
        name = random.choice(last_names) + random.choice(first_names)
        sn = str(random.randint(15, 25)) + "-" + str(10000 + i)
        rank = random.choice(ranks)
        branch = random.choice(branches)
        
        if i <= 240:
            assigned_unit = random.choice(units_pool_6bde)
        else:
            assigned_unit = random.choice(units_pool_others)
            
        if i % 10 == 0:
            branch = "수송"
            cert = "특수운전면허, 구난차운전면허"
            edu = "구난차량운용교육(이수), 수송안전교육(이수)"
        elif i % 7 == 0:
            branch = "병기"
            cert = "위험물산업기사, 위험물관리자"
            edu = "안전관리교육(이수)"
        else:
            cert = random.choice(cert_pool)
            edu = random.choice(edu_pool)
            
        exp = str(random.randint(1, 15)) + "년"
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

raw_df = generate_personnel_db()

if current_user["accessible_units"] == ["ALL"]:
    df = raw_df.copy()
else:
    df = raw_df[raw_df["소속부대"].isin(current_user["accessible_units"])].copy()

# 4. 탭 구성
tab1, tab2 = st.tabs([
    "🤖 1. Gemini LLM 기반 적합자 분석", 
    "🚨 2. 예하 부대 의무교육 관제 대시보드"
])

# ==========================================
# TAB 1: Gemini LLM 기반 적합자 분석
# ==========================================
with tab1:
    st.subheader("🤖 Gemini LLM 인사 자력 지능형 추론")
    st.write("현재 권한 관할 부대 DB 인원: **총 " + str(len(df)) + "명**")

    user_prompt = st.text_input(
        "임무 요구사항 (자연어로 자유롭게 입력):",
        value="내일 바로 구난차 끌고 현장 출동할 수 있는 숙련된 간부 찾아줘"
    )

    top_n = st.slider("최대 추출 인원 수 선택:", min_value=1, max_value=5, value=3)

    if st.button("🚀 Gemini LLM 실시간 분석 및 추천 실행", type="primary"):
        if not user_prompt.strip():
            st.warning("⚠️ 요구사항을 입력해 주세요.")
        else:
            with st.spinner("🤖 Gemini AI가 DB를 스캔하여 적합자를 심사 중입니다..."):
                if gemini_api_key:
                    try:
                        prompt_lower = user_prompt.lower()
                        keywords = [
                            w for w in ["구난", "운전", "드론", "통신", "위험물", "안전", "보급"] 
                            if w in prompt_lower
                        ]
                        
                        if keywords:
                            pattern = "|".join(keywords)
                            filtered_candidates = df[
                                df["보유자격증"].str.contains(pattern, na=False) | 
                                df["교육이수현황"].str.contains(pattern, na=False) |
                                df["병과"].str.contains(pattern, na=False)
                            ]
                            if len(filtered_candidates) < 5:
                                filtered_candidates = df.head(20)
                        else:
                            filtered_candidates = df.head(20)
                            
                        target_df = filtered_candidates.head(15)
                        db_json = target_df[
                            ["소속부대", "성명", "계급", "병과", "보유자격증", "교육이수현황", "관련경력", "투입가용일", "최종평정"]
                        ].to_json(orient="records", force_ascii=False)
                        
                        prompt_text = (
                            "너는 대한민국 육군 인사참모 AI 보조관이다.\n"
                            "주어진 DB에서 요구사항에 맞는 간부 상위 " + str(top_n) + "명을 선발해라.\n\n"
                            "[요구사항]: " + user_prompt + "\n"
                            "[DB]: " + db_json + "\n\n"
                            "반드시 JSON 배열 형식으로만 응답해라.\n"
                            "[\n"
                            "  {\n"
                            '    "성명": "이름",\n'
                            '    "계급": "계급",\n'
                            '    "소속부대": "부대명",\n'
                            '    "적합도점수": 95,\n'
                            '    "추천사유": "상세 추천 사유"\n'
                            "  }\n"
                            "]"
                        )
                        
                        model = genai.GenerativeModel('gemini-3.6-flash')
                        response = model.generate_content(prompt_text)
                        
                        clean_text = re.sub(r'```(?:json)?', '', response.text).strip()
                        results = json.loads(clean_text)
                        
                        st.success("🎯 Google Gemini AI가 최적격자 " + str(len(results)) + "명을 도출했습니다.")
                        
                        for rank, item in enumerate(results, 1):
                            title_text = "🏅 " + str(rank) + "순위: [" + str(item["소속부대"]) + "] " + str(item["성명"]) + " " + str(item["계급"]) + " (" + str(item["적합도점수"]) + "점)"
                            with st.expander(title_text, expanded=True):
                                st.write("🤖 **Gemini 참모 AI 판단 사유:**")
                                st.info(item["추천사유"])
                            
                    except Exception as e:
                        st.error("❌ Gemini API 연동 오류 발생: " + str(e))
                else:
                    st.error("⚠️ Streamlit Secrets에 GEMINI_API_KEY가 설정되어 있지 않습니다.")

    st.divider()
    st.subheader("📋 관할 부대 간부 인사자력 현황 (총 " + str(len(df)) + "명)")
    st.dataframe(
        df[["소속부대", "군번", "성명", "계급", "병과", "보유자격증", "교육이수현황", "관련경력", "투입가용일", "최종평정"]], 
        use_container_width=True, 
        hide_index=True
    )

# ==========================================
# TAB 2: 예하 부대 의무교육 관제 대시보드
# ==========================================
with tab2:
    st.subheader("📢 관할 예하 부대별 필수 의무교육 미이수 관제")
    st.write("접속 권한: **[" + current_user['unit'] + "]** 관할 예하 부대원 현황입니다.")
    
    available_unit_options = ["관할 부대 전체"] + list(df["소속부대"].unique())
    selected_sub_unit = st.selectbox("📌 조회할 예하 부대/중대 선택:", available_unit_options)
    
    if selected_sub_unit != "관할 부대 전체":
        edu_view_df = df[df["소속부대"] == selected_sub_unit].copy()
    else:
        edu_view_df = df.copy()

    uncompleted_df = edu_view_df[edu_view_df["이수상태"] == "미이수"]
    urgent_uncompleted = uncompleted_df[uncompleted_df["D_Day"] <= 7]
    completed_count = len(edu_view_df[edu_view_df["이수상태"] == "이수완료"])
    
    if len(edu_view_df) > 0:
        completion_rate = round((completed_count / len(edu_view_df)) * 100, 1)
    else:
        completion_rate = 0
    
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    with col_e1:
        st.metric(label="👥 관할 대상 인원", value=str(len(edu_view_df)) + "명")
    with col_e2:
        st.metric(label="✅ 평균 교육 이수율", value=str(completion_rate) + "%")
    with col_e3:
        st.metric(label="❌ 미이수 인원 수", value=str(len(uncompleted_df)) + "명")
    with col_e4:
        st.metric(label="🚨 마감 임박(D-7 이내)", value=str(len(urgent_uncompleted)) + "명")
        
    st.divider()
    
    st.subheader("🚨 마감 임박 / 초과 미이수자 (부대별 독려 대상)")
    
    if len(urgent_uncompleted) == 0:
        st.success("🎉 관할 선택 부대에 마감 임박(D-7 이내) 미이수자가 없습니다.")
    else:
        urgent_sorted = urgent_uncompleted.sort_values(by="
