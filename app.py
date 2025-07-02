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
        col_name = find_column(df, "입금자명")
        col_phone = find_column(df, "연락처")
        col_receiver = find_column(df, "받는사람 성명")
        col_receiver_phone = find_column(df, "받는사람 전화번호")
        col_address = find_column(df, "주소")
        col_note = find_column(df, "의견")

        # "2kg", "4kg" 항목 찾기
        #col_2kg = [col for col in df.columns if "2kg" in col][0]
        #col_4kg = [col for col in df.columns if "4kg" in col][0]
        #col_1kg = [col for col in df.columns if "1.5kg" in col][0]

        def find_col_by_keyword(columns, keyword):
            matches = [col for col in columns if keyword in col]
            return matches[0] if matches else None

        col_2kg = find_col_by_keyword(df.columns, "2kg")
        col_4kg = find_col_by_keyword(df.columns, "4kg")
        col_1kg = find_col_by_keyword(df.columns, "1.5kg")
        
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

        filter_2kg = st.checkbox("✅ 2kg 수량 1개 이상", value=True)
        filter_4kg = st.checkbox("✅ 4kg 수량 1개 이상", value=True)
        filter_1kg = st.checkbox("✅ 1.5kg 수량 1개 이상", value=True)

        for col in [col_2kg, col_4kg, col_1kg]:
         if col:
          df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
         else:
          df[col] = 0  # 컬럼이 없어도 오류 안 나게 기본값 0 설정

        if col_2kg:
           df[col_2kg] = pd.to_numeric(df[col_2kg], errors='coerce').fillna(0)
        if col_4kg:
           df[col_4kg] = pd.to_numeric(df[col_4kg], errors='coerce').fillna(0)
        if col_1kg:
           df[col_1kg] = pd.to_numeric(df[col_1kg], errors='coerce').fillna(0)
    
        df[col_2kg] = pd.to_numeric(df[col_2kg], errors='coerce').fillna(0)
        df[col_4kg] = pd.to_numeric(df[col_4kg], errors='coerce').fillna(0)
        df[col_1kg] = pd.to_numeric(df[col_1kg], errors='coerce').fillna(0)

        filtered_df = df[(df[col_date] >= start_dt) & (df[col_date] <= end_dt)]

        def normalize_phone(phone):
            phone_str = str(phone).strip()
            if phone_str.endswith(".0"):
                phone_str = phone_str[:-2]
            phone_str = re.sub(r"[^0-9]", "", phone_str)
            if phone_str.startswith("1") and not phone_str.startswith("01"):
                phone_str = "0" + phone_str
            return phone_str

        # 수취인 정보 정리
        filtered_df["수취인명"] = filtered_df[col_receiver].fillna("").replace("", np.nan)
        filtered_df["수취인명"] = filtered_df["수취인명"].fillna(filtered_df[col_name])
        filtered_df["수취인 전화번호"] = filtered_df[col_phone].apply(normalize_phone)

        # 배송지 연락처 우선, 없으면 주문자 연락처
        filtered_df["수취인 전화번호"] = filtered_df.apply(
          lambda row: normalize_phone(row[col_receiver_phone]) if pd.notna(row.get(col_receiver_phone)) and str(row[col_receiver_phone]).strip() != "" 
          else normalize_phone(row[col_phone]),axis=1)

        # 행 반복
        output_rows = []
        for _, row in filtered_df.iterrows():
          if col_2kg and filter_2kg and row[col_2kg] > 0:
            for _ in range(int(row[col_2kg])):
                output_rows.append({
                    "상품명": "복숭아 2kg",
                    "수취인명": row["수취인명"],
                    "수취인 우편번호": "",
                    "수취인 주소": row[col_address],
                    "수취인 전화번호": row["수취인 전화번호"],
                })
          if col_4kg and filter_4kg and row[col_4kg] > 0:
            for _ in range(int(row[col_4kg])):
                output_rows.append({
                    "상품명": "복숭아 4kg",
                    "수취인명": row["수취인명"],
                    "수취인 우편번호": "",
                    "수취인 주소": row[col_address],
                    "수취인 전화번호": row["수취인 전화번호"],
                })
          if col_1kg and filter_1kg and row[col_1kg] > 0:
            for _ in range(int(row[col_1kg])):
                output_rows.append({
                    "상품명": "복숭아 1.5kg",
                    "수취인명": row["수취인명"],
                    "수취인 우편번호": "",
                    "수취인 주소": row[col_address],
                    "수취인 전화번호": row["수취인 전화번호"],
                })

        order_df = pd.DataFrame(output_rows)

        def to_excel_bytes(df_dict):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                for sheet, df in df_dict.items():
                    df.to_excel(writer, index=False, sheet_name=sheet)
            return output.getvalue()

        st.success(f"📦 총 {len(order_df)}건 추출됨")
        st.download_button(
            label="📥 복숭아 주문 엑셀 다운로드",
            data=to_excel_bytes({"주문서": order_df}),
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

            sheet1 = notes_df[["주문자명", "연락처", "문의내용"]]
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
