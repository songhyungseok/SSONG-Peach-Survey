import streamlit as st
import pandas as pd
import numpy as np
import re
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
        # 컬럼 찾기 (포함 단어 기반)
        def find_column(df, keyword):
            for col in df.columns:
                if keyword in str(col):
                    return col
            return None

        col_date = find_column(df, "응답일시")
        col_2kg = find_column(df, "2kg")
        col_4kg = find_column(df, "4kg")
        col_name = find_column(df, "입금자명")
        col_phone = find_column(df, "연락처")
        col_receiver = find_column(df, "배송지 성명")
        col_address = find_column(df, "주소")
        col_note = find_column(df, "의견")

        df[col_date] = pd.to_datetime(df[col_date], errors='coerce')

        # 날짜 필터 UI
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

        df[col_2kg] = pd.to_numeric(df[col_2kg], errors='coerce').fillna(0)
        df[col_4kg] = pd.to_numeric(df[col_4kg], errors='coerce').fillna(0)

        filtered_df = df[
            (df[col_date] >= start_dt) & (df[col_date] <= end_dt)
        ]

        # 주문 수량에 따라 행 반복 생성
       output_rows = []
       for _, row in filtered_df.iterrows():
       for _ in range(int(row["2kg"])):
         output_rows.append({
            "상품명": "복숭아 2kg",
            "수취인명": row["수취인명"],
            "수취인 우편번호": "",
            "수취인 주소": row[col_address],
            "수취인 전화번호": row["수취인 전화번호"],
         })
       for _ in range(int(row["4kg"])):
         output_rows.append({
            "상품명": "복숭아 4kg",
            "수취인명": row["수취인명"],
            "수취인 우편번호": "",
            "수취인 주소": row[col_address],
            "수취인 전화번호": row["수취인 전화번호"],
         })

         output = pd.DataFrame(output_rows)

        # 아무 필터도 안했으면 비움
        if not filter_2kg and not filter_4kg:
            output_rows = []

        output_df = pd.DataFrame(output_rows)

        # 수취인 정보 정리
        output_df["수취인명"] = output_df[col_receiver].fillna("").replace("", np.nan)
        output_df["수취인명"] = output_df["수취인명"].fillna(output_df[col_name])

        def normalize_phone(phone):
          phone_str = str(phone).strip()
          if phone_str.endswith(".0"):
            phone_str = phone_str[:-2]
          if phone_str.startswith("1") and not phone_str.startswith("01"):
            phone_str = "0" + phone_str
          return phone_str

        output_df["수취인 전화번호"] = output_df[col_phone].apply(normalize_phone)

        order_excel = pd.DataFrame({
            "상품명": "복숭아",
            "수취인명": output_df["수취인명"],
            "수취인 우편번호": "",
            "수취인 주소": output_df[col_address],
            "수취인 전화번호": output_df["수취인 전화번호"],
        })

        # 엑셀 변환
        def to_excel_bytes(df_dict):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                for sheet, df in df_dict.items():
                    df.to_excel(writer, index=False, sheet_name=sheet)
            return output.getvalue()

        st.success(f"📦 총 {len(order_excel)}건 추출됨")
        st.download_button(
            label="📥 복숭아 주문 엑셀 다운로드",
            data=to_excel_bytes({"주문서": order_excel}),
            file_name="SSONG-Peach-Filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # -------------------- 문의사항 추출 ----------------------
        st.markdown("---")
        st.subheader("💬 문의사항 추출")

        if st.button("📄 문의사항 엑셀 추출"):
            notes_df = df[df[col_note].notnull() & (df[col_note].astype(str).str.strip() != "")].copy()
            notes_df["주문자명"] = notes_df[col_name]
            notes_df["연락처"] = notes_df[col_phone].apply(normalize_phone)
            notes_df["문의내용"] = notes_df[col_note]

            # 시트1: 전체 문의사항
            sheet1 = notes_df[["주문자명", "연락처", "문의내용"]]

            # 시트2: '흠과'가 포함된 문의사항
            sheet2 = sheet1[sheet1["문의내용"].str.contains("흠과", case=False, na=False)]

            inquiry_excel = to_excel_bytes({"전체문의": sheet1, "흠과문의": sheet2})

            st.download_button(
                label="📥 문의사항 엑셀 다운로드",
                data=inquiry_excel,
                file_name="SSONG-Peach-Inquiry.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # -------------------- 카카오톡 요약 ----------------------
        st.subheader("📲 문의사항 카카오톡 요약")
        notes_df = df[df[col_note].notnull() & (df[col_note].astype(str).str.strip() != "")].copy()
        summary_lines = []

        for idx, row in notes_df.iterrows():
            name = str(row[col_name]).strip()
            phone = normalize_phone(row[col_phone])
            note = str(row[col_note]).strip()
            summary_lines.append(f"{idx+1}. 주문자: {name} / 연락처: {phone}\n   ➤ 요청: {note}")

        kakao_summary = "\n\n".join(summary_lines)

        st.text_area("📋 카카오톡용 요약", kakao_summary, height=300)

        st.download_button("📄 텍스트 파일로 저장", kakao_summary.strip(), file_name="문의사항요약.txt")
        st.code(kakao_summary, language="text")

    except Exception as e:
        st.error(f"처리 중 오류 발생: {e}")
