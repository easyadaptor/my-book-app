import streamlit as st
import pandas as pd
from datetime import datetime
import easyocr
import numpy as np
from PIL import Image

# 1. 앱 페이지 설정
st.set_page_config(page_title="나의 독서 기록장", page_icon="📚", layout="wide")

# 2. 성능을 위해 OCR 도구 준비 (캐싱)
@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['ko', 'en'], gpu=False)

# 3. 세션 상태 초기화 (앱이 켜진 동안 데이터 유지)
if 'book_info' not in st.session_state:
    st.session_state.book_info = {
        'title': '',
        'author': '',
        'translator': '',
        'publisher': '',
        'year': ''
    }

if 'db' not in st.session_state:
    # 저장될 엑셀의 컬럼 구조 정의
    st.session_state.db = pd.DataFrame(columns=[
        '날짜', '책제목', '저자', '번역가', '출판사', '발행년도', '내용', '메모'
    ])

# --- 사이드바: 입력 설정 ---
with st.sidebar:
    st.title("📚 책 정보 등록")
    
    with st.expander("① 현재 읽는 책 정보 (클릭)", expanded=True):
        # 입력값 변경 시 바로 세션에 저장되도록 설정
        current_title = st.text_input("책 제목", value=st.session_state.book_info['title'])
        current_author = st.text_input("저자 (지은이)", value=st.session_state.book_info['author'])
        current_trans = st.text_input("번역가 (옮긴이)", value=st.session_state.book_info['translator'])
        current_pub = st.text_input("출판사", value=st.session_state.book_info['publisher'])
        current_year = st.text_input("발행년도", value=st.session_state.book_info['year'])
        
        # 입력된 내용을 세션에 업데이트 (입력하자마자 기억함)
        st.session_state.book_info.update({
            'title': current_title,
            'author': current_author,
            'translator': current_trans,
            'publisher': current_pub,
            'year': current_year
        })

    st.divider()
    
    st.header("② 내용 입력")
    uploaded_file = st.file_uploader("책 페이지 찍기", type=['png', 'jpg', 'jpeg'])
    
    st.header("③ 메모 및 저장")
    memo = st.text_input("페이지/메모", placeholder="p.123 핵심 문장")
    save_btn = st.button("💾 이 내용 저장하기", type="primary", use_container_width=True)

# --- 메인 화면 ---
st.title(f"📖 {current_title if current_title else '독서'} 기록장")

# 책 정보가 비어있으면 알림
if not current_title:
    st.info("👈 왼쪽 사이드바에서 [책 정보]를 먼저 입력해주세요.")

# 4. 화면 구성 (2단 레이아웃)
col1, col2 = st.columns([1, 1])

# 왼쪽: 이미지 및 OCR 버튼
with col1:
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='업로드된 사진', use_column_width=True)
        
        if st.button("🔍 텍스트 추출하기 (AI 실행)", use_container_width=True):
            with st.spinner('글자를 읽고 있습니다... (약 10~20초)'):
                try:
                    reader = load_ocr_model()
                    image_np = np.array(image)
                    result = reader.readtext(image_np, detail=0)
                    extracted_text = " ".join(result)
                    st.session_state['temp_ocr_result'] = extracted_text
                except Exception as e:
                    st.error(f"오류 발생: {e}")
    else:
        st.write("사진을 업로드하면 여기에 표시됩니다.")

# 오른쪽: 텍스트 결과 및 수정
with col2:
    current_text = st.session_state.get('temp_ocr_result', "")
    st.subheader("✏️ 내용 확인 및 수정")
    final_text = st.text_area("추출된 내용 (직접 수정 가능)", value=current_text, height=400)

# 5. 저장 로직
if save_btn:
    if not current_title:
        st.error("책 제목이 없습니다! 왼쪽에서 입력해주세요.")
    elif not final_text and not uploaded_file:
        st.warning("저장할 내용이 없습니다.")
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        content_to_save = final_text if final_text else "(사진만 저장됨)"
        
        new_data = pd.DataFrame({
            '날짜': [now],
            '책제목': [current_title],
            '저자': [current_author],
            '번역가': [current_trans],
            '출판사': [current_pub],
            '발행년도': [current_year],
            '내용': [content_to_save],
            '메모': [memo]
        })
        
        st.session_state.db = pd.concat([st.session_state.db, new_data], ignore_index=True)
        st.toast("✅ 저장되었습니다!", icon='🎉')

# 6. 저장된 목록 보여주기 & 다운로드
st.divider()
st.subheader(f"📋 저장된 독서 리스트")

if not st.session_state.db.empty:
    st.dataframe(st.session_state.db, use_container_width=True)

    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8-sig')

    csv = convert_df(st.session_state.db)
    
    st.download_button(
        label="📥 엑셀(CSV)로 전체 다운로드",
        data=csv,
        file_name='나의_독서기록.csv',
        mime='text/csv',
    )
else:
    st.info("아직 저장된 내용이 없습니다.")
