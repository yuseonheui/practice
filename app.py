import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# --- 1. 페이지 설정 및 스타일 ---
st.set_page_config(page_title="BakeMap - 데이터 기반 입지 분석", layout="wide")

# --- 2. 데이터 로딩 (Mock Data 포함) ---
@st.cache_data
def get_advanced_data():
    # 기본 상권 데이터 (SRS 로직 기반) [cite: 32, 99]
    base_data = {
        '지역': ['강남역/서초', '성수동/연남', '잠실/마포', '노원/은평', '한남/이태원'],
        '위험점수': [65.2, 32.1, 44.5, 25.4, 41.2],
        '매장수': [120, 85, 92, 45, 60],
        '월평균매출': [5200, 4100, 3800, 2600, 4800], # 단위: 만원
        '위도': [37.497, 37.544, 37.513, 37.654, 37.535],
        '경도': [127.027, 127.056, 127.100, 127.056, 127.001],
        '주방문층': ['3040 오피스', '2030 트렌드', '3040 가족', '5060 주거', '2030 외국인']
    }
    df = pd.DataFrame(base_data)
    return df

df = get_advanced_data()

# --- 3. 사이드바: 지역 선택 및 필터 ---
st.sidebar.title("🥐 BakeMap 분석 필터")
selected_region = st.sidebar.selectbox("분석 대상 지역 선택", df['지역'])
target_info = df[df['지역'] == selected_region].iloc[0]

# --- 4. 메인 대시보드 ---
st.title(f"📍 {selected_region} 상권 상세 분석 보고서")
st.markdown(f"**핵심 가치:** {target_info['주방문층']} 중심의 {selected_region} 상권 데이터 분석 결과입니다.") [cite: 14]

# 상단 KPI (주요 지표) [cite: 59, 60]
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("창업 위험도(SRS)", f"{target_info['위험점수']}점", "상대지표") [cite: 95]
kpi2.metric("예상 월 매출", f"{target_info['월평균매출']}만원", "평균치")
kpi3.metric("현재 운영 매장", f"{target_info['매장수']}개")
kpi4.metric("주요 타겟층", target_info['주방문층'])

st.write("---")

# 중간 섹션: 지도 및 연령대 분석
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("🗺️ 입지 밀집도 (Heatmap)") [cite: 48, 56]
    m = folium.Map(location=[target_info['위도'], target_info['경도']], zoom_start=14, tiles="cartodbpositron")
    folium.Circle(
        location=[target_info['위도'], target_info['경도']],
        radius=500, color="orange", fill=True, tooltip=f"{selected_region} 핵심 상권"
    ).add_to(m)
    st_folium(m, width="100%", height=400)

with col2:
    st.subheader("👥 지역별 방문 연령대")
    # 가상의 연령대 데이터
    age_data = pd.DataFrame({
        '연령대': ['10대', '20대', '30대', '40대', '50대', '60대+'],
        '비중': [5, 25, 30, 20, 15, 5] if "2030" in target_info['주방문층'] else [5, 10, 20, 30, 25, 10]
    })
    fig_age = px.pie(age_data, values='비중', names='연령대', hole=0.4, 
                     color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_age, use_container_width=True)

# 하단 섹션: 시간대별 분석 및 메뉴 추천
st.write("---")
col3, col4 = st.columns(2)

with col3:
    st.subheader("⏰ 시간대별 매출 비중")
    time_data = pd.DataFrame({
        '시간대': ['오전(07-11)', '점심(11-14)', '오후(14-17)', '저녁(17-21)'],
        '매출비중(%)': [20, 15, 45, 20]
    })
    fig_time = px.line(time_data, x='시간대', y='매출비중(%)', markers=True)
    st.plotly_chart(fig_time, use_container_width=True)

with col4:
    st.subheader("🥖 시간대별 인기 메뉴 추천")
    # 비즈니스 로직에 기반한 추천
    recommendations = {
        '오전(07-11)': "샌드위치, 아메리카노 세트",
        '점심(11-14)': "식사용 빵(사워도우, 바게트)",
        '오후(14-17)': "디저트류(타르트, 휘낭시에)",
        '저녁(17-21)': "식빵류, 홀케이크"
    }
    for time, menu in recommendations.items():
        st.write(f"**{time}**: {menu}")

# --- 5. 리포트 생성 섹션 --- [cite: 73, 74]
st.write("---")
if st.button("📄 상세 상권 분석 PDF 리포트 생성"):
    st.info(f"{selected_region} 지역의 데이터 기반 창업 제안서를 생성 중입니다...")
    st.success("리포트 생성이 완료되었습니다. (다운로드 링크 활성화)")
