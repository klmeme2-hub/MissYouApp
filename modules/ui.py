import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 1. 全局緊湊化設定 --- */
        .block-container {
            padding-top: 1rem !important; /* 縮小頂部留白 */
            padding-bottom: 2rem !important;
            max-width: 1000px; /* 內容集中 */
        }
        
        /* 強制白字 */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div, li { 
            color: #FAFAFA !important; 
        }
        
        /* --- 2. 標題區塊優化 --- */
        h1 {
            font-size: 28px !important; /* 縮小主標題 */
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            text-shadow: 0 0 15px rgba(124, 77, 255, 0.6);
        }
        .subtitle {
            font-size: 14px;
            color: #AAA !important;
            margin-top: -5px;
            margin-bottom: 10px;
        }

        /* --- 3. 圓形進度條 (Stepper) 極致緊湊版 --- */
        .step-wrapper { 
            display: flex; 
            justify-content: space-between; 
            margin: 10px 0 20px 0; /* 縮小上下邊距 */
            padding: 10px 0;
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
        }
        .step-item { text-align: center; width: 100%; position: relative; }
        
        /* 連接線 */
        .step-item:not(:last-child)::after {
            content: ''; position: absolute; top: 12px; left: 50%; width: 100%; height: 2px;
            background: #333; z-index: -1;
        }
        
        .step-circle {
            width: 26px; height: 26px; /* 縮小圓圈 */
            border-radius: 50%; background: #222; margin: 0 auto 4px;
            display: flex; align-items: center; justify-content: center; 
            font-weight: bold; color: #888; font-size: 12px;
            border: 2px solid #444; transition: all 0.3s;
        }
        
        .step-active .step-circle {
            background: #FF4B4B; color: white; border-color: #FF4B4B;
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.6);
        }
        .step-label { font-size: 11px; color: #888; }
        .step-active .step-label { color: #FF4B4B; font-weight: bold; }

        /* --- 4. 狀態列 (縮小版) --- */
        .status-bar {
            background: linear-gradient(90deg, #1E1E1E 0%, #252525 100%);
            border: 1px solid #333;
            padding: 8px 15px; /* 縮小內距 */
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 15px; 
            font-size: 13px;
        }
        .status-item { margin-left: 10px; color: #BBB !important; }
        
        /* --- 5. 右上角用戶資訊區 --- */
        .user-info-box {
            text-align: right;
            background: #1A1C24;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid #333;
            display: inline-block;
            float: right;
        }
        .user-email { font-size: 12px; color: #888 !important; margin-bottom: 4px; }

        /* --- 輸入框與按鈕 --- */
        input, textarea, .stSelectbox > div > div {
            background-color: #1F2229 !important; color: #FAFAFA !important; border: 1px solid #444 !important;
        }
        div[data-baseweb="popover"] li:hover { background-color: #FF4B4B !important; }
        
        /* 卡片 */
        .script-box { 
            background: #151515; padding: 15px; border-radius: 8px; 
            border-left: 3px solid #FFD700; font-size: 14px; line-height: 1.5; color: #DDD !important;
        }
        .ai-bubble {
            background-color: #262730; padding: 15px; border-radius: 10px;
            border-left: 3px solid #FF4B4B; margin: 10px 0; color: #E0E0E0 !important;
        }

        /* 隱藏 */
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
    tier_map = {"basic": "🚀 初級練習生", "intermediate": "🛡️ 中級守護者", "advanced": "🔥 高級刻錄師", "eternal": "♾️ 永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    user_label = "👋 訪客" if is_guest else f"{tier_name}"
    xp_html = f'<span class="status-item">⭐ XP: <span style="color:#FFD700">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-weight:bold; color:#FFF;">{user_label}</div>
        <div>
            <span class="status-item">❤️ 電量: <span style="color:#FF4081!important;">{energy}</span></span>
            {xp_html}
            <span class="status-item">| {engine_name}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""
    <div style="background:#1A1C24; padding:15px; border-radius:8px; border:1px solid #444; text-align:center; margin-bottom:10px;">
        <div style="color:#888; font-size:12px; margin-bottom:5px;">{title}</div>
        <div style="font-size:20px; font-weight:bold; color:#FAFAFA;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
