import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* 全局設定 */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp div, .stApp span {
            color: #FAFAFA !important;
            font-family: "Source Sans Pro", sans-serif;
        }
        
        /* 容器寬度 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 1000px !important;
        }
        
        /* 隱藏分隔線 */
        hr { display: none !important; }
        
        /* 標題樣式 */
        .header-title {
            font-size: 34px !important;
            font-weight: 700 !important;
            margin-bottom: 5px !important;
        }
        .header-subtitle {
            font-size: 16px !important;
            color: #B0B0B0 !important;
            font-weight: 400;
        }
        
        /* 右上角資訊 */
        .user-info-box {
            display: flex; 
            flex-direction: column; 
            align-items: flex-end; 
            justify-content: center;
        }
        .user-email {
            font-size: 13px !important; 
            color: #888 !important; 
            margin-bottom: 5px;
        }
        
        /* Stepper */
        .step-wrapper {
            display: flex; justify-content: center; align-items: center;
            margin: 30px 0; width: 100%; position: relative;
        }
        .step-item {
            text-align: center; position: relative; z-index: 2; padding: 0 20px;
        }
        .step-circle {
            width: 30px; height: 30px; border-radius: 50%; background: #1E1E1E;
            border: 2px solid #444; color: #666; display: flex; 
            align-items: center; justify-content: center; font-weight: bold;
        }
        .step-active .step-circle {
            background: #FF4B4B; border-color: #FF4B4B; color: white;
        }
        
        /* 輸入框背景 */
        input, textarea, .stSelectbox > div > div {
            background-color: #1F2229 !important;
            border: 1px solid #444 !important;
            color: white !important;
        }
        
        /* 按鈕 */
        button[kind="primary"] {
            background-color: #FF4B4B !important;
            color: white !important;
            border: none;
        }
        
        #MainMenu, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"]
    items = ""
    for i, name in enumerate(steps):
        is_active = "step-active" if i + 1 == current_step else ""
        items += f'<div class="step-item {is_active}"><div class="step-circle">{i+1}</div><div class="step-label">{name}</div></div>'
    st.markdown(f'<div class="step-wrapper">{items}</div>', unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    icon = "🚀" if tier == "basic" else "🛡️"
    left = f"👋 訪客" if is_guest else f"{icon} {tier_name}"
    xp_html = f'<span style="margin-left:15px; color:#FFD700">⭐ XP: {xp}</span>' if not is_guest else ''
    
    st.markdown(f"""
    <div style="background:#1A1C24; padding:12px 20px; border-radius:8px; display:flex; justify-content:space-between; border:1px solid #333; margin-bottom:20px;">
        <div style="color:white; font-weight:bold;">{left}</div>
        <div>
            <span style="color:#FF4081; font-weight:bold;">❤️ 電量: {energy}</span>
            {xp_html}
            <span style="margin-left:15px; color:#888;">| {engine}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.info(f"🎙️ **Q{index}/{total}: {question}**")

def render_history_card(q, a):
    st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")

def render_dashboard_card(title, content):
    st.metric(label=title, value=content)
