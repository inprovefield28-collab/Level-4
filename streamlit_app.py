import streamlit as st
import pandas as pd
import os
import re
import random

# ==========================================
# 老師修改區
# ==========================================
APP_TITLE = "線上聽力測驗 Level 4"
INTRO_BOX_TEXT = """• 小學五年級單字、句型"""

COLOR_MAIN = "#8B5CF6"   # 主色
COLOR_LIGHT = "#F5F3FF"  # 說明框背景
COLOR_BG = "#F8F9FD"     # 網頁底色
# ==========================================

st.set_page_config(page_title=APP_TITLE, layout="centered")

# --- 1. 樣式注入 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; }}
    header {{ visibility: hidden; }}
    
    /* 縮減網頁最上方留白 */
    .block-container {{
        padding-top: 1rem !important;
    }}

    /* 大卡片容器 (針對 st.form) */
    [data-testid="stForm"] {{
        background-color: white !important;
        padding: 30px 40px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        border: none !important;
        border-top: 10px solid {COLOR_MAIN} !important;
        max-width: 600px;
        margin: 0px auto;
    }}
    
    .app-title {{
        color: {COLOR_MAIN};
        font-weight: 800;
        font-size: 32px;
        margin-top: -10px; /* 標題上移 */
        margin-bottom: 10px;
        text-align: center;
    }}
    
    .intro-box {{
        background-color: {COLOR_LIGHT};
        padding: 12px 25px !important; /* 縮減說明框內部的上下距離 */
        border-radius: 12px;
        color: {COLOR_MAIN};
        font-size: 15px;
        line-height: 1.4;
        margin-bottom: 20px;
        white-space: pre-wrap;
        text-align: left;
    }}

    .stTextInput input {{
        background-color: #F9FAFB !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 10px !important;
    }}

    /* 進入挑戰按鈕置中 */
    [data-testid="stFormSubmitButton"] {{
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }}

    [data-testid="stFormSubmitButton"] button {{
        width: auto !important;
        min-width: 150px !important;
        background-color: {COLOR_MAIN} !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 40px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        margin-top: 10px !important;
    }}

    /* 測驗選項按鈕 */
    .quiz-btn button {{
width: 100% !important;
        background-color: white !important;
        color: #333 !important;
        border: 2px solid #F3F4F6 !important;
        text-align: left !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
        font-size: 26px !important; /* 直接加入這一行，數字可改 22-26 */
    }}
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心功能 ---
@st.cache_data
def load_and_shuffle_data():
    df_list = []
    file_pattern = re.compile(r"([a-zA-Z0-9]+)(\d+-\d+)\.csv$")
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for file_name in all_files:
        match = file_pattern.match(file_name)
        if match:
            cat, rng = match.group(1), match.group(2)
            try:
                temp_df = pd.read_csv(file_name, encoding='utf-8-sig')
            except:
                temp_df = pd.read_csv(file_name, encoding='big5')
            temp_df.columns = [c.strip().lower() for c in temp_df.columns]
            temp_df['cat'], temp_df['rng'] = cat, rng
            df_list.append(temp_df)
    
    if not df_list: return []
    full_df = pd.concat(df_list, ignore_index=True)
    questions = []
    for q in full_df.to_dict('records'):
        opts = [str(q.get('a','')), str(q.get('b','')), str(q.get('c',''))]
        correct_text = opts[0]
        random.shuffle(opts)
        questions.append({
            'id': str(q.get('id', 0)).zfill(3),
            'q': q.get('question', ''), # 資料仍保留供結果頁面使用
            'opts': opts,
            'ans': opts.index(correct_text),
            'path': f"audio_{q['cat']}{q['rng']}/q_{str(q.get('id', 0)).zfill(3)}.mp3",
            'level_info': f"{q['cat']}{q['rng']}"
        })
    return questions

if 'step' not in st.session_state:
    st.session_state.step = 'start'

# A. 首頁
if st.session_state.step == 'start':
    with st.form("start_form"):
        st.markdown(f'<div class="app-title">{APP_TITLE}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="intro-box">{INTRO_BOX_TEXT}</div>', unsafe_allow_html=True)
        user_name = st.text_input("user_name", label_visibility="collapsed", placeholder="請輸入姓名")
        submit = st.form_submit_button("進入挑戰")
        if submit:
            if user_name.strip() == "":
                st.error("請輸入姓名後再開始唷！")
            else:
                st.session_state.user_name = user_name
                st.session_state.all_pool = load_and_shuffle_data()
                if not st.session_state.all_pool:
                    st.error("找不到題庫檔案 (CSV)")
                else:
                    st.session_state.quiz_data = random.sample(st.session_state.all_pool, min(len(st.session_state.all_pool), 10))
                    st.session_state.current_idx = 0
                    st.session_state.results = []
                    st.session_state.step = 'quiz'
                    st.rerun()

# B. 測驗頁 (已刪除題目文字顯示)
elif st.session_state.step == 'quiz':
    q = st.session_state.quiz_data[st.session_state.current_idx]
    st.markdown(f"### 第 {st.session_state.current_idx + 1} / 10 題")
    
    if os.path.exists(q['path']):
        st.audio(q['path'])
    else:
        st.warning(f"找不到音檔: {q['path']}")
    
    # 此處已刪除 st.write(f"#### {q['q']}")
    
    st.markdown('<div class="quiz-btn">', unsafe_allow_html=True)
    keys = ['A', 'B', 'C']
    for i, opt_text in enumerate(q['opts']):
        if st.button(f"{keys[i]}. {opt_text}", key=f"q_{st.session_state.current_idx}_{i}"):
            st.session_state.results.append({
                "question": q['q'],
                "user_choice": opt_text,
                "correct_answer": q['opts'][q['ans']],
                "is_correct": (i == q['ans'])
            })
            st.session_state.current_idx += 1
            if st.session_state.current_idx >= 10:
                st.session_state.step = 'result'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# C. 結果頁
elif st.session_state.step == 'result':
    st.markdown(f"""
    <div style="background-color: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-top: 10px solid {COLOR_MAIN}; max-width: 600px; margin: 20px auto;">
        <h2 style='text-align:center;'>🏆 練習結束！</h2>
    """, unsafe_allow_html=True)
    
    score = sum(1 for item in st.session_state.results if item['is_correct'])
    final_score = score * 10
    st.markdown(f"<h3 style='text-align:center; color:{COLOR_MAIN};'>得分：{final_score} 分</h3>", unsafe_allow_html=True)

    wrong_txt = ""
    for i, item in enumerate(st.session_state.results):
        if not item['is_correct']:
            wrong_txt += f"Q{i+1}: {item['question']}\\n   ❌ 您選: {item['user_choice']}\\n   ✅ 正確: {item['correct_answer']}\\n\\n"
    
    level_tag = st.session_state.quiz_data[0]['level_info']
    report_text = f"【{APP_TITLE}】\\n姓名：{st.session_state.user_name}\\n成績：{final_score}\\n\\n{wrong_txt}"

    html_code = f"""
        <button id="copyBtn" style="background-color:{COLOR_MAIN}; color:white; border:none; padding:15px; font-size:20px; font-weight:bold; border-radius:15px; width:100%; cursor:pointer;">
            按我複製成績給老師
        </button>
        <script>
            document.getElementById('copyBtn').onclick = function() {{
                const text = "{report_text}";
                navigator.clipboard.writeText(text.replace(/\\\\n/g, '\\n')).then(function() {{
                    document.getElementById('copyBtn').innerText = '✅ 複製成功！';
                    setTimeout(function() {{ document.getElementById('copyBtn').innerText = '按我複製成績給老師'; }}, 2000);
                }});
            }};
        </script>
    """
    st.components.v1.html(html_code, height=100)
    st.write("---")
    for i, item in enumerate(st.session_state.results):
        if not item['is_correct']:
            st.error(f"**Q{i+1}: {item['question']}**\n\n❌ 您選: {item['user_choice']}  \n✅ 正確: {item['correct_answer']}")

    if st.button("再玩一次"):
        st.session_state.step = 'start'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
