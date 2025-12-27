import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 1. 全局設定 --- */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div, li { 
            color: #FAFAFA !important; 
        }
        
        /* 修正標題被切掉的問題：加大頂部間距 */
        .block-container {
            padding-top: 3rem !important; /* 加大到 3rem */
            padding-bottom: 3rem !important;
            max-width: 1000px !important;
        }

        /* 移除分隔線 */
        hr { display: none !important; }
        
        /* --- 2. 移除強制不換行 (關鍵修正) --- */
        /* 
           我移除了之前導致手機版按鈕被擠扁的 flex-wrap: nowrap 設定。
           現在 Streamlit 會自動判斷：電腦版並排，手機版自動變成上下堆疊 (更適合手機操作)。
        */

        /* --- 3. 標題與副標題 --- */
        .header-title h1 {
            font-size: 32px !important;
            margin-bottom: 5px !important;
            padding: 0 !important;
            text-shadow: 0 0 15px rgba(124, 77, 255, 0.6);
            line-height: 1.2;
        }
        .header-subtitle {
            font-size: 16px !important;
            color: #CCC !important;
            margin-top: 0px !important;
            margin-bottom: 20px !important;
            font-weight: 400;
        }
        
        /* --- 4. 右上角用戶資訊區 (電腦版) --- */
        .user-info-container {
            display: flex;
            flex-direction: row;
            justify-content: flex-end;
            align-items: center;
            gap: 15px; 
            height: 100%;
            padding-top: 15px; 
        }
        .user-email-text {
            font-size: 13px;
            color: #888 !important;
            white-space: nowrap;
        }

        /* --- 5. 圓形進度條 (Stepper) --- */
        /* 電腦版樣式 */
        .step-wrapper { 
            display: flex; 
            justify-content: center;
            align-items: center;
            gap: 0; 
            margin: 10px 0 20px 0;
            position: relative;
        }
        .step-item { 
            text-align: center; position: relative; z-index: 2; padding: 0 25px;
        }
        .step-circle {
            width: 28px; height: 28px;
            border-radius: 50%; background: #1E1E1E; margin: 0 auto 5px;
            display: flex; align-items: center; justify-content: center; 
            font-weight: bold; color: #666; font-size: 12px;
            border: 2px solid #444; transition: all 0.3s;
        }
        .step-line-bg {
            position: absolute; top: 14px; left: 50px; right: 50px; height: 2px;
            background: #333; z-index: 1;
        }
        .step-active .step-circle {
            background: #FF4B4B; color: white; border-color: #FF4B4B;
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.6);
        }
        .step-active .step-label { color: #FF4B4B; font-weight: bold; }
        .step-label { font-size: 12px; color: #888; }

        /* --- 6. 狀態列 --- */
        .status-bar {
            background: linear-gradient(90deg, #1E1E1E 0%, #252525 100%);
            border: 1px solid #333;
            padding: 10px 20px;
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px; 
            font-size: 14px;
        }
        .status-item { margin-left: 15px; color: #BBB !important; }
        .status-value { color: #FFD700 !important; font-weight: bold; }

        /* --- 其他元件 --- */
        .question-card-active {
            background-color: #1A1C24; padding: 20px; border-radius: 12px;
            border: 2px solid #2196F3; text-align: center; margin-bottom: 20px;
        }
        .q-text { font-size: 20px; color: #FFFFFF !important; font-weight: bold; margin: 10px 0; }
        
        .history-card { 
            background-color: #262730; padding: 12px; border: 1px solid #444; 
            border-radius: 8px; margin-bottom: 8px; 
        }
        .script-box { 
            background: #1E1E1E; padding: 15px; border-radius: 8px; margin: 10px 0; 
            border-left: 4px solid #FFD700; color: #DDD !important;
        }
        .ai-bubble {
            background-color: #262730; padding: 15px; border-radius: 10px;
            border-left: 3px solid #FF4B4B; margin: 10px 0; color: #E0E0E0 !important;
        }
        .dashboard-card {
            background-color: #1A1C24; padding: 15px; border-radius: 10px;
            border: 1px solid #333; text-align: center; margin-bottom: 10px;
        }

        /* 輸入框與按鈕 */
        input, textarea, .stSelectbox > div > div {
            background-color: #1F2229 !important; color: #FAFAFA !important; border: 1px solid #444 !important;
        }
        div[data-baseweb="popover"] li:hover { background-color: #FF4B4B !important; }
        button[kind="primary"] { background-color: #FF4B4B !important; color: white !important; border: none; }
        
        #MainMenu, footer {visibility: hidden;}

        /* =============================================
           7. 手機版專用修正 (Mobile RWD)
           ============================================= */
        @media only screen and (max-width: 600px) {
            
            /* (1) 隱藏 Email，右上角只留登出按鈕 */
            .user-email-text { display: none !important; }
            .user-info-container { padding-top: 0 !important; }
            
            /* (2) 手機版標題再縮小一點，避免換行 */
            .header-title h1 { font-size: 26px !important; }

            /* (3) Stepper 縮放與隱藏線條 */
            .step-wrapper {
                transform: scale(0.85); /* 縮小 */
                margin: 0;
                width: 110%; margin-left: -5%; /* 修正置中 */
            }
            .step-line-bg { display: none !important; }
            .step-item { padding: 0 2px !important; }
            .step-circle { width: 24px; height: 24px; font-size: 10px; margin-bottom: 2px; }
            .step-label { font-size: 9px; }

            /* (4) 狀態列垂直排列 (避免擠在一起) */
            .status-bar {
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }
            .status-item { margin-left: 0 !important; margin-right: 10px; font-size: 12px; }
        }
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"]
    items_html = ""
    for i, name in enumerate(steps):
        is_active = "step-active" if i + 1 == current_step else ""
        items_html += f"""<div class="step-item {is_active}"><div class="step-circle">{i+1}</div><div class="step-label">{name}</div></div>"""
    st.markdown(f"""<div class="step-wrapper"><div class="step-line-bg"></div>{items_html}</div>""", unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    
    if engine_type == "elevenlabs": engine_info = "🚀 Gemini Pro"
    else: engine_info = "⚡ Gemini Flash"
    
    if tier == "basic": icon = "🚀"
    elif tier == "intermediate": icon = "🛡️"
    elif tier == "advanced": icon = "🔥"
    else: icon = "♾️"

    user_label = "👋 訪客" if is_guest else f"{icon} {tier_name}"
    xp_html = f'<span class="status-item">⭐ XP: <span class="status-value">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-weight:bold; color:#FFF;">{user_label}</div>
        <div>
            <span class="status-item">❤️ 電量: <span class="status-value" style="color:#FF4081!important;">{energy}</span></span>
            {xp_html}
            <span class="status-item">| {engine_info}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""<div class="question-card-active"><div style="color:#888; font-size:12px; margin-bottom:5px;">PROGRESS {index}/{total}</div><div class="q-text">{question}</div><div style="font-size:13px; color:#AAA; margin-top:10px;">🎙️ 請按下錄音...</div></div>""", unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""<div class="history-card"><b style="color:#FF4B4B;">Q: {q}</b><br><span style="color:#CCC; font-size:13px;">{a[:40]}...</span></div>""", unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""<div class="dashboard-card"><div style="color:#888; font-size:13px; margin-bottom:5px;">{title}</div><div style="font-size:24px; font-weight:bold; color:#FAFAFA;">{content}</div></div>""", unsafe_allow_html=True)
