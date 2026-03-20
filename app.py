import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px

st.set_page_config(
    page_title="BakeMap",
    layout="wide"import os
st.write("현재 폴더 파일 목록:", os.listdir("."))
if os.path.exists("data"):
    st.write("data 폴더 안의 파일:", os.listdir("data"))
)

st.title("🥐 BakeMap - 베이커리 창업 입지 분석")
st.markdown("서울 공공데이터 기반 베이커리 상권 분석 MVP")

# -------------------------
# 데이터 로드
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/bakery_license.csv")
    
    df["인허가일자"] = pd.to_datetime(df["인허가일자"], errors="coerce")
    df["폐업일자"] = pd.to_datetime(df["폐업일자"], errors="coerce")

    return df

df = load_data()

# -------------------------
# 사이드바
# -------------------------
st.sidebar.header("지역 선택")

districts = sorted(df["자치구"].dropna().unique())
selected_district = st.sidebar.selectbox("자치구", districts)

df_district = df[df["자치구"] == selected_district]

# -------------------------
# 기본 지표 계산
# -------------------------
current_year = datetime.datetime.now().year

active = df_district[df_district["영업상태"] == "영업"]

recent_open = df_district[
    df_district["인허가일자"].dt.year == current_year - 1
]

recent_close = df_district[
    df_district["폐업일자"].dt.year == current_year - 1
]

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

col1.metric("현재 영업 매장", active_count)
col2.metric("최근 개업", open_count)
col3.metric("최근 폐업", close_count)
col4.metric("창업 위험도", risk_score)

# -------------------------
# 연도별 개업 추이
# -------------------------
st.subheader("연도별 개업 추이")

df_district["year"] = df_district["인허가일자"].dt.year

open_trend = (
    df_district.groupby("year")
    .size()
    .reset_index(name="개업수")
)

fig = px.bar(
    open_trend,
    x="year",
    y="개업수",
    title="연도별 베이커리 개업 추이"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 폐업 추이
# -------------------------
st.subheader("연도별 폐업 추이")

df_district["close_year"] = df_district["폐업일자"].dt.year

close_trend = (
    df_district.groupby("close_year")
    .size()
    .reset_index(name="폐업수")
)

fig2 = px.line(
    close_trend,
    x="close_year",
    y="폐업수",
    title="연도별 폐업 추이"
)

st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# 데이터 테이블
# -------------------------
st.subheader("데이터 미리보기")

st.dataframe(df_district.head(100))
