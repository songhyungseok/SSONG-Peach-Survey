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
        # 열명 유추
        col_name = [col for col in df.columns if "입금자" in col or "주문자명" in col][0]
        col_phone = [col for col in df.columns if "연락처" in col][0]
        col_receiver = [col for col in df.columns if "배송지 성명" in col][0]
        col_address = [col for col in df.columns if "주소" in col][0]
        col_memo = [col for col in df.columns if "의견" in col or "문의" in col][0]
        col_date = [col for col in df.columns if "응답일시" in col][0]

        # 수량 항목 자동 매핑
        col_2kg = [col for col in df.columns if "2kg" in col][0]
        col_4kg = [col for col in df.columns if "4kg" in col][0]

        # 날짜 필터
        df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
        min_date, max_date = df[col_date].min(), df[col_date].max()
        start_date = st.date_input("시작 날짜", min_value=min_date.date(), value=min_date.date())
        start_time = st.time_input("시작 시간", value=min_date.time())
        end_date = st.date_input("종료 날짜", max_value=max_date.date(), value=max_date.date())
        end_time = st.time_input("종료 시간", value=max_date.time())
        start_dt = pd.to_datetime(f"{start_date} {start_time}")
        end_dt = pd.to_datetime(f"{end_date} {end_time}")

        # 수량 숫자화
        df[col_2kg] = pd.to_numeric(df[col_2kg].astype(str).str.strip(), errors="coerce").fillna(0)
        df[col_4kg] = pd.to_numeric(df[col_4kg].astype(str).str.strip(), errors="coerce").fillna(0)

        # 필터 옵션
        filter_2kg = st.checkbox("✅ 2kg 수량 1개 이상", value=True)
        filter_4kg = st.checkbox("✅ 4kg 수량 1개 이상", value=True)

        # 기본 필터링
        filtered_df = df[(df[col_date] >= start_dt) & (df[col_date] <= end_dt)]

        # 수량 필터 적용
        result_rows = []
        for _, row in filtered_df.iterrows():
            count_2kg = int(row[col_2kg])
            count_4kg = int(row[col_4kg])

            if filter_2kg and count_2kg > 0:
                for _ in range(count_2kg):
                    result_rows.append({
                        "상품명": "복숭아",
                        "수취인명": row[col_receiver] if pd.notna(row[col_receiver]) and str(row[col_receiver]).strip() != "" else row[col_name],
                        "수취인 우편번호": "",
                        "수취인 주소": row[col_address],
                        "수취인 전화번호": str(row[col_phone]).strip().replace(".0", "")
                    })

            if filter_4kg and count_4kg > 0:
                for _ in range(count_4kg):
                    result_rows.append({
                        "상품명": "복숭아",
                        "수취인명": row[col_receiver] if pd.notna(row[col_receiver]) and str(row[col_receiver]).strip() != "" else row[col_name],
                        "수취인 우편번호": "",
                        "수취인 주소": row[col_address],
                        "수취인 전화번호": str(row[col_phone]).strip().replace(".0", "")
                    })

        if result_rows:
            output_df = pd.DataFrame(result_rows)
            st.success(f"📦 총 {len(output_df)}건 추출됨")
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                output_df.to_excel(writer, index=False, sheet_name="주문추출")
            st.download_button("📥 복숭아 주문 엑셀 다운로드", data=buffer.getvalue(), file_name="SSONG-Peach-Filtered.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("조건에 맞는 주문이 없습니다.")

        # --- 📌 문의사항 요약 및 내보내기 ---
        st.subheader("💬 문의사항 요약 추출")

        memo_df = df[df[col_memo].notna() & (df[col_memo].astype(str).str.strip() != "")]
        if not memo_df.empty:
            # 카카오톡 요약
            kakao_summary = ""
            for i, row in memo_df.iterrows():
                name = row[col_name]
                phone = str(row[col_phone]).strip().replace(".0", "")
                memo = str(row[col_memo]).strip()
                kakao_summary += f"{len(kakao_summary.splitlines())//3+1}. 주문자: {name} / 연락처: {phone}\n   ➤ 요청: {memo}\n\n"

            st.text_area("카카오톡 요약", value=kakao_summary.strip(), height=250)
            st.download_button("📋 텍스트 파일로 저장", data=kakao_summary.strip(), file_name="문의사항요약.txt")

            # 시트로 저장
            buffer2 = BytesIO()
            with pd.ExcelWriter(buffer2, engine="xlsxwriter") as writer:
                memo_df.to_excel(writer, index=False, sheet_name="문의사항전체")
                memo_df[memo_df[col_memo].str.contains("흠과", na=False)].to_excel(writer, index=False, sheet_name="문의사항-흠과")
            st.download_button("📥 문의사항 엑셀 다운로드", data=buffer2.getvalue(), file_name="문의사항추출.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("문의사항이 없습니다.")

    except Exception as e:
        st.error(f"❌ 오류 발생: {e}")
