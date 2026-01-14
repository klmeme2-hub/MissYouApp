import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 1. 全局基礎 (深色模式) --- */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* 強制所有文字顏色 */
        h1, h2, h3, h4, h5, h6, p, label, span, div, li, button, .stMarkdown {
            color: #FAFAFA !important;
            font-family: "Source Sans Pro", sans-serif;
        }
        
        /* 調整主容器寬度 */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 5rem !important;
            max-width: 1000px !important;
        }
        
        /* 隱藏預設分隔線 */
        hr { display: none !important; }
        
        /* 縮小元件間距 */
        .stElementContainer { margin-bottom: -10px !important; }

        /* --- 2. Header --- */
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

        /* --- 3. 狀態列 (關鍵修復對象) --- */
        .status-bar {
            background: #1A1C24;
            border: 1px solid #333;
            padding: 12px 20px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            width: 100%;
            box-sizing: border-box;
        }
        
        /* 狀態文字容器 */
        .status-text-left {
            font-size: 16px;
            font-weight: bold;
            color: #FFF !important;
        }
        
        .status-text-right {
            font-size: 15px;
            font-weight: 500;
            display: flex;
            align-items: center;
        }

        /* --- 4. 其他元件 --- */
        .user-info-box { display: flex; flex-direction: column; align-items: flex-end; justify-content: center; }
        .user-email { font-size: 13px !important; color: #888 !important; }
        
        .step-wrapper { display: flex; justify-content: center; margin: 30px 0; }
        .step-item { text-align: center; padding: 0 20px; position: relative; z-index: 2; }
        .step-circle { width: 30px; height: 30px; border-radius: 50%; background: #1E1E1E; border: 2px solid #444; display: flex; align-items: center; justify-content: center; margin: 0 auto 5px; }
        .step-active .step-circle { background: #FF4B4B; border-color: #FF4B4B; }
        .step-line-bg { position: absolute; top: 15px; left: 10%; right: 10%; height: 2px; background: #333; z-index: 1; }

        input, textarea, .stSelectbox > div > div { background-color: #1F2229 !important; border: 1px solid #444 !important; }
        button[kind="primary"] { background-color: #FF4B4B !important; border: none; }
        
        .question-card-active { background-color: #1A1C24; padding: 20px; border-radius: 12px; border: 2px solid #2196F3; text-align: center; margin-bottom: 20px; }
        .q-text { font-size: 20px; font-weight: bold; margin: 10px 0; }
        .history-card { background-color: #262730; padding: 12px; border-radius: 8px; margin-bottom: 8px; }
        .dashboard-card { background-color: #1A1C24; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
        .ai-bubble { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 3px solid #FF4B4B; margin: 10px 0; }

        #MainMenu, footer {visibility: hidden;}
        
        @media (max-width: 600px) {
            .status-bar { flex-direction: column; align-items: flex-start; gap: 10px; }
            .user-info-box { display: none; }
            .step-line-bg { display: none; }
        }
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"]
    items = ""
    for i, name in enumerate(steps):
        active = "step-active" if i + 1 == current_step else ""
        items += f'<div class="step-item {active}"><div class="step-circle">{i+1}</div><div class="step-label">{name}</div></div>'
    st.markdown(f'<div class="step-wrapper"><div class="step-line-bg"></div>{items}</div>', unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    # 準備變數
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"

    # 左側文字
    left_text = f"👋 訪客" if is_guest else f"{icon} {tier_name}"
    
    # 右側文字 (拼接 HTML)
    # 注意：這裡使用單引號包覆 style 屬性，避免與 f-string 衝突
    xp_html = f"<span style='margin-left:15px; color:#FFD700;'>⭐ XP: {xp}</span>" if not is_guest else ""
    
    right_html = f"""
        <span style='color:#FF4081; font-weight:bold;'>❤️ 電量: {energy}</span>
        {xp_html}
        <span style='margin-left:15px; color:#888;'>| {engine_name}</span>
    """
    
    # 最終渲染 (確保結構完整)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-text-left">{left_text}</div>
        <div class="status-text-right">{right_html}</div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total): st.info(f"🎙️ **Q{index}/{total}: {question}**")
def render_history_card(q, a): st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")
def render_dashboard_card(title, content): st.metric(label=title, value=content)
