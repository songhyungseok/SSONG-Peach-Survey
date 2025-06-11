import streamlit as st
import pandas as pd
import io

# 비밀번호 설정
PASSWORD = "gudtjr0428"

def check_password():
    st.title("🍑 복숭아 주문 추출 도구")
    password = st.text_input("비밀번호를 입력하세요", type="password")
    if password == PASSWORD:
        return True
    else:
        st.stop()

def main():
    if not check_password():
        return

    st.subheader("1. 네이버 폼 엑셀 파일 업로드")
    uploaded_file = st.file_uploader("응답 파일 (.xlsx)", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        st.success("파일 업로드 완료 ✅")
        st.dataframe(df.head())

        st.subheader("2. 추출할 열 자동 선택 및 저장")

        # 선택할 열 이름 (리스트 형태로 고정)
        selected_columns = [
            "참여자",
            "개인정보 수집 동의(*)",
            "신선 2kg (24,000원) (box단위)(*)",
            "신선 4kg (43,000원) (box단위)(*)",
            "주문자명 (입금자명)(*)",
            "주문자 연락처(*)",
            "배송지 성명(주문자와 동일 할 경우 미입력)",
            "배송지 전화번호 (주문자와 동일 할 경우 미입력)",
            "주소(*)",
            "💡추가 문의사항 및 의견"
        ]

        # 실제 존재하는 열만 필터링
        valid_columns = [col for col in selected_columns if col in df.columns]
        extracted_df = df[valid_columns]

        # 다운로드
        st.write("👇 추출된 데이터 미리보기")
        st.dataframe(extracted_df)

        towrite = io.BytesIO()
        extracted_df.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        st.download_button(
            label="📥 추출된 데이터 다운로드 (.xlsx)",
            data=towrite,
            file_name="추출결과.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
