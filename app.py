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
    random
