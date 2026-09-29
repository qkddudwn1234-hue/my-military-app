import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random

# 1. 페이지 설정
st.set_page_config(page_title="AI 군 인력정보 플랫폼", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    div[data-testid="metric-container"] { background-color: #1E2130; border: 1px solid #2B3040; padding: 15px; border-radius: 10px; }
    .main-header { font-size: 28px; font-weight: bold; color: #4DA8DA; border-bottom: 2px solid #2B3040; padding-bottom: 10px; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# 2. 시스템 내부에서 여단급 DB 및 당직표 자동 생성 (파일 업로드 오류 원천 차단)
@st.cache_data
def load_military_data():
    np.random.seed(42)
    random.seed(42)
    
    # 인원 생성
    rank_distribution = {'대령':1, '중령':6, '소령':15, '대위':40, '중위':50, '소위':30, '원사':15, '상사':50, '중사':120, '하사':173}
    units = ['여단본부', '1대대', '2대대', '3대대', '포병대대', '군지대대']
    last_names = list("김이박최정강조윤장임한오서신권황안송전홍류고문양손배백허남심노")
    c1 = list("지민현동승상기진우재도연정성영호주시하서예건은태수찬종용훈환철명광진영")
    c2 = list("훈우준호진민희빈윤영성환석현원연섭재형수철규찬태기겸혁석수")
    
    data_rows = []
    person_counter = 1
    
    for rank, count in rank_distribution.items():
        for _ in range(count):
            is_officer = rank in ['대령', '중령', '소령', '대위', '중위', '소위']
            years = random.randint(5, 25)
            mil_id = f"{str(2026 - years)[-2:]}-{'1' if is_officer else '5'}{str(person_counter).zfill(4)}"
            name = random.choice(last_names) + random.choice(c1) + random.choice(c2)
            unit = random.choice(units)
            
            data_rows.append({
                '개인ID': mil_id, '성명': name, '계급': rank, '소속': unit,
                '병과': random.choice(['보병', '포병', '통신', '공병', '의무', '정보']),
                '직책': '참모/대원', '복무연차': years,
                '자격정보': '드론조종, 전술통신' if random.random() > 0.5 else '없음',
                '현재 상태': np.random.choice(['가용', '휴가', '교육파견'], p=[0.8, 0.1, 0.1])
            })
            person_counter += 1
            
    df_main = pd.DataFrame(data_rows)
    
    # 당직표 생성 (최근 14일)
    duty_rows = []
    dates = pd.date_range(start="2026-09-15", end="2026-09-29")
    for date_obj in dates:
        d_str = date_obj.strftime('%Y-%m-%d')
        is_weekend = date_obj.weekday() >= 5
        shifts = ['주간', '야간'] if is_weekend else ['야간']
        
        for u in units:
            subset = df_main[df_main['소속'] == u]
            if not subset.empty:
                for shift in shifts:
                    person = subset.sample(1).iloc[0]
                    duty_rows.append({'일자': d_str, '구분': shift, '부대': u, '개인ID': person['개인ID'], '성명': person['성명']})
                    
    df_duty = pd.DataFrame(duty_rows)
    return df_main, df_duty

df_main, df_duty = load_military_data()

# 3. 사이드바: 작전 기준일자 설정 (동적 피로도 계산)
with st.sidebar:
    st.header("🎯 작전 통제 기준")
    target_date = st.date_input("작전 기준일자 선택", datetime.date(2026, 9, 29))
    st.info("💡 지정된 날짜로부터 직전 7일간의 당직 이력을 역산하여 실시간 피로도를 산출합니다.")

st.markdown('<div class="main-header">AI·데이터 기반 군 인력정보 통합·분석 및 최적 인력운용 플랫폼</div>', unsafe_allow_html=True)

# 4. 동적 피로도 계산 알고리즘
df_duty['일자_dt'] = pd.to_datetime(df_duty['일자']).dt.date
start_date = target_date - datetime.timedelta(days=7)
recent_duty = df_duty[(df_duty['일자_dt'] >= start_date) & (df_duty['일자_dt'] <= target_date)]

# 야간 당직 횟수 집계
night_counts = recent_duty[recent_duty['구분'] == '야간'].groupby('개인ID').size().to_dict()
df_main['최근7일_야간당직수'] = df_main['개인ID'].map(night_counts).fillna(0)
df_main['실시간_피로도점수'] = 15 + (df_main['최근7일_야간당직수'] * 25)

def get_grade(score):
    if score <= 30: return '낮음'
    elif score <= 70: return '보통'
    else: return '높음'

df_main['피로도등급'] = df_main['실시간_피로도점수'].apply(get_grade)

# 5. KPI 대시보드
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

# 6. AI 추천 및 현황
col1, col2 = st.columns([1.1, 1])

with col1:
    st.subheader("📊 부대 소속별 인원 및 상태 현황")
    unit_status = df_main.groupby(['소속', '현재 상태']).size().unstack(fill_value=0)
    st.dataframe(unit_status, use_container_width=True)
    
with col2:
    st.subheader("🎯 AI 임무 적합 인원 추천 (실시간 동적 피로도 연동)")
    selected_mission = st.selectbox("임무 선택", ["드론 정찰 및 감시", "전술 통신 지원"])
    
    candidates = df_main[df_main['현재 상태'] == '가용'].copy()
    candidates['적합도점수'] = 70 + (candidates['복무연차'] * 1.5)
    candidates.loc[candidates['피로도등급'] == '낮음', '적합도점수'] += 15
    candidates.loc[candidates['피로도등급'] == '높음', '적합도점수'] -= 30 # 번아웃 방지 패널티
    
    top_5 = candidates.sort_values(by='적합도점수', ascending=False).head(5)
    display_df = top_5[['성명', '계급', '소속', '직책', '자격정보', '최근7일_야간당직수', '피로도등급', '적합도점수']]
    display_df.index = range(1, len(display_df) + 1)
    
    st.success(f"📌 기준일자({target_date}) 당직 이력을 역산하여 산출된 최적의 인원입니다.")
    st.dataframe(display_df, use_container_width=True)
