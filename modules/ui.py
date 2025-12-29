import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 1. 全局基礎 (安全版) --- */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* 修正主容器寬度與邊距 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 1100px !important;
        }
        
        /* 隱藏預設分隔線 */
        hr { display: none !important; }
        
        /* --- 文字顏色修正 (移除 div，避免誤殺) --- */
        h1, h2, h3, h4, h5, h6, p, span, label, li, button, .stMarkdown {
            color: #FAFAFA !important;
            font-family: "Source Sans Pro", sans-serif;
        }

        /* --- 2. 頂部標題區 --- */
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

        /* --- 3. 右上角用戶資訊 (修復對齊) --- */
        .user-info-box {
            display: flex;
            flex-direction: column;
            align-items: flex-end; /* 靠右 */
            justify-content: center;
            height: 100%;
            margin-top: 10px;
        }
        .user-email {
            font-size: 14px !important;
            color: #888 !important;
            margin-bottom: 5px;
        }

        /* --- 4. 圓形進度條 (Stepper) --- */
        .step-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 30px 0;
            position: relative;
            width: 100%;
        }
        .step-item {
            text-align: center;
            position: relative;
            z-index: 2;
            padding: 0 30px;
        }
        .step-circle {
            width: 32px; height: 32px;
            border-radius: 50%;
            background: #1E1E1E;
            border: 2px solid #444;
            color: #666;
            display: flex; align-items: center; justify-content: center;
            font-weight: bold;
            font-size: 14px;
            margin: 0 auto 8px;
            transition: all 0.3s;
        }
        .step-label {
            font-size: 14px;
            color: #888;
            font-weight: 500;
        }
        .step-line-bg {
            position: absolute;
            top: 16px;
            left: 10%; right: 10%;
            height: 2px;
            background: #333;
            z-index: 1;
        }
        .step-active .step-circle {
            background: #FF4B4B;
            border-color: #FF4B4B;
            color: white;
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
        }
        .step-active .step-label {
            color: #FF4B4B !important;
            font-weight: bold;
        }

        /* --- 5. 狀態列 --- */
        .status-bar {
            background: #1A1C24;
            border: 1px solid #333;
            padding: 12px 20px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        .status-text { font-size: 15px; font-weight: 500; }

        /* --- 6. 輸入框與按鈕優化 --- */
        /* 針對 Streamlit 的輸入框容器 */
        .stSelectbox > div > div, 
        .stTextInput > div > div > input {
            background-color: #1F2229 !important;
            border: 1px solid #444 !important;
            color: white !important;
        }
        
        /* 下拉選單文字顏色 */
        div[data-baseweb="select"] span {
            color: white !important;
        }
        
        /* 按鈕 */
        button[kind="primary"] {
            background-color: #FF4B4B !important;
            color: white !important;
            border: none;
            font-weight: bold;
            padding: 0.5rem 1rem;
            font-size: 16px;
        }

        /* 手機版適配 */
        @media (max-width: 600px) {
            .step-line-bg { display: none; }
            .user-info-box { display: none; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 10px; }
        }
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"]
    items_html = ""
    for i, name in enumerate(steps):
        is_active = "step-active" if i + 1 == current_step else ""
        items_html += f'<div class="step-item {is_active}"><div class="step-circle">{i+1}</div><div class="step-label">{name}</div></div>'
    
    final_html = f'<div class="step-wrapper"><div class="step-line-bg"></div>{items_html}</div>'
    st.markdown(final_html, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    
    left = f"👋 訪客" if is_guest else f"{icon} {tier_name}"
    xp_html = f'<span style="margin-left:15px; color:#FFD700">⭐ XP: {xp}</span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-text" style="color:#FFF !important;">{left}</div>
        <div class="status-text">
            <span style="color:#FF4081; font-weight:bold;">❤️ 電量: {energy}</span>
            {xp_html}
            <span style="margin-left:15px; color:#888;">| {engine}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.info(f"🎙️ **Q{index}/{total}: {question}**\n\n請按下錄音回答...")

def render_history_card(q, a):
    st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")

def render_dashboard_card(title, content):
    st.metric(label=title, value=content)
