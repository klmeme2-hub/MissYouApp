import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* =============================================
           1. 全局字體控制 (強制 16px / 1.6)
           ============================================= */
        
        /* 基礎設定 */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* 針對所有文字元件強制設定 */
        html, body, p, label, span, div, li, .stMarkdown, .caption {
            font-size: 16px !important;
            line-height: 1.6 !important;
            font-family: "Source Sans Pro", sans-serif;
            color: #FAFAFA !important;
        }
        
        /* 標題維持層級，但行高統一 */
        h1 { font-size: 34px !important; line-height: 1.4 !important; }
        h2 { font-size: 28px !important; line-height: 1.4 !important; }
        h3 { font-size: 24px !important; line-height: 1.4 !important; }
        
        /* 調整主容器 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 1000px !important;
        }
        
        /* 隱藏預設分隔線 */
        hr { display: none !important; }

        /* =============================================
           2. 互動元件字體修正
           ============================================= */
        
        /* 按鈕文字 */
        button, .stButton > button {
            font-size: 16px !important;
            line-height: 1.6 !important;
            font-weight: 600 !important;
            height: auto !important;
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }
        /* 特別針對 Primary 按鈕 */
        button[kind="primary"] {
            background-color: #FF4B4B !important;
            color: white !important;
            border: none;
        }
        
        /* 輸入框內的文字 */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] div {
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: white !important;
            background-color: #1F2229 !important;
        }
        
        /* 下拉選單選項 */
        div[data-baseweb="popover"] li, div[data-baseweb="popover"] span {
            font-size: 16px !important;
        }

        /* Tab 分頁標籤 */
        button[data-baseweb="tab"] div {
            font-size: 16px !important;
            font-weight: 600 !important;
        }

        /* =============================================
           3. 自定義元件樣式
           ============================================= */

        /* Header */
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

        /* 右上角用戶資訊 */
        .user-info-box {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            justify-content: center;
        }
        .user-email {
            font-size: 14px !important; /* Email 稍微小一點點做區隔，也可改16 */
            color: #888 !important;
            margin-bottom: 5px;
        }

        /* 狀態列 */
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
        .status-text { 
            font-size: 16px !important; /* 強制 16px */
            font-weight: 500; 
        }

        /* Stepper (圓形進度條) */
        .step-wrapper {
            display: flex; justify-content: center; align-items: center;
            margin: 30px 0; width: 100%; position: relative;
        }
        .step-item {
            text-align: center; position: relative; z-index: 2; padding: 0 20px;
        }
        .step-circle {
            width: 32px; height: 32px;
            border-radius: 50%;
            background: #1E1E1E; border: 2px solid #444; color: #666;
            display: flex; align-items: center; justify-content: center;
            font-weight: bold; font-size: 14px !important; /* 圓圈內數字維持小一點 */
            margin: 0 auto 5px;
        }
        .step-label { 
            font-size: 14px !important; /* 標籤文字稍小，避免擁擠，若需16可改 */
            color: #888; 
        }
        .step-line-bg {
            position: absolute; top: 16px; left: 10%; right: 10%;
            height: 2px; background: #333; z-index: 1;
        }
        .step-active .step-circle {
            background: #FF4B4B; border-color: #FF4B4B; color: white;
        }
        .step-active .step-label { color: #FF4B4B !important; font-weight: bold; }

        /* 手機版適配 */
        @media (max-width: 600px) {
            .step-line-bg { display: none; }
            .user-info-box { display: none; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 10px; }
            /* 手機版字體保持 16px 易讀性 */
            p, div, span, label { font-size: 16px !important; }
        }
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"]
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
    st.info(f"🎙️ **Q{index}/{total}: {question}**")

def render_history_card(q, a):
    st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")

def render_dashboard_card(title, content):
    st.metric(label=title, value=content)
