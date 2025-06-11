import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="복숭아 주문 필터", layout="centered")
st.title("🍑 복숭아 주문 필터링 및 문의사항 추출 도구")

# 비밀번호 보호
password = st.text_input("비밀번호를 입력하세요", type="password")
if password != "gudtjr0428":
    st.stop()

# 파일 업로드
uploaded_file = st.file_uploader("📤 네이버폼 엑셀(.xlsx) 업로드", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # 관련 컬럼 검색
    col_date = "응답일시"
    col_2kg = next((col for col in df.columns if "2kg" in col), None)
    col_4kg = next((col for col in df.columns if "4kg" in col), None)
    col_name = next((col for col in df.columns if "주문자명" in col), None)
    col_phone = next((col for col in df.columns if "연락처" in col), None)
    col_receiver = next((col for col in df.columns if "배송지 성명" in col), None)
    col_address = next((col for col in df.columns if "주소" in col), None)
    col_memo = next((col for col in df.columns if "문의" in col), None)

    try:
        # 날짜 필터 UI
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
        filter_2kg = st.checkbox("✅ 2kg 주문 포함", value=False)
        filter_4kg = st.checkbox("✅ 4kg 주문 포함", value=False)

        df[col_2kg] = pd.to_numeric(df[col_2kg], errors='coerce').fillna(0).astype(int)
        df[col_4kg] = pd.to_numeric(df[col_4kg], errors='coerce').fillna(0).astype(int)

        # 필터 적용
        filtered_df = df[(df[col_date] >= start_dt) & (df[col_date] <= end_dt)]

        # 수량별 행 복제
        exploded_rows = []
        for _, row in filtered_df.iterrows():
            if filter_2kg and row[col_2kg] > 0:
                for _ in range(row[col_2kg]):
                    exploded_rows.append(("복숭아 2kg", row))
            if filter_4kg and row[col_4kg] > 0:
                for _ in range(row[col_4kg]):
                    exploded_rows.append(("복숭아 4kg", row))

        result_df = pd.DataFrame([{
            "상품명": kind,
            "수취인명": row[col_receiver] if pd.notna(row[col_receiver]) and row[col_receiver].strip() else row[col_name],
            "수취인 우편번호": "",
            "수취인 주소": row[col_address],
            "수취인 전화번호": str(row[col_phone]).replace(".0", "").strip(),
        } for kind, row in exploded_rows])

        # 결과 다운로드 버튼
        def to_excel_bytes(multi_df_dict):
            output_stream = BytesIO()
            with pd.ExcelWriter(output_stream, engine="xlsxwriter") as writer:
                for sheet_name, sheet_df in multi_df_dict.items():
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
            return output_stream.getvalue()

        # 📥 주문 추출
        if len(result_df) > 0:
            st.success(f"📦 총 {len(result_df)}건 주문 추출됨")
            st.download_button(
                label="📥 주문 엑셀 다운로드",
                data=to_excel_bytes({"주문리스트": result_df}),
                file_name="SSONG-Peach-Orders.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("✅ 주문 필터 조건에 맞는 데이터가 없습니다.")

        # 📥 문의사항 추출
        st.markdown("---")
        st.subheader("📮 문의사항 추출")

        if st.button("📤 문의사항 추출하기"):
            df_memo = df[df[col_memo].notna() & (df[col_memo].astype(str).str.strip() != "")]

            if len(df_memo) == 0:
                st.info("문의사항이 존재하지 않습니다.")
            else:
                sheet_all = df_memo[[col_name, col_phone, col_memo]].copy()
                sheet_all.columns = ["주문자명", "연락처", "문의내용"]

                sheet_hmg = sheet_all[sheet_all["문의내용"].str.contains("흠과", case=False, na=False)]

                excel_data = to_excel_bytes({
                    "문의전체": sheet_all,
                    "흠과문의": sheet_hmg
                })

                st.download_button(
                    label="📥 문의사항 엑셀 다운로드",
                    data=excel_data,
                    file_name="SSONG-Peach-Inquiries.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # 카카오톡 메시지 요약 생성
                summary = "\n".join([
                    f"{row['주문자명']} ({str(row['연락처']).replace('.0','').strip()}): {row['문의내용']}"
                    for _, row in sheet_all.iterrows()
                ])

                st.markdown("#### 📩 카카오톡 전달용 요약:")
                st.text_area("카톡용 복사 텍스트", summary, height=200)

    except Exception as e:
        st.error(f"🚨 오류 발생: {e}")
