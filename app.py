import streamlit as st
import pandas as pd
from datetime import datetime
import easyocr
import numpy as np
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# 1. 앱 설정
st.set_page_config(page_title="나의 독서 기록장 (클라우드)", page_icon="☁️", layout="wide")

# 2. OCR 로딩
@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['ko', 'en'], gpu=False)

# 3. 구글 시트 연결 (이게 핵심!)
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 데이터 불러오기 함수
def load_data():
    try:
        # 구글 시트에서 데이터를 읽어옴 (없으면 에러날 수 있으니 예외처리)
        df = conn.read(worksheet="시트1", usecols=list(range(8)), ttl=5)
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=['날짜', '책제목', '저자', '번역가', '출판사', '발행년도', '내용', '메모'])

# --- 사이드바 ---
with st.sidebar:
    st.title("☁️ 구글 시트 연동됨")
    
    # 데이터 새로고침 버튼
    if st.button("🔄 최신 데이터 불러오기"):
        st.cache_data.clear()
        st.rerun()

    # 현재 DB 상태 불러오기
    current_df = load_data()
    
    st.divider()
    
    # 책 정보 선택 (기존 데이터 기반)
    existing_books = current_df['책제목'].unique().tolist() if not current_df.empty else []
    selected_book = st.selectbox("책 선택 (자동 채우기)", ["(새로 입력)"] + existing_books)
    
    # 책 정보 초기값 설정
    default_info = {'title':'', 'author':'', 'trans':'', 'pub':'', 'year':''}
    
    if selected_book != "(새로 입력)":
        book_record = current_df[current_df['책제목'] == selected_book].iloc[-1]
        default_info['title'] = book_record['책제목']
        default_info['author'] = str(book_record.get('저자', ''))
        default_info['trans'] = str(book_record.get('번역가', ''))
        default_info['pub'] = str(book_record.get('출판사', ''))
        default_info['year'] = str(book_record.get('발행년도', ''))

    # 입력창
    current_title = st.text_input("책 제목", value=default_info['title'])
    current_author = st.text_input("저자", value=default_info['author'])
    current_trans = st.text_input("번역가", value=default_info['trans'])
    current_pub = st.text_input("출판사", value=default_info['pub'])
    current_year = st.text_input("발행년도", value=default_info['year'])

    st.divider()
    uploaded_file = st.file_uploader("책 페이지 찍기", type=['png', 'jpg', 'jpeg'])
    memo = st.text_input("메모", placeholder="p.123")
    save_btn = st.button("💾 구글 시트에 저장", type="primary")

# --- 메인 화면 ---
st.title(f"📖 {current_title if current_title else '독서'} 기록장")

col1, col2 = st.columns([1, 1])

with col1:
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='업로드된 사진', use_column_width=True)
        if st.button("🔍 텍스트 추출 (EasyOCR)"):
            with st.spinner('읽는 중...'):
                try:
                    reader = load_ocr_model()
                    image_np = np.array(image)
                    result = reader.readtext(image_np, detail=0, paragraph=True)
                    st.session_state['temp_text'] = "\n".join(result)
                except Exception as e:
                    st.error(f"오류: {e}")

with col2:
    final_text = st.text_area("내용 확인", value=st.session_state.get('temp_text', ""), height=500)

# 5. 저장 로직 (구글 시트로 전송)
if save_btn:
    if not current_title:
        st.error("책 제목이 없습니다!")
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_row = pd.DataFrame([{
            '날짜': now,
            '책제목': current_title,
            '저자': current_author,
            '번역가': current_trans,
            '출판사': current_pub,
            '발행년도': current_year,
            '내용': final_text if final_text else "(사진만 저장됨)",
            '메모': memo
        }])
        
        # 기존 데이터에 새 행 추가
        updated_df = pd.concat([current_df, new_row], ignore_index=True)
        
        # 구글 시트에 업데이트 (덮어쓰기)
        try:
            conn.update(worksheet="시트1", data=updated_df)
            st.toast("☁️ 구글 시트에 안전하게 저장되었습니다!", icon="✅")
            st.cache_data.clear() # 캐시 비우기 (새로고침 시 반영되게)
        except Exception as e:
            st.error(f"저장 실패: {e}")

st.divider()
st.subheader("📋 구글 시트 데이터 (실시간 연동)")
if not current_df.empty:
    st.dataframe(current_df)
