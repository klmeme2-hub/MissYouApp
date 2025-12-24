import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 1. 全局設定 --- */
        .stApp, p, h1, h2, h3, h4, h5, h6, label, span, div, li { 
            color: #FAFAFA !important; 
        }
        
        /* 調整主區塊寬度 (縮窄至 1000px) */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1000px !important;
        }

        /* --- 2. 頂部標題與用戶區 --- */
        h1 {
            font-size: 32px !important;
            margin-bottom: 0 !important;
            text-shadow: 0 0 15px rgba(124, 77, 255, 0.6);
        }
        .subtitle {
            font-size: 14px;
            color: #AAA !important;
            margin-top: 5px;
        }
        
        /* 右上角用戶資訊區 (關鍵修改：下移對齊副標題) */
        .user-info-box {
            text-align: right;
            margin-top: 45px; /* 強制下移，對齊左邊的副標題 */
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 10px; /* Email 和按鈕的間距 */
        }
        .user-email-text {
            font-size: 13px;
            color: #888 !important;
        }

        /* --- 3. 圓形進度條 (Stepper) 緊湊集中版 --- */
        .step-wrapper { 
            display: flex; 
            justify-content: center; /* 改為置中集中 */
            gap: 40px; /* 控制圓圈之間的距離，讓它們靠在一起 */
            margin: 5px 0 15px 0; /* 大幅縮小上下邊距 */
            padding: 10px 0;
            background: rgba(255,255,255,0.02);
            border-radius: 50px;
            border: 1px solid #333;
        }
        .step-item { text-align: center; position: relative; width: auto; /* 寬度自動，不再撐滿 */ }
        
        /* 連接線 (調整位置) */
        .step-item:not(:last-child)::after {
            content: ''; position: absolute; top: 12px; left: 40px; width: 40px; height: 2px;
            background: #333; z-index: -1;
        }
        
        .step-circle {
            width: 24px; height: 24px;
            border-radius: 50%; background: #222; margin: 0 auto 4px;
            display: flex; align-items: center; justify-content: center; 
            font-weight: bold; color: #888; font-size: 11px;
            border: 2px solid #444; transition: all 0.3s;
        }
        
        .step-active .step-circle {
            background: #FF4B4B; color: white; border-color: #FF4B4B;
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.6);
        }
        .step-label { font-size: 11px; color: #888; }
        .step-active .step-label { color: #FF4B4B; font-weight: bold; }

        /* --- 4. 狀態列 --- */
        .status-bar {
            background: linear-gradient(90deg, #1E1E1E 0%, #252525 100%);
            border: 1px solid #333;
            padding: 8px 20px;
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px; font-size: 13px;
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
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名/口頭禪", "安慰", "鼓勵", "詼諧", "完成"]
    st.markdown('<div class="step-wrapper">', unsafe_allow_html=True)
    cols = st.columns(len(steps)) # 雖然用 columns 但受 CSS flex gap 控制
    for i, (col, name) in enumerate(zip(cols, steps)):
        is_active = "step-active" if i + 1 == current_step else ""
        # 注意：這裡直接輸出 HTML 字串，不使用 st.columns 的寬度分配，完全靠 CSS flex
        pass 
    
    # 直接生成 HTML 結構
    html = ""
    for i, name in enumerate(steps):
        is_active = "step-active" if i + 1 == current_step else ""
        html += f"""
        <div class="step-item {is_active}">
            <div class="step-circle">{i+1}</div>
            <div class="step-label">{name}</div>
        </div>
        """
    st.markdown(f'<div class="step-wrapper">{html}</div>', unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "🚀 初級練習生", "intermediate": "🛡️ 中級守護者", "advanced": "🔥 高級刻錄師", "eternal": "♾️ 永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    
    # 更新 AI 圖示
    if tier in ['advanced', 'eternal']:
        engine_info = "✨ Gemini Pro"
    else:
        engine_info = "⚡ Gemini Flash"

    user_label = "👋 訪客" if is_guest else f"{tier_name}"
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
