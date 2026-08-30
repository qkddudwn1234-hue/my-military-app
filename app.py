import streamlit as st
import pandas as pd
import random
import json
from datetime import datetime, date, timedelta
import google.generativeai as genai

# 1. 페이지 레이아웃 및 기본 설정
st.set_page_config(
    page_title="LLM 기반 부대별 인사 & 의무교육 관제 시스템",
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

# 부대별 사용자 계정 DB (시연용)
USER_DB = {
    "6bde": {
        "password": "1234", 
        "name": "김지휘 대위 (6여단 인사실무자)", 
        "unit": "6여단",
        "accessible_units": ["6여단 본부", "6여단 101대대", "6여단 102대대", "6여단 103대대", "6여단 포병대대"]
    },
    "101bn": {
        "password": "1234", 
        "name": "강우진 중사 (101대대 인사담당관)", 
        "unit": "6여단 101대대",
        "accessible_units": ["6여단 101대대"]
    },
    "HQ": {
        "password": "1234", 
        "name": "박군수 소령 (상급부대 인사처장)", 
        "unit": "군수사령부",
        "accessible_units": ["ALL"] # 전 부대 접근 가능
    }
}

# --- 로그인 화면 UI ---
if not st.session_state["logged_in"]:
    st.markdown('<div class="main-header">🔒 부대별 인사 & 의무교육 관제 시스템 - 로그인</div>', unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.info(
            "💡 **부대 권한별 테스트 로그인 계정**\n"
            "- **6여단 인사실무자:** ID `6bde` / PW `1234` (6여단 본부 및 예하 대대 관제)\n"
            "- **101대대 인사담당관:** ID `101bn` / PW `1234` (101대대 전용 관제)\n"
            "- **상급부대 지휘관:** ID `HQ` / PW `1234` (전체 부대 총괄)"
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

# 사이드바 설정 (보안 차단 해제를 위해 직접 입력받는 방식으로 변경)
with st.sidebar:
    st.write(f"👤 **접속자:** {current_user['name']}")
    st.write(f"🎖️ **소속:** {current_user['unit']}")
    st.divider()
    
    st.subheader("🔑 Gemini LLM 연동 설정")
    gemini_api_key = st.text_input(
        "Google Gemini API Key 입력", 
        type="password",
        placeholder="aistudio.google.com에서 발급받은 키 입력"
    )
    if gemini_api_key:
        try:
            genai.configure(api_key=gemini_api_key)
            st.caption("🟢 Gemini 1.5 Flash AI 연동 중")
        except Exception as e:
            st.caption("🔴 API 키 오류")
    else:
        st.caption("🟡 로그인 후 사이드바에 API 키를 입력하시면 진짜 LLM이 동작합니다.")
            
    st.divider()
    if st.button("🚪 로그아웃", type="secondary"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

st.markdown(f'<div class="main-header">🤖 [{current_user["unit"]}] Gemini LLM 인사 & 의무교육 통합 관제</div>', unsafe_allow_html=True)

# 4. 부대 지정 포함 100명 간부 DB 자동 생성
@st.cache_data
def generate_100_personnel():
    random.seed(42)
    today = date(2026, 8, 30)
    
    units_pool = [
        "6여단 본부", "6여단 101대대", "6여단 102대대", "6여단 103대대", "6여단 포병대대",
        "군수사 직할대", "작전사 본부"
    ]
    
    last_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"]
    first_names = ["민준", "서준", "도현", "우진", "지후", "하준", "도윤", "시우", "유진", "소희", "지민", "서연", "하은", "지아", "수아", "예은", "지원", "현우", "건우", "성민"]
    ranks = ["하사", "중사", "상사", "원사", "소위", "중위", "대위", "소령", "중령"]
    branches = ["통신", "병기", "수송", "보급", "보병", "포병", "공병", "정보통신"]
    
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
    for i in range(1, 101):
        name = random.choice(last_names) + random.choice(first_names)
        year = random.randint(18, 24)
        sn = f"{year}-{10000 + i}"
        rank = random.choice(ranks)
        branch = random.choice(branches)
        
        assigned_unit = random.choice(units_pool[:5]) if i <= 80 else random.choice(units_pool[5:])
            
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
            
        exp = f"{random.randint(1, 12)}년"
        avail = random.choice(avail_pool)
        rating = random.choice(ratings)
        
        course_target = random.choice(mandatory_courses)
        status = random.choices(["이수완료", "미이수"], weights=[0.65, 0.35])[0]
        
        days_offset = random.choice([-2, 2, 4, 6, 10, 18, 25])
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

raw_df = generate_100_personnel()

# 권한 기반 부대 데이터 필터링
if current_user["accessible_units"] == ["ALL"]:
    df = raw_df.copy()
else:
    df = raw_df[raw_df["소속부대"].isin(current_user["accessible_units"])].copy()

# 5. 대시보드 탭 구성을 위한 렌더링
tab1, tab2 = st.tabs(["🤖 1. Gemini LLM 기반 적합자 심층 분석", "🚨 2. 예하 부대 의무교육 관제 대시보드"])

# ==========================================
# TAB 1: Gemini LLM 기반 적합자 추론
# ==========================================
with tab1:
    st.subheader("🤖 Gemini 1.5 LLM 인사 자력 지능형 추론")
    st.write(f"현재 관할 부대: **{', '.join(current_user['accessible_units'] if current_user['accessible_units'] != ['ALL'] else ['전체 부대'])}** (총 {len(df)}명)")

    user_prompt = st.text_input(
        "임무 요구사항 (자연어로 자유롭게 입력):",
        value="내일 바로 구난차 끌고 현장 출동할 수 있는 숙련된 간부 찾아줘"
    )

    top_n = st.slider("최대 추출 인원 수 선택:", min_value=1, max_value=5, value=3)

    if st.button("🚀 Gemini LLM 실시간 분석 및 추천 실행", type="primary"):
        if not user_prompt.strip():
            st.warning("⚠️ 요구사항을 입력해 주세요.")
        else:
            with st.spinner("🤖 Google Gemini 1.5 AI가 관할 부대 DB를 다각도로 분석 중입니다..."):
                if gemini_api_key:
                    try:
                        db_json = df[["소속부대", "성명", "계급", "병과", "보유자격증", "교육이수현황", "관련경력", "투입가용일", "최종평정"]].to_json(orient="records", force_ascii=False)
                        
                        prompt_text = f"""
                        너는 대한민국 육군 인사참모 AI 보조관이다.
                        주어진 [부대 간부 DB]를 종합적으로 분석해서 사용자의 [요구사항]에 가장 잘 부합하는 간부를 상위 {top_n}명 선발해라.
                        자격증, 가용일, 병과, 관련경력, 최종평정 등을 종합 고려하여 자연스러운 군 인사 참모 문체로 추천 사유를 작성해라.

                        [요구사항]: {user_prompt}
                        [부대 간부 DB]: {db_json}

                        반드시 아래 JSON 배열 형식으로만 응답해라. 텍스트 설명이나 코드블록 표시는 제거해라.
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
                        
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content(prompt_text)
                        
                        clean_json = response.text.replace("```json", "").replace("```", "").strip()
                        results = json.loads(clean_json)
                        
                        st.success("🎯 **Google Gemini 1.5 AI가 문맥을 이해하고 최적격자를 도출했습니다.**")
                        
                        for rank, item in enumerate(results, 1):
                            st.markdown(f"""
                                <div class="card-box">
                                    <h4 style="margin:0; color:#1E3A8A;">🏅 {rank}순위 추천: [{item['소속부대']}] {item['성명']} {item['계급']} (적합도 점수: {item['적합도점수']}점)</h4>
                                    <p style="margin:8px 0 0 0; line-height:1.6;">
                                    🤖 <b>Gemini 참모 AI 판단 사유:</b><br>
                                    <span style="color:#1D4ED8; font-weight:bold;">{item['추천사유']}</span>
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"❌ Gemini API 연동 오류 발생: {e}")
                else:
                    st.info("💡 **[사용 안내]** 왼쪽 사이드바의 **`Google Gemini API Key 입력`** 칸에 발급받으신 API 키를 붙여넣으시면 진짜 Gemini LLM 분석이 구동됩니다.")

    st.divider()
    st.subheader("📋 관할 부대 간부 인사자력 현황")
    st.dataframe(df[["소속부대", "군번", "성명", "계급", "병과", "보유자격증", "교육이수현황", "관련경력", "투입가용일", "최종평정"]], use_container_width=True, hide_index=True)


# ==========================================
# TAB 2: 예하 부대 의무교육 관제 대시보드
# ==========================================
with tab2:
    st.subheader("📢 관할 예하 부대별 필수 의무교육 미이수 관제")
    st.write(f"접속 권한: **[{current_user['unit']}]** 관할 예하 부대원들의 의무교육 마감일 및 미이수 현황입니다.")
    
    available_unit_options = ["관할 부대 전체"] + list(df["소속부대"].unique())
    selected_sub_unit = st.selectbox("📌 조회할 예하 부대 선택:", available_unit_options)
    
    if selected_sub_unit != "관할 부대 전체":
        edu_view_df = df[df["소속부대"] == selected_sub_unit].copy()
    else:
        edu_view_df = df.copy()

    uncompleted_df = edu_view_df[edu_view_df["이수상태"] == "미이수"]
    urgent_uncompleted = uncompleted_df[uncompleted_df["D_Day"] <= 7]
    completed_count = len(edu_view_df[edu_view_df["이수상태"] == "이수완료"])
    completion_rate = round((completed_count / len(edu_view_df)) * 100, 1) if len(edu_view_df) > 0 else 0
    
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    with col_e1:
        st.metric(label="👥 관할 대상 인원", value=f"{len(edu_view_df)}명")
    with col_e2:
        st.metric(label="✅ 평균 교육 이수율", value=f"{completion_rate}%")
    with col_e3:
        st.metric(label="❌ 미이수 인원 수", value=f"{len(uncompleted_df)}명", delta=f"-{len(uncompleted_df)}명", delta_color="inverse")
    with col_e4:
        st.metric(label="🚨 마감 임박(D-7 이내) 미이수자", value=f"{len(urgent_uncompleted)}명", delta="긴급 독려 필요", delta_color="inverse")
        
    st.divider()
    
    st.subheader("🚨 마감 임박 / 초과 미이수자 (부대별 독려 대상)")
    
    if len(urgent_uncompleted) == 0:
        st.success("🎉 관할 선택 부대에 마감 임박(D-7 이내) 미이수자가 없습니다.")
    else:
        urgent_sorted = urgent_uncompleted.sort_values(by="D_Day")
        
        for idx, row in urgent_sorted.iterrows():
            d_day_str = f"D-{row['D_Day']}일" if row['D_Day'] >= 0 else f"마감 {abs(row['D_Day'])}일 경과 초과"
            
            st.markdown(f"""
                <div class="warning-box">
                    <h4 style="margin:0; color:#DC2626;">⚠️ [미이수 경고] [{row['소속부대']}] {row['성명']} {row['계급']} ({row['군번']})</h4>
                    <p style="margin:5px 0 0 0;">
                    • <b>미이수 과목:</b> <span style="font-weight:bold; color:#1E3A8A;">{row['필수의무교육']}</span><br>
                    • <b>교육 마감일:</b> {row['교육마감일']} (<span style="color:#DC2626; font-weight:bold;">{d_day_str}</span>)<br>
                    • <b>조치 권고사항:</b> 해당 대대({row['소속부대']}) 인사담당관에게 교육이수 독려 지시 발송
                    </p>
                </div>
            """, unsafe_allow_html=True)

    st.divider()
    
    st.subheader("📋 관할 부대 의무교육 상세 현황")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_course = st.selectbox("교육 과목 선택:", ["전체 과목", "자살예방교육", "성폭력 예방교육", "보안 및 정보보호교육", "군대윤리교육"])
    with col_f2:
        selected_status = st.selectbox("이수 상태 선택:", ["전체 상태", "미이수자만 보기", "이수완료자만 보기"])
        
    filtered_edu_df = edu_view_df.copy()
    
    if selected_course != "전체 과목":
        filtered_edu_df = filtered_edu_df[filtered_edu_df["필수의무교육"] == selected_course]
        
    if selected_status == "미이수자만 보기":
        filtered_edu_df = filtered_edu_df[filtered_edu_df["이수상태"] == "미이수"]
    elif selected_status == "이수완료자만 보기":
        filtered_edu_df = filtered_edu_df[filtered_edu_df["이수상태"] == "이수완료"]
        
    display_edu_df = filtered_edu_df[["소속부대", "군번", "성명", "계급", "병과", "필수의무교육", "이수상태", "교육마감일", "D_Day"]].copy()
    display_edu_df = display_edu_df.sort_values(by=["이수상태", "D_Day"], ascending=[True, True])
    
    st.dataframe(display_edu_df, use_container_width=True, hide_index=True)
