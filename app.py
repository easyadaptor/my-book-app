import streamlit as st
import pandas as pd
from datetime import datetime
import easyocr
import numpy as np
from PIL import Image

# 1. 앱 제목 설정
st.title("📚 AI 책 스캐너 (무료버전)")
st.write("사진을 올리고 [텍스트 추출] 버튼을 눌러보세요!")

# 2. 성능을 위해 OCR 도구를 미리 준비시키는 함수 (캐싱)
@st.cache_resource
def load_ocr_model():
    # 한국어(ko)와 영어(en)를 읽을 수 있게 설정
    # gpu=False는 무료 서버에서 에러가 안 나게 하는 핵심 설정입니다.
    return easyocr.Reader(['ko', 'en'], gpu=False)

# 3. 사이드바 (왼쪽 설정창)
with st.sidebar:
    st.header("1. 사진 입력")
    # 카메라로 찍거나 파일 올리기
    uploaded_file = st.file_uploader("책 페이지 찍기", type=['png', 'jpg', 'jpeg'])
    
    st.header("2. 내용 저장")
    # 메모 입력창
    memo = st.text_input("메모 (페이지 등)", placeholder="예: p.45 중요")
    # 저장 버튼
    save_btn = st.button("내용 저장하기")

# 4. 메인 기능 (사진이 올라오면 작동)
if uploaded_file is not None:
    # 이미지 보여주기
    image = Image.open(uploaded_file)
    st.image(image, caption='선택한 이미지', use_column_width=True)
    
    # 텍스트 추출 버튼 만들기
    if st.button("🔍 텍스트 추출하기 (클릭!)"):
        with st.spinner('AI가 글자를 읽고 있습니다... (10~20초 소요)'):
            try:
                # OCR 도구 불러오기
                reader = load_ocr_model()
                # 이미지를 숫자로 변환 (AI가 읽을 수 있게)
                image_np = np.array(image)
                # 글자 읽기 실행!
                result = reader.readtext(image_np, detail=0)
                # 읽은 글자들을 문장으로 합치기
                extracted_text = " ".join(result)
                
                # 성공 메시지와 결과 보여주기
                st.success("글자를 읽어왔습니다!")
                # 세션에 임시 저장 (화면이 깜빡여도 내용 유지)
                st.session_state['temp_text'] = extracted_text
                
            except Exception as e:
                st.error(f"오류가 났어요: {e}")

# 5. 결과 확인 및 수정 영역
# 세션에 저장된 텍스트가 있으면 가져오기
final_text_value = st.session_state.get('temp_text', "")

st.subheader("결과 확인 및 수정")
# 텍스트 상자에 넣어서 수정 가능하게 함
edited_text = st.text_area("여기서 내용을 다듬으세요", value=final_text_value, height=200)

# 6. 저장 시스템 (데이터베이스 역할)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['날짜', '내용', '메모'])

if save_btn:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if not edited_text:
        st.warning("저장할 내용이 없어요! 사진을 찍고 텍스트를 추출해주세요.")
    else:
        # 데이터 한 줄 만들기
        new_data = pd.DataFrame({
            '날짜': [now], 
            '내용': [edited_text], 
            '메모': [memo]
        })
        # 기존 데이터에 합치기
        st.session_state.db = pd.concat([st.session_state.db, new_data], ignore_index=True)
        st.success("리스트에 저장되었습니다! 아래 목록을 확인하세요.")

# 7. 저장된 목록 보여주기 & 엑셀 다운로드
st.divider()
st.subheader("📋 저장된 참고문헌 목록")
st.dataframe(st.session_state.db)

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

if not st.session_state.db.empty:
    csv = convert_df(st.session_state.db)
    st.download_button(
        label="📥 엑셀(CSV)로 다운로드 받기",
        data=csv,
        file_name='나의_책_정리.csv',
        mime='text/csv',
    )
