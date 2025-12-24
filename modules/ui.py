import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* 基礎配色：適應深色模式 */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* 確保所有文字都是白色，避免黑屏 */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div, li, button { 
            color: #FAFAFA !important; 
        }
        
        /* 輸入框背景 */
        input, textarea, .stSelectbox > div > div {
            background-color: #262730 !important;
            color: white !important;
            border: 1px solid #444 !important;
        }

        /* 隱藏預設選單 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 簡單的卡片樣式 */
        .info-card {
            background-color: #1A1C24;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #444;
            margin-bottom: 10px;
        }
        
        /* 按鈕樣式 */
        div.stButton > button {
            background-color: #FF4B4B;
            color: white;
            border-radius: 8px;
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "🚀 初級", "intermediate": "🛡️ 中級", "advanced": "🔥 高級", "eternal": "♾️ 永恆"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Flash"
    user_label = "👋 訪客" if is_guest else f"👤 {tier_name}"
    
    # 使用原生 Markdown 表格排版，最穩
    st.markdown(f"""
    <div style="background:#262730; padding:10px 15px; border-radius:8px; border:1px solid #444; margin-bottom:20px;">
        <span style="font-weight:bold; font-size:1.1em;">{user_label}</span>
        <span style="float:right;">
            <span style="color:#FF4081;">❤️ {energy}</span> | 
            <span style="color:#FFD700;">⭐ {xp}</span> | 
            <span style="color:#00E5FF;">⚡ {engine}</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["1.喚名", "2.安慰", "3.鼓勵", "4.詼諧", "5.完成"]
    # 改用原生進度條，雖然不炫但絕對不會壞
    st.progress(current_step / 5)
    st.caption(f"目前進度：{steps[current_step-1]} (Step {current_step}/5)")

def render_question_card(question, index, total):
    st.info(f"📝 題目 ({index}/{total})：\n\n**{question}**")

def render_history_card(q, a):
    st.markdown(f"""
    <div style="background:#1E1E1E; padding:10px; border-radius:5px; margin-bottom:5px; border:1px solid #333;">
        <b style="color:#FF4B4B">Q: {q}</b><br>
        <span style="color:#CCC">{a[:30]}...</span>
    </div>
    """, unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.metric(label=title, value=content)
