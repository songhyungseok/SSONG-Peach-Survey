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

    # --------- 유틸 함수 ---------
    def normalize_phone(phone):
        phone_str = str(phone).strip()
        if phone_str.endswith(".0"):
            phone_str = phone_str[:-2]
        if phone_str.startswith("1") and not phone_str.startswith("01"):
            return "0" + phone_str
        return phone_str

    def to_excel_bytes(sheets: dict):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for name, sheet_df in sheets.items():
                sheet_df.to_excel(writer, index=False, sheet_name=name)
        return output.getvalue()

    def find_col(cols, keyword):
        for col in cols:
            if keyword in col:
                return col
        return None

    # --------- 컬럼 탐색 ---------
    col_date = find_col(df.columns, "응답일시")
    col_2kg = find_col(df.columns, "2kg")
    col_4kg = find_col(df.columns, "4kg")
    col_name = find_col(df.columns, "입금자명")
    col_phone = find_col(df.columns, "연락처")
    col_receiver = find_col(df.columns, "성명")
    col_address = find_col(df.columns, "주소")
    col_comment = find_col(df.columns, "의견")

    # 날짜 필터 설정
    if col_date:
        df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
        min_date = df[col_date].min()
        max_date = df[col_date].max()

        st.subheader("📅 주문 필터 설정")
        start_date = st.date_input("시작 날짜", value=min_date.date())
        start_time = st.time_input("시작 시간", value=min_date.time())
        end_date = st.date_input("종료 날짜", value=max_date.date())
        end_time = st.time_input("종료 시간", value=max_date.time())

        start_dt = pd.to_datetime(f"{start_date} {start_time}")
        end_dt = pd.to_datetime(f"{end_date} {end_time}")

    filter_2kg = st.checkbox("✅ 2kg 수량 1개 이상", value=True)
    filter_4kg = st.checkbox("✅ 4kg 수량 1개 이상", value=True)

    # --------- 주문 필터링 ---------
    if st.button("📦 복숭아 주문 추출"):
        if not all([col_date, col_2kg, col_4kg, col_name, col_phone, col_address]):
            st.error("필수 컬럼이 누락되었습니다.")
        else:
            df[col_2kg] = pd.to_numeric(df[col_2kg], errors="coerce").fillna(0).astype(int)
            df[col_4kg] = pd.to_numeric(df[col_4kg], errors="coerce").fillna(0).astype(int)

            filtered_df = df[(df[col_date] >= start_dt) & (df[col_date] <= end_dt)].copy()

            if not (filter_2kg or filter_4kg):
                filtered_df = filtered_df[filtered_df[[col_2kg, col_4kg]].sum(axis=1) == -1]  # 빈 결과
            else:
                condition = pd.Series([False] * len(filtered_df))
                if filter_2kg:
                    condition |= filtered_df[col_2kg] >= 1
                if filter_4kg:
                    condition |= filtered_df[col_4kg] >= 1
                filtered_df = filtered_df[condition]

            filtered_df["수취인명"] = filtered_df[col_receiver].fillna("").replace("", np.nan)
            filtered_df["수취인명"] = filtered_df["수취인명"].fillna(filtered_df[col_name])
            filtered_df["수취인 전화번호"] = filtered_df[col_phone].apply(normalize_phone)

            rows = []
            for _, row in filtered_df.iterrows():
                for _ in range(row[col_2kg]):
                    rows.append({
                        "상품명": "복숭아 2kg",
                        "수취인명": row["수취인명"],
                        "수취인 우편번호": "",
                        "수취인 주소": row[col_address],
                        "수취인 전화번호": row["수취인 전화번호"]
                    })
                for _ in range(row[col_4kg]):
                    rows.append({
                        "상품명": "복숭아 4kg",
                        "수취인명": row["수취인명"],
                        "수취인 우편번호": "",
                        "수취인 주소": row[col_address],
                        "수취인 전화번호": row["수취인 전화번호"]
                    })

            final_df = pd.DataFrame(rows)
            st.success(f"✅ 총 {len(final_df)}건 추출 완료")
            st.download_button(
                label="📥 주문 엑셀 다운로드",
                data=to_excel_bytes({"주문 목록": final_df}),
                file_name="SSONG-Peach-Filtered.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # --------- 문의사항 추출 ---------
    if st.button("📋 문의사항 추출"):
        if not col_comment or not col_name or not col_phone:
            st.warning("문의사항 또는 기본 정보 컬럼이 누락되었습니다.")
        else:
            comment_df = df[df[col_comment].astype(str).str.strip() != ""].copy()
            if comment_df.empty:
                st.info("문의사항이 있는 주문이 없습니다.")
            else:
                comment_df["연락처"] = comment_df[col_phone].apply(normalize_phone)
                sheet1_df = comment_df[[col_name, col_phone, col_comment]].rename(columns={
                    col_name: "주문자명",
                    col_phone: "연락처",
                    col_comment: "문의내용"
                })
                sheet2_df = sheet1_df[sheet1_df["문의내용"].str.contains("흠과", na=False)]

                st.success(f"📋 문의 주문 {len(sheet1_df)}건 (흠과 포함: {len(sheet2_df)}건)")
                st.download_button(
                    label="📥 문의사항 엑셀 다운로드",
                    data=to_excel_bytes({
                        "문의사항 전체": sheet1_df,
                        "흠과 문의": sheet2_df
                    }),
                    file_name="문의사항_주문목록.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
