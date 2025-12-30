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

        /* --- 2. 頂部標題區 --- */
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
        
        /* 右上角用戶資訊區 (僅電腦版顯示) */
        .user-info-box {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            justify-content: center;
            height: 100%;
            margin-top: 10px;
        }
        .user-email {
            font-size: 14px !important;
            color: #888 !important;
            margin-bottom: 5px;
        }

        /* --- 3. 圓形進度條 (Stepper) --- */
        .step-wrapper { 
            display: flex; 
            justify-content: center; /* 電腦版置中 */
            align-items: center;
            margin: 30px 0;
            position: relative;
            width: 100%;
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
            position: absolute; top: 14px; left: 10%; right: 10%;
            height: 2px; background: #333; z-index: 1;
        }
        .step-active .step-circle {
            background: #FF4B4B; color: white; border-color: #FF4B4B;
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
        }
        .step-active .step-label { color: #FF4B4B !important; font-weight: bold; }
        .step-label { font-size: 12px; color: #888; }

        /* --- 4. 狀態列 --- */
        .status-bar {
            background: #1A1C24;
            border: 1px solid #333;
            padding: 12px 20px;
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px;
        }
        .status-text { font-size: 15px; font-weight: 500; }

        /* --- 5. 其他元件 --- */
        .stSelectbox > div > div, .stTextInput > div > div > input {
            background-color: #1F2229 !important;
            border: 1px solid #444 !important;
            color: white !important;
        }
        button[kind="primary"] {
            background-color: #FF4B4B !important; color: white !important; border: none;
        }
        
        .question-card-active { background-color: #1A1C24; padding: 20px; border-radius: 12px; border: 2px solid #2196F3; text-align: center; margin-bottom: 20px; }
        .q-text { font-size: 20px; color: #FFFFFF !important; font-weight: bold; margin: 10px 0; }
        .history-card { background-color: #262730; padding: 12px; border: 1px solid #444; border-radius: 8px; margin-bottom: 8px; }
        .dashboard-card { background-color: #1A1C24; padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; margin-bottom: 10px; }

        #MainMenu, footer {visibility: hidden;}

        /* =============================================
           6. 手機版專用修正 (Mobile RWD)
           ============================================= */
        @media only screen and (max-width: 600px) {
            
            /* (1) 隱藏 Header 右側資訊 */
            .user-info-box { display: none !important; }
            
            /* (2) 狀態列調整 */
            .status-bar { 
                flex-direction: column; 
                align-items: flex-start; 
                gap: 8px; 
                padding: 15px;
            }
            /* 加大狀態列文字 */
            .status-text { font-size: 16px !important; } 

            /* (3) Stepper 靠左 + 縮放調整 */
            .step-wrapper {
                justify-content: flex-start !important; /* 靠左 */
                transform: scale(0.9); /* 稍微縮小 */
                transform-origin: left center; /* 從左邊開始縮放 */
                margin: 20px 0 20px 0 !important;
                width: 110%; /* 寬度稍微拉大避免被切 */
            }
            .step-line-bg { display: none !important; }
            .step-item { padding: 0 10px !important; } /* 縮小圓圈間距 */
            
            /* (4) Tab 標籤字體加大 */
            button[data-baseweb="tab"] div {
                font-size: 16px !important; 
                padding: 10px 5px !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"]
    items_html = ""
    for i, name in enumerate(steps):
        is_active = "step-active" if i + 1 == current_step else ""
        items_html += f'<div class="step-item {is_active}"><div class="step-circle">{i+1}</div><div class="step-label">{name}</div></div>'
    
    st.markdown(f'<div class="step-wrapper"><div class="step-line-bg"></div>{items_html}</div>', unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"

    left = f"👋 訪客" if is_guest else f"{icon} {tier_name}"
    xp_html = f'<span style="margin-left:15px; color:#FFD700">⭐ XP: {xp}</span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-text" style="color:#FFF !important; font-weight:bold;">{left}</div>
        <div class="status-text">
            <span style="color:#FF4081; font-weight:bold;">❤️ 電量: {energy}</span>
            {xp_html}
            <span style="margin-left:15px; color:#888;">| {engine}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.info(f"🎙️ **Q{index}/{total}: {question}**\n\n請按下錄音回答...")

def render_history_card(q, a):
    st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")

def render_dashboard_card(title, content):
    st.metric(label=title, value=content)
