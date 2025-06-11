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
        # 컬럼 이름 추출
        col_name = [c for c in df.columns if "주문자명" in c][0]
        col_phone = [c for c in df.columns if "연락처" in c][0]
        col_receiver = [c for c in df.columns if "배송지 성명" in c][0]
        col_address = [c for c in df.columns if "주소" in c][0]
        col_date = [c for c in df.columns if "응답일시" in c][0]
        col_2kg = [c for c in df.columns if "2kg" in c][0]
        col_4kg = [c for c in df.columns if "4kg" in c][0]
        col_inquiry = [c for c in df.columns if "문의" in c or "의견" in c]
        col_inquiry = col_inquiry[0] if col_inquiry else None

        # 날짜 필터 설정
        df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
        start_date = st.date_input("시작 날짜", value=df[col_date].min().date())
        start_time = st.time_input("시작 시간", value=df[col_date].min().time())
        end_date = st.date_input("종료 날짜", value=df[col_date].max().date())
        end_time = st.time_input("종료 시간", value=df[col_date].max().time())

        start_dt = pd.to_datetime(f"{start_date} {start_time}")
        end_dt = pd.to_datetime(f"{end_date} {end_time}")

        # 수량 필터 UI
        filter_2kg = st.checkbox("✅ 2kg 수량 1개 이상", value=False)
        filter_4kg = st.checkbox("✅ 4kg 수량 1개 이상", value=False)

        df[col_2kg] = pd.to_numeric(df[col_2kg], errors="coerce").fillna(0).astype(int)
        df[col_4kg] = pd.to_numeric(df[col_4kg], errors="coerce").fillna(0).astype(int)

        # 필터링
        filtered_df = df[
            (df[col_date] >= start_dt) &
            (df[col_date] <= end_dt)
        ].copy()

        exploded_rows = []

        for _, row in filtered_df.iterrows():
            if filter_2kg and row[col_2kg] > 0:
                for _ in range(int(row[col_2kg])):
                    exploded_rows.append({
                        "상품명": "복숭아 2kg",
                        "수취인명": row[col_receiver] if pd.notna(row[col_receiver]) and str(row[col_receiver]).strip() else row[col_name],
                        "수취인 우편번호": "",
                        "수취인 주소": row[col_address],
                        "수취인 전화번호": str(row[col_phone]).replace(".0", "") if ".0" in str(row[col_phone]) else str(row[col_phone])
                    })
            if filter_4kg and row[col_4kg] > 0:
                for _ in range(int(row[col_4kg])):
                    exploded_rows.append({
                        "상품명": "복숭아 4kg",
                        "수취인명": row[col_receiver] if pd.notna(row[col_receiver]) and str(row[col_receiver]).strip() else row[col_name],
                        "수취인 우편번호": "",
                        "수취인 주소": row[col_address],
                        "수취인 전화번호": str(row[col_phone]).replace(".0", "") if ".0" in str(row[col_phone]) else str(row[col_phone])
                    })

        result_df = pd.DataFrame(exploded_rows)

        # 문의사항 데이터 추출
        if col_inquiry:
            inquiry_df = df[df[col_inquiry].notna() & (df[col_inquiry].astype(str).str.strip() != "")]
            inquiry_export = inquiry_df[[col_name, col_phone, col_inquiry]].copy()
        else:
            inquiry_export = pd.DataFrame(columns=[col_name, col_phone, "문의사항"])

        def to_excel_bytes(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()

        # 주문 데이터 다운로드
        st.success(f"📦 총 {len(result_df)}건 추출됨")
        st.download_button(
            label="📥 주문 엑셀 다운로드",
            data=to_excel_bytes(result_df),
            file_name="SSONG-Peach-Orders.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 문의사항 다운로드
        if not inquiry_export.empty:
            st.download_button(
                label="📝 문의사항만 다운로드",
                data=to_excel_bytes(inquiry_export),
                file_name="SSONG-Peach-Inquiries.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"처리 중 오류 발생: {e}")
