import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 全域設定：強制白字 (適應深色背景) --- */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div { 
            color: #FAFAFA !important; 
        }
        
        /* --- 輸入框優化 --- */
        input, textarea {
            color: #FAFAFA !important;
            background-color: #262730 !important;
            border: 1px solid #444 !important;
        }
        
        /* --- 下拉選單修復 --- */
        div[data-baseweb="select"] > div { 
            background-color: #262730 !important; 
            color: #FAFAFA !important; 
            border-color: #444 !important;
        }
        div[data-baseweb="popover"] li { 
            background-color: #262730 !important; 
            color: #FAFAFA !important; 
        }
        div[data-baseweb="popover"] li:hover { 
            background-color: #FF4B4B !important; 
            color: white !important;
        }

        /* --- AI 對話氣泡 --- */
        .ai-bubble {
            background-color: #262730; 
            padding: 20px; 
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
            border-left: 4px solid #FF4B4B; 
            margin: 15px 0; 
            color: #E0E0E0 !important; 
            font-size: 16px; 
            line-height: 1.6;
        }
        
        /* --- 狀態列 --- */
        .status-bar {
            background: linear-gradient(90deg, #1E1E1E 0%, #2D2D2D 100%);
            border: 1px solid #444;
            color: white !important;
            padding: 12px 20px; 
            border-radius: 10px;
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            margin-bottom: 25px; 
        }
        .status-item { margin-left: 15px; font-size: 14px; color: #B0B0B0 !important; }
        
        /* --- 卡片樣式 --- */
        .question-card, .dashboard-card { 
            background-color: #1A1C24; 
            padding: 20px; 
            border-radius: 12px; 
            border: 1px solid #FF4B4B; 
            text-align: center; 
            margin-bottom: 20px; 
        }
        .question-card-active {
            background-color: #1A1C24;
            padding: 20px;
            border-radius: 12px;
            border: 2px solid #FF4B4B;
            text-align: center;
            margin-bottom: 20px;
        }
        .q-text { 
            font-size: 20px; 
            color: #FFFFFF !important; 
            font-weight: bold; 
            margin: 10px 0;
        }
        
        /* --- 歷史回憶卡片 --- */
        .history-card { 
            background-color: #262730; 
            padding: 15px; 
            border: 1px solid #444; 
            border-radius: 8px; 
            margin-bottom: 10px; 
        }
        
        /* --- 腳本框 --- */
        .script-box { 
            background: #1E1E1E; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 15px 0; 
            border-left: 4px solid #FFD700; 
            color: #DDD !important;
        }

        /* 隱藏選單 */
        #MainMenu, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {
        "basic": "🔰 初級練習生", "intermediate": "🛡️ 中級守護者", 
        "advanced": "🔥 高級刻錄師", "eternal": "♾️ 永恆上鏈"
    }
    tier_name = tier_map.get(tier, tier)
    
    if tier in ['advanced', 'eternal']: engine_info = "🚀 Gemini Pro"
    else: engine_info = "⚡ Gemini Flash"

    user_label = "👋 親友訪客" if is_guest else f"👤 {tier_name}"
    xp_html = f'<span class="status-item">⭐ XP: <span style="color:#FF4B4B">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-size:16px;">{user_label}</div>
        <div>
            <span class="status-item">❤️ 電量: <span style="color:#FF4B4B">{energy}</span></span>
            {xp_html}
            <span class="status-item">| {engine_info}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""
    <div class="question-card-active">
        <div style="color:#888; font-size:12px; margin-bottom:5px;">PROGRESS {index}/{total}</div>
        <div class="q-text">{question}</div>
        <div style="font-size:13px; color:#AAA; margin-top:10px;">🎙️ 請按下錄音...</div>
    </div>
    """, unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""
    <div class="history-card">
        <b style="color:#FF4B4B;">Q: {q}</b><br>
        <span style="color:#CCC; font-size:13px;">{a[:40]}...</span>
    </div>
    """, unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""
    <div class="dashboard-card">
        <div style="color:#888; font-size:13px; margin-bottom:5px;">{title}</div>
        <div style="font-size:24px; font-weight:bold; color:#FAFAFA;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
