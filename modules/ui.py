import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 全局設定 --- */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* 確保所有文字可見 */
        h1, h2, h3, h4, h5, h6, p, div, span, label, li, button, .stMarkdown {
            color: #FAFAFA !important;
        }
        
        /* 調整寬度與邊距 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 1000px !important;
        }
        
        /* 隱藏預設分隔線 */
        hr { display: none !important; }
        
        /* --- Header 樣式 --- */
        .header-title {
            font-size: 34px !important;
            font-weight: 700 !important;
            margin-bottom: 0 !important;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .header-subtitle {
            font-size: 16px !important;
            color: #B0B0B0 !important;
            margin-top: 5px !important;
        }

        /* --- 右上角用戶資訊 --- */
        .user-info-box {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            justify-content: center;
            height: 100%;
        }
        .user-email {
            font-size: 14px !important;
            color: #888 !important;
            margin-bottom: 5px;
        }

        /* --- 圓形進度條 (Stepper) --- */
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
            padding: 0 20px;
        }
        .step-circle {
            width: 30px; height: 30px;
            border-radius: 50%;
            background: #1E1E1E;
            border: 2px solid #444;
            color: #666;
            display: flex; align-items: center; justify-content: center;
            font-weight: bold; font-size: 14px;
            margin: 0 auto 5px;
        }
        .step-label { font-size: 12px; color: #888; }
        
        /* 連接線 */
        .step-line-bg {
            position: absolute;
            top: 15px;
            left: 10%; right: 10%;
            height: 2px; background: #333; z-index: 1;
        }
        
        /* 激活狀態 */
        .step-active .step-circle {
            background: #FF4B4B; border-color: #FF4B4B; color: white;
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
        }
        .step-active .step-label { color: #FF4B4B !important; font-weight: bold; }

        /* --- 狀態列 --- */
        .status-bar {
            background: #1A1C24;
            border: 1px solid #333;
            padding: 12px 20px;
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px;
        }
        .status-text { font-size: 15px; font-weight: 500; }

        /* --- 輸入框與按鈕 --- */
        .stSelectbox > div > div, .stTextInput > div > div > input {
            background-color: #1F2229 !important;
            border: 1px solid #444 !important;
            color: white !important;
        }
        button[kind="primary"] {
            background-color: #FF4B4B !important;
            color: white !important;
            border: none;
        }

        /* 手機適配 */
        @media (max-width: 600px) {
            .step-line-bg { display: none; }
            .user-info-box { display: none; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 10px; }
        }
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"]
    
    # 組合 HTML (單行模式，避免 Markdown 解析錯誤)
    items = ""
    for i, name in enumerate(steps):
        is_active = "step-active" if i + 1 == current_step else ""
        items += f'<div class="step-item {is_active}"><div class="step-circle">{i+1}</div><div class="step-label">{name}</div></div>'
    
    st.markdown(f'<div class="step-wrapper"><div class="step-line-bg"></div>{items}</div>', unsafe_allow_html=True)

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
