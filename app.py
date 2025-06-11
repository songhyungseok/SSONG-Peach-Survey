
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="복숭아 주문 필터", layout="centered")
st.title("🍑 복숭아 주문서 필터링 도구")

password = st.text_input("비밀번호를 입력하세요", type="password")
if password != "gudtjr0428":
    st.stop()
    
uploaded_file = st.file_uploader("📤 네이버폼 엑셀(.xlsx) 업로드", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    try:
        # 컬럼 설정
        col_date = "응답일시"
        col_2kg = "신선 2kg (24,000원) (box단위)(*)"
        col_4kg = "신선 4kg (43,000원) (box단위)(*)"
        col_name = "주문자명 (입금자명)(*)"
        col_phone = "주문자 연락처(*)"
        col_receiver = "배송지 성명(주문자와 동일 할 경우 미입력)"
        col_address = "주소(*)"

        # 날짜+시간 필터 UI
        df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
        min_date = df[col_date].min()
        max_date = df[col_date].max()

        start_date = st.date_input("시작 날짜", value=min_date.date())
        start_time = st.time_input("시작 시간", value=min_date.time())
        end_date = st.date_input("종료 날짜", value=max_date.date())
        end_time = st.time_input("종료 시간", value=max_date.time())

        start_dt = pd.to_datetime(f"{start_date} {start_time}")
        end_dt = pd.to_datetime(f"{end_date} {end_time}")

        # 수량 필터
        filter_2kg = st.checkbox("✅ 2kg 수량 1개 이상", value=True)
        filter_4kg = st.checkbox("✅ 4kg 수량 1개 이상", value=True)

        # 수량 숫자화
        df[col_2kg] = pd.to_numeric(df[col_2kg].astype(str).str.strip(), errors="coerce").fillna(0)
        df[col_4kg] = pd.to_numeric(df[col_4kg].astype(str).str.strip(), errors="coerce").fillna(0)

        # 필터 적용
        filtered_df = df[
            (df[col_date] >= start_dt) &
            (df[col_date] <= end_dt)
        ]
        if filter_2kg and not filter_4kg:
            filtered_df = filtered_df[filtered_df[col_2kg] >= 1]
        elif filter_4kg and not filter_2kg:
            filtered_df = filtered_df[filtered_df[col_4kg] >= 1]
        elif filter_2kg and filter_4kg:
            filtered_df = filtered_df[(filtered_df[col_2kg] >= 1) | (filtered_df[col_4kg] >= 1)]

        filtered_df["수취인명"] = filtered_df[col_receiver].fillna("").replace("", np.nan)
        filtered_df["수취인명"] = filtered_df["수취인명"].fillna(filtered_df[col_name])

        def normalize_phone(phone):
            phone_str = str(phone).strip()
            if phone_str.startswith("1") and not phone_str.startswith("01"):
                return "0" + phone_str
            return phone_str

        filtered_df["수취인 전화번호"] = filtered_df[col_phone].apply(normalize_phone)

        output = pd.DataFrame({
            "상품명": "복숭아",
            "수취인명": filtered_df["수취인명"],
            "수취인 우편번호": "",
            "수취인 주소": filtered_df[col_address],
            "수취인 전화번호": filtered_df["수취인 전화번호"],
        })

        def to_excel_bytes(df):
            output_stream = BytesIO()
            with pd.ExcelWriter(output_stream, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False)
            return output_stream.getvalue()

        st.success(f"📦 총 {len(output)}건 추출됨")
        st.download_button(
            label="📥 엑셀 다운로드",
            data=to_excel_bytes(output),
            file_name="SSONG-Peach-Filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"처리 중 오류 발생: {e}")
