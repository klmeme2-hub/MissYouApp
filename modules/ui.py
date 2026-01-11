import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 1. 全局設定 --- */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div, li { 
            color: #FAFAFA !important; 
        }
        
        /* 主區塊寬度 1000px */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 1000px !important;
        }
        
        /* 隱藏分隔線 */
        hr { display: none !important; }
        .stElementContainer { margin-bottom: -15px !important; }
        
        /* --- 2. 標題與 Header --- */
        .header-title h1 {
            font-size: 36px !important;
            margin-bottom: 5px !important;
            padding: 0 !important;
            text-shadow: 0 0 15px rgba(124, 77, 255, 0.6);
            line-height: 1.1;
        }
        .header-subtitle {
            font-size: 16px !important;
            color: #BBB !important;
            margin-top: 0px !important;
            margin-bottom: 15px !important;
            font-weight: 400;
        }
        
        /* 右上角用戶資訊 (僅電腦版) */
        .user-info-box {
            display: flex; flex-direction: column; align-items: flex-end; justify-content: center; height: 100%; margin-top: 10px;
        }
        .user-email { font-size: 14px !important; color: #888 !important; margin-bottom: 5px; }

        /* --- 3. 狀態列 --- */
        .status-bar {
            background: #1A1C24;
            border: 1px solid #333;
            padding: 12px 20px;
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px;
        }
        .status-text { font-size: 15px; font-weight: 500; }

        /* --- 4. 輸入框與按鈕 --- */
        .stSelectbox > div > div, .stTextInput > div > div > input {
            background-color: #1F2229 !important;
            border: 1px solid #444 !important;
            color: white !important;
        }
        button[kind="primary"] {
            background-color: #FF4B4B !important; color: white !important; border: none;
        }
        /* 次要按鈕樣式 (用於未選中的導航) */
        button[kind="secondary"] {
            background-color: transparent !important;
            color: #AAA !important;
            border: 1px solid #444 !important;
        }
        button[kind="secondary"]:hover {
            border-color: #FF4B4B !important;
            color: #FF4B4B !important;
        }
        
        /* --- 5. 卡片樣式 --- */
        .question-card-active { background-color: #1A1C24; padding: 20px; border-radius: 12px; border: 2px solid #2196F3; text-align: center; margin-bottom: 20px; }
        .q-text { font-size: 20px; color: #FFFFFF !important; font-weight: bold; margin: 10px 0; }
        .history-card { background-color: #262730; padding: 12px; border: 1px solid #444; border-radius: 8px; margin-bottom: 8px; }
        .script-box { background: #1E1E1E; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #FFD700; color: #DDD !important; }
        .ai-bubble { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 3px solid #FF4B4B; margin: 10px 0; color: #E0E0E0 !important; }
        .dashboard-card { background-color: #1A1C24; padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; margin-bottom: 10px; }

        #MainMenu, footer {visibility: hidden;}

        /* 手機版適配 */
        @media (max-width: 600px) {
            .user-info-box { display: none; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 8px; padding: 15px; }
        }
    </style>
    """, unsafe_allow_html=True)

# 已移除 render_stepper，因為改用按鈕列了

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    left = f"👋 訪客" if is_guest else f"{icon} {tier_name}"
    xp_html = f'<span style="margin-left:15px; color:#FFD700">⭐ XP: {xp}</span>' if not is_guest else ''
    st.markdown(f"""<div class="status-bar"><div class="status-text" style="color:#FFF !important;">{left}</div><div class="status-text"><span style="color:#FF4081; font-weight:bold;">❤️ 電量: {energy}</span>{xp_html}<span style="margin-left:15px; color:#888;">| {engine}</span></div></div>""", unsafe_allow_html=True)

def render_question_card(question, index, total): st.info(f"🎙️ **Q{index}/{total}: {question}**")
def render_history_card(q, a): st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")
def render_dashboard_card(title, content): st.metric(label=title, value=content)
