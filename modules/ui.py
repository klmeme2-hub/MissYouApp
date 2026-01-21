import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* ==========================================
           EchoSoul Design System v3.0
           ========================================== */
        
        /* --- 1. 全局基礎 --- */
        .stApp { 
            background: linear-gradient(135deg, #0a0a0f 0%, #12121a 50%, #0d0d14 100%);
            color: #FAFAFA; 
            min-height: 100vh;
        }
        
        /* 文字樣式 */
        .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp li {
            color: #FAFAFA !important; 
            font-family: "Inter", "Source Sans Pro", sans-serif;
            line-height: 1.6;
        }
        
        .block-container { 
            padding-top: 1rem !important; 
            padding-bottom: 5rem !important; 
            max-width: 1000px !important; 
        }
        hr { display: none !important; }
        .stElementContainer { margin-bottom: -10px !important; }

        /* --- 2. 漸變與動畫定義 --- */
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 20px rgba(167, 139, 250, 0.3); }
            50% { box-shadow: 0 0 40px rgba(167, 139, 250, 0.5); }
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
        }
        
        @keyframes gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* --- 3. 狀態列 (Status Bar) --- */
        .status-bar {
            background: linear-gradient(135deg, rgba(30,32,44,0.8), rgba(26,28,36,0.9));
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(167, 139, 250, 0.3);
            padding: 14px 24px;
            border-radius: 12px; 
            display: flex; 
            justify-content: space-between;
            align-items: center; 
            margin-bottom: 25px; 
            width: 100%; 
            box-sizing: border-box;
            box-shadow: 0 4px 24px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        .status-bar:hover {
            border-color: rgba(167, 139, 250, 0.5);
            box-shadow: 0 6px 32px rgba(167, 139, 250, 0.15);
        }
        .status-left { font-size: 16px; font-weight: bold; color: #FFF; }
        .status-right { font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 15px; }
        
        /* Tooltip */
        .tooltip-container { position: relative; display: inline-block; cursor: help; }
        .sim-score { 
            color: #22D3EE; 
            font-weight: bold; 
            border-bottom: 1px dashed #22D3EE; 
            transition: color 0.3s;
        }
        .val-energy { 
            color: #F472B6; 
            font-weight: bold; 
            border-bottom: 1px dashed #F472B6; 
            cursor: help; 
        }
        
        .tooltip-text {
            visibility: hidden; 
            width: 200px; 
            background: linear-gradient(135deg, rgba(30,32,44,0.95), rgba(20,22,30,0.98));
            backdrop-filter: blur(10px);
            color: #fff; 
            text-align: center;
            border-radius: 8px; 
            padding: 10px; 
            position: absolute; 
            z-index: 10;
            top: 130%; 
            left: 50%; 
            margin-left: -100px; 
            opacity: 0; 
            transition: opacity 0.3s;
            border: 1px solid rgba(167, 139, 250, 0.3); 
            font-size: 12px !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

        /* --- 4. 輸入元件 --- */
        input, textarea, .stSelectbox > div > div { 
            background-color: rgba(31, 34, 41, 0.8) !important; 
            backdrop-filter: blur(5px);
            border: 1px solid rgba(100, 100, 120, 0.4) !important; 
            color: white !important; 
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        input:focus, textarea:focus {
            border-color: rgba(167, 139, 250, 0.6) !important;
            box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.15) !important;
        }
        
        /* 主按鈕 */
        button[kind="primary"] { 
            background: linear-gradient(135deg, #A78BFA, #8B5CF6) !important; 
            border: none !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(167, 139, 250, 0.4) !important;
        }
        
        /* --- 5. 卡片元件 --- */
        .question-card-active { 
            background: linear-gradient(135deg, rgba(30,32,44,0.7), rgba(26,28,36,0.8));
            backdrop-filter: blur(10px);
            padding: 30px; 
            border-radius: 16px; 
            border: 1px solid rgba(167, 139, 250, 0.2); 
            text-align: center; 
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        .question-card-active:hover {
            border-color: rgba(167, 139, 250, 0.4);
            transform: translateY(-3px);
        }
        .q-text { font-size: 24px; font-weight: 700; margin: 10px 0; color: #FFF; }
        .q-hint { font-size: 14px; color: #FCD34D; margin-top: 15px; font-weight: 500; }

        .history-card { 
            background: rgba(38, 39, 48, 0.6); 
            backdrop-filter: blur(5px);
            padding: 12px; 
            border-radius: 10px; 
            margin-bottom: 8px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .ai-bubble { 
            background: linear-gradient(135deg, rgba(38, 39, 48, 0.8), rgba(30, 32, 40, 0.9)); 
            backdrop-filter: blur(5px);
            padding: 15px; 
            border-radius: 12px; 
            border-left: 3px solid #A78BFA; 
            margin: 10px 0;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }

        #MainMenu, footer {visibility: hidden;}
        
        /* --- 6. Tab 分頁樣式 --- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 5px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 45px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 6px 6px 0 0;
            gap: 2px;
            padding: 10px 20px;
            color: #9ca3af; /* Gray-400 */
            transition: all 0.3s ease;
            font-weight: 500;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #E2E8F0; /* Gray-200 */
            background-color: rgba(255, 255, 255, 0.05);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(180deg, rgba(30, 32, 44, 0) 0%, rgba(167, 139, 250, 0.1) 100%);
            border-bottom: 2px solid #A78BFA;
            color: #A78BFA !important;
            font-weight: 700;
        }
        
        /* 移除預設的紅色線條 */
        .stTabs [data-baseweb="tab-highlight"] {
            display: none;
        }

        /* --- 7. 響應式設計 --- */
        @media (max-width: 600px) {
            .status-bar { flex-direction: column; align-items: flex-start; gap: 10px; padding: 12px 16px; }
            .user-info-box { display: none; }
            .tooltip-container .tooltip-text { left: 0; margin-left: 0; }
            
            /* Tab 在手機版可捲動 */
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: nowrap;
                overflow-x: auto;
                padding-bottom: 0px;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 10px 15px;
                flex-shrink: 0;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, similarity=0, sim_hint="", sim_gain=0, is_guest=False, member_name=""):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"

    left_content = f"👉 您正在與 <span style='color:#FFD700; font-weight:bold;'>{member_name}</span> 對話中..." if is_guest else f"{icon} {tier_name}"
    
    right_items = []
    energy_tooltip = f"約還可對話 {energy} 句"
    energy_html = f"""<div class="tooltip-container"><span>❤️ 電量: <span class="val-energy">{energy}</span></span><span class="tooltip-text">{energy_tooltip}</span></div>"""
    right_items.append(energy_html)

    if not is_guest:
        tooltip = f"下一步：{sim_hint} (+{sim_gain}%)" if sim_gain > 0 else "已達目前等級上限"
        sim_part = f"""<div class="tooltip-container" style="margin-left:15px;"><span style="color:#BBB">相似度 <span class="sim-score">{similarity}%</span></span><span class="tooltip-text">{tooltip}</span></div>"""
        xp_part = f"""<span style="margin-left:15px;">⭐ XP: <span style="color:#FFD700; font-weight:bold;">{xp}</span></span>"""
        right_items.append(sim_part)
        right_items.append(xp_part)
        engine_html = f"""<span style="margin-left:15px; color:#888; border-left:1px solid #444; padding-left:10px;">| {engine_name}</span>"""
        right_items.append(engine_html)

    right_content = "".join(right_items)
    html = f"""<div class="status-bar"><div class="status-left">{left_content}</div><div class="status-right">{right_content}</div></div>"""
    st.markdown(html, unsafe_allow_html=True)

def render_question_card(question, index, total, hint=""):
    hint_html = f'<div class="q-hint">💡 提示：{hint}</div>' if hint else ""
    st.markdown(f"""<div class="question-card-active"><div style="color:#888; font-size:12px; margin-bottom:5px;">第 {index} 題</div><div class="q-text">{question}</div>{hint_html}</div>""", unsafe_allow_html=True)

def render_history_card(q, a): st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")

# 【關鍵修復】使用 Inline Style 強制渲染卡片背景與邊框
def render_dashboard_card(title, content):
    st.markdown(f"""
    <div style="
        background-color: #1A1C24; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #444; 
        text-align: center; 
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="color: #94A3B8; font-size: 13px; margin-bottom: 5px;">{title}</div>
        <div style="font-size: 26px; font-weight: 700; color: #FAFAFA;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
