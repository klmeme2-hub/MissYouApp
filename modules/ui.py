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

        /* --- 2. Header --- */
        .header-title { font-size: 34px !important; font-weight: 700 !important; margin-bottom: 5px !important; }
        .header-subtitle { font-size: 16px !important; color: #B0B0B0 !important; font-weight: 400; }
        .user-info-box { display: flex; flex-direction: column; align-items: flex-end; justify-content: center; }

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
            box-sizing: border-box;
        }
        .status-left { font-size: 16px; font-weight: bold; color: #FFF; }
        .status-right { font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 15px; }
        
        /* Tooltip (通用) */
        .tooltip-container { position: relative; display: inline-block; cursor: help; }
        .sim-score { color: #00E5FF; font-weight: bold; border-bottom: 1px dashed #00E5FF; }
        .val-energy { color: #FF4081; font-weight: bold; border-bottom: 1px dashed #FF4081; cursor: help; }
        
        .tooltip-text {
            visibility: hidden; width: 180px; background-color: #333; color: #fff; text-align: center;
            border-radius: 6px; padding: 8px; position: absolute; z-index: 99;
            top: 130%; left: 50%; margin-left: -90px; opacity: 0; transition: opacity 0.3s;
            border: 1px solid #555; font-size: 12px !important; line-height: 1.4 !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        }
        .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

        /* --- 4. 其他元件 --- */
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
            .tooltip-container .tooltip-text { left: 0; margin-left: 0; }
        }
    </style>
    """, unsafe_allow_html=True)

# 增加 member_name 參數
def render_status_bar(tier, energy, xp, engine_type, similarity=0, sim_hint="", sim_gain=0, is_guest=False, member_name=""):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"

    # 左側文字邏輯修改
    if is_guest:
        # 訪客模式：顯示「您正在與 XX 對話中」
        left_content = f"👉 您正在與 <span style='color:#FFD700; font-weight:bold;'>{member_name}</span> 對話中..."
    else:
        # 會員模式：顯示等級
        left_content = f"{icon} {tier_name}"
    
    # 右側內容
    right_html = ""
    
    # 電量 Tooltip (計算剩餘句數，假設平均 1 電量 1 句)
    energy_tooltip = f"約還可對話 {energy} 句"
    energy_part = f"""
    <div class="tooltip-container">
        <span style="color:#FFF">❤️ 電量: <span class="val-energy">{energy}</span></span>
        <span class="tooltip-text">{energy_tooltip}</span>
    </div>
    """

    if is_guest:
        # 訪客模式：只顯示電量
        right_html = energy_part
    else:
        # 會員模式：顯示相似度、XP、引擎
        tooltip = f"下一步：{sim_hint} (+{sim_gain}%)" if sim_gain > 0 else "已達目前等級上限"
        sim_part = f"""<div class="tooltip-container"><span style="color:#BBB">相似度 <span class="sim-score">{similarity}%</span></span><span class="tooltip-text">{tooltip}</span></div>"""
        xp_part = f"""&nbsp;&nbsp;<span style="color:#FFD700">⭐ XP: {xp}</span>"""
        engine_part = f"""&nbsp;&nbsp;<span style="color:#888; border-left:1px solid #444; padding-left:10px;">| {engine_name}</span>"""
        
        right_html = f"""<div style="display:flex; align-items:center;">{sim_part}{xp_part}<span style="margin-left:15px;">{energy_part}</span>{engine_part}</div>"""

    # 最終渲染
    html = f"""<div class="status-bar"><div class="status-left">{left_content}</div><div class="status-right">{right_html}</div></div>"""
    
    st.markdown(html, unsafe_allow_html=True)

def render_question_card(question, index, total): st.info(f"🎙️ **Q{index}/{total}: {question}**")
def render_history_card(q, a): st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")
def render_dashboard_card(title, content): st.metric(label=title, value=content)
