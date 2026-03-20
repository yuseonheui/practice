import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import pydeck as pdk
from sklearn.preprocessing import MinMaxScaler

# ------------------------------------------------
# 기본 설정
# ------------------------------------------------

st.set_page_config(
    page_title="BakeMap",
    layout="wide"
)

st.title("🥐 BakeMap - 데이터 기반 베이커리 입지 분석")
st.markdown("서울 공공데이터 기반 창업 상권 분석 플랫폼 MVP")

# ------------------------------------------------
# 데이터 로드
# ------------------------------------------------

@st.cache_data
def load_data():

    df = pd.read_csv("data/bakery_license.csv")

    df["인허가일자"] = pd.to_datetime(df["인허가일자"], errors="coerce")
    df["폐업일자"] = pd.to_datetime(df["폐업일자"], errors="coerce")

    return df

df = load_data()

# ------------------------------------------------
# 데이터 전처리
# ------------------------------------------------

df["open_year"] = df["인허가일자"].dt.year
df["close_year"] = df["폐업일자"].dt.year

df_active = df[df["영업상태"] == "영업"]

# ------------------------------------------------
# 사이드바
# ------------------------------------------------

st.sidebar.header("지역 선택")

districts = sorted(df["자치구"].dropna().unique())

selected_district = st.sidebar.selectbox(
    "자치구",
    districts
)

df_district = df[df["자치구"] == selected_district].copy()

# ------------------------------------------------
# KPI 계산
# ------------------------------------------------

current_year = datetime.datetime.now().year

active = df_district[df_district["영업상태"] == "영업"]

recent_open = df_district[
    df_district["open_year"] == current_year - 1
]

recent_close = df_district[
    df_district["close_year"] == current_year - 1
]

active_count = len(active)
open_count = len(recent_open)
close_count = len(recent_close)

closure_rate = close_count / open_count if open_count > 0 else 0

# ------------------------------------------------
# 밀집도 계산 (행정동 기준)
# ------------------------------------------------

density_table = (
    df[df["영업상태"] == "영업"]
    .groupby("행정동")
    .size()
    .reset_index(name="density")
)

# ------------------------------------------------
# 개업 증가율 계산
# ------------------------------------------------

growth_table = (
    df.groupby(["행정동", "open_year"])
    .size()
    .reset_index(name="open_count")
)

growth_table["prev_year"] = growth_table.groupby("행정동")["open_count"].shift(1)

growth_table["growth"] = (
    growth_table["open_count"] - growth_table["prev_year"]
) / growth_table["prev_year"]

growth_table = growth_table.replace([np.inf, -np.inf], np.nan)

growth_table = growth_table.dropna()

# ------------------------------------------------
# 폐업률 계산
# ------------------------------------------------

closure_table = (
    df.groupby("행정동")
    .apply(
        lambda x: len(x[x["폐업일자"].notna()]) / len(x)
    )
    .reset_index(name="closure_rate")
)

# ------------------------------------------------
# SRS 계산
# ------------------------------------------------

risk_df = density_table.merge(
    closure_table,
    on="행정동",
    how="left"
)

latest_growth = growth_table.sort_values(
    "open_year"
).groupby("행정동").tail(1)

risk_df = risk_df.merge(
    latest_growth[["행정동", "growth"]],
    on="행정동",
    how="left"
)

risk_df = risk_df.fillna(0)

scaler = MinMaxScaler()

risk_df[["density_norm","closure_norm","growth_norm"]] = scaler.fit_transform(
    risk_df[["density","closure_rate","growth"]]
)

risk_df["SRS"] = (
    risk_df["closure_norm"] * 0.40 +
    risk_df["density_norm"] * 0.35 +
    risk_df["growth_norm"] * 0.25
) * 100

risk_df["SRS"] = risk_df["SRS"].round(1)

# ------------------------------------------------
# KPI 표시
# ------------------------------------------------

st.subheader("상권 요약")

col1, col2, col3, col4 = st.columns(4)

col1.metric("현재 영업 매장", active_count)
col2.metric("최근 개업", open_count)
col3.metric("최근 폐업", close_count)
col4.metric("폐업률", round(closure_rate,2))

# ------------------------------------------------
# 지도 시각화
# ------------------------------------------------

st.subheader("베이커리 위치 지도")

if "위도" in df.columns:

    map_df = df_active[["위도","경도"]].dropna()

    layer = pdk.Layer(
        "ScatterplotLayer",
        map_df,
        get_position="[경도, 위도]",
        radius_scale=10,
        radius_min_pixels=3,
        get_fill_color=[200,30,0,160],
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=37.55,
        longitude=126.98,
        zoom=11
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/light-v9"
    )

    st.pydeck_chart(r)

# ------------------------------------------------
# 밀집도 히트맵
# ------------------------------------------------

st.subheader("행정동 베이커리 밀집도")

density_chart = density_table.sort_values(
    "density",
    ascending=False
).head(15)

fig_density = px.bar(
    density_chart,
    x="행정동",
    y="density",
    title="베이커리 밀집 상위 지역"
)

st.plotly_chart(fig_density,use_container_width=True)

# ------------------------------------------------
# 연도별 개업 추이
# ------------------------------------------------

st.subheader("연도별 개업 추이")

open_trend = (
    df_district.groupby("open_year")
    .size()
    .reset_index(name="개업수")
)

fig_open = px.bar(
    open_trend,
    x="open_year",
    y="개업수",
    title="연도별 개업"
)

st.plotly_chart(fig_open,use_container_width=True)

# ------------------------------------------------
# 폐업 추이
# ------------------------------------------------

st.subheader("연도별 폐업 추이")

close_trend = (
    df_district.dropna(subset=["close_year"])
    .groupby("close_year")
    .size()
    .reset_index(name="폐업수")
)

fig_close = px.line(
    close_trend,
    x="close_year",
    y="폐업수",
    title="연도별 폐업"
)

st.plotly_chart(fig_close,use_container_width=True)

# ------------------------------------------------
# 위험도 순위
# ------------------------------------------------

st.subheader("창업 위험도 분석 (SRS)")

risk_rank = risk_df.sort_values("SRS")

st.dataframe(
    risk_rank[["행정동","SRS"]].head(20)
)

# ------------------------------------------------
# 추천 상권
# ------------------------------------------------

st.subheader("추천 창업 상권 TOP 5")

recommend = risk_df.sort_values("SRS").head(5)

for i,row in recommend.iterrows():

    st.write(
        f"⭐ {row['행정동']}  |  위험도 {row['SRS']}"
    )

# ------------------------------------------------
# 데이터 테이블
# ------------------------------------------------

st.subheader("데이터 미리보기")

st.dataframe(df_district.head(100))

# ------------------------------------------------
# 서비스 설명
# ------------------------------------------------

st.markdown("---")

st.markdown(
"""
### BakeMap 분석 기준

창업 위험도(SRS)는 아래 지표 기반으로 계산됩니다.

- 폐업률 40%
- 밀집도 35%
- 개업 증가율 25%

점수 해석

0~30 : 창업 유망  
31~50 : 보통  
51~70 : 진입 주의  
71~100 : 고위험
"""
)
