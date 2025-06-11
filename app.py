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
        def find_column(keyword, columns):
            matches = [col for col in columns if keyword.lower() in col.lower()]
            if not matches:
                raise ValueError(f"'{keyword}'를 포함하는 컬럼을 찾을 수 없습니다.")
            return matches[0]

        col_date = "응답일시"
        col_2kg = find_column("2kg", df.columns)
        col_4kg = find_column("4kg", df.columns)
        col_name = "주문자명 (입금자명)(*)"
        col_phone = "주문자 연락처(*)"
        col_receiver = "배송지 성명(주문자와 동일 할 경우 미입력)"
        col_address = "주소(*)"

        df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
        min_date = df[col_date].min()
        max_date = df[col_date].max()

        start_date = st.date_input("시작 날짜", value=min_date.date())
        start_time = st.time_input("시작 시간", value=min_date.time())
        end_date = st.date_input("종료 날짜", value=max_date.date())
        end_time = st.time_input("종료 시간", value=max_date.time())

        start_dt = pd.to_datetime(f"{start_date} {start_time}")
        end_dt = pd.to_datetime(f"{end_date} {end_time}")

        filter_2kg = st.checkbox("✅ 2kg 수량 1개 이상", value=False)
        filter_4kg = st.checkbox("✅ 4kg 수량 1개 이상", value=False)

        if not filter_2kg and not filter_4kg:
            st.warning("✅ 필터를 하나 이상 선택해주세요.")
            st.stop()

        df[col_2kg] = pd.to_numeric(df[col_2kg].astype(str).str.strip(), errors="coerce").fillna(0)
        df[col_4kg] = pd.to_numeric(df[col_4kg].astype(str).str.strip(), errors="coerce").fillna(0)

        filtered_df = df[
            (df[col_date] >= start_dt) &
            (df[col_date] <= end_dt)
        ].copy()  # ✅ View 대신 복사본으로 처리하여 경고 방지

        # 수취인명 처리 (경고 해결)
        filtered_df.loc[:, "수취인명"] = filtered_df[col_receiver].fillna("").astype(str)
        filtered_df.loc[:, "수취인명"] = filtered_df["수취인명"].replace("", np.nan)
        filtered_df.loc[:, "수취인명"] = filtered_df["수취인명"].fillna(filtered_df[col_name])

        def normalize_phone(phone):
            phone_str = str(phone).strip()
            if phone_str.startswith("1") and not phone_str.startswith("01"):
                return "0" + phone_str
            return phone_str

        filtered_df.loc[:, "수취인 전화번호"] = filtered_df[col_phone].apply(normalize_phone)

        expanded_rows = []
        for _, row in filtered_df.iterrows():
            name = row["수취인명"]
            address = row[col_address]
            phone = row["수취인 전화번호"]

            if filter_2kg:
                for _ in range(int(row[col_2kg])):
                    expanded_rows.append({
                        "상품명": "복숭아 2kg",
                        "수취인명": name,
                        "수취인 우편번호": "",
                        "수취인 주소": address,
                        "수취인 전화번호": phone,
                    })

            if filter_4kg:
                for _ in range(int(row[col_4kg])):
                    expanded_rows.append({
                        "상품명": "복숭아 4kg",
                        "수취인명": name,
                        "수취인 우편번호": "",
                        "수취인 주소": address,
                        "수취인 전화번호": phone,
                    })

        output = pd.DataFrame(expanded_rows)

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
