import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 페이지 설정 ---
st.set_page_config(
    page_title="BakeMap - 데이터 기반 베이커리 입지 분석",
    layout="wide"
)

# --- 1. 데이터 로드 및 전처리 ---
@st.cache_data
def load_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(BASE_DIR, "data", "bakery_license.csv")
    
    # 데이터 로드 (파일 부재 시 빈 데이터프레임 생성 방지)
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        st.error("데이터 파일을 찾을 수 없습니다. 'data/bakery_license.csv' 경로를 확인해주세요.")
        st.stop()

    # 날짜 형식 변환 [cite: 179]
    df["인허가일자"] = pd.to_datetime(df["인허가일자"], errors="coerce")
    df["폐업일자"] = pd.to_datetime(df["폐업일자"], errors="coerce")
    return df

df = load_data()

# --- 2. 사이드바 (지역 선택) ---
st.sidebar.header("📍 지역 설정")
districts = sorted(df["자치구"].dropna().unique())
selected_district = st.sidebar.selectbox("자치구 선택", districts)

# 선택 지역 데이터 필터링
df_district = df[df["자치구"] == selected_district].copy()

# --- 3. 핵심 지표 계산 (SRS 알고리즘 2.0) ---
# 기획안 7.2 산출 방식 반영 [cite: 246, 250]
current_year = datetime.datetime.now().year
recent_3y = current_year - 3

# 지표 A: 폐업률 (최근 3년 폐업 수 / 동기간 누적 개업 수)
opened_3y = len(df_district[df_district["인허가일자"].dt.year >= recent_3y])
closed_3y = len(df_district[df_district["폐업일자"].dt.year >= recent_3y])
closure_rate = (closed_3y / opened_3y) if opened_3y > 0 else 0

# 지표 B: 밀집도 (현재 영업 매장 수)
active_count = len(df_district[df_district["영업상태"] == "영업"])
density_index = active_count / 10  # 단순화된 지수

# 지표 C: 개업 증가율
this_year_open = len(df_district[df_district["인허가일자"].dt.year == current_year - 1])
last_year_open = len(df_district[df_district["인허가일자"].dt.year == current_year - 2])
entry_growth = (this_year_open - last_year_open) / last_year_open if last_year_open > 0 else 0

# SRS 최종 점수 산출 (가중치: 40%, 35%, 25%) [cite: 250]
risk_score = (closure_rate * 40) + (min(density_index, 100) * 0.35) + (max(entry_growth, 0) * 25)
risk_score = min(100, round(risk_score, 1))

# --- 4. 메인 화면 구성 ---
st.title("🥐 BakeMap - 베이커리 창업 입지 분석")
st.markdown(f"**{selected_district}** 상권의 공공데이터 및 매출 구조 분석 리포트입니다. [cite: 161]")

# KPI 지표 표시
col1, col2, col3, col4 = st.columns(4)
col1.metric("현재 영업 매장", f"{active_count}개")
col2.metric("최근 1년 개업", f"{this_year_open}개")
col3.metric("최근 1년 폐업", f"{len(df_district[df_district['폐업일자'].dt.year == current_year - 1])}개")

# 위험도 점수에 따른 색상 표기 [cite: 252]
if risk_score <= 30:
    col4.metric("창업 위험도", f"{risk_score}점", "안전", delta_color="inverse")
elif risk_score <= 70:
    col4.metric("창업 위험도", f"{risk_score}점", "주의", delta_color="off")
else:
    col4.metric("창업 위험도", f"{risk_score}점", "위험", delta_color="normal")

st.divider()

# --- 5. 매출 구조 및 방문객 분석 (추가 요청 사항) ---
st.subheader("📊 지역별 매출 구조 및 방문객 특성")
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    st.write("**💰 지역별 매출 구조 (월평균)**")
    # 기획안 기반 가상 데이터 매핑
    revenue_map = {"강남구": 5200, "성북구": 2800, "마포구": 4200, "은평구": 2400}
    avg_rev = revenue_map.get(selected_district, 3200)
    st.info(f"예상 월 평균 매출: **약 {avg_rev}만원**")
    st.caption("주요 특징: 선물용 디저트 및 홀케이크 비중 높음")

with m_col2:
    st.write("**⏰ 시간대별 매출 비중**")
    time_df = pd.DataFrame({
        "시간대": ["오전(07-10)", "오후(13-16)", "저녁(17-20)"],
        "비중": [20, 45, 35]
    })
    fig_time = px.bar(time_df, x="시간대", y="비중", color="비중", color_continuous_scale="Oranges")
    fig_time.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_time, use_container_width=True)

with m_col3:
    st.write("**👥 방문 연령대 분포**")
    age_df = pd.DataFrame({
        "연령대": ["20대", "30대", "40대", "50대+"],
        "비중": [25, 35, 25, 15]
    })
    fig_age = px.pie(age_df, values="비중", names="연령대", hole=.4)
    fig_age.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_age, use_container_width=True)

# --- 6. 시계열 트렌드 시각화 ---
st.divider()
t_col1, t_col2 = st.columns(2)

with t_col1:
    st.subheader("📈 연도별 개업 추이")
    df_district["year"] = df_district["인허가일자"].dt.year
    open_trend = df_district.groupby("year").size().reset_index(name="개업수")
    fig1 = px.bar(open_trend, x="year", y="개업수", labels={'year': '연도', '개업수': '신규 매장 수'})
    st.plotly_chart(fig1, use_container_width=True)

with t_col2:
    st.subheader("📉 연도별 폐업 추이")
    df_district["close_year"] = df_district["폐업일자"].dt.year
    close_trend = df_district.groupby("close_year").size().reset_index(name="폐업수")
    fig2 = px.line(close_trend, x="close_year", y="폐업수", markers=True, color_discrete_sequence=['red'])
    st.plotly_chart(fig2, use_container_width=True)

# --- 7. 데이터 테이블 및 리포트 (Pro 기능) ---
st.divider()
st.subheader("📄 상세 데이터 미리보기")
st.dataframe(df_district.sort_values("인허가일자", ascending=False).head(50), use_container_width=True)

if st.button("🚀 전체 상권 분석 리포트 PDF 다운로드 (Pro)"):
    st.write(f"{selected_district} 지역의 정밀 분석 리포트를 생성 중입니다... [cite: 222]")
