import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 1. 全局基礎 --- */
        .stApp { background-color: #050505; color: #FAFAFA; }
        .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp div, .stApp span, .stApp li {
            color: #FAFAFA !important; font-family: "Source Sans Pro", sans-serif;
        }
        
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; max-width: 1000px !important; }
        hr { display: none !important; }
        .stElementContainer { margin-bottom: -10px !important; }

        /* --- 2. Header 標題樣式 --- */
        .brand-header {
            display: flex; align-items: center; gap: 15px; margin-bottom: 20px;
        }
        .header-title {
            font-size: 34px !important; font-weight: 700 !important; margin: 0 !important; line-height: 1.2 !important;
        }
        .header-subtitle {
            font-size: 14px !important; color: #94A3B8 !important; font-weight: 400 !important; margin: 0 !important;
        }

        /* --- 3. 狀態列 (Status Bar) --- */
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
        }
        .status-left { font-size: 16px; font-weight: bold; color: #FFF; }
        .status-right { font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 15px; }
        
        /* 狀態數值顏色 */
        .val-energy { color: #FF4081; font-weight: bold; }
        .val-xp { color: #FCD34D; font-weight: bold; }
        .val-engine { color: #94A3B8; border-left: 1px solid #444; padding-left: 15px; }

        /* Tooltip */
        .tooltip-container { position: relative; display: inline-block; cursor: help; }
        .sim-score { color: #00E5FF; font-weight: bold; border-bottom: 1px dashed #00E5FF; }
        .tooltip-text {
            visibility: hidden; width: 200px; background-color: #333; color: #fff; text-align: center;
            border-radius: 6px; padding: 8px; position: absolute; z-index: 10;
            top: 120%; left: 50%; margin-left: -100px; opacity: 0; transition: opacity 0.3s;
            border: 1px solid #555; font-size: 12px !important;
        }
        .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

        /* --- 4. 其他元件 --- */
        .user-info-box { display: flex; flex-direction: column; align-items: flex-end; justify-content: center; }
        .user-email { font-size: 13px !important; color: #888 !important; margin-bottom: 5px; }
        
        input, textarea, .stSelectbox > div > div { background-color: #1F2229 !important; border: 1px solid #444 !important; color: white !important; }
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
        }
    </style>
    """, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, similarity=0, sim_hint="", sim_gain=0, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    
    # 判斷引擎名稱
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    
    # 圖示
    icon = "🚀"
    if tier == "intermediate": icon = "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"

    # 左側文字
    left_content = f"👋 訪客" if is_guest else f"{icon} {tier_name}"
    
    # 右側內容 (使用 f-string 注入變數，但 HTML 結構保持簡單)
    # XP 部分
    xp_section = ""
    if not is_guest:
        # Tooltip
        tooltip = f"下一步：{sim_hint} (+{sim_gain}%)" if sim_gain > 0 else "已達目前等級上限"
        xp_section = f"""
        <div class="tooltip-container">
            <span style="color:#BBB">相似度 <span class="sim-score">{similarity}%</span></span>
            <span class="tooltip-text">{tooltip}</span>
        </div>
        &nbsp;&nbsp;
        <span>⭐ XP <span class="val-xp">{xp}</span></span>
        """

    # 組合最終 HTML
    html = f"""
    <div class="status-bar">
        <div class="status-left">{left_content}</div>
        <div class="status-right">
            <span>❤️ 電量 <span class="val-energy">{energy}</span></span>
            {xp_section}
            <span class="val-engine">| {engine_name}</span>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def render_question_card(question, index, total): st.info(f"🎙️ **Q{index}/{total}: {question}**")
def render_history_card(q, a): st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")
def render_dashboard_card(title, content): st.metric(label=title, value=content)
