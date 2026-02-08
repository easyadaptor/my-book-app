import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract

# 1. 앱 설정
st.set_page_config(page_title="나의 독서 기록장", page_icon="📚", layout="wide")

# 2. 가벼운 OCR 도구 설정 (Tesseract)
# 무료 서버에서는 별도 설치 없이 이 라이브러리가 내장된 경우가 많아 가장 안전합니다.

# 3. 데이터 저장소 초기화
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        '날짜', '책제목', '저자', '번역가', '출판사', '발행년도', '내용', '메모'
    ])
    
# 책 정보 기억하기
if 'book_info' not in st.session_state:
    st.session_state.book_info = {
        'title': '', 'author': '', 'trans': '', 'pub': '', 'year': ''
    }

# --- 사이드바: 책 정보 입력 ---
with st.sidebar:
    st.title("📚 책 정보 등록")
    st.info("💡 팁: 한 번 입력하면 계속 유지됩니다.")
    
    # 입력값을 세션에 바로 저장하는 방식
    def update_info():
        st.session_state.book_info['title'] = st.session_state.title_input
        st.session_state.book_info['author'] = st.session_state.author_input
        st.session_state.book_info['trans'] = st.session_state.trans_input
        st.session_state.book_info['pub'] = st.session_state.pub_input
        st.session_state.book_info['year'] = st.session_state.year_input

    current_title = st.text_input("책 제목", key='title_input', value=st.session_state.book_info['title'], on_change=update_info)
    current_author = st.text_input("저자", key='author_input', value=st.session_state.book_info['author'], on_change=update_info)
    current_trans = st.text_input("번역가", key='trans_input', value=st.session_state.book_info['trans'], on_change=update_info)
    current_pub = st.text_input("출판사", key='pub_input', value=st.session_state.book_info['pub'], on_change=update_info)
    current_year = st.text_input("발행년도", key='year_input', value=st.session_state.book_info['year'], on_change=update_info)

    st.divider()
    uploaded_file = st.file_uploader("책 페이지 찍기", type=['png', 'jpg', 'jpeg'])
    memo = st.text_input("메모", placeholder="p.123")
    save_btn = st.button("💾 저장하기", type="primary", use_container_width=True)

# --- 메인 화면 ---
st.title(f"📖 {current_title if current_title else '독서'} 기록장")

col1, col2 = st.columns([1, 1])

with col1:
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='업로드된 사진', use_column_width=True)
        
        # 가벼운 OCR 실행 버튼
        if st.button("🔍 텍스트 추출 (Light)", use_container_width=True):
            with st.spinner('읽는 중...'):
                try:
                    # Tesseract로 텍스트 추출
                    text = pytesseract.image_to_string(image, lang='kor+eng') # 한글+영어
                    st.session_state['temp_text'] = text
                except Exception as e:
                    # Tesseract가 서버에 없을 경우를 대비한 안내
                    st.warning("서버 설정 문제로 텍스트 인식이 안 될 수 있습니다. (packages.txt 필요)")
                    st.error(f"에러 내용: {e}")
                    st.session_state['temp_text'] = ""
    else:
        st.info("왼쪽에서 사진을 올려주세요.")

with col2:
    final_text = st.text_area("내용 확인/수정", value=st.session_state.get('temp_text', ""), height=400)

# 저장 로직
if save_btn:
    if not current_title:
        st.error("책 제목을 입력해주세요!")
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_data = pd.DataFrame({
            '날짜': [now],
            '책제목': [current_title],
            '저자': [current_author],
            '번역가': [current_trans],
            '출판사': [current_pub],
            '발행년도': [current_year],
            '내용': [final_text if final_text else "(사진만 저장됨)"],
            '메모': [memo]
        })
        st.session_state.db = pd.concat([st.session_state.db, new_data], ignore_index=True)
        st.success("저장되었습니다!")

st.divider()
if not st.session_state.db.empty:
    st.dataframe(st.session_state.db)
    csv = st.session_state.db.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 엑셀 다운로드", csv, "독서기록.csv", "text/csv")
