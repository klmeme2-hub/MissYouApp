import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 全域設定：強制白字 (適應深色背景) --- */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div, li { 
            color: #FAFAFA !important; 
        }
        
        /* --- 輸入框與選單優化 --- */
        input, textarea, div[data-baseweb="select"] > div, div[data-baseweb="popover"] li {
            color: #FAFAFA !important;
            background-color: #262730 !important;
            border-color: #444 !important;
        }
        
        /* 選單滑過變色 */
        div[data-baseweb="popover"] li:hover { 
            background-color: #FF4B4B !important; 
            color: white !important;
        }

        /* --- 圓形進度條 (Stepper) --- */
        .step-wrapper { display: flex; justify-content: space-between; margin: 20px 0; }
        .step-item { text-align: center; width: 100%; position: relative; }
        .step-circle {
            width: 35px; height: 35px; border-radius: 50%; background: #444; margin: 0 auto 8px;
            display: flex; align-items: center; justify-content: center; font-weight: bold; color: #BBB;
            border: 2px solid #666; transition: all 0.3s;
        }
        .step-active .step-circle { background: #FF4B4B; color: white; border-color: #FF4B4B; box-shadow: 0 0 10px rgba(255, 75, 75, 0.5); }
        .step-label { font-size: 13px; color: #888; }
        .step-active .step-label { color: #FF4B4B; font-weight: bold; }

        /* --- 狀態列 (玻璃質感) --- */
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
        .status-item { margin-left: 15px; font-size: 14px; color: #DDD !important; }
        
        /* --- 卡片與氣泡 --- */
        .ai-bubble {
            background-color: #262730; 
            padding: 20px; 
            border-radius: 15px;
            border-left: 4px solid #FF4B4B; 
            margin: 15px 0; 
            color: #E0E0E0 !important;
        }
        
        .question-card, .dashboard-card { 
            background-color: #1A1C24; padding: 20px; border-radius: 12px; 
            border: 1px solid #444; text-align: center; margin-bottom: 20px; 
        }
        .question-card-active {
            background-color: #1A1C24; padding: 20px; border-radius: 12px;
            border: 2px solid #FF4B4B; text-align: center; margin-bottom: 20px;
        }
        .q-text { font-size: 20px; color: #FFFFFF !important; font-weight: bold; margin: 10px 0; }
        
        .history-card { 
            background-color: #262730; padding: 15px; border: 1px solid #444; 
            border-radius: 8px; margin-bottom: 10px; 
        }
        
        .script-box { 
            background: #1E1E1E; padding: 20px; border-radius: 8px; margin: 15px 0; 
            border-left: 4px solid #FFD700; color: #DDD !important; font-family: monospace;
        }

        /* 按鈕與其他 */
        button[kind="primary"] { background-color: #FF4B4B !important; color: white !important; border: none; }
        #MainMenu, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名/口頭禪", "安慰", "鼓勵", "詼諧", "完成"]
    st.markdown('<div class="step-wrapper">', unsafe_allow_html=True)
    cols = st.columns(len(steps))
    for i, (col, name) in enumerate(zip(cols, steps)):
        is_active = "step-active" if i + 1 == current_step else ""
        col.markdown(f"""
        <div class="step-item {is_active}">
            <div class="step-circle">{i+1}</div>
            <div class="step-label">{name}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {
        "basic": "🔰 初級練習生", "intermediate": "🛡️ 中級守護者", 
        "advanced": "🔥 高級刻錄師", "eternal": "♾️ 永恆上鏈"
    }
    tier_name = tier_map.get(tier, tier)
    engine_name = "🚀 Gemini Pro" if engine_type == "elevenlabs" else "⚡ Gemini Flash"
    user_label = "👋 親友訪客" if is_guest else f"👤 {tier_name}"
    xp_html = f'<span class="status-item">⭐ XP: <span style="color:#FFD700">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-size:16px;">{user_label}</div>
        <div>
            <span class="status-item">❤️ 電量: <span style="color:#FF4B4B">{energy}</span></span>
            {xp_html}
            <span class="status-item">| {engine_name}</span>
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
