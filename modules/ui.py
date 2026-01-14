import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 1. 全局設定 --- */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div, li { 
            color: #FAFAFA !important; 
        }
        
        /* 調整主區塊寬度 */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 1000px !important;
        }
        
        hr { display: none !important; }
        .stElementContainer { margin-bottom: -15px !important; }
        div[data-testid="stButton"], div[data-testid="stSelectbox"] {
            margin-bottom: 5px !important;
        }

        /* --- 2. Header --- */
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
        
        .user-info-box {
            display: flex; flex-direction: column; align-items: flex-end; justify-content: center; height: 100%; margin-top: 10px;
        }
        .user-email { font-size: 14px !important; color: #888 !important; margin-bottom: 5px; }

        /* --- 3. 狀態列 (Status Bar) --- */
        .status-bar {
            background: #1A1C24;
            border: 1px solid #333;
            padding: 12px 20px;
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px;
        }
        .status-text { font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 15px; }
        
        /* 相似度 Tooltip */
        .tooltip-container { position: relative; display: inline-block; cursor: help; }
        .sim-score { color: #00E5FF; font-weight: bold; border-bottom: 1px dashed #00E5FF; }
        .tooltip-text {
            visibility: hidden; width: 200px; background-color: #333; color: #fff; text-align: center;
            border-radius: 6px; padding: 8px; position: absolute; z-index: 10;
            top: 120%; left: 50%; margin-left: -100px; opacity: 0; transition: opacity 0.3s;
            border: 1px solid #555; box-shadow: 0 4px 10px rgba(0,0,0,0.5); font-size: 12px !important;
        }
        .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

        /* --- 4. 輸入框與按鈕 --- */
        .stSelectbox > div > div, .stTextInput > div > div > input {
            background-color: #1F2229 !important; border: 1px solid #444 !important; color: white !important;
        }
        button[kind="primary"] {
            background-color: #FF4B4B !important; color: white !important; border: none;
        }
        
        /* 手機適配 */
        @media (max-width: 600px) {
            .user-info-box { display: none; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 8px; padding: 15px; }
            .tooltip-container .tooltip-text { left: 0; margin-left: 0; }
        }
    </style>
    """, unsafe_allow_html=True)

# 為了配合 member.py 的呼叫，這裡增加了 similarity 相關參數的預設值
def render_status_bar(tier, energy, xp, engine_type, similarity=0, sim_hint="", sim_gain=0, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    
    left = f"👋 訪客" if is_guest else f"{icon} {tier_name}"
    
    # 處理相似度顯示 (只在會員模式顯示)
    sim_html = ""
    if not is_guest:
        tooltip = f"下一步：{sim_hint} (+{sim_gain}%)" if sim_gain > 0 else "已達目前等級上限"
        sim_html = f"""<div class="tooltip-container"><span style="color:#BBB">聲音相似度 <span class="sim-score">{similarity}%</span></span><span class="tooltip-text">{tooltip}</span></div>"""

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
