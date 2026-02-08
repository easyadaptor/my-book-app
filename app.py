import streamlit as st
import pandas as pd
from datetime import datetime
import easyocr
import numpy as np
from PIL import Image

# 1. 앱 설정 (페이지 제목 등)
st.set_page_config(page_title="📚 나만의 독서 기록장", layout="wide")

# 2. 성능을 위해 OCR 도구 미리 로딩 (캐싱)
@st.cache_resource
def load_ocr_model():
    # 무료 서버용 경량화 설정
    return easyocr.Reader(['ko', 'en'], gpu=False)

# 3. 사이드바: 책 정보 및 입력 설정
with st.sidebar:
    st.title("⚙️ 입력 설정")
    
    # [핵심 기능] 책 제목 기억하기 로직
    # 만약 'book_name'이라는 저장소가 없으면 빈칸으로 시작
    if 'book_name' not in st.session_state:
        st.session_state.book_name = ""

    # 텍스트 입력창 (여기에 입력하면 자동으로 기억됨)
    book_title = st.text_input(
        "📖 현재 읽고 있는 책 제목", 
        value=st.session_state.book_name,
        placeholder="예: 이어령의 마지막 수업"
    )

    # 입력값이 바뀌면 저장소에 업데이트
    if book_title:
        st.session_state.book_name = book_title
        st.success(f"현재 '{book_title}' 기록 중...")
    else:
        st.warning("먼저 책 제목을 입력해주세요!")

    st.divider() # 구분선

    st.header("📸 사진 입력")
    uploaded_file = st.file_uploader("책 페이지 찍기", type=['png', 'jpg', 'jpeg'])
    
    st.header("📝 메모 및 저장")
    memo = st.text_input("페이지/메모", placeholder="p.123 핵심 문장")
    save_btn = st.button("💾 내용 저장하기", type="primary")

# 4. 메인 화면 구성
st.title(f"📚 {book_title if book_title else '독서'} 기록장")

if not book_title:
    st.info("👈 왼쪽 사이드바에서 '책 제목'을 먼저 입력해주세요.")

# 5. OCR 및 텍스트 처리 로직
final_text = ""  # 저장할 최종 텍스트

if uploaded_file is not None:
    # 2단 컬럼 나누기 (왼쪽: 이미지, 오른쪽: 텍스트)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        image = Image.open(uploaded_file)
        st.image(image, caption='업로드된 사진', use_column_width=True)
        
        # OCR 실행 버튼
        if st.button("🔍 텍스트 추출하기 (AI 실행)"):
            with st.spinner('글자를 읽고 있습니다... (약 10초)'):
                try:
                    reader = load_ocr_model()
                    image_np = np.array(image)
                    result = reader.readtext(image_np, detail=0)
                    extracted_text = " ".join(result)
                    # 추출된 텍스트를 세션에 저장
                    st.session_state['temp_ocr_result'] = extracted_text
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    with col2:
        # 추출된 텍스트 가져오기 (없으면 빈칸)
        current_text = st.session_state.get('temp_ocr_result', "")
        st.subheader("✏️ 내용 확인 및 수정")
        final_text = st.text_area("추출된 내용 (직접 수정 가능)", value=current_text, height=300)

# 6. 저장 시스템
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['날짜', '책제목', '내용', '메모'])

if save_btn:
    if not book_title:
        st.error("책 제목이 없습니다! 왼쪽에서 입력해주세요.")
    elif not final_text and not uploaded_file: # 사진이나 텍스트 둘 다 없으면
        st.warning("저장할 내용이 없습니다.")
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        content_to_save = final_text if final_text else "(사진만 저장됨)"
        
        new_data = pd.DataFrame({
            '날짜': [now], 
            '책제목': [book_title], # 책 제목도 같이 저장
            '내용': [content_to_save], 
            '메모': [memo]
        })
        
        st.session_state.db = pd.concat([st.session_state.db, new_data], ignore_index=True)
        st.toast("✅ 저장되었습니다!", icon='🎉') # 예쁜 알림창

# 7. 저장된 목록 보여주기 & 다운로드
st.divider()
st.subheader(f"📋 '{book_title}' 독서 리스트")

# 현재 책 제목과 일치하는 내용만 필터링해서 보여주기 (옵션)
if not st.session_state.db.empty:
    # 전체 보기 옵션
    view_all = st.checkbox("모든 책 기록 보기", value=False)
    
    if view_all:
        display_df = st.session_state.db
    else:
        # 지금 입력한 책 제목만 골라내기
        display_df = st.session_state.db[st.session_state.db['책제목'] == book_title]
    
    st.dataframe(display_df, use_container_width=True)

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
