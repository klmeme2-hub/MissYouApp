import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 全局設定 --- */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div, li { color: #FAFAFA !important; }
        .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; max-width: 1000px !important; }
        hr { display: none !important; }
        .stElementContainer { margin-bottom: -15px !important; }
        div[data-testid="stButton"], div[data-testid="stSelectbox"] { margin-bottom: 5px !important; }

        /* --- Header --- */
        .header-title h1 { font-size: 36px !important; margin-bottom: 5px !important; padding: 0 !important; text-shadow: 0 0 15px rgba(124, 77, 255, 0.6); line-height: 1.1; }
        .header-subtitle { font-size: 16px !important; color: #BBB !important; margin-top: 0px !important; margin-bottom: 15px !important; font-weight: 400; }
        .user-info-box { display: flex; flex-direction: column; align-items: flex-end; justify-content: center; height: 100%; margin-top: 10px; }
        .user-email { font-size: 14px !important; color: #888 !important; margin-bottom: 5px; }

        /* --- 狀態列 (Status Bar) --- */
        .status-bar {
            background: #1A1C24; border: 1px solid #333; padding: 12px 20px; border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;
        }
        .status-text { font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 15px; }
        
        /* 相似度指標樣式 */
        .sim-score { color: #00E5FF; font-weight: bold; cursor: help; position: relative; border-bottom: 1px dashed #00E5FF; }
        
        /* Tooltip (純 CSS 實作) */
        .tooltip-container { position: relative; display: inline-block; }
        .tooltip-container .tooltip-text {
            visibility: hidden; width: 220px; background-color: #333; color: #fff; text-align: center;
            border-radius: 6px; padding: 8px; position: absolute; z-index: 1;
            top: 150%; left: 50%; margin-left: -110px; opacity: 0; transition: opacity 0.3s;
            border: 1px solid #555; box-shadow: 0 4px 10px rgba(0,0,0,0.5); font-size: 12px !important; line-height: 1.4 !important;
        }
        .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

        /* --- 輸入框與按鈕 --- */
        .stSelectbox > div > div, .stTextInput > div > div > input { background-color: #1F2229 !important; border: 1px solid #444 !important; color: white !important; }
        button[kind="primary"] { background-color: #FF4B4B !important; color: white !important; border: none; }
        
        /* --- 其他元件 --- */
        .question-card-active { background-color: #1A1C24; padding: 20px; border-radius: 12px; border: 2px solid #2196F3; text-align: center; margin-bottom: 20px; }
        .q-text { font-size: 20px; color: #FFFFFF !important; font-weight: bold; margin: 10px 0; }
        .history-card { background-color: #262730; padding: 12px; border: 1px solid #444; border-radius: 8px; margin-bottom: 8px; }
        .script-box { background: #1E1E1E; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #FFD700; color: #DDD !important; }
        .ai-bubble { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 3px solid #FF4B4B; margin: 10px 0; color: #E0E0E0 !important; }
        .dashboard-card { background-color: #1A1C24; padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; margin-bottom: 10px; }

        #MainMenu, footer {visibility: hidden;}

        @media (max-width: 600px) {
            .user-info-box { display: none; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 8px; padding: 15px; }
            .tooltip-container .tooltip-text { left: 0; margin-left: 0; } /* 手機版 Tooltip 靠左 */
        }
    </style>
    """, unsafe_allow_html=True)

# Stepper 改為按鈕式，移除 render_stepper

def render_status_bar(tier, energy, xp, engine_type, similarity, sim_hint, sim_gain, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    
    left = f"👋 訪客" if is_guest else f"{icon} {tier_name}"
    
    # 相似度 Tooltip 邏輯
    if sim_gain > 0:
        tooltip_txt = f"下一步：{sim_hint}<br>可增加 {sim_gain}% 相似度"
    else:
        tooltip_txt = "恭喜！您已達到目前版本的最高相似度"
    
    # 組合 HTML
    sim_html = f"""
    <div class="tooltip-container">
        <span class="status-item">聲音相似度 <span class="sim-score">{similarity}%</span></span>
        <span class="tooltip-text">{tooltip_txt}</span>
    </div>
    """
    
    xp_html = f'<span style="margin-left:15px; color:#FFD700">⭐ XP: {xp}</span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-text" style="color:#FFF !important; font-weight:bold;">{left}</div>
        <div class="status-text">
            {sim_html}
            <span style="margin-left:15px; color:#FF4081; font-weight:bold;">❤️ 電量: {energy}</span>
            {xp_html}
            <span style="margin-left:15px; color:#888;">| {engine}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total): st.info(f"🎙️ **Q{index}/{total}: {question}**")
def render_history_card(q, a): st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")
def render_dashboard_card(title, content): st.metric(label=title, value=content)
