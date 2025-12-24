import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* 基礎配色：深色模式優化 */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* 全局文字顏色 */
        .stApp, p, h1, h2, h3, h4, label, div, span, button { color: #FAFAFA !important; }
        
        /* 輸入框與選單背景 */
        .stTextInput > div > div > input, .stSelectbox > div > div {
            background-color: #262730 !important;
            color: white !important;
            border: 1px solid #444;
        }

        /* 隱藏預設選單 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 讓按鈕好看一點點，但不要強制定位 */
        div.stButton > button {
            background-color: #FF4B4B;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
        }
        
        /* 卡片樣式 (僅保留背景色，移除複雜定位) */
        .info-card {
            background-color: #1A1C24;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #333;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    # 使用原生 Markdown 表格來排版，保證絕對對齊
    tier_map = {"basic": "🚀 初級", "intermediate": "🛡️ 中級", "advanced": "🔥 高級", "eternal": "♾️ 永恆"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Flash"
    
    # 簡單的 HTML 排版
    st.markdown(f"""
    <div style="background:#262730; padding:10px 20px; border-radius:10px; border:1px solid #444; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:1.1em; font-weight:bold;">👤 {tier_name}</span>
        <span>
            <span style="color:#FF4081;">❤️ {energy}</span> &nbsp;|&nbsp; 
            <span style="color:#FFD700;">⭐ {xp}</span> &nbsp;|&nbsp; 
            <span style="color:#00E5FF;">⚡ {engine}</span>
        </span>
    </div>
    <div style="margin-bottom: 20px;"></div>
    """, unsafe_allow_html=True)

# 移除複雜的 Stepper HTML，改用 Streamlit 原生 progress bar 或簡單文字
def render_stepper(current_step):
    steps = ["1.喚名", "2.安慰", "3.鼓勵", "4.詼諧", "5.完成"]
    # 簡單的文字進度條
    st.progress(current_step / 5)
    st.caption(f"目前進度：{steps[current_step-1]} (Step {current_step}/5)")

def render_dashboard_card(title, content):
    st.markdown(f"""
    <div class="info-card" style="text-align:center;">
        <div style="color:#888; font-size:12px;">{title}</div>
        <div style="font-size:24px; font-weight:bold;">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.info(f"📝 題目 ({index}/{total})：\n\n**{question}**")

def render_history_card(q, a):
    st.markdown(f"> **Q:** {q}\n\n{a[:30]}...")
