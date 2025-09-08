# -*- coding: utf-8 -*-
"""상암고 급식데이터 스트림릿 사이트"""
import run
import streamlit as st
import requests
import datetime
import pytz
import re
import plotly.express as px
import random

# --- 한국 시간 기준 오늘 날짜 ---
한국시간 = pytz.timezone('Asia/Seoul')
오늘날짜 = datetime.datetime.now(한국시간).date()

# --- 날짜 포맷 변환 ---
def date_to_str(date_obj):
    return date_obj.strftime("%y%m%d")

# --- 급식 API 요청 ---
def get_meal(date_obj):
    date_str = date_to_str(date_obj)
    url = f'https://open.neis.go.kr/hub/mealServiceDietInfo?ATPT_OFCDC_SC_CODE=B10&SD_SCHUL_CODE=7010806&Type=json&MLSV_YMD={date_str}'
    try:
        response = requests.get(url)
        data = response.json()
        dish_str = data['mealServiceDietInfo'][1]['row'][0]['DDISH_NM']
        nutri_str = data['mealServiceDietInfo'][1]['row'][0]['NTR_INFO']
        return dish_str, nutri_str
    except Exception:
        return None, None

# --- 급식 텍스트 클리닝 ---
def clean_meal(raw_menu):
    if not raw_menu:
        return "급식 정보가 없어요."
    step1 = raw_menu.replace('<br/>', '\n')
    step2 = re.sub(r'\d', '', step1)
    step3 = step2.replace('(', '').replace(')', '').replace('.', '')
    return step3.strip()

# --- 영양정보 파싱 ---
def parse_nutrition(nutri_str):
    if not nutri_str:
        return {}
    nutri_str = nutri_str.replace('<br/>', '\n')
    items = nutri_str.split('\n')
    nutri_dict = {}
    for item in items:
        if ':' in item:
            key, value = item.split(':')
            try:
                nutri_dict[key.strip()] = float(re.findall(r"[-+]?\d*\.\d+|\d+", value)[0])
            except:
                pass
    return nutri_dict

# --- Streamlit UI ---
st.set_page_config(page_title="상암고 급식", page_icon="🍱", layout="centered")
st.title("🍱 상암고 급식 조회")
st.caption("어제·오늘·내일 버튼 또는 달력에서 날짜를 선택해 급식을 확인하세요!")

# --- 날짜 버튼 ---
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⬅️ 어제"):
        오늘날짜 = 오늘날짜 - datetime.timedelta(days=1)
with col2:
    if st.button("📅 오늘"):
        오늘날짜 = datetime.datetime.now(한국시간).date()
with col3:
    if st.button("➡️ 내일"):
        오늘날짜 = 오늘날짜 + datetime.timedelta(days=1)

# --- 달력 선택 ---
선택날짜 = st.date_input("날짜 선택", value=오늘날짜, min_value=datetime.date(2020,1,1))
오늘날짜 = 선택날짜

# --- 급식 데이터 불러오기 ---
급식원본, 영양원본 = get_meal(오늘날짜)

if 급식원본:
    클린급식 = clean_meal(급식원본)
    st.success(f"📅 {오늘날짜.strftime('%Y-%m-%d')} 급식 메뉴")
    st.text(클린급식)

    # --- 주요 영양소 막대 그래프 ---
    영양정보 = parse_nutrition(영양원본)
    if 영양정보:
        st.subheader("⚖️ 주요 영양소 비교 (탄수화물 / 단백질 / 지방)")
        macro_keys = ["탄수화물(g)", "단백질(g)", "지방(g)"]
        macro_data = {k: 영양정보[k] for k in macro_keys if k in 영양정보}

        if macro_data:
            fig_bar = px.bar(
                x=list(macro_data.keys()),
                y=list(macro_data.values()),
                text=list(macro_data.values()),
                color=list(macro_data.keys()),
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_bar.update_traces(
                textposition="outside",
                textfont_size=14
            )
            fig_bar.update_layout(
                yaxis_title="영양소(g)",
                xaxis_title="",
                height=500,
                margin=dict(t=50, b=80, l=80, r=50),
                font=dict(size=16),
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("탄수화물, 단백질, 지방 정보가 제공되지 않았습니다.")

    else:
        st.info("영양정보가 제공되지 않았습니다.")
else:
    st.error("해당 날짜에 급식 정보가 없어요.")

# --- 랜덤 메뉴 추천 ---
추천메뉴목록 = [
    # 한식
    "김치찌개", "된장찌개", "부대찌개", "갈비탕", "삼계탕", "순두부찌개", "청국장",
    "제육볶음", "불고기", "닭볶음탕", "찜닭", "갈비찜", "비빔밥", "콩나물국밥",
    "떡국", "설렁탕", "순대국밥", "감자탕",

    # 분식
    "떡볶이", "라면", "김밥", "쫄면", "순대", "튀김", "치즈돈까스", "핫도그",

    # 중식
    "짜장면", "짬뽕", "탕수육", "깐풍기", "유산슬", "마파두부", "중화비빔밥", "양꼬치",

    # 일식
    "초밥", "돈카츠", "가츠동", "오야코동", "라멘", "우동", "소바", "규동", "카레라이스",

    # 양식
    "스파게티", "알리오올리오", "까르보나라", "토마토파스타", "피자", "햄버거",
    "스테이크", "리조또", "오믈렛라이스", "프렌치토스트",

    # 기타/세계 음식
    "케밥", "부리또", "타코", "쌀국수", "커리", "팟타이", "필라프", "바비큐",
    "샌드위치", "핫도그", "치킨윙", "샐러드"
]

if st.button("🎲 랜덤 메뉴 추천 받기"):
    추천 = random.choice(추천메뉴목록)
    st.info(f"오늘의 랜덤 추천 메뉴는 👉 **{추천}** 입니다!")


# --- 푸터 정보 ---
st.markdown("---")
st.caption("📍 상암고등학교 | 개발: 엄수아")
