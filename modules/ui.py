import streamlit as st

def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        /* =============================================
           1. 全局基礎設定 (Songer Dark Theme)
           ============================================= */
        .stApp {
            background-color: #030304; /* 極致深黑 */
            background-image: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #030304 40%); /* 頂部微弱紫光 */
            color: #FFFFFF;
            font-family: 'Inter', sans-serif;
        }
        
        /* 文字顏色統整 */
        p, h1, h2, h3, h4, h5, h6, label, span, div, li { 
            color: #E2E8F0 !important; /* 灰白色，比純白更舒適 */
        }
        
        /* 調整主區塊寬度 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 960px !important; /* 稍微縮窄，增加精緻感 */
        }
        
        /* 移除預設分隔線與間距 */
        hr { display: none !important; }
        .stElementContainer { margin-bottom: -10px !important; }

        /* =============================================
           2. 標題與 Header (大標題，漸層字)
           ============================================= */
        .header-title h1 {
            font-size: 42px !important;
            font-weight: 700 !important;
            letter-spacing: -1px;
            margin-bottom: 0px !important;
            background: linear-gradient(90deg, #FFFFFF 0%, #94A3B8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }
        .header-subtitle {
            font-size: 16px !important;
            color: #64748B !important; /* 較深的灰色 */
            margin-top: 8px !important;
            margin-bottom: 25px !important;
            font-weight: 400;
        }
        
        /* 右上角用戶資訊 */
        .user-info-container {
            display: flex;
            flex-direction: row;
            justify-content: flex-end;
            align-items: center;
            gap: 15px; 
            height: 100%;
            padding-top: 10px;
        }
        .user-email-text {
            font-size: 13px;
            color: #64748B !important;
            font-weight: 500;
        }

        /* =============================================
           3. 輸入框與選單 (極簡黑底微邊框)
           ============================================= */
        input, textarea, .stSelectbox > div > div {
            background-color: #0F1115 !important; 
            color: #F8FAFC !important;
            border: 1px solid #2D3039 !important;
            border-radius: 12px !important; /* 較大的圓角 */
            padding: 5px !important;
        }
        /* 聚焦時的紫色光暈 */
        .stTextInput > div > div > div:focus-within {
            border-color: #8B5CF6 !important;
            box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important;
        }

        /* 下拉選單列表 */
        div[data-baseweb="popover"] { background-color: #0F1115 !important; border: 1px solid #333; }
        div[data-baseweb="popover"] li:hover { background-color: #8B5CF6 !important; color: white !important; }

        /* =============================================
           4. 按鈕 (Songer 風格：漸層圓角)
           ============================================= */
        button[kind="primary"] {
            background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%) !important; /* 紫到藍 */
            border: none !important;
            color: white !important;
            font-weight: 600 !important;
            border-radius: 50px !important; /* 膠囊狀 */
            padding: 0.5rem 1.5rem !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
        }
        /* 次要按鈕 (登出等) */
        button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid #333 !important;
            color: #94A3B8 !important;
            border-radius: 50px !important;
        }

        /* =============================================
           5. 卡片與容器 (深灰微透)
           ============================================= */
        /* 狀態列 */
        .status-bar {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 12px 24px;
            border-radius: 16px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px; margin-top: 10px;
            backdrop-filter: blur(10px);
        }
        .status-item { margin-left: 20px; color: #94A3B8 !important; font-size: 13px; font-weight: 500; }
        .status-value { color: #A78BFA !important; font-weight: 700; } /* 淺紫色 */

        /* 題目卡片 */
        .question-card-active {
            background: linear-gradient(180deg, rgba(30, 27, 75, 0.5) 0%, rgba(15, 17, 21, 0.5) 100%);
            border: 1px solid #4338ca; /* 深靛藍邊框 */
            padding: 30px; border-radius: 20px;
            text-align: center; margin-bottom: 20px;
            box-shadow: 0 0 30px rgba(67, 56, 202, 0.1);
        }
        .q-text { font-size: 22px; color: #F8FAFC !important; font-weight: 600; margin: 15px 0; }

        /* 歷史回憶卡 */
        .history-card { 
            background-color: #0F1115; padding: 16px; 
            border: 1px solid #2D3039; border-radius: 12px; margin-bottom: 10px; 
            transition: border-color 0.2s;
        }
        .history-card:hover { border-color: #8B5CF6; }

        /* Stepper 進度條 */
        .step-wrapper { 
            display: flex; justify-content: center; align-items: center;
            gap: 0; margin: 20px 0 30px 0; position: relative;
        }
        .step-item { text-align: center; position: relative; z-index: 2; padding: 0 30px; }
        .step-circle {
            width: 26px; height: 26px;
            border-radius: 50%; background: #0F1115; margin: 0 auto 8px;
            display: flex; align-items: center; justify-content: center; 
            font-weight: 700; color: #475569; font-size: 12px;
            border: 2px solid #334155; transition: all 0.3s;
        }
        .step-line-bg {
            position: absolute; top: 12px; left: 50px; right: 50px; height: 2px;
            background: #1E293B; z-index: 1;
        }
        
        /* 啟動狀態 (紫色光暈) */
        .step-active .step-circle {
            background: #0F1115; color: #A78BFA; border-color: #8B5CF6;
            box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
        }
        .step-active .step-label { color: #E2E8F0; font-weight: 600; }
        .step-label { font-size: 11px; color: #64748B; }

        /* 對話氣泡 */
        .ai-bubble {
            background-color: #1E1B4B; /* 深靛藍底 */
            padding: 20px; border-radius: 16px;
            border: 1px solid #4338ca;
            margin: 15px 0; color: #E2E8F0 !important;
        }
        .dashboard-card {
            background-color: #0F1115; padding: 20px; border-radius: 16px;
            border: 1px solid #2D3039; text-align: center; margin-bottom: 15px;
        }

        #MainMenu, footer {visibility: hidden;}

        /* --- 手機版適配 --- */
        @media only screen and (max-width: 600px) {
            .header-title h1 { font-size: 28px !important; }
            .user-info-container { display: none !important; }
            .step-wrapper { transform: scale(0.8); width: 110%; margin-left: -5%; }
            .step-line-bg { display: none !important; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 8px; }
            .status-item { margin-left: 0 !important; margin-right: 15px; }
            .step-item { padding: 0 5px !important; }
        }
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"]
    items_html = ""
    for i, name in enumerate(steps):
        is_active = "step-active" if i + 1 == current_step else ""
        items_html += f"""
        <div class="step-item {is_active}">
            <div class="step-circle">{i+1}</div>
            <div class="step-label">{name}</div>
        </div>
        """
    st.markdown(f"""<div class="step-wrapper"><div class="step-line-bg"></div>{items_html}</div>""", unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    
    if engine_type == "elevenlabs": engine_info = "Gemini Pro"
    else: engine_info = "Gemini Flash"
    
    # 圖示處理
    if tier == "basic": icon = "🌱"
    elif tier == "intermediate": icon = "🛡️"
    elif tier == "advanced": icon = "🔥"
    else: icon = "♾️"

    user_label = "👋 訪客模式" if is_guest else f"{icon} {tier_name}"
    xp_html = f'<span class="status-item">⭐ XP <span class="status-value">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-weight:600; font-size:15px; color:#FFF;">{user_label}</div>
        <div>
            <span class="status-item">⚡ <span class="status-value" style="color:#F472B6!important;">{energy}</span></span>
            {xp_html}
            <span class="status-item" style="border-left:1px solid #444; padding-left:15px;">{engine_info}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""
    <div class="question-card-active">
        <div style="color:#94A3B8; font-size:11px; margin-bottom:8px; letter-spacing:1px; text-transform:uppercase;">Question {index} / {total}</div>
        <div class="q-text">{question}</div>
        <div style="font-size:13px; color:#64748B; margin-top:15px;">🎙️ 點擊下方錄音按鈕...</div>
    </div>
    """, unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""
    <div class="history-card">
        <b style="color:#A78BFA;">Q: {q}</b><br>
        <span style="color:#94A3B8; font-size:13px;">{a[:40]}...</span>
    </div>
    """, unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""
    <div class="dashboard-card">
        <div style="color:#94A3B8; font-size:12px; margin-bottom:5px;">{title}</div>
        <div style="font-size:24px; font-weight:700; color:#F8FAFC;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
