import streamlit as st
import pandas as pd
from datetime import datetime

# 제목과 설명
st.title("📚 나의 책 스캐너")
st.write("핸드폰으로 찍고, 내용을 정리하세요.")

# 1. 사이드바 (설정 메뉴 같은 곳)
with st.sidebar:
    st.header("입력 설정")
    # 파일 업로드 (카메라 촬영 가능)
    uploaded_file = st.file_uploader("책 사진 찍기", type=['png', 'jpg', 'jpeg'])
    
    # 텍스트 직접 입력 (OCR 대신 직접 칠 수도 있음)
    manual_text = st.text_area("직접 내용 입력하기", height=150)
    
    # 메모 입력
    memo = st.text_input("메모 (페이지 등)", placeholder="p.123 중요 내용")
    
    save_btn = st.button("저장하기")

# 2. 메인 화면 (결과 보여주는 곳)
if uploaded_file is not None:
    st.image(uploaded_file, caption='찍은 사진', use_column_width=True)
    st.info("사진이 업로드되었습니다! (현재 버전은 텍스트 직접 입력을 권장합니다)")

# 3. 저장 로직 (임시 저장)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['날짜', '내용', '메모'])

if save_btn:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 내용이 비어있으면 사진 파일명이라도 넣기
    content = manual_text if manual_text else "사진 저장됨"
    
    new_data = pd.DataFrame({'날짜': [now], '내용': [content], '메모': [memo]})
    st.session_state.db = pd.concat([st.session_state.db, new_data], ignore_index=True)
    st.success("저장 완료!")

# 4. 저장된 목록 보여주기
st.divider()
st.subheader("📋 저장된 참고문헌 목록")
st.dataframe(st.session_state.db)

# 5. 다운로드 버튼
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

csv = convert_df(st.session_state.db)

st.download_button(
    label="엑셀(CSV)로 다운로드 받기",
    data=csv,
    file_name='참고문헌_정리.csv',
    mime='text/csv',
)
