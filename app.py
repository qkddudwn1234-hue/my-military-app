import streamlit as st
import pandas as pd
from datetime import datetime, date

# 1. 페이지 레이아웃 및 기본 설정
st.set_page_config(
    page_title="LLM 기반 간부 인사자력 추천 시스템",
    page_icon="🎖️",
    layout="wide"
)

# 2. 커스텀 CSS (폰트, 스타일, 군부대 대시보드 느낌 디자인)
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
st.markdown('<div class="main-header">🎖️ LLM 기반 임무 적합자 추천 시스템 (군수사)</div>', unsafe_allow_html=True)

# 4. 상단: 모집 임무 및 마감 현황 (D-Day 카운트다운)
st.subheader("📅 현재 모집 중인 주요 임무 현황")

col_m1, col_m2, col_m3 = st.columns(3)

# 마감일 지정 (2026년 9월 15일 예시)
target_date = date(2026, 9, 15)
today = date.today()
d_day = (target_date - today).days

with col_m1:
    st.metric(label="🎯 모집 임무", value="드론 조교 요원 선발")
with col_m2:
    st.metric(label="⏰ 신청 마감일", value=target_date.strftime("%Y-%m-%d"))
with col_m3:
    if d_day > 0:
        st.metric(label="⏳ 마감까지 남은 기간", value=f"D-{d_day}일", delta=f"{d_day}일 남음")
    else:
        st.metric(label="⏳ 마감까지 남은 기간", value="마감됨", delta="접수 종료", delta_color="inverse")

st.divider()

# 5. 인사 자력 더미 데이터 준비
@st.cache_data
def load_personnel_data():
    return pd.DataFrame([
        {
            "군번": "21-10001", "성명": "강우진", "계급": "대위", "병과": "통신",
            "보유자격증": "초경량비행장치 지도조종자, 무선통신산업기사",
            "교육이수현황": "드론전문교관과정(이수), 군수재정교육(이수)",
            "관련경력": "4년", "투입가용일": "즉시 가용", "최종평정": "A+"
        },
        {
            "군번": "19-10002", "성명": "김민준", "계급": "소령", "병과": "병기",
            "보유자격증": "초경량비행장치 조종자, 위험물산업기사",
            "교육이수현황": "드론전문교관과정(이수), 자원관리교육(이수)",
            "관련경력": "6년", "투입가용일": "2026-09-05", "최종평정": "S"
        },
        {
            "군번": "22-10003", "성명": "박서준", "계급": "중위", "병과": "수송",
            "보유자격증": "대형운전면허, 물류관리사",
            "교육이수현황": "드론기초조종과정(이수), 수송안전교육(이수)",
            "관련경력": "2년", "투입가용일": "즉시 가용", "최종평정": "A"
        },
        {
            "군번": "20-10004", "성명": "이도현", "계급": "대위", "병과": "보급",
            "보유자격증": "자원관리사, 초경량비행장치 조종자",
            "교육이수현황": "드론전문교관과정(교육 중), 보급기획과정(이수)",
            "관련경력": "3년", "투입가용일": "2026-09-10", "최종평정": "B+"
        },
        {
            "군번": "21-10007", "성명": "한소희", "계급": "중사", "병과": "수송",
            "보유자격증": "초경량비행장치 지도조종자, 특수운전면허",
            "교육이수현황": "드론전문교관과정(이수), 안전관리교육(이수)",
            "관련경력": "5년", "투입가용일": "2026-09-01", "최종평정": "A+"
        }
    ])

df = load_personnel_data()

# 6. 자연어 질문 입력 및 LLM 추천 시뮬레이션 구역
st.subheader("🤖 AI 인사 추천 및 분석")

user_prompt = st.text_input(
    "임무 요구사항을 자연어로 입력하세요:",
    value="드론 조교 임무 수행자 추천해줘. 드론 교관 교육 이수하고 즉시 투입 가능한 인원 우대."
)

if st.button("🚀 AI 분석 및 적합 인원 추출", type="primary"):
    with st.spinner("AI가 간부 자력 DB 및 교육 이수 현황을 분석 중입니다..."):
        st.success("🎯 **AI 추천 결과가 도출되었습니다.**")
        
        # 1순위 추천 카드
        st.markdown("""
            <div class="card-box">
                <h4 style="margin:0; color:#1E3A8A;">🥇 1순위 추천: 강우진 대위 (적합도 점수: 96.5점)</h4>
                <p style="margin:5px 0 0 0;">
                • <b>병과/경력:</b> 통신 / 관련 경력 4년<br>
                • <b>핵심 자격:</b> 초경량비행장치 지도조종자(교관) 자격증 보유<br>
                • <b>교육/가용:</b> 드론전문교관과정 이수 완료, <b>즉시 투입 가능</b>
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # 2순위 추천 카드
        st.markdown("""
            <div class="card-box">
                <h4 style="margin:0; color:#1E3A8A;">🥈 2순위 추천: 한소희 중사 (적합도 점수: 91.0점)</h4>
                <p style="margin:5px 0 0 0;">
                • <b>병과/경력:</b> 수송 / 관련 경력 5년<br>
                • <b>핵심 자격:</b> 초경량비행장치 지도조종자 보유<br>
                • <b>교육/가용:</b> 드론전문교관과정 이수 완료 (2026-09-01 이후 투입 가능)
                </p>
            </div>
        """, unsafe_allow_html=True)

st.divider()

# 7. 하단: 인사자력 DB 및 교육 이수 현황 전체 데이터표
st.subheader("📋 전체 대상 간부 자력 및 교육 이수 현황 DB")
st.dataframe(df, use_container_width=True, hide_index=True)
