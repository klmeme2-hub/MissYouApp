import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* =============================================
           1. 暴力全域設定 (Force Global Styles)
           ============================================= */
        
        /* 強制背景 (覆蓋 stApp) */
        [data-testid="stAppViewContainer"] {
            background-color: #0E1117;
            background-image: radial-gradient(circle at 50% 0%, #1c1c2e 0%, #0E1117 80%);
            background-attachment: fixed;
        }
        
        /* 強制所有文字變白 (使用萬用選擇器) */
        [data-testid="stAppViewContainer"] * {
            color: #FAFAFA !important;
            font-family: 'Helvetica Neue', sans-serif;
        }

        /* =============================================
           2. 輸入元件強制黑底白字
           ============================================= */
        
        /* 輸入框本體 */
        input[type="text"], textarea {
            background-color: #1F2229 !important;
            color: #FFFFFF !important;
            border: 1px solid #444 !important;
            border-radius: 8px !important;
        }
        
        /* 下拉選單容器 */
        div[data-baseweb="select"] > div {
            background-color: #1F2229 !important;
            border-color: #444 !important;
            color: #FFFFFF !important;
        }
        
        /* 下拉選單文字 */
        div[data-baseweb="select"] span {
            color: #FFFFFF !important;
        }

        /* 下拉選單彈出層 */
        div[data-baseweb="menu"], div[data-baseweb="popover"] {
            background-color: #1F2229 !important;
            border: 1px solid #555 !important;
        }
        
        /* 修正 Placeholder 顏色 (讓提示文字看得到) */
        ::placeholder {
            color: #888 !important;
            opacity: 1;
        }

        /* =============================================
           3. 按鈕發光特效 (Neon Glow)
           ============================================= */
        
        /* Primary Button (紅色那顆) */
        button[kind="primary"] {
            background: linear-gradient(45deg, #FF4B4B, #FF9100) !important;
            border: none !important;
            color: white !important;
            font-weight: bold !important;
            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4) !important;
            transition: all 0.3s ease !important;
        }
        button[kind="primary"]:hover {
            transform: scale(1.05);
            box-shadow: 0 0 25px rgba(255, 75, 75, 0.8) !important;
        }

        /* Secondary Button (普通按鈕) */
        button[kind="secondary"] {
            background-color: #262730 !important;
            border: 1px solid #555 !important;
            color: #EEE !important;
        }
        button[kind="secondary"]:hover {
            border-color: #FF4B4B !important;
            color: #FF4B4B !important;
        }

        /* =============================================
           4. 分頁 Tab 優化
           ============================================= */
        
        /* Tab 未選中 */
        button[data-baseweb="tab"] {
            background-color: transparent !important;
        }
        /* Tab 文字顏色 */
        button[data-baseweb="tab"] > div {
            color: #888 !important;
        }
        /* Tab 選中時 */
        button[data-baseweb="tab"][aria-selected="true"] > div {
            color: #FF4B4B !important;
        }
        /* Tab 下底線 */
        button[data-baseweb="tab"][aria-selected="true"] {
            border-bottom: 3px solid #FF4B4B !important;
        }

        /* =============================================
           5. 自定義元件樣式 (HTML Rendered)
           ============================================= */
        
        /* 狀態列 HUD */
        .status-bar {
            background: rgba(30, 30, 40, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-left: 4px solid #00E5FF;
            padding: 15px 20px; 
            border-radius: 12px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        /* 題目卡片 */
        .question-card-active {
            background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0.02) 100%);
            border: 1px solid #2196F3;
            box-shadow: 0 0 15px rgba(33, 150, 243, 0.2);
            padding: 25px; border-radius: 16px; text-align: center; margin-bottom: 20px;
        }
        
        /* 歷史卡片 */
        .history-card {
            background-color: rgba(255,255,255,0.05);
            border: 1px solid #444;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }

        /* 隱藏選單 */
        #MainMenu, footer, header {visibility: hidden;}
        
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名/口頭禪", "安慰", "鼓勵", "詼諧", "完成"]
    st.markdown('<div style="display:flex; justify-content:space-between; margin:20px 0;">', unsafe_allow_html=True)
    cols = st.columns(len(steps))
    for i, (col, name) in enumerate(zip(cols, steps)):
        active_color = "#FF4B4B" if i + 1 <= current_step else "#444"
        text_color = "#FFF" if i + 1 <= current_step else "#666"
        border = f"2px solid {active_color}"
        shadow = f"0 0 15px {active_color}80" if i + 1 == current_step else "none"
        
        col.markdown(f"""
        <div style="text-align:center;">
            <div style="width:35px; height:35px; border-radius:50%; background:#1E1E1E; border:{border}; margin:0 auto; display:flex; align-items:center; justify-content:center; color:{text_color}; font-weight:bold; box-shadow:{shadow};">
                {i+1}
            </div>
            <div style="font-size:12px; color:{text_color}; margin-top:8px;">{name}</div>
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
    xp_html = f'<span style="color:#B0BEC5; margin-right:10px;">⭐ XP: <b style="color:#FFD700">{xp}</b></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-size:18px; font-weight:bold; color:#FFF;">{user_label}</div>
        <div style="text-align:right;">
            <span style="color:#B0BEC5; margin-right:10px;">❤️ 電量: <b style="color:#FF4081">{energy}</b></span>
            {xp_html}
            <span style="color:#666;">|</span>
            <span style="color:#00E5FF; margin-left:10px;">🚀 {engine_name}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""
    <div class="question-card-active">
        <div style="color:#00E5FF; font-size:12px; margin-bottom:10px; letter-spacing:2px; text-transform:uppercase;">Processing {index}/{total}</div>
        <div style="font-size:24px; color:#FFF; font-weight:bold; margin:15px 0;">{question}</div>
        <div style="font-size:13px; color:#AAA; margin-top:15px;">🎙️ 點擊下方按鈕錄音...</div>
    </div>
    """, unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""
    <div class="history-card">
        <b style="color:#00E5FF;">Q: {q}</b><br>
        <span style="color:#CCC; font-size:13px;">{a[:40]}...</span>
    </div>
    """, unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""
    <div style="background:#1F2229; padding:20px; border-radius:10px; border:1px solid #333; text-align:center; margin-bottom:10px;">
        <div style="color:#888; font-size:12px; margin-bottom:5px;">{title}</div>
        <div style="font-size:24px; font-weight:bold; color:#FFF;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
