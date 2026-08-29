import streamlit as st
import pandas as pd
import random

# 1. 페이지 레이아웃 및 기본 설정
st.set_page_config(
    page_title="LLM 기반 간부 인사자력 추천 시스템",
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
    </style>
""", unsafe_allow_html=True)

# 3. 메인 타이틀 헤더
st.markdown('<div class="main-header">🎖️ LLM 기반 임무 적합자 실시간 추천 시스템</div>', unsafe_allow_html=True)

# 4. 100명 간부 인사 자력 데이터베이스 (DB) 자동 생성
@st.cache_data
def generate_100_personnel():
    random.seed(42)  # 데이터 고정
    
    last_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"]
    first_names = ["민준", "서준", "도현", "우진", "지후", "하준", "도윤", "시우", "유진", "소희", "지민", "서연", "하은", "지아", "수아", "예은", "지원", "현우", "건우", "성민"]
    ranks = ["하사", "중사", "상사", "원사", "소위", "중위", "대위", "소령", "중령"]
    branches = ["통신", "병기", "수송", "보급", "보병", "포병", "공병", "정보통신"]
    
    cert_pool = [
        "대형운전면허", "특수운전면허", "초경량비행장치 지도조종자", "초경량비행장치 조종자", 
        "무선통신산업기사", "정보처리기사", "위험물산업기사", "물류관리사", "자원관리사", "위험물관리자", "없음"
    ]
    
    edu_pool = [
        "수송안전교육(이수)", "드론전문교관과정(이수)", "드론기초조종과정(이수)", "군수재정교육(이수)", "자원관리교육(이수)",
        "보급기획과정(이수)", "안전관리교육(이수)", "지휘관과정(이수)"
    ]
    
    avail_pool = ["즉시 가용", "2026-08-30", "2026-09-01", "2026-09-05", "2026-09-10", "임무 수행 중(불가)"]
    ratings = ["S", "A+", "A", "B+", "B"]
    
    data = []
    for i in range(1, 101):
        name = random.choice(last_names) + random.choice(first_names)
        year = random.randint(18, 24)
        sn = f"{year}-{10000 + i}"
        rank = random.choice(ranks)
        branch = random.choice(branches)
        
        # 운전 / 수송 관련 인원 및 드론 관련 인원 고르게 분포
        if i % 4 == 0:
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
        
        data.append({
            "군번": sn,
            "성명": name,
            "계급": rank,
            "병과": branch,
            "보유자격증": cert,
            "교육이수현황": edu,
            "관련경력": exp,
            "투입가용일": avail,
            "최종평정": rating
        })
        
    return pd.DataFrame(data)

df = generate_100_personnel()

# 5. 사용자 입력 구역
st.subheader("🔍 임무 요구사항 입력")
st.write(f"현재 등록된 **전체 간부 DB ({len(df)}명)**에서 의도에 부합하는 적합자를 AI가 실시간 추출합니다.")

user_prompt = st.text_input(
    "요구사항 입력창:",
    value="내일 버스 운전 가능한 사람 추천해줘"
)

top_n = st.slider("추출할 추천 인원 수 선택:", min_value=1, max_value=10, value=3)

# 6. 스마트 자연어 실시간 DB 분석 및 추출 로직
if st.button("🚀 100명 DB 실시간 분석 및 추천 추출", type="primary"):
    if not user_prompt.strip():
        st.warning("⚠️ 요구사항을 입력해 주세요.")
    else:
        with st.spinner("AI가 요구사항 키워드 분석 및 100명 DB 스캔 중입니다..."):
            
            # 입력된 프롬프트의 의도 카테고리 실시간 파악
            prompt_lower = user_prompt.lower()
            
            # 카테고리별 매칭 키워드 설정
            is_driving = any(w in prompt_lower for w in ["운전", "버스", "수송", "차량", "대형"])
            is_drone = any(w in prompt_lower for w in ["드론", "조교", "비행", "지도조종자", "교관"])
            is_comm = any(w in prompt_lower for w in ["통신", "무선", "정보"])
            is_urgent = any(w in prompt_lower for w in ["내일", "즉시", "지금", "빠른", "오늘"])
            
            matched_results = []
            for idx, row in df.iterrows():
                score = 50  # 기본 점수
                reasons = []
                
                # 1. 운전/수송 의도 분석
                if is_driving:
                    if "대형운전면허" in row["보유자격증"] or "특수운전면허" in row["보유자격증"]:
                        score += 35
                        reasons.append("대형/특수 운전면허 보유")
                    if row["병과"] == "수송":
                        score += 15
                        reasons.append("수송 병과 전문 인원")
                    if "수송안전교육(이수)" in row["교육이수현황"]:
                        score += 10
                        reasons.append("수송안전교육 이수")

                # 2. 드론 의도 분석
                if is_drone:
                    if "지도조종자" in row["보유자격증"]:
                        score += 35
                        reasons.append("지도조종자(교관) 자격증 보유")
                    elif "조종자" in row["보유자격증"]:
                        score += 20
                        reasons.append("드론 조종자 자격 보유")
                    if "드론전문교관과정(이수)" in row["교육이수현황"]:
                        score += 15
                        reasons.append("드론 전문교관 과정 이수 완료")

                # 3. 통신 의도 분석
                if is_comm:
                    if row["병과"] in ["통신", "정보통신"]:
                        score += 25
                        reasons.append("통신/정보통신 병과")
                    if "무선통신산업기사" in row["보유자격증"] or "정보처리기사" in row["보유자격증"]:
                        score += 20
                        reasons.append("통신 관련 전문 자격 보유")

                # 4. 가용일/긴급성 분석 (내일/즉시)
                if is_urgent:
                    if row["투입가용일"] in ["즉시 가용", "2026-08-30"]:
                        score += 20
                        reasons.append("즉시/내일 투입 가능 인원")
                    elif "불가" in row["투입가용일"]:
                        score -= 40  # 불가 인원은 점수 크게 감점
                
                # 5. 근무 평정 가산점
                if row["최종평정"] in ["S", "A+"]:
                    score += 5
                    reasons.append(f"우수 평정자({row['최종평정']})")
                
                matched_results.append({
                    "info": row,
                    "score": score,
                    "reasons": reasons
                })
            
            # 점수 높은 순 정렬
            matched_results = sorted(matched_results, key=lambda x: x["score"], reverse=True)
            
            st.success(f"🎯 **전체 100명 중 요구사항에 맞는 상위 적합자 {top_n}명을 도출했습니다.**")
            
            # 결과 카드 출력
            for rank, item in enumerate(matched_results[:top_n], 1):
                person = item["info"]
                score = item["score"]
                reasons_str = " | ".join(item["reasons"]) if item["reasons"] else "기본 요건 충족"
                
                st.markdown(f"""
                    <div class="card-box">
                        <h4 style="margin:0; color:#1E3A8A;">🏅 {rank}순위: {person['성명']} {person['계급']} (추출 적합도 점수: {score}점)</h4>
                        <p style="margin:5px 0 0 0;">
                        • <b>군번 / 병과 / 경력:</b> {person['군번']} / {person['병과']} / {person['관련경력']}<br>
                        • <b>보유 자격:</b> {person['보유자격증']}<br>
                        • <b>교육 현황:</b> {person['교육이수현황']}<br>
                        • <b>투입 가용일:</b> <span style="color:#DC2626; font-weight:bold;">{person['투입가용일']}</span> (최종평정: {person['최종평정']})<br>
                        • <b>AI 추천 사유:</b> <span style="color:#1D4ED8; font-weight:bold;">{reasons_str}</span>
                        </p>
                    </div>
                """, unsafe_allow_html=True)

st.divider()

# 7. 전체 DB 표시
st.subheader("📋 전체 간부 인사자력 DB 현황 (총 100명)")
st.dataframe(df, use_container_width=True, hide_index=True)
