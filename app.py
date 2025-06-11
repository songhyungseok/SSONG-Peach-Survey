import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="복숭아 주문 필터", layout="centered")
st.title("🍑 복숭아 주문서 필터링 도구")

# 비밀번호 입력
password = st.text_input("비밀번호를 입력하세요", type="password")
if password != "gudtjr0428":
    st.stop()

# 파일 업로드
uploaded_file = st.file_uploader("📤 네이버폼 엑셀(.xlsx) 업로드", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    try:
        # 컬럼명 지정
        col_date = "응답일시"
        col_2kg = "신선 2kg (24,000원) (box단위)(*)"
        col_4kg = "신선 4kg (43,000원) (box단위)(*)"
        col_name =
