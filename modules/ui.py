import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* =============================================
           1. 全局基礎設定 (電腦/手機通用)
           ============================================= */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div, li { 
            color: #FAFAFA !important; 
        }
        
        /* 電腦版寬度設定 */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 3rem !important;
            max-width: 1000px !important;
        }

        /* 移除所有預設分隔線 */
        hr { display: none !important; }
        
        /* 縮小所有 Streamlit 元件的預設垂直間距 (關鍵！) */
        .stElementContainer {
            margin-bottom: -15px !important; /* 讓元件靠得非常近 */
        }
        /* 針對按鈕和輸入框稍微放寬一點，避免重疊 */
        div[data-testid="stButton"], div[data-testid="stSelectbox"] {
            margin-bottom: 5px !important;
        }

        /* --- 2. 元件樣式 (Header, Card, etc.) --- */
        .header-title h1 {
            font-size: 32px !important;
            margin-bottom: 0 !important;
            padding: 0 !important;
            text-shadow: 0 0 15px rgba(124, 77, 255, 0.6);
            line-height: 1.2;
        }
        .header-subtitle {
            font-size: 16px !important;
            color: #CCC !important;
            margin-top: 5px !important;
            margin-bottom: 20px !important;
            font-weight: 400;
        }
        
        /* 右上角用戶資訊區 (電腦版) */
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

        /* 狀態列 */
        .status-bar {
            background: linear-gradient(90deg, #1E1E1E 0%, #252525 100%);
            border: 1px solid #333;
            padding: 10px 20px;
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px; font-size: 14px;
        }
        .status-item { margin-left: 15px; color: #BBB !important; }
        .status-value { color: #FFD700 !important; font-weight: bold; }

        /* Stepper (電腦版) */
        .step-wrapper { 
            display: flex; justify-content: center; align-items: center;
            gap: 0; margin: 15px 0; position: relative;
            transform-origin: top center; /* 縮放錨點 */
        }
        .step-item { text-align: center; position: relative; z-index: 2; padding: 0 25px; }
        .step-circle {
            width: 28px; height: 28px; border-radius: 50%; background: #1E1E1E; margin: 0 auto 5px;
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

        /* 輸入框與按鈕 */
        input, textarea, .stSelectbox > div > div {
            background-color: #1F2229 !important; color: #FAFAFA !important; border: 1px solid #444 !important;
        }
        div[data-baseweb="popover"] li:hover { background-color: #FF4B4B !important; }
        button[kind="primary"] { background-color: #FF4B4B !important; color: white !important; border: none; }
        
        /* 隱藏 */
        #MainMenu, footer {visibility: hidden;}

        /* =============================================
           3. 手機版專用修正 (Mobile RWD) - 針對 < 600px 螢幕
           ============================================= */
        @media only screen and (max-width: 600px) {
            
            /* (1) 頂部縮小 */
            .header-title h1 { font-size: 24px !important; }
            .header-subtitle { font-size: 12px !important; margin-bottom: 5px !important; }
            
            /* (2) 隱藏 Email，只保留按鈕 */
            .user-email-text { display: none !important; }
            .user-info-container { padding-top: 0 !important; }
            
            /* (3) 強制「控制台區」並排顯示 (解決浪費版面) */
            /* Streamlit 預設在手機會把 columns 變成垂直堆疊，這裡強制改回水平 */
            [data-testid="stHorizontalBlock"] {
                flex-wrap: nowrap !important; /* 禁止換行 */
                gap: 5px !important;
            }
            [data-testid="column"] {
                min-width: 0 !important; /* 允許縮到最小 */
                width: auto !important;
            }
            
            /* (4) Tab 標籤字體縮小 */
            button[data-baseweb="tab"] div {
                font-size: 14px !important;
                padding: 5px 8px !important;
            }
            
            /* (5) Stepper 整體縮小 (0.7倍) 且隱藏連接線 */
            .step-wrapper {
                transform: scale(0.75); /* 整體縮小 */
                margin: -10px 0 0px 0 !important; /* 調整縮放後的留白 */
                width: 120%; /* 放大容器寬度以免縮放後被裁切 */
                margin-left: -10%; /* 修正置中 */
            }
            .step-line-bg { display: none !important; } /* 隱藏線條讓畫面更乾淨 */
            .step-item { padding: 0 5px !important; } /* 極致縮小間距 */
            
            /* (6) 狀態列變成垂直堆疊 */
            .status-bar {
                flex-direction: column;
                align-items: flex-start;
                padding: 10px;
                gap: 5px;
            }
            .status-item { margin-left: 0 !important; margin-right: 10px; font-size: 12px; }
        }
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"] # 縮短文字以適應手機
    items_html = ""
    for i, name in enumerate(steps):
        is_active = "step-active" if i + 1 == current_step else ""
        items_html += f"""<div class="step-item {is_active}"><div class="step-circle">{i+1}</div><div class="step-label">{name}</div></div>"""
    st.markdown(f"""<div class="step-wrapper"><div class="step-line-bg"></div>{items_html}</div>""", unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    
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
            <span class="status-item">| {engine_name}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ... (其他的 render_card 函數維持不變) ...
def render_question_card(question, index, total):
    st.markdown(f"""<div class="question-card-active"><div style="color:#888; font-size:12px; margin-bottom:5px;">PROGRESS {index}/{total}</div><div class="q-text">{question}</div><div style="font-size:13px; color:#AAA; margin-top:10px;">🎙️ 請按下錄音...</div></div>""", unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""<div class="history-card"><b style="color:#FF4B4B;">Q: {q}</b><br><span style="color:#CCC; font-size:13px;">{a[:40]}...</span></div>""", unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""<div class="dashboard-card"><div style="color:#888; font-size:13px; margin-bottom:5px;">{title}</div><div style="font-size:24px; font-weight:bold; color:#FAFAFA;">{content}</div></div>""", unsafe_allow_html=True)
