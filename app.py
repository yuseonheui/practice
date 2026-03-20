import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import os  # os 모듈이 누락되어 추가했습니다.

st.set_page_config(
    page_title="BakeMap",
    layout="wide")

# -------------------------
# 경로 설정 및 파일 확인 (디버깅용)
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 'data' 폴더와 'csv' 파일의 경로를 시스템에 맞게 결합
csv_path = os.path.join(BASE_DIR, "data", "bakery_license.csv")

# 배포 시 파일이 있는지 확인하기 위한 로그 (불필요하면 나중에 삭제 가능)
if not os.path.exists(csv_path):
    st.error(f"⚠️ 파일을 찾을 수 없습니다: {csv_path}")
    st.info("GitHub 저장소에 'data' 폴더와 'bakery_license.csv' 파일이 있는지 확인해주세요.")
    st.stop() # 파일이 없으면 아래 코드를 실행하지 않고 멈춤

st.title("🥐 BakeMap - 베이커리 창업 입지 분석")
st.markdown("서울 공공데이터 기반 베이커리 상권 분석 MVP")

# -------------------------
# 데이터 로드
# -------------------------
@st.cache_data
def load_data():
    # 수정된 경로(csv_path)를 사용합니다.
    df = pd.read_csv(csv_path)
    
    df["인허가일자"] = pd.to_datetime(df["인허가일자"], errors="coerce")
    df["폐업일자"] = pd.to_datetime(df["폐업일자"], errors="coerce")

    return df

df = load_data()

# -------------------------
# 사이드바
# -------------------------
st.sidebar.header("지역 선택")

# '자치구' 컬럼에 결측치가 있을 경우를 대비해 처리
districts = sorted(df["자치구"].dropna().unique())
selected_district = st.sidebar.selectbox("자치구", districts)

df_district = df[df["자치구"] == selected_district].copy() # SettingWithCopyWarning 방지

# -------------------------
# 기본 지표 계산
# -------------------------
current_year = datetime.datetime.now().year

active = df_district[df_district["영업상태"] == "영업"]

# 최근 개업/폐업 (작년 기준)
recent_open = df_district[df_district["인허가일자"].dt.year == current_year - 1]
recent_close = df_district[df_district["폐업일자"].dt.year == current_year - 1]

active_count = len(active)
open_count = len(recent_open)
close_count = len(recent_close)

# -------------------------
# 위험도 점수 계산 (단순 MVP)
# -------------------------
closure_rate = close_count / open_count if open_count > 0 else 0
density_index = active_count / 10
entry_growth = open_count / 10

risk_score = (
    closure_rate * 40 +
    density_index * 35 +
    entry_growth * 25
)
risk_score = min(100, round(risk_score, 1))

# -------------------------
# KPI 표시
# -------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("현재 영업 매장", f"{active_count}개")
col2.metric("최근 개업 (작년)", f"{open_count}개")
col3.metric("최근 폐업 (작년)", f"{close_count}개")
col4.metric("창업 위험도", f"{risk_score}점")

# -------------------------
# 시각화 (차트)
# -------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("연도별 개업 추이")
    df_district["year"] = df_district["인허가일자"].dt.year
    open_trend = df_district.groupby("year").size().reset_index(name="개업수")
    fig = px.bar(open_trend, x="year", y="개업수", color_discrete_sequence=['#FF8C00'])
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("연도별 폐업 추이")
    df_district["close_year"] = df_district["폐업일자"].dt.year
    close_trend = df_district.groupby("close_year").size().reset_index(name="폐업수")
    fig2 = px.line(close_trend, x="close_year", y="폐업수", markers=True)
    st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# 데이터 테이블
# -------------------------
st.subheader(f"📍 {selected_district} 데이터 상세 내역")
st.dataframe(df_district.sort_values("인허가일자", ascending=False).head(100))
