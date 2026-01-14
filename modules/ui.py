import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 全局基礎 --- */
        .stApp { background-color: #050505; color: #FAFAFA; }
        .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp div, .stApp span, .stApp li {
            color: #FAFAFA !important; font-family: "Source Sans Pro", sans-serif;
        }
        
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; max-width: 1000px !important; }
        hr { display: none !important; }
        .stElementContainer { margin-bottom: -10px !important; }

        /* --- Header --- */
        .header-title { font-size: 34px !important; font-weight: 700 !important; margin-bottom: 5px !important; }
        .header-subtitle { font-size: 16px !important; color: #B0B0B0 !important; font-weight: 400; }
        .user-info-box { display: flex; flex-direction: column; align-items: flex-end; justify-content: center; }
        .user-email { font-size: 13px !important; color: #888 !important; margin-bottom: 5px; }

        /* --- 狀態列 --- */
        .status-bar {
            background: #1A1C24; border: 1px solid #333; padding: 12px 20px;
            border-radius: 8px; display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px; width: 100%; box-sizing: border-box;
        }
        .status-left { font-size: 16px; font-weight: bold; color: #FFF; }
        .status-right { font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 15px; }
        
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

        /* --- 卡片樣式 (統一深色風格) --- */
        
        /* 題目卡片 (Active) - 改為深色 */
        .question-card-active { 
            background-color: #1A1C24; 
            padding: 25px; 
            border-radius: 12px; 
            border: 1px solid #333; /* 深灰邊框 */
            text-align: center; 
            margin-bottom: 20px; 
        }
        .q-progress { color: #888; font-size: 12px; margin-bottom: 10px; letter-spacing: 1px; }
        .q-text { 
            font-size: 22px; 
            color: #FFFFFF !important; /* 強制白字 */
            font-weight: 700; 
            margin: 15px 0; 
            line-height: 1.4;
        }
        .q-hint { font-size: 14px; color: #AAA; margin-top: 10px; }

        /* 歷史回憶卡 */
        .history-card { background-color: #262730; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #444; }
        
        /* 儀表板卡 */
        .dashboard-card { background-color: #1A1C24; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; border: 1px solid #333; }
        
        /* 對話氣泡 */
        .ai-bubble { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 3px solid #FF4B4B; margin: 10px 0; }

        input, textarea, .stSelectbox > div > div { background-color: #1F2229 !important; border: 1px solid #444 !important; color: white !important; }
        button[kind="primary"] { background-color: #FF4B4B !important; border: none; }
        #MainMenu, footer {visibility: hidden;}
        
        @media (max-width: 600px) {
            .status-bar { flex-direction: column; align-items: flex-start; gap: 10px; }
            .user-info-box { display: none; }
        }
    </style>
    """, unsafe_allow_html=True)

# 狀態列 (維持不變)
def render_status_bar(tier, energy, xp, engine_type, similarity=0, sim_hint="", sim_gain=0, is_guest=False, member_name=""):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"

    left_content = f"👉 您正在與 <span style='color:#FFD700; font-weight:bold;'>{member_name}</span> 對話中..." if is_guest else f"{icon} {tier_name}"
    
    xp_part = ""
    if not is_guest:
        tooltip = f"下一步：{sim_hint} (+{sim_gain}%)" if sim_gain > 0 else "已達目前等級上限"
        sim_part = f"""<div class="tooltip-container"><span style="color:#BBB">相似度 <span class="sim-score">{similarity}%</span></span><span class="tooltip-text">{tooltip}</span></div>"""
        xp_part = f"""{sim_part}&nbsp;&nbsp;<span style="color:#FFD700">⭐ XP: {xp}</span>"""

    engine_display = "" if is_guest else f"""<span style='margin-left:15px; color:#888;'>| {engine_name}</span>"""

    html = f"""
    <div class="status-bar">
        <div class="status-left">{left_content}</div>
        <div class="status-right">
            <span style="color:#FF4081; font-weight:bold;">❤️ 電量: {energy}</span>
            {xp_part}
            {engine_display}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# 題目卡片 (更新為深色版)
def render_question_card(question, index, total, hint=""):
    hint_html = f'<div class="q-hint">💡 提示：{hint}</div>' if hint else ""
    st.markdown(f"""
    <div class="question-card-active">
        <div class="q-progress">第 {index} 題 (共 {total} 題)</div>
        <div class="q-text">{question}</div>
        {hint_html}
    </div>
    """, unsafe_allow_html=True)

def render_history_card(q, a): st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")
def render_dashboard_card(title, content): st.metric(label=title, value=content)
