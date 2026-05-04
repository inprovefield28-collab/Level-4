import streamlit as st
import pandas as pd
import os
import re
import random

# --- 1. 設定網頁樣式 ---
st.set_page_config(page_title="HWG 聽力測驗", layout="centered")

st.markdown("""
    <style>
    div.stButton > button {
        width: 100% !important;
        height: auto !important;
        padding: 15px 20px !important;
        background-color: white !important;
        border: 2px solid #eee !important;
        border-radius: 15px !important;
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
    }
    div.stButton > button p {
        font-size: 22px !important;
        font-weight: bold !important;
        text-align: left !important;
        white-space: pre-wrap !important; 
    }
    audio { width: 100% !important; height: 50px !important; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 讀取資料並預處理隨機選項 ---
@st.cache_data
def load_and_shuffle_data():
    df_list = []
    file_pattern = re.compile(r"([a-zA-Z]+)(\d+-\d+)\.csv$")
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    
    for file_name in all_files:
        match = file_pattern.match(file_name)
        if match:
            category = match.group(1)
            range_str = match.group(2)
            try:
                temp_df = pd.read_csv(file_name, encoding='utf-8-sig')
            except:
                temp_df = pd.read_csv(file_name, encoding='big5')
            
            temp_df.columns = [c.strip().lower() for c in temp_df.columns]
            temp_df['source_category'] = category 
            temp_df['source_range'] = range_str
            df_list.append(temp_df)
    
    if not df_list:
        return []

    full_df = pd.concat(df_list, ignore_index=True)
    raw_records = full_df.to_dict('records')
    
    processed_questions = []
    for q in raw_records:
        # 1. 取得原本在 A 的正確答案，以及 B, C 的干擾項
        # 假設你的 Excel 欄位是 a, b, c
        correct_content = str(q.get('a', ''))
        distractor_1 = str(q.get('b', ''))
        distractor_2 = str(q.get('c', ''))
        
        # 2. 隨機打亂這三個內容
        options = [correct_content, distractor_1, distractor_2]
        random.shuffle(options)
        
        # 3. 找出打亂後，正確答案在哪一個 index (0, 1, 2)
        correct_idx = options.index(correct_content)
        idx_to_key = {0: 'A', 1: 'B', 2: 'C'}
        
        # 4. 重新封裝成一個測驗物件
        processed_q = {
            'id': str(q.get('id', 0)).zfill(3),
            'question': q.get('question', ''),
            'A': options[0],
            'B': options[1],
            'C': options[2],
            'correct_key': idx_to_key[correct_idx],
            'category': q['source_category'],
            'range': q['source_range']
        }
        processed_questions.append(processed_q)
        
    return processed_questions

# --- 3. 初始化 Session ---
if 'all_quiz_pool' not in st.session_state:
    st.session_state.all_quiz_pool = load_and_shuffle_data()

if not st.session_state.all_quiz_pool:
    st.error("❌ 找不到符合格式的 CSV。")
    st.stop()

if 'quiz_data' not in st.session_state:
    # 從處理好的題目池中隨機抽 10 題
    st.session_state.quiz_data = random.sample(st.session_state.all_quiz_pool, min(len(st.session_state.all_quiz_pool), 10))
    st.session_state.current_idx = 0
    st.session_state.results = []

# --- 4. 測驗介面 ---
if st.session_state.current_idx < len(st.session_state.quiz_data):
    q = st.session_state.quiz_data[st.session_state.current_idx]
    
    st.write(f"### 第 {st.session_state.current_idx + 1} / 10 題")
    
    # 根據系列與範圍抓取音檔
    audio_path = f"audio_{q['category']}{q['range']}/q_{q['id']}.mp3"
    if os.path.exists(audio_path):
        st.audio(audio_path)
    else:
        st.warning(f"音檔缺失: {audio_path}")

    # 顯示隨機化後的選項
    for key in ['A', 'B', 'C']:
        if st.button(f"{key}. {q[key]}", key=f"btn_{st.session_state.current_idx}_{key}"):
            is_correct = (key == q['correct_key'])
            st.session_state.results.append({
                "question": q['question'],
                "user_choice": q[key],
                "correct_answer": q[q['correct_key']],
                "is_correct": is_correct
            })
            st.session_state.current_idx += 1
            st.rerun()

# --- 5. 結果頁面 ---
else:
    st.header("🏆 練習結束！")
    score = sum(1 for item in st.session_state.results if item['is_correct'])
    st.subheader(f"得分：{score * 10} 分")

    # (此處保留原本的成績複製與詳情顯示代碼...)
    if st.button("再玩一次"):
        # 重新打亂所有題目 pool (確保下一輪答案位置也不同)
        st.session_state.all_quiz_pool = load_and_shuffle_data()
        del st.session_state.quiz_data
        st.rerun()