import streamlit as st import pandas as pd import numpy as np from io import BytesIO

st.set_page_config(page_title="복숭아 주문 필터", layout="centered") st.title("🍑 복숭아 주문서 필터링 도구")

password = st.text_input("비밀번호를 입력하세요", type="password") if password != "gudtjr0428": st.stop()

uploaded_file = st.file_uploader("📤 네이버폼 엑셀(.xlsx) 업로드", type="xlsx")

if uploaded_file: df = pd.read_excel(uploaded_file)

try:
    # 컬럼 자동 탐색
    col_date = [c for c in df.columns if "응답일시" in c][0]
    col_name = [c for c in df.columns if "주문자명" in c][0]
    col_phone = [c for c in df.columns if "연락처" in c][0]
    col_receiver = [c for c in df.columns if "배송지 성명" in c][0]
    col_address = [c for c in df.columns if "주소" in c][0]
    col_2kg = [c for c in df.columns if "2kg" in c][0]
    col_4kg = [c for c in df.columns if "4kg" in c][0]

    # 날짜 필터
    df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
    min_date = df[col_date].min()
    max_date = df[col_date].max()

    start_date = st.date_input("시작 날짜", value=min_date.date())
    start_time = st.time_input("시작 시간", value=min_date.time())
    end_date = st.date_input("종료 날짜", value=max_date.date())
    end_time = st.time_input("종료 시간", value=max_date.time())

    start_dt = pd.to_datetime(f"{start_date} {start_time}")
    end_dt = pd.to_datetime(f"{end_date} {end_time}")

    # 필터 체크박스
    filter_2kg = st.checkbox("✅ 2kg 수량 1개 이상", value=True)
    filter_4kg = st.checkbox("✅ 4kg 수량 1개 이상", value=True)

    # 수량 정제
    df[col_2kg] = pd.to_numeric(df[col_2kg].astype(str).str.strip(), errors="coerce").fillna(0).astype(int)
    df[col_4kg] = pd.to_numeric(df[col_4kg].astype(str).str.strip(), errors="coerce").fillna(0).astype(int)

    # 날짜 필터
    filtered_df = df[(df[col_date] >= start_dt) & (df[col_date] <= end_dt)]

    # 수량 조건 반영하여 행 확장
    expanded_rows = []
    for _, row in filtered_df.iterrows():
        if filter_2kg:
            for _ in range(int(row[col_2kg])):
                expanded_rows.append(row)
        if filter_4kg:
            for _ in range(int(row[col_4kg])):
                expanded_rows.append(row)
    filtered_df = pd.DataFrame(expanded_rows)

    # 수취인 정보 보완
    filtered_df["수취인명"] = filtered_df[col_receiver].fillna("").replace("", np.nan)
    filtered_df["수취인명"] = filtered_df["수취인명"].fillna(filtered_df[col_name])

    def normalize_phone(phone):
        phone_str = str(phone).strip().replace(".0", "")
        if phone_str.startswith("1") and not phone_str.startswith("01"):
            return "0" + phone_str
        return phone_str

    filtered_df["수취인 전화번호"] = filtered_df[col_phone].apply(normalize_phone)

    output = pd.DataFrame({
        "상품명": "복숭아",
        "수취인명": filtered_df["수취인명"],
        "수취인 우편번호": "",
        "수취인 주소": filtered_df[col_address],
        "수취인 전화번호": filtered_df["수취인 전화번호"]
    })

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

    # 문의사항 처리
    if "문의사항" in df.columns:
        문의사항_포함 = df[df["문의사항"].astype(str).str.strip() != ""]
        흠과_포함 = 문의사항_포함[문의사항_포함["문의사항"].str.contains("흠과", na=False)]

        문의사항_output1 = 문의사항_포함[[col_name, col_phone, "문의사항"]]
        문의사항_output2 = 흠과_포함[[col_name, col_phone, "문의사항"]]

        def 문의사항_to_excel_bytes(df1, df2):
            output_stream = BytesIO()
            with pd.ExcelWriter(output_stream, engine="xlsxwriter") as writer:
                df1.to_excel(writer, index=False, sheet_name="문의사항 전체")
                df2.to_excel(writer, index=False, sheet_name="흠과만 추출")
            return output_stream.getvalue()

        if not 문의사항_output1.empty:
            st.download_button(
                label="📥 문의사항 엑셀 다운로드",
                data=문의사항_to_excel_bytes(문의사항_output1, 문의사항_output2),
                file_name="SSONG-Peach-Inquiry.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 카카오톡 요약
            문의_리스트 = []
            for idx, row in 문의사항_output1.iterrows():
                name = str(row[col_name])
                phone = normalize_phone(row[col_phone])
                note = str(row["문의사항"]).strip()
                문의_리스트.append(f"{len(문의_리스트)+1}. 주문자: {name} / 연락처: {phone}\n   ➤ 요청: {note}")

            요약_텍스트 = "[문의사항 요약]\n\n" + "\n\n".join(문의_리스트) + f"\n\n총 {len(문의_리스트)}건"
            st.text_area("📋 카카오톡용 문의사항 요약", 요약_텍스트, height=300)
            st.download_button(
                label="📥 요약 텍스트 다운로드",
                data=요약_텍스트,
                file_name="문의사항_요약.txt",
                mime="text/plain"
            )
        else:
            st.info("문의사항이 입력된 응답이 없습니다.")

except Exception as e:
    st.error(f"처리 중 오류 발생: {e}")

