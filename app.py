import streamlit as st
import pandas as pd
import random
from datetime import datetime, date, timedelta

# 1. 페이지 레이아웃 및 기본 설정
st.set_page_config(
    page_title="LLM 기반 군 인사 & 교육 관리 대시보드",
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
        font-size: 28px !important;
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

# 3. 메인 타이틀 헤더
st.markdown('<div class="main-header">🎖️ LLM 기반 군 인사 & 의무교육 통합 관리 시스템</div>', unsafe_allow_html=True)

# 4. 100명 간부 데이터 통합 생성 (인사 자력 + 의무교육 이수 현황)
@st.cache_data
def generate_100_personnel():
    random.seed(42)
    today = date(2026, 8, 29)
    
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
    
    avail_pool = ["즉시 가용", "2026-08-30", "2026-09-01", "2026-09-05", "2026-09-10", "임무 수행 중(불가)"]
    ratings = ["S", "A+", "A", "B+", "B"]
    
    mandatory_courses = ["자살예방교육", "성폭력 예방교육", "보안 및 정보보호교육", "군대윤리교육"]
    
    data = []
    for i in range(1, 101):
        name = random.choice(last_names) + random.choice(first_names)
        year = random.randint(18, 24)
        sn = f"{year}-{10000 + i}"
        rank = random.choice(ranks)
        branch = random.choice(branches)
        
        # 인사 자력 데이터
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
        
        # 필수 의무교육 이수 현황 데이터 생성
        course_target = random.choice(mandatory_courses)
        status = random.choices(["이수완료", "미이수"], weights=[0.7, 0.3])[0]
        
        # 마감일 난수 설정 (과거, 임박, 여유)
        days_offset = random.choice([-2, 3, 5, 7, 12, 20, 30])
        due_date = today + timedelta(days=days_offset)
        d_day_val = (due_date - today).days
        
        data.append({
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

df = generate_100_personnel()

# 5. 탭 메뉴 생성 (두 개의 대시보드로 분리)
tab1, tab2 = st.tabs(["🔍 1. 임무 적합자 추천 대시보드", "🚨 2. 필수 의무교육 이수 관리 대시보드"])

# ==========================================
# TAB 1: 임무 적합자 추천 대시보드
# ==========================================
with tab1:
    st.subheader("🔍 임무 요구사항 입력 및 실시간 추출")
    st.write(f"현재 등록된 **전체 간부 DB ({len(df)}명)**에서 의도에 부합하는 **실제 자격자만** 필터링하여 추천합니다.")

    user_prompt = st.text_input(
        "요구사항 입력창:",
        value="위험물 수송 및 관리 가능한 인원 추천해줘",
        placeholder="예: 위험물 관리자, 물류 기획 요원, 안전관리관, 드론 조교, 구난차 운전 등"
    )

    top_n = st.slider("최대 추출 인원 수 선택:", min_value=1, max_value=10, value=3)

    if st.button("🚀 DB 실시간 분석 및 조건 일치자 추출", type="primary"):
        if not user_prompt.strip():
            st.warning("⚠️ 요구사항을 입력해 주세요.")
        else:
            with st.spinner("AI가 입력 조건과 일치하는 핵심 자격 보유자만 검증 중입니다..."):
                prompt_lower = user_prompt.lower()
                
                is_hazmat = any(w in prompt_lower for w in ["위험물", "유류", "탄약", "화약"])
                is_logistics = any(w in prompt_lower for w in ["물류", "보급", "자원", "재정", "군수"])
                is_safety = any(w in prompt_lower for w in ["안전", "통제", "관리관", "감독"])
                is_tow = any(w in prompt_lower for w in ["구난차", "견인", "렉카", "구난"])
                is_driving = any(w in prompt_lower for w in ["운전", "버스", "수송", "차량", "대형"]) and not is_tow
                is_drone = any(w in prompt_lower for w in ["드론", "조교", "비행", "지도조종자", "교관"])
                is_comm = any(w in prompt_lower for w in ["통신", "무선", "정보", "사이버", "전산"])
                is_urgent = any(w in prompt_lower for w in ["내일", "즉시", "지금", "빠른", "오늘"])
                
                matched_results = []
                
                for idx, row in df.iterrows():
                    score = 0
                    reasons = []
                    has_core_qualification = False
                    
                    if is_hazmat:
                        if "위험물산업기사" in row["보유자격증"] or "위험물관리자" in row["보유자격증"]:
                            score += 50
                            reasons.append("위험물 산업기사/관리자 자격 보유")
                            has_core_qualification = True
                        if row["병과"] in ["병기", "보급"]:
                            score += 15
                            reasons.append("병기/보급 병과 전문 인원")

                    elif is_logistics:
                        if "물류관리사" in row["보유자격증"] or "자원관리사" in row["보유자격증"]:
                            score += 40
                            reasons.append("물류/자원 관리사 자격 보유")
                            has_core_qualification = True
                        if "보급기획과정(이수)" in row["교육이수현황"] or "군수재정교육(이수)" in row["교육이수현황"]:
                            score += 20
                            reasons.append("군수/보급 기획 전문교육 이수")
                            has_core_qualification = True

                    elif is_safety:
                        if "안전관리교육(이수)" in row["교육이수현황"] or "수송안전교육(이수)" in row["교육이수현황"]:
                            score += 45
                            reasons.append("안전관리 전문교육 이수자")
                            has_core_qualification = True

                    elif is_tow:
                        if "구난차운전면허" in row["보유자격증"] or "특수운전면허" in row["보유자격증"]:
                            score += 50
                            reasons.append("구난차/특수 운전면허 보유")
                            has_core_qualification = True

                    elif is_driving:
                        if "대형운전면허" in row["보유자격증"] or "특수운전면허" in row["보유자격증"]:
                            score += 40
                            reasons.append("대형/특수 운전면허 보유")
                            has_core_qualification = True
                        elif row["병과"] == "수송":
                            score += 20
                            reasons.append("수송 병과 전문 인원")
                            has_core_qualification = True

                    elif is_drone:
                        if "지도조종자" in row["보유자격증"]:
                            score += 40
                            reasons.append("지도조종자(교관) 자격증 보유")
                            has_core_qualification = True
                        elif "조종자" in row["보유자격증"]:
                            score += 25
                            reasons.append("드론 조종자 자격 보유")
                            has_core_qualification = True

                    elif is_comm:
                        if row["병과"] in ["통신", "정보통신"]:
                            score += 30
                            reasons.append("통신/정보통신 병과")
                            has_core_qualification = True

                    if has_core_qualification:
                        if is_urgent and row["투입가용일"] in ["즉시 가용", "2026-08-30"]:
                            score += 15
                            reasons.append("즉시/내일 투입 가능")
                        
                        if row["최종평정"] in ["S", "A+"]:
                            score += 5
                            reasons.append(f"우수 평정자({row['최종평정']})")
                        
                        matched_results.append({
                            "info": row,
                            "score": score + 50,
                            "reasons": reasons
                        })
                
                if not matched_results:
                    st.error("⚠️ **검색 조건에 부합하는 해당 자격자가 DB 내에 존재하지 않습니다.**")
                else:
                    matched_results = sorted(matched_results, key=lambda x: x["score"], reverse=True)
                    final_list = matched_results[:top_n]
                    
                    st.success(f"🎯 **요구조건(핵심 자격)을 충족하는 적합자 총 {len(matched_results)}명 중 상위 {len(final_list)}명을 추천합니다.**")
                    
                    for rank, item in enumerate(final_list, 1):
                        person = item["info"]
                        score = item["score"]
                        reasons_str = " | ".join(item["reasons"])
                        
                        st.markdown(f"""
                            <div class="card-box">
                                <h4 style="margin:0; color:#1E3A8A;">🏅 {rank}순위: {person['성명']} {person['계급']} (추출 적합도 점수: {score}점)</h4>
                                <p style="margin:5px 0 0 0;">
                                • <b>군번 / 병과 / 경력:</b> {person['군번']} / {person['병과']} / {person['관련경력']}<br>
                                • <b>보유 자격:</b> <span style="color:#1D4ED8; font-weight:bold;">{person['보유자격증']}</span><br>
                                • <b>교육 현황:</b> {person['교육이수현황']}<br>
                                • <b>투입 가용일:</b> <span style="color:#DC2626; font-weight:bold;">{person['투입가용일']}</span> (최종평정: {person['최종평정']})<br>
                                • <b>AI 충족 자격 및 추천 사유:</b> <span style="color:#1D4ED8; font-weight:bold;">{reasons_str}</span>
                                </p>
                            </div>
                        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📋 전체 간부 인사자력 DB 현황 (총 100명)")
    st.dataframe(df[["군번", "성명", "계급", "병과", "보유자격증", "교육이수현황", "관련경력", "투입가용일", "최종평정"]], use_container_width=True, hide_index=True)


# ==========================================
# TAB 2: 필수 의무교육 이수 관리 대시보드
# ==========================================
with tab2:
    st.subheader("📢 필수 의무교육 이수 현황 및 마감 임박자 모니터링")
    st.write("전 간부의 자살예방교육, 성폭력 예방교육 등 **필수 의무교육 이수 여부 및 D-Day 현황**을 관제합니다.")
    
    # 1. 의무교육 요약 메트릭 카드
    uncompleted_df = df[df["이수상태"] == "미이수"]
    urgent_uncompleted = uncompleted_df[uncompleted_df["D_Day"] <= 7]
    completed_count = len(df[df["이수상태"] == "이수완료"])
    completion_rate = round((completed_count / len(df)) * 100, 1)
    
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    with col_e1:
        st.metric(label="👥 전체 대상 인원", value=f"{len(df)}명")
    with col_e2:
        st.metric(label="✅ 평균 교육 이수율", value=f"{completion_rate}%")
    with col_e3:
        st.metric(label="❌ 미이수 인원 수", value=f"{len(uncompleted_df)}명", delta=f"-{len(uncompleted_df)}명", delta_color="inverse")
    with col_e4:
        st.metric(label="🚨 마감 임박(D-7 이내) 미이수자", value=f"{len(urgent_uncompleted)}명", delta="긴급독려 필요", delta_color="inverse")
        
    st.divider()
    
    # 2. 마감 임박 / 초과 미이수자 경고 구역
    st.subheader("🚨 마감 임박 / 초과 미이수자 (긴급 독려 대상)")
    st.write("마감일이 **7일 이내로 남았거나 이미 경과했으나 미이수한 인원 목록**입니다.")
    
    if len(urgent_uncompleted) == 0:
        st.success("🎉 현재 마감 임박(D-7 이내) 미이수자가 없습니다.")
    else:
        # D-Day 기준 오름차순 정렬 (마감일 가장 빠른순)
        urgent_sorted = urgent_uncompleted.sort_values(by="D_Day")
        
        for idx, row in urgent_sorted.iterrows():
            d_day_str = f"D-{row['D_Day']}일" if row['D_Day'] >= 0 else f"마감 {abs(row['D_Day'])}일 경과 초과"
            
            st.markdown(f"""
                <div class="warning-box">
                    <h4 style="margin:0; color:#DC2626;">⚠️ [미이수 경고] {row['성명']} {row['계급']} ({row['군번']} / {row['병과']})</h4>
                    <p style="margin:5px 0 0 0;">
                    • <b>미이수 과목:</b> <span style="font-weight:bold; color:#1E3A8A;">{row['필수의무교육']}</span><br>
                    • <b>교육 마감일:</b> {row['교육마감일']} (<span style="color:#DC2626; font-weight:bold;">{d_day_str}</span>)<br>
                    • <b>조치 사항:</b> 교육이수 독려 알림 발송 대상
                    </p>
                </div>
            """, unsafe_allow_html=True)

    st.divider()
    
    # 3. 의무교육 전체 현황 검색 및 필터링 표
    st.subheader("📋 전체 의무교육 이수 현황 검색 및 관제")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_course = st.selectbox("교육 과목 선택:", ["전체 과목", "자살예방교육", "성폭력 예방교육", "보안 및 정보보호교육", "군대윤리교육"])
    with col_f2:
        selected_status = st.selectbox("이수 상태 선택:", ["전체 상태", "미이수자만 보기", "이수완료자만 보기"])
        
    # 필터링 로직
    filtered_edu_df = df.copy()
    
    if selected_course != "전체 과목":
        filtered_edu_df = filtered_edu_df[filtered_edu_df["필수의무교육"] == selected_course]
        
    if selected_status == "미이수자만 보기":
        filtered_edu_df = filtered_edu_df[filtered_edu_df["이수상태"] == "미이수"]
    elif selected_status == "이수완료자만 보기":
        filtered_edu_df = filtered_edu_df[filtered_edu_df["이수상태"] == "이수완료"]
        
    # 데이터표 정렬 및 보기 좋게 가공
    display_edu_df = filtered_edu_df[["군번", "성명", "계급", "병과", "필수의무교육", "이수상태", "교육마감일", "D_Day"]].copy()
    display_edu_df = display_edu_df.sort_values(by=["이수상태", "D_Day"], ascending=[True, True])
    
    st.dataframe(display_edu_df, use_container_width=True, hide_index=True)
