import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 페이지 설정 [cite: 148, 149] ---
st.set_page_config(
    page_title="BakeMap - 유동인구 기반 입지 분석",
    layout="wide"
)

# --- 1. 데이터 로드 및 시뮬레이션 [cite: 178, 179, 191] ---
@st.cache_data
def load_all_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(BASE_DIR, "data", "bakery_license.csv")
    
    # A. 인허가 데이터 로드 [cite: 159, 174]
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        st.error("데이터 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
        st.stop()

    df["인허가일자"] = pd.to_datetime(df["인허가일자"], errors="coerce")
    df["폐업일자"] = pd.to_datetime(df["폐업일자"], errors="coerce")

    # B. 자치구별 유동인구 데이터 (기획안 로드맵 반영 시뮬레이션) 
    # 실제 운영 시 서울시 생활인구 API 연동 구간
    footfall_data = {
        "자치구": ["강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", 
                  "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", 
                  "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"],
        "일평균유동인구": [850000, 420000, 310000, 580000, 490000, 380000, 410000, 250000, 
                        520000, 280000, 360000, 390000, 620000, 350000, 780000, 340000, 
                        410000, 810000, 430000, 590000, 320000, 450000, 290000, 310000, 340000],
        "매출지수": [1.8, 1.1, 0.8, 1.2, 0.9, 1.1, 1.0, 0.9, 0.8, 0.7, 1.0, 1.1, 1.5, 1.0, 1.7, 1.4, 0.9, 1.6, 1.1, 1.3, 1.4, 0.9, 1.2, 1.3, 0.8]
    }
    df_footfall = pd.DataFrame(footfall_data)
    
    return df, df_footfall

df_license, df_footfall = load_all_data()

# --- 2. 사이드바 설정 [cite: 202] ---
st.sidebar.header("📍 분석 지역 선택")
districts = sorted(df_license["자치구"].dropna().unique())
selected_district = st.sidebar.selectbox("자치구", districts)

# 데이터 필터링
df_dist = df_license[df_license["자치구"] == selected_district].copy()
footfall_info = df_footfall[df_footfall["자치구"] == selected_district].iloc[0]

# --- 3. 고도화된 SRS 알고리즘 (유동인구 가중치 포함)  ---
def calculate_advanced_srs(data, footfall):
    # 1. 폐업률 지표 (40%) 
    opened = len(data[data["인허가일자"].dt.year >= 2022])
    closed = len(data[data["폐업일자"].dt.year >= 2022])
    c_rate = (closed / opened * 100) if opened > 0 else 50
    
    # 2. 밀집도 대비 유동인구 지표 (35%) 
    active = len(data[data["영업상태"] == "영업"])
    density_per_pop = (active / (footfall["일평균유동인구"] / 10000)) * 10 # 만명당 매장수
    
    # 3. 유동인구 매출 잠재력 지수 (25%) [cite: 187, 288]
    potential = (1 / footfall["매출지수"]) * 50 # 지수가 높을수록 위험도 낮음
    
    srs = (c_rate * 0.4) + (density_per_pop * 0.35) + (potential * 0.25)
    return round(min(100, srs), 1), active

risk_score, active_count = calculate_advanced_srs(df_dist, footfall_info)

# --- 4. 메인 대시보드 UI [cite: 205, 206] ---
st.title(f"🥐 BakeMap: {selected_district} 정밀 상권 분석")
st.markdown(f"**{selected_district}**의 인허가 데이터와 유동인구 흐름을 결합한 분석 결과입니다[cite: 176, 181].")

# 핵심 지표 KPI [cite: 207, 242, 252]
k1, k2, k3, k4 = st.columns(4)
k1.metric("일평균 유동인구", f"{footfall_info['일평균유동인구']:,}명", "서울시 데이터")
k2.metric("현재 운영 매장", f"{active_count}개")
k3.metric("상권 매출 지수", f"{footfall_info['매출지수']}x", "평균대비")
status = "위험" if risk_score > 70 else "주의" if risk_score > 40 else "안전"
k4.metric("창업 위험도(SRS)", f"{risk_score}점", status, delta_color="inverse")

st.divider()

# --- 5. 유동인구 및 매출 구조 분석 [cite: 181, 183] ---

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("👥 시간대별 유동인구 및 매출 비중")
    # 기획안 3장 및 추가 요청 사항 반영
    time_data = pd.DataFrame({
        "시간대": ["오전(07-11)", "점심(11-14)", "오후(14-17)", "저녁(17-21)"],
        "유동인구비중": [25, 30, 20, 25],
        "매출비중": [20, 15, 45, 20]
    })
    fig_time = go.Figure()
    fig_time.add_trace(go.Bar(x=time_data["시간대"], y=time_data["유동인구비중"], name="유동인구 %", marker_color='lightgrey'))
    fig_time.add_trace(go.Scatter(x=time_data["시간대"], y=time_data["매출비중"], name="매출 비중 %", line=dict(color='#E67E22', width=4)))
    fig_time.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_time, use_container_width=True)

with col_right:
    st.subheader("🎯 지역별 방문 연령대 및 인기 메뉴")
    age_df = pd.DataFrame({
        "연령대": ["20대", "30대", "40대", "50대+"],
        "비중": [25, 35, 25, 15] if footfall_info['매출지수'] > 1.3 else [15, 25, 35, 25]
    })
    fig_age = px.pie(age_df, values="비중", names="연령대", hole=0.5, color_discrete_sequence=px.colors.sequential.Oranges)
    st.plotly_chart(fig_age, use_container_width=True)

# --- 6. 시계열 및 추천 전략 [cite: 209, 210, 218] ---
st.divider()
st.subheader("📈 상권 성장성 및 진입 전략")
c1, c2 = st.columns([2, 1])

with c1:
    df_dist["year"] = df_dist["인허가일자"].dt.year
    trend = df_dist.groupby("year").size().reset_index(name="개업수")
    fig_trend = px.area(trend, x="year", y="개업수", title="연도별 신규 개업 추이", color_discrete_sequence=['#F39C12'])
    st.plotly_chart(fig_trend, use_container_width=True)

with c2:
    st.write("**📝 데이터 기반 가이드라인**")
    if footfall_info['매출지수'] > 1.5:
        st.success("🌟 **고매출 잠재 상권**: 유동인구가 매우 많으며 객단가가 높은 선물용 디저트 구성이 유리합니다.")
    elif risk_score < 40:
        st.info("✅ **안정적 진입 가능**: 경쟁 강도가 낮으므로 식사용 빵 위주의 충성 고객 확보 전략을 추천합니다.")
    else:
        st.warning("⚠️ **레드오션 주의**: 매장 밀집도가 높습니다. 유동인구 동선에 맞춘 테이크아웃 특화 전략이 필요합니다.")

# --- 7. 리포트 생성 및 데이터 [cite: 220, 221, 264] ---
st.divider()
if st.button("📄 상세 상권 분석 리포트 생성 (PDF)"):
    st.write(f"**{selected_district}** 지역 분석 리포트를 생성 중입니다... (Pro 플랜 전용) [cite: 264]")
st.dataframe(df_dist.sort_values("인허가일자", ascending=False).head(20), use_container_width=True)
