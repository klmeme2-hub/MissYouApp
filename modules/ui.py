import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* =============================================
           1. 版面結構調整 (空間壓縮核心)
           ============================================= */
        /* 縮減頂部留白，並將寬度設定為 1000px (比預設寬，比全螢幕窄) */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 1000px !important;
        }
        
        /* 標題區域緊湊化 */
        h1 { margin-bottom: 0px !important; padding-bottom: 0px !important; font-size: 2.5rem !important; }
        p { margin-bottom: 10px !important; }
        
        /* =============================================
           2. 基底配色 (深空黑 + 霓虹)
           ============================================= */
        .stApp {
            background-color: #0E1117;
            background-image: radial-gradient(circle at 50% 0%, #1c1c2e 0%, #0E1117 80%);
            background-attachment: fixed;
            color: #FAFAFA;
        }
        h1, h2, h3, h4, h5, h6, p, label, span, div { color: #FAFAFA; }

        /* =============================================
           3. 元件樣式
           ============================================= */
        /* 輸入框 */
        input[type="text"], input[type="password"], textarea {
            background-color: #1F2229 !important;
            border: 1px solid #444 !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
        }
        
        /* 下拉選單 */
        div[data-baseweb="select"] > div {
            background-color: #1F2229 !important;
            border-color: #444 !important;
            color: #FFFFFF !important;
        }
        div[data-baseweb="popover"], div[data-baseweb="menu"] {
            background-color: #1F2229 !important;
            border: 1px solid #555 !important;
        }
        div[data-baseweb="option"] { color: white !important; }

        /* 按鈕 */
        button[kind="primary"] {
            background: linear-gradient(45deg, #FF4B4B, #FF9100) !important;
            border: none !important;
            color: white !important;
            font-weight: bold !important;
            box-shadow: 0 4px 10px rgba(255, 75, 75, 0.3);
        }

        /* =============================================
           4. 狀態列與卡片 (緊湊化)
           ============================================= */
        .status-bar {
            background: linear-gradient(90deg, #1E1E1E 0%, #2D2D2D 100%);
            border: 1px solid #444;
            padding: 8px 20px; /* 縮減高度 */
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 15px; /* 縮減下邊距 */
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            border-left: 4px solid #00E5FF;
        }
        .status-item { margin-left: 15px; font-size: 14px; color: #DDD !important; }
        
        /* 圓形進度條 (縮減高度) */
        .step-wrapper { 
            display: flex; justify-content: space-between; 
            margin: 10px 0; /* 大幅縮減上下邊距 */
            padding: 0 20px;
        }
        .step-item { text-align: center; width: 100%; position: relative; }
        .step-circle {
            width: 30px; height: 30px; /* 稍微縮小 */
            border-radius: 50%; background: #444; margin: 0 auto 4px;
            display: flex; align-items: center; justify-content: center; font-weight: bold; color: #BBB;
            border: 2px solid #666; transition: all 0.3s;
            font-size: 14px;
        }
        .step-active .step-circle { background: #FF4B4B; color: white; border-color: #FF4B4B; box-shadow: 0 0 8px rgba(255, 75, 75, 0.5); }
        .step-label { font-size: 11px; color: #888; }
        .step-active .step-label { color: #FF4B4B; font-weight: bold; }

        /* 題目卡片 */
        .question-card-active {
            background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0.02) 100%);
            border: 1px solid #2196F3;
            box-shadow: 0 0 10px rgba(33, 150, 243, 0.2);
            padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 15px;
        }
        .q-text { font-size: 20px; color: #FFF !important; font-weight: 600; margin: 10px 0; }
        
        /* 儀表板卡片 */
        .dashboard-card {
            background-color: #1A1C24;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #444;
            text-align: center;
            margin-bottom: 10px;
        }

        /* 歷史卡片 */
        .history-card {
            background-color: #262730; padding: 10px; border: 1px solid #444; 
            border-radius: 6px; margin-bottom: 8px;
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
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    user_label = "👋 訪客模式" if is_guest else f"{tier_name}"
    xp_html = f'<span class="status-item">⭐ XP: <span style="color:#FFD700; font-weight:bold;">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-size:16px; font-weight:bold; color:#FFF;">{user_label}</div>
        <div style="text-align:right;">
            <span class="status-item">❤️ 電量: <span style="color:#FF4081; font-weight:bold;">{energy}</span></span>
            {xp_html}
            <span class="status-item">| <span style="color:#00E5FF;">🚀 {engine_name}</span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""
    <div class="question-card-active">
        <div style="color:#00E5FF; font-size:12px; margin-bottom:5px; letter-spacing:2px; text-transform:uppercase;">Processing {index}/{total}</div>
        <div class="q-text">{question}</div>
        <div style="font-size:13px; color:#AAA; margin-top:10px;">🎙️ 點擊下方按鈕錄音...</div>
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
        <div style="color:#888; font-size:12px; text-transform:uppercase; letter-spacing:1px; margin-bottom:5px;">{title}</div>
        <div style="font-size:24px; font-weight:bold; color:#FAFAFA;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
