import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 核心基底：深空黑 --- */
        .stApp {
            background-color: #0E1117;
            background-image: radial-gradient(circle at 50% 0%, #1c1c2e 0%, #0E1117 70%);
            color: #FAFAFA;
        }
        
        /* --- 全域文字與元件修正 --- */
        p, h1, h2, h3, h4, h5, h6, label, span, div, li { color: #FAFAFA !important; }
        
        /* --- 輸入框與選單 (科技感深灰) --- */
        input, textarea, .stSelectbox > div > div {
            background-color: #1F2229 !important;
            color: #FAFAFA !important;
            border: 1px solid #333 !important;
            border-radius: 8px !important;
        }
        /* 下拉選單列表 */
        div[data-baseweb="popover"] { background-color: #1F2229 !important; border: 1px solid #444; }
        div[data-baseweb="popover"] li { color: #FFF !important; }
        div[data-baseweb="popover"] li:hover { background-color: #7C4DFF !important; }

        /* --- 頂部狀態列 (HUD 風格) --- */
        .status-bar {
            background: rgba(30, 30, 40, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px 25px; 
            border-radius: 12px;
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            margin-bottom: 30px; 
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            border-left: 4px solid #00E5FF; /* Cyan Accent */
        }
        .status-item { margin-left: 20px; font-size: 14px; color: #B0BEC5 !important; letter-spacing: 0.5px; }
        .status-value { color: #00E5FF !important; font-weight: bold; text-shadow: 0 0 10px rgba(0, 229, 255, 0.5); }
        
        /* --- 玻璃擬態卡片 (共用) --- */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.4);
            border-color: rgba(255, 255, 255, 0.2);
        }

        /* --- 題目卡片 (Active) --- */
        .question-card-active {
            background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0.02) 100%);
            border: 1px solid #2196F3;
            box-shadow: 0 0 15px rgba(33, 150, 243, 0.2);
            padding: 25px; border-radius: 16px; text-align: center; margin-bottom: 20px;
        }
        .q-text { font-size: 22px; color: #FFF !important; font-weight: 600; margin: 15px 0; letter-spacing: 1px; }

        /* --- AI 對話氣泡 --- */
        .ai-bubble {
            background: linear-gradient(90deg, #1E1E2E 0%, #252535 100%);
            padding: 20px; border-radius: 0 15px 15px 15px;
            border-left: 3px solid #7C4DFF; /* Purple Accent */
            margin: 15px 0; color: #E0E0E0 !important; font-size: 16px; line-height: 1.6;
        }

        /* --- 圓形進度條 (Stepper) --- */
        .step-wrapper { display: flex; justify-content: space-between; margin: 30px 0; padding: 0 10px; }
        .step-item { text-align: center; width: 100%; position: relative; z-index: 1; }
        
        /* 連接線 */
        .step-item:not(:last-child)::after {
            content: ''; position: absolute; top: 15px; left: 50%; width: 100%; height: 2px;
            background: #333; z-index: -1;
        }
        
        .step-circle {
            width: 32px; height: 32px; border-radius: 50%; background: #1E1E1E; margin: 0 auto 8px;
            display: flex; align-items: center; justify-content: center; font-weight: bold; color: #666;
            border: 2px solid #444; transition: all 0.3s;
        }
        
        .step-active .step-circle {
            background: #7C4DFF; color: white; border-color: #7C4DFF;
            box-shadow: 0 0 15px rgba(124, 77, 255, 0.6);
        }
        .step-active .step-label { color: #7C4DFF; font-weight: bold; }
        .step-label { font-size: 12px; color: #888; margin-top: 5px; }

        /* --- 按鈕美化 (Glow Effect) --- */
        button[kind="primary"] {
            background: linear-gradient(45deg, #FF4B4B, #FF9100) !important;
            border: none !important;
            color: white !important;
            font-weight: bold !important;
            transition: all 0.3s !important;
        }
        button[kind="primary"]:hover {
            box-shadow: 0 0 15px rgba(255, 75, 75, 0.6) !important;
            transform: scale(1.02);
        }
        
        /* 隱藏選單 */
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
        "basic": "🚀 初級練習生", "intermediate": "🛡️ 中級守護者", 
        "advanced": "🔥 高級刻錄師", "eternal": "♾️ 永恆上鏈"
    }
    tier_name = tier_map.get(tier, tier)
    
    if tier in ['advanced', 'eternal']: engine_info = "Gemini Pro (Pro)"
    else: engine_info = "Gemini Flash"

    user_label = "👋 訪客模式" if is_guest else f"{tier_name}"
    xp_html = f'<span class="status-item">⭐ XP: <span class="status-value">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-size:16px; font-weight:bold; color:#FFF;">{user_label}</div>
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
        <div style="color:#888; font-size:12px; margin-bottom:5px; letter-spacing:2px;">PROGRESS {index}/{total}</div>
        <div class="q-text">{question}</div>
        <div style="font-size:13px; color:#AAA; margin-top:15px;">🎙️ 點擊下方錄音，開始鎸刻...</div>
    </div>
    """, unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""
    <div class="glass-card" style="padding:15px; margin-bottom:10px;">
        <b style="color:#00E5FF;">Q: {q}</b><br>
        <span style="color:#CCC; font-size:13px;">{a[:40]}...</span>
    </div>
    """, unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;">
        <div style="color:#888; font-size:12px; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">{title}</div>
        <div style="font-size:26px; font-weight:bold; color:#FAFAFA; text-shadow:0 0 10px rgba(255,255,255,0.2);">{content}</div>
    </div>
    """, unsafe_allow_html=True)
