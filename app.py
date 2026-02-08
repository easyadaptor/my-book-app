import streamlit as st
import pandas as pd
from datetime import datetime
import easyocr
import numpy as np
from PIL import Image

# 1. 앱 설정
st.set_page_config(page_title="나의 독서 기록장", page_icon="📚", layout="wide")

# 2. [핵심] 인식률 높이는 설정 (EasyOCR)
# @st.cache_resource는 AI 모델을 한 번만 불러와서 서버가 안 뻗게 잡아주는 역할입니다.
@st.cache_resource
def load_model():
    # gpu=False : 무료 서버용 설정 (중요!)
    # quantize=False : 인식률을 위해 정밀도 유지
    return easyocr.Reader(['ko', 'en'], gpu=False, verbose=False)

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
    
    # 입력값을 세션에 바로 저장하는 로직
    current_title = st.text_input("책 제목", value=st.session_state.book_info['title'])
    current_author = st.text_input("저자", value=st.session_state.book_info['author'])
    current_trans = st.text_input("번역가", value=st.session_state.book_info['trans'])
    current_pub = st.text_input("출판사", value=st.session_state.book_info['pub'])
    current_year = st.text_input("발행년도", value=st.session_state.book_info['year'])
    
    # 입력 즉시 저장
    st.session_state.book_info.update({
        'title': current_title, 'author': current_author, 
        'trans': current_trans, 'pub': current_pub, 'year': current_year
    })

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
        
        # EasyOCR 실행 버튼
        if st.button("🔍 텍스트 추출 (고성능)", use_container_width=True):
            with st.spinner('AI가 글자를 읽고 있습니다... (약 10~20초 소요)'):
                try:
                    # 모델 불러오기
                    reader = load_model()
                    
                    # 이미지를 AI가 읽을 수 있는 숫자로 변환
                    image_np = np.array(image)
                    
                    # [꿀팁] 문단 단위로 묶어서 읽기 (detail=0)
                    result = reader.readtext(image_np, detail=0, paragraph=True)
                    
                    # 결과 합치기
                    extracted_text = "\n".join(result)
                    st.session_state['temp_text'] = extracted_text
                    
                except Exception as e:
                    st.error(f"오류 발생: {e}")
                    st.session_state['temp_text'] = ""
    else:
        st.info("왼쪽에서 사진을 올려주세요.")

with col2:
    final_text = st.text_area("내용 확인/수정", value=st.session_state.get('temp_text', ""), height=600)

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
        st.toast("✅ 저장되었습니다!")

st.divider()
if not st.session_state.db.empty:
    st.dataframe(st.session_state.db)
    csv = st.session_state.db.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 엑셀 다운로드", csv, "독서기록.csv", "text/csv")
