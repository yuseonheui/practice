import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="BakeMap - 데이터 기반 입지 분석", layout="wide")

# --- 데이터 로드 및 전처리 ---
@st.cache_data
def load_and_augment_data():
    # 1. 인허가 데이터 로드 (기본 소스)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(BASE_DIR, "data", "bakery_license.csv")
    
    if not os.path.exists(csv_path):
        # 데모용 샘플 데이터 생성 (파일이 없을 경우 대비)
        df = pd.DataFrame({
            "자치구": ["강남구", "성동구", "마포구", "은평구", "송파구"],
            "영업상태": ["영업", "영업", "폐업", "영업", "폐업"],
            "인허가일자": pd.to_datetime(["2023-01-01", "2022-05-15", "2021-10-10", "2023-06-01", "2020-03-01"]),
            "폐업일자": pd.to_datetime([np.nan, np.nan, "2023-12-01", np.nan, "2023-05-01"])
        })
    else:
        df = pd.read_csv(csv_path)
        df["인허가일자"] = pd.to_datetime(df["인허가일자"], errors="coerce")
        df["폐업일자"] = pd.to_datetime(df["폐업일자"], errors="coerce")
    
    return df

df = load_and_augment_data()

# --- 사이드바 및 지역 선택 ---
st.sidebar.title("🥐 BakeMap 분석 필터")
districts = sorted(df["자치구"].dropna().unique())
selected_district = st.sidebar.selectbox("자치구 선택", districts)

# 지역 필터링
df_district = df[df["자치구"] == selected_district].copy()

# --- 핵심 지표 계산 (SRS 알고리즘) ---
def calculate_srs(data):
    # 1. 폐업률 (최근 3년) [cite: 246]
    recent_3y = datetime.datetime.now().year - 3
    closed = len(data[data["폐업일자"].dt.year >= recent_3y])
    opened = len(data[data["인허가일자"].dt.year >= recent_3y])
    closure_rate = (closed / opened * 100) if opened > 0 else 0
    
    # 2. 밀집도 (단순 매장 수 기반) [cite: 246]
    active_count = len(data[data["영업상태"] == "영업"])
    density_index = active_count / 5 # 면적 데이터 부재 시 가중치 조정
    
    # 3. 위험도 점수 합산 (가중치: 폐업률 40%, 밀집도 35%, 기타 25%) [cite: 250]
    srs = (closure_rate * 0.4) + (density_index * 0.35) + (15 * 0.25)
    return round(min(100, srs), 1), active_count

risk_score, active_total = calculate_srs(df_district)

# --- 메인 대시보드 UI ---
st.title(f"📍 {selected_district} 베이커리 상권 분석")
st.markdown(f"**{selected_district}** 지역의 인허가 흐름과 매출 구조 분석 결과입니다.")

# KPI 영역 [cite: 195, 207]
col1, col2, col3, col4 = st.columns(4)
col1.metric("현재 영업 매장", f"{active_total}개")
col2.metric("창업 위험도(SRS)", f"{risk_score}점")
col3.metric("예상 월 매출", "3,800만원", "상권 평균") # 기획안 기반 가상치
col4.metric("주 방문 연령대", "3040 세대", "가족 단위") # 기획안 기반 가상치

st.divider()

# --- 1. 지역별 매출 및 연령대 분석 (추가 요청 사항) ---
st.subheader("📊 상권 정밀 분석")
tab1, tab2 = st.tabs(["매출 및 시간대 분석", "방문객 특성"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        # 시간대별 매출 비중 (기획안 3장 반영) 
        time_data = pd.DataFrame({
            "시간대": ["오전(07-10)", "오후(13-16)", "저녁(17-20)"],
            "매출비중": [20, 45, 35]
        })
        fig_time = px.bar(time_data, x="시간대", y="매출비중", title="시간대별 매출 비중 (%)",
                          color_discrete_sequence=['#E67E22'])
        st.plotly_chart(fig_time, use_container_width=True)
    
    with c2:
        st.write("**🕒 시간대별 추천 전략**")
        st.info("- **오전**: 직장인 대상 샌드위치 세트 강화\n- **오후**: 주부/관광객 대상 디저트 및 구움과자 주력\n- **저녁**: 퇴근길 식빵 및 기념일 홀케이크 배치")

with tab2:
    c3, c4 = st.columns(2)
    with c3:
        # 연령대 분석 (기획안 4장 반영)
        age_data = pd.DataFrame({
            "연령대": ["20대 이하", "30대", "40대", "50대 이상"],
            "비중": [15, 35, 30, 20]
        })
        fig_age = px.pie(age_data, values="비중", names="연령대", title="방문 연령대 분포", hole=0.4)
        st.plotly_chart(fig_age, use_container_width=True)
    
    with c4:
        st.write("**👥 타겟팅 인사이트**")
        if risk_score > 70:
            st.warning("⚠️ 고위험 상권: 기존 매장과의 차별화된 메뉴(유기농, 비건 등) 없이는 진입이 어렵습니다.")
        else:
            st.success("✅ 진입 가능: 3040 세대를 겨냥한 건강 식사빵 위주의 라인업을 추천합니다.")

# --- 2. 개폐업 추이 시각화 ---
st.divider()
st.subheader("📈 연도별 개·폐업 트렌드")
df_district["year"] = df_district["인허가일자"].dt.year
open_trend = df_district.groupby("year").size().reset_index(name="개업수")
close_trend = df_district.groupby(df_district["폐업일자"].dt.year).size().reset_index(name="폐업수")

fig_trend = go.Figure()
fig_trend.add_trace(go.Bar(x=open_trend["year"], y=open_trend["개업수"], name="신규 개업", marker_color='#3498DB'))
fig_trend.add_trace(go.Scatter(x=close_trend["폐업일자"], y=close_trend["폐업수"], name="폐업 발생", line=dict(color='#E74C3C', width=3)))
st.plotly_chart(fig_trend, use_container_width=True)

# --- 3. 리포트 생성 기능 (기획안 5장) [cite: 221] ---
if st.button("📄 분석 리포트 PDF 생성 (Pro 기능)"):
    st.write(f"'{selected_district}' 상권 분석 결과 리포트를 생성 중입니다...")
    st.download_button("리포트 다운로드", data="Sample Content", file_name=f"BakeMap_Report_{selected_district}.pdf")
