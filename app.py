import streamlit as st
import pandas as pd
import numpy as np
import datetime

# 1. 페이지 설정 (와이드 레이아웃, 다크 테마)
st.set_page_config(page_title="AI 군 인력정보 플랫폼", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    div[data-testid="metric-container"] { background-color: #1E2130; border: 1px solid #2B3040; padding: 15px; border-radius: 10px; }
    .main-header { font-size: 28px; font-weight: bold; color: #4DA8DA; border-bottom: 2px solid #2B3040; padding-bottom: 10px; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# 2. 사이드바: 데이터 업로드 및 작전 기준일자 설정 (동적 피로도 계산의 핵심!)
with st.sidebar:
    st.header("📂 시스템 연동 설정")
    uploaded_file = st.file_uploader("여단급 인원DB 및 당직표 엑셀 업로드", type=['xlsx'])
    
    st.markdown("---")
    st.subheader("🎯 작전 통제 기준")
    # 실무자가 날짜를 지정하면 해당 날짜 기준으로 피로도가 동적 계산됨
    target_date = st.date_input("작전 기준일자 선택", datetime.date(2026, 9, 26))
    st.info("💡 지정된 날짜로부터 직전 7일간의 당직 이력을 역산하여 실시간 피로도를 산출합니다.")

st.markdown('<div class="main-header">AI·데이터 기반 군 인력정보 통합·분석 및 최적 인력운용 플랫폼</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    try:
        # 멀티 시트 읽기 (인원DB, 당직근무표)
        df_main = pd.read_excel(uploaded_file, sheet_name='인원DB')
        df_duty = pd.read_excel(uploaded_file, sheet_name='당직근무표')
        
        # 날짜 형식 통일
        df_duty['일자'] = pd.to_datetime(df_duty['일자']).dt.date
        
        # 3. [동적 피로도 계산 알고리즘]
        # 선택된 날짜 기준 직전 7일 범위 설정
        start_date = target_date - datetime.timedelta(days=7)
        recent_duty = df_duty[(df_duty['일자'] >= start_date) & (df_duty['일자'] <= target_date)]
        
        # 야간 당직 횟수 실시간 집계
        night_duty_counts = recent_duty[recent_duty['구분'] == '야간'].groupby('개인ID').size().to_dict()
        
        # 데이터프레임에 실시간 반영 (고정값 제거 후 동적 산출)
        df_main['최근7일_야간당직수'] = df_main['개인ID'].map(night_duty_counts).fillna(0)
        df_main['실시간_피로도점수'] = 15 + (df_main['최근7일_야간당직수'] * 25)
        
        # 피로도 등급 분류 함수
        def get_fatigue_grade(score):
            if score <= 30: return '낮음'
            elif score <= 70: return '보통'
            else: return '높음'
            
        df_main['피로도등급'] = df_main['실시간_피로도점수'].apply(get_fatigue_grade)
        
        # 4. 상단 KPI 요약
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        total = len(df_main)
        avail = len(df_main[df_main['현재 상태'] == '가용'])
        high_fatigue = len(df_main[df_main['피로도등급'] == '높음'])
        
        kpi1.metric("부대 총원", f"{total}명")
        kpi2.metric("가용 인원", f"{avail}명", f"{(avail/total)*100:.1f}%")
        kpi3.metric("휴가 인원", f"{len(df_main[df_main['현재 상태'] == '휴가'])}명")
        kpi4.metric("교육파견", f"{len(df_main[df_main['현재 상태'] == '교육파견'])}명")
        kpi5.metric("고피로 인원 (위험)", f"{high_fatigue}명", delta_color="inverse")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 5. 화면 분할: 좌측 종합 현황 / 우측 AI 임무추천
        col1, col2 = st.columns([1.1, 1])
        
        with col1:
            st.subheader("📊 부대 소속별 인원 및 상태 현황")
            unit_status = df_main.groupby(['소속', '현재 상태']).size().unstack(fill_value=0)
            st.dataframe(unit_status, use_container_width=True)
            
        with col2:
            st.subheader("🎯 AI 임무 적합 인원 추천 (실시간 피로도 연동)")
            selected_mission = st.selectbox("임무 선택", ["드론 정찰 및 감시", "전술 통신 지원", "재난 대응"])
            
            if selected_mission == "드론 정찰 및 감시":
                # 조건 필터링: 가용 상태 + 드론 관련 자격 보유자
                candidates = df_main[(df_main['현재 상태'] == '가용') & (df_main['자격정보'].str.contains('드론조종|정보분석기사', na=False))].copy()
                
                if not candidates.empty:
                    # AI 점수 산출: 기본점수 70 + 복무연차 가중치 - 피로도 패널티(고피로자 감점)
                    candidates['적합도점수'] = 70 + (candidates['복무연차'] * 2)
                    candidates.loc[candidates['피로도등급'] == '낮음', '적합도점수'] += 10
                    candidates.loc[candidates['피로도등급'] == '높음', '적합도점수'] -= 20 # 번아웃 방지 안전장치
                    
                    top_5 = candidates.sort_values(by='적합도점수', ascending=False).head(5)
                    
                    display_df = top_5[['성명', '계급', '소속', '직책', '자격정보', '최근7일_야간당직수', '피로도등급', '적합도점수']]
                    display_df.index = range(1, len(display_df) + 1)
                    
                    st.success(f"📌 기준일자({target_date}) 당직 이력을 역산하여 산출된 최적의 인원입니다.")
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.warning("조건에 부합하는 가용 인원이 없습니다.")

    except Exception as e:
        st.error(f"데이터를 읽거나 연동하는 중 오류가 발생했습니다: {e}")

else:
    st.info("👈 좌측 사이드바에서 엑셀 파일(`.xlsx`)을 업로드하면 시스템이 가동됩니다.")
