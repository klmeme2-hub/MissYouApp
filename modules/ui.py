import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* =============================================
           1. 全局背景與文字 (Deep Space Theme)
           ============================================= */
        .stApp {
            background-color: #0E1117;
            background-image: radial-gradient(circle at 50% 0%, #1c1c2e 0%, #0E1117 80%);
            background-attachment: fixed;
            color: #FAFAFA;
        }
        
        /* 強制所有文字顏色 */
        .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, div, label {
            color: #FAFAFA !important;
        }

        /* =============================================
           2. 輸入框美化 (Input Fields)
           目標：深灰底、微發光邊框
           ============================================= */
        /* 文字輸入框 & 數字輸入框的容器 */
        div[data-baseweb="input"] {
            background-color: #1F2229 !important;
            border: 1px solid #444 !important;
            border-radius: 8px !important;
        }
        
        /* 輸入框內的文字 */
        input.stTextInput {
            color: white !important;
        }
        
        /* 下拉選單 (Selectbox) */
        div[data-baseweb="select"] > div {
            background-color: #1F2229 !important;
            border-color: #444 !important;
            color: white !important;
        }
        
        /* 下拉選單彈出的列表 */
        div[data-baseweb="popover"], div[data-baseweb="menu"] {
            background-color: #1F2229 !important;
            border: 1px solid #555 !important;
        }
        
        /* 下拉選項滑過的效果 */
        li[role="option"]:hover {
            background-color: #FF4B4B !important;
            color: white !important;
        }

        /* =============================================
           3. 按鈕美化 (Neon Buttons)
           目標：漸層、發光、圓角
           ============================================= */
        /* Primary Button (主要按鈕) */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(45deg, #FF4B4B, #FF9100) !important;
            border: none !important;
            color: white !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
            transition: all 0.3s ease;
        }
        div.stButton > button[kind="primary"]:hover {
            transform: scale(1.02);
            box-shadow: 0 0 20px rgba(255, 75, 75, 0.6);
        }

        /* Secondary Button (次要按鈕) */
        div.stButton > button[kind="secondary"] {
            background-color: #262730 !important;
            border: 1px solid #555 !important;
            color: white !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            border-color: #FF4B4B !important;
            color: #FF4B4B !important;
        }

        /* =============================================
           4. 分頁標籤 (Tabs)
           ============================================= */
        button[data-baseweb="tab"] {
            background-color: transparent !important;
            color: #888 !important;
            font-weight: bold;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #FF4B4B !important;
            border-bottom-color: #FF4B4B !important;
        }

        /* =============================================
           5. 自定義元件 CSS (HTML Components)
           ============================================= */
        
        /* 頂部狀態列 HUD */
        .status-bar {
            background: linear-gradient(90deg, rgba(30,30,40,0.9) 0%, rgba(45,45,60,0.9) 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-left: 4px solid #00E5FF;
            padding: 15px 20px; 
            border-radius: 10px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            backdrop-filter: blur(5px);
        }
        .status-val { color: #00E5FF; font-weight: bold; text-shadow: 0 0 8px rgba(0, 229, 255, 0.6); }
        .status-warn { color: #FF4081; font-weight: bold; text-shadow: 0 0 8px rgba(255, 64, 129, 0.6); }

        /* 進行中任務卡片 (Active) */
        .question-card-active {
            background: linear-gradient(135deg, rgba(0, 229, 255, 0.05) 0%, rgba(0, 0, 0, 0) 100%);
            border: 1px solid #00E5FF;
            border-radius: 16px; padding: 25px; text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 0 20px rgba(0, 229, 255, 0.1);
        }
        .q-text { font-size: 22px; color: #FFF !important; font-weight: 600; margin: 15px 0; }

        /* 歷史卡片 */
        .history-card {
            background-color: #1F2229;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            transition: transform 0.2s;
        }
        .history-card:hover { transform: translateX(5px); border-color: #FF4B4B; }

        /* 腳本框 */
        .script-box {
            background: #1A1C24; padding: 20px; border-radius: 8px; margin: 15px 0;
            border-left: 4px solid #FFD700; color: #DDD !important;
        }

        /* 隱藏 Streamlit 浮水印 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名/口頭禪", "安慰", "鼓勵", "詼諧", "完成"]
    st.markdown('<div style="display:flex; justify-content:space-between; margin:20px 0;">', unsafe_allow_html=True)
    cols = st.columns(len(steps))
    for i, (col, name) in enumerate(zip(cols, steps)):
        # 判斷顏色：已完成/當前為紅色，未完成為灰色
        active_color = "#FF4B4B" if i + 1 <= current_step else "#444"
        text_color = "#FFF" if i + 1 <= current_step else "#888"
        border = f"2px solid {active_color}"
        shadow = f"0 0 10px {active_color}80" if i + 1 == current_step else "none"
        
        col.markdown(f"""
        <div style="text-align:center;">
            <div style="width:30px; height:30px; border-radius:50%; background:#1E1E1E; border:{border}; margin:0 auto; display:flex; align-items:center; justify-content:center; color:{text_color}; font-weight:bold; box-shadow:{shadow};">
                {i+1}
            </div>
            <div style="font-size:12px; color:{text_color}; margin-top:5px;">{name}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {
        "basic": "🚀 初級練習生", "intermediate": "🛡️ 中級守護者", 
        "advanced": "🔥 高級刻錄師", "eternal": "♾️ 永恆上鏈"
    }
    tier_name = tier_map.get(tier, tier)
    
    if tier in ['advanced', 'eternal']: engine_info = "Gemini Pro"
    else: engine_info = "Gemini Flash"

    user_label = "👋 訪客模式" if is_guest else f"{tier_name}"
    
    # 使用 Flexbox 排版
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-size:16px; font-weight:bold; color:#FFF;">
            <span style="font-size:20px; vertical-align:middle;">👤</span> {user_label}
        </div>
        <div style="text-align:right;">
            <span style="color:#B0BEC5; margin-right:10px;">❤️ 電量: <span class="status-warn">{energy}</span></span>
            {f'<span style="color:#B0BEC5; margin-right:10px;">⭐ XP: <span class="status-val">{xp}</span></span>' if not is_guest else ''}
            <span style="color:#666;">|</span>
            <span style="color:#00E5FF; margin-left:10px;">🚀 {engine_info}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""
    <div class="question-card-active">
        <div style="color:#00E5FF; font-size:12px; margin-bottom:10px; letter-spacing:2px; text-transform:uppercase;">Processing {index}/{total}</div>
        <div class="q-text">{question}</div>
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
