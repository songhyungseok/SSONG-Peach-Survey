import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="복숭아 주문 필터", layout="centered")
st.title("🍑 복숭아 주문서 필터링 도구")

# 비밀번호
password = st.text_input("비밀번호를 입력하세요", type="password")
if password != "gudtjr0428":
    st.stop()

# 엑셀 업로드
uploaded_file = st.file_uploader("📤 네이버폼 엑셀(.xlsx) 업로드", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    try:
        # 컬럼 추출
        col_date = "응답일시"
        col_name = "주문자명 (입금자명)(*)"
        col_phone = "주문자 연락처(*)"
        col_receiver = "배송지 성명(주문자와 동일 할 경우 미입력)"
        col_address = "주소(*)"
        col_memo = "💡추가 문의사항 및 의견"

        # 동적 수량 컬럼 찾기
        col_2kg = [col for col in df.columns if "2kg" in col][0]
        col_4kg = [col for col in df.columns if "4kg" in col][0]

        # 날짜 필터 UI
        df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
        min_date, max_date = df[col_date].min(), df[col_date].max()
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
        df[col_2kg] = pd.to_numeric(df[col_2kg], errors="coerce").fillna(0).astype(int)
        df[col_4kg] = pd.to_numeric(df[col_4kg], errors="coerce").fillna(0).astype(int)

        # 날짜 필터 적용
        filtered_df = df[(df[col_date] >= start_dt) & (df[col_date] <= end_dt)]

        # 수량 기준 필터
        if not (filter_2kg or filter_4kg):
            filtered_df = filtered_df[filtered_df[col_2kg] == -1]  # 빈 결과 처리
        else:
            filtered_df = filtered_df[
                ((filtered_df[col_2kg] >= 1) if filter_2kg else False) |
                ((filtered_df[col_4kg] >= 1) if filter_4kg else False)
            ]

        # 수량만큼 행 복제
        rows = []
        for _, row in filtered_df.iterrows():
            if filter_2kg:
                rows += [row] * row[col_2kg]
            if filter_4kg:
                rows += [row] * row[col_4kg]
        filtered_df_expanded = pd.DataFrame(rows)

        # 수취인명 처리
        filtered_df_expanded["수취인명"] = (
            filtered_df_expanded[col_receiver]
            .fillna("").replace("", np.nan)
            .fillna(filtered_df_expanded[col_name])
        )

        # 전화번호 포맷
        def normalize_phone(phone):
            phone_str = str(phone).strip()
            if phone_str.endswith(".0"):
                phone_str = phone_str[:-2]
            if phone_str.startswith("1") and not phone_str.startswith("01"):
                return "0" + phone_str
            return phone_str
        filtered_df_expanded["수취인 전화번호"] = filtered_df_expanded[col_phone].apply(normalize_phone)

        # 출력 데이터
        output = pd.DataFrame({
            "상품명": "복숭아",
            "수취인명": filtered_df_expanded["수취인명"],
            "수취인 우편번호": "",
            "수취인 주소": filtered_df_expanded[col_address],
            "수취인 전화번호": filtered_df_expanded["수취인 전화번호"],
        })

        # 엑셀 저장 함수
        def to_excel_bytes(df):
            output_stream = BytesIO()
            with pd.ExcelWriter(output_stream, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="복숭아 주문")
            return output_stream.getvalue()

        st.success(f"📦 총 {len(output)}건 추출됨")
        st.download_button(
            label="📥 복숭아 주문 엑셀 다운로드",
            data=to_excel_bytes(output),
            file_name="SSONG-Peach-Filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # ------------------------ #
        # 문의사항 추출 기능 시작
        # ------------------------ #
        st.markdown("---")
        st.header("📮 문의사항 추출")

        if st.button("📤 문의사항 엑셀 추출"):
            df_memo = df[df[col_memo].notna() & (df[col_memo].astype(str).str.strip() != "")]
            df_memo["흠과 포함"] = df_memo[col_memo].str.contains("흠과", case=False, na=False)

            output_stream = BytesIO()
            with pd.ExcelWriter(output_stream, engine="xlsxwriter") as writer:
                df_memo.to_excel(writer, index=False, sheet_name="문의사항 전체")
                df_memo[df_memo["흠과 포함"]].to_excel(writer, index=False, sheet_name="흠과 포함")

            st.download_button(
                label="📥 문의사항 엑셀 다운로드",
                data=output_stream.getvalue(),
                file_name="SSONG-Memo-Filtered.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # 카카오톡 요약 생성
        df_memo = df[df[col_memo].notna() & (df[col_memo].astype(str).str.strip() != "")]
        if not df_memo.empty:
            st.subheader("💬 카카오톡 요약")
            kakao_summary = ""
            for idx, row in df_memo.iterrows():
                name = row[col_name]
                phone = normalize_phone(row[col_phone])
                memo = row[col_memo]
                kakao_summary += f"{idx+1}. 주문자: {name} / 연락처: {phone}\n   ➤ 요청: {memo}\n\n"
            st.text_area("문의사항 요약", value=kakao_summary.strip(), height=200)
            st.download_button("📋 텍스트 파일로 저장", data=kakao_summary.strip(), file_name="문의사항요약.txt")
