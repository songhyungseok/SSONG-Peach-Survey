import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

# 페이지 설정
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
        # 컬럼 설정
        col_date = "응답일시"
        col_2kg = "신선 2kg (24,000원) (box단위)(*)"
        col_4kg = "신선 4kg (43,000원) (box단위)(*)"
        col_name = "주문자명 (입금자명)(*)"
        col_phone = "주문자 연락처(*)"
        col_receiver = "배송지 성명(주문자와 동일 할 경우 미입력)"
        col_address = "주소(*)"
        col_issue = "추가 문의사항 및 의견"

        # 날짜 + 시간 필터 UI
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

        # 전화번호 처리 함수
        def normalize_phone(phone):
            phone_str = str(phone).strip()
            phone_str = re.sub(r"[^\d]", "", phone_str)  # 숫자만 추출

            if phone_str.startswith("1") and len(phone_str) == 10:
                phone_str = "0" + phone_str  # 1012345678 → 01012345678

            return phone_str

        filtered_df["수취인 전화번호"] = filtered_df[col_phone].apply(normalize_phone)

        # 전체 주문 엑셀 다운로드
        output = pd.DataFrame({
            "상품명": "복숭아",
            "수취인명": filtered_df["수취인명"],
            "수취인 우편번호": "",
            "수취인 주소": filtered_df[col_address],
            "수취인 전화번호": filtered_df["수취인 전화번호"],
        })

        # 문의사항 텍스트 추출 및 요약
        issue_df = filtered_df[filtered_df[col_issue].notnull()]
        issue_summary = ""
        for index, row in issue_df.iterrows():
            issue_summary += f"{index + 1}. 주문자: {row[col_name]} / 연락처: {normalize_phone(row[col_phone])}\n➤ 요청: {row[col_issue]}\n\n"

        # 카카오톡 요약본
        if issue_summary:
            st.text_area("📋 카카오톡 요약본", value=issue_summary.strip(), height=300)

            # 클립보드 복사 버튼
            st.download_button("📋 텍스트 파일로 저장", issue_summary.strip(), file_name="문의사항요약.txt")

        # 엑셀로 다운로드
        def to_excel_bytes(df):
            output_stream = BytesIO()
            with pd.ExcelWriter(output_stream, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False)
            return output_stream.getvalue()

        st.success(f"📦 총 {len(output)}건 추출됨")
        st.download_button(
            label="📥 복숭아 주문 엑셀 다운로드",
            data=to_excel_bytes(output),
            file_name="SSONG-Peach-Filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 문의사항이 있을 경우 문의사항 엑셀 다운로드
        if len(issue_summary) > 0:
            issue_output = pd.DataFrame({
                "상품명": "복숭아",
                "주문자명": issue_df[col_name],
                "전화번호": issue_df[col_phone].apply(normalize_phone),
                "문의사항": issue_df[col_issue],
            })
            st.download_button(
                label="📥 문의사항 엑셀 다운로드",
                data=to_excel_bytes(issue_output),
                file_name="SSONG-Peach-Issues.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"처리 중 오류 발생: {e}")
