import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 全域設定 --- */
        /* 強制重置字體顏色為淺色 (適應深色背景) */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div { 
            color: #FAFAFA !important; 
        }
        
        /* --- 下拉選單修復 (深色版) --- */
        /* 讓選單背景變深灰，文字變白 */
        div[data-baseweb="select"] > div { 
            background-color: #262730 !important; 
            color: #FAFAFA !important; 
            border-color: #4A4A4A !important;
        }
        div[data-baseweb="popover"] li { 
            background-color: #262730 !important; 
            color: #FAFAFA !important; 
        }
        div[data-baseweb="popover"] li:hover { 
            background-color: #FF4B4B !important; /* 滑過變紅色 */
            color: white !important;
        }
        
        /* --- 輸入框優化 --- */
        input, textarea {
            color: #FAFAFA !important;
            background-color: #262730 !important;
        }

        /* --- AI 對話氣泡 (深灰底 + 紅邊) --- */
        .ai-bubble {
            background-color: #262730; 
            padding: 20px; 
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
            border-left: 4px solid #FF4B4B; /* Streamlit Red */
            margin: 15px 0; 
            color: #E0E0E0 !important; 
            font-size: 16px; 
            line-height: 1.6;
        }
        
        /* --- 頂部狀態列 (玻璃質感) --- */
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
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        .status-item { 
            margin-left: 15px; 
            font-size: 14px; 
            color: #B0B0B0 !important;
        }
        .status-value {
            color: #FF4B4B !important;
            font-weight: bold;
        }
        
        /* --- 題目卡片 (Active) --- */
        .question-card { 
            background-color: #1A1C24; 
            padding: 25px; 
            border-radius: 12px; 
            border: 1px solid #FF4B4B; 
            text-align: center; 
            margin-bottom: 20px; 
            box-shadow: 0 0 15px rgba(255, 75, 75, 0.1); /* 紅色微光 */
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
            transition: transform 0.2s;
        }
        .history-card:hover {
            border-color: #FF4B4B;
            transform: translateX(5px);
        }
        
        /* --- 儀表板卡片 --- */
        .dashboard-card {
            background-color: #262730;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #333;
            margin-bottom: 10px;
            text-align: center;
        }
        
        /* --- 腳本框 --- */
        .script-box { 
            background: #1E1E1E; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 15px 0; 
            border-left: 4px solid #FFD700; /* 金色邊條區分 */
            color: #DDD !important;
            font-family: monospace;
        }

        /* 隱藏選單 */
        #MainMenu, footer {visibility: hidden;}
        
        /* 按鈕優化 */
        button[kind="primary"] {
            background-color: #FF4B4B !important;
            border: none !important;
            transition: all 0.3s !important;
        }
        button[kind="primary"]:hover {
            background-color: #FF2B2B !important;
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
        }
    </style>
    """, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {
        "basic": "🔰 初級練習生", "intermediate": "🛡️ 中級守護者", 
        "advanced": "🔥 高級刻錄師", "eternal": "♾️ 永恆上鏈"
    }
    tier_name = tier_map.get(tier, tier)
    
    # 判斷引擎
    if tier in ['advanced', 'eternal']:
        engine_info = "🚀 Gemini Pro"
    else:
        engine_info = "⚡ Gemini Flash"

    user_label = "👋 親友訪客" if is_guest else f"👤 {tier_name}"
    
    # 使用 f-string 插入 HTML，注意顏色 class
    xp_html = f'<span class="status-item">⭐ XP: <span class="status-value">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-size:16px;">{user_label}</div>
        <div>
            <span class="status-item">❤️ 電量: <span class="status-value">{energy}</span></span>
            {xp_html}
            <span class="status-item">| {engine_info}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""
    <div class="question-card">
        <div style="color:#888; font-size:12px; margin-bottom:5px; text-transform:uppercase; letter-spacing:1px;">PROGRESS {index}/{total}</div>
        <div class="q-text">{question}</div>
        <div style="font-size:13px; color:#AAA; margin-top:15px;">🎙️ 請按下錄音，自然地回答...</div>
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
        <div style="color:#888; font-size:13px; text-transform:uppercase; letter-spacing:1px; margin-bottom:5px;">{title}</div>
        <div style="font-size:24px; font-weight:bold; color:#FAFAFA;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
