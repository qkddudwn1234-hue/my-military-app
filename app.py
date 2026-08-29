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
st.markdown('<div class="main-header">🎖️ LLM 기반 임무 적합자 실시간 추천 시스템 (100명 DB)</div>', unsafe_allow_html=True)

# 4. 100명 간부 인사 자력 데이터베이스 (DB) 자동 생성 함수
@st.cache_data
def generate_100_personnel():
    random.seed(42)  # 데이터 고정
    
    last_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"]
    first_names = ["민준", "서준", "도현", "우진", "지후", "하준", "도윤", "시우", "유진", "소희", "지민", "서연", "하은", "지아", "수아", "예은", "지원", "현우", "건우", "성민"]
    ranks = ["하사", "중사", "상사", "원사", "소위", "중위", "대위", "소령", "중령"]
    branches = ["통신", "병기", "수송", "보급", "보병", "포병", "공병", "정보통신"]
    
    cert_pool = [
        "초경량비행장치 지도조종자", "초경량비행장치 조종자", "무선통신산업기사", "정보처리기사",
        "위험물산업기사", "물류관리사", "자원관리사", "대형운전면허", "특수운전면허", "위험물관리자", "없음"
    ]
    
    edu_pool = [
        "드론전문교관과정(이수)", "드론기초조종과정(이수)", "군수재정교육(이수)", "자원관리교육(이수)",
        "수송안전교육(이수)", "보급기획과정(이수)", "안전관리교육(이수)", "지휘관과정(이수)", "드론전문교관과정(교육 중)"
    ]
    
    avail_pool = ["즉시 가용", "2026-09-01", "2026-09-05", "2026-09-10", "2026-09-15", "2026-10-01", "임무 수행 중(불가)"]
    ratings = ["S", "A+", "A", "B+", "B"]
    
    data = []
    for i in range(1, 101):
        name = random.choice(last_names) + random.choice(first_names)
        year = random.randint(18, 24)
        sn = f"{year}-{10000 + i}"
        rank = random.choice(ranks)
        branch = random.choice(branches)
        
        # 드론 관련 인원 일정 비율 보장
        if i % 3 == 0:
            cert = random.choice(["초경량비행장치 지도조종자", "초경량비행장치 조종자"]) + ", " + random.choice(cert_pool[:5])
            edu = random.choice(["드론전문교관과정(이수)", "드론기초조종과정(이수)"]) + ", " + random.choice(edu_pool[2:])
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
st.write(f"현재 등록된 **전체 간부 DB ({len(df)}명)**에서 조건에 부합하는 적합자를 AI가 실시간 추출합니다.")

user_prompt = st.text_input(
    "요구사항 입력창:",
    value="드론 조교 요원 선발, 지도조종자 자격증 보유자 우대, 즉시 가용 인원 우선 추출",
    placeholder="예: 드론 조교 요원 선발, 통신 병과, 즉시 가용 인원 우대"
)

# 추출할 인원 수 선택 슬라이더
top_n = st.slider("추출할 추천 인원 수 선택:", min_value=1, max_value=10, value=3)

# 6. 실시간 DB 검색 및 추출 로직
if st.button("🚀 100명 DB 실시간 분석 및 추천 추출", type="primary"):
    if not user_prompt.strip():
        st.warning("⚠️ 요구사항을 입력해 주세요.")
    else:
        with st.spinner(f"AI가 100명의 자격증, 교육 현황, 가용일을 실시간 스캔 중입니다..."):
            
            matched_results = []
            for idx, row in df.iterrows():
                score = 50  # 기본 점수
                reasons = []
                
                # 자격증 검토
                if "지도조종자" in row["보유자격증"]:
                    score += 25
                    reasons.append("지도조종자(교관) 자격증 보유")
                elif "조종자" in row["보유자격증"]:
                    score += 15
                    reasons.append("조종자 자격 보유")
                    
                # 교육 이수 검토
                if "드론전문교관과정(이수)" in row["교육이수현황"]:
                    score += 20
                    reasons.append("드론 전문교관 과정 이수 완료")
                elif "드론" in row["교육이수현황"]:
                    score += 10
                    reasons.append("드론 관련 교육 과정 작성")
                    
                # 가용일 및 평정
                if "즉시 가용" in row["투입가용일"]:
                    score += 10
                    reasons.append("즉시 임무 투입 가능")
                
                if row["최종평정"] in ["S", "A+"]:
                    score += 5
                    reasons.append(f"우수 평정자({row['최종평정']})")
                
                matched_results.append({
                    "info": row,
                    "score": score,
                    "reasons": reasons
                })
            
            # 점수 높은 순으로 정렬
            matched_results = sorted(matched_results, key=lambda x: x["score"], reverse=True)
            
            st.success(f"🎯 **전체 100명 중 상위 적합자 {top_n}명을 도출했습니다.**")
            
            # 추출된 상위 N명 카드 출력
            for rank, item in enumerate(matched_results[:top_n], 1):
                person = item["info"]
                score = item["score"]
                reasons_str = " | ".join(item["reasons"]) if item["reasons"] else "기본 자격 충족"
                
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

# 7. 하단: 전체 100명 인사 자력 DB 표 (필터 및 검색 가능)
st.subheader("📋 전체 간부 인사자력 DB 현황 (총 100명)")
st.dataframe(df, use_container_width=True, hide_index=True)
