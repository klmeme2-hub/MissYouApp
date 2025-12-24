import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* =============================================
           1. 基底設定 (Flat Dark Theme)
           ============================================= */
        .stApp {
            background-color: #0E1117; /* 純深黑背景 */
            color: #E0E0E0;
        }
        
        /* 通用文字顏色 */
        h1, h2, h3, h4, h5, h6, p, label, span, div, li {
            color: #E0E0E0;
        }
        
        /* =============================================
           2. 元件樣式 (Solid Colors)
           ============================================= */
        
        /* 輸入框 */
        input[type="text"], input[type="password"], textarea {
            background-color: #161920 !important;
            border: 1px solid #30363D !important; /* GitHub 風格邊框 */
            color: #FFFFFF !important;
            border-radius: 6px !important;
        }
        
        /* 下拉選單 */
        div[data-baseweb="select"] > div {
            background-color: #161920 !important;
            border-color: #30363D !important;
            color: #FFFFFF !important;
        }
        
        /* 折疊選單 (Expander) */
        div[data-testid="stExpander"] details summary {
            background-color: #161920 !important;
            border: 1px solid #30363D !important;
            border-radius: 6px !important;
            color: #E0E0E0 !important;
        }
        div[data-testid="stExpander"] details summary:hover {
            border-color: #8B949E !important; /* 滑過變亮灰 */
        }
        
        /* 修正圖示顏色 */
        div[data-testid="stExpander"] details summary svg {
            fill: #8B949E !important;
        }

        /* =============================================
           3. 自定義介面元件
           ============================================= */
        
        /* 狀態列 (扁平化設計) */
        .status-bar {
            background-color: #161920;
            border: 1px solid #30363D;
            padding: 15px 20px; 
            border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px;
        }
        .status-item { margin-left: 15px; font-size: 14px; color: #8B949E !important; }
        
        /* 題目卡片 (Active) */
        .question-card-active {
            background-color: #1F242C; /* 稍微亮一點的灰 */
            border: 1px solid #FF4B4B; /* 保留品牌紅框 */
            padding: 25px; border-radius: 8px; text-align: center;
            margin-bottom: 20px;
        }
        .q-text { font-size: 20px; color: #FFF !important; font-weight: 600; margin: 15px 0; }
        
        /* 歷史卡片 */
        .history-card { 
            background-color: #161920; 
            padding: 15px; 
            border: 1px solid #30363D; 
            border-radius: 6px; 
            margin-bottom: 10px; 
        }
        
        /* 儀表板小卡 */
        .dashboard-card {
            background-color: #161920;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #30363D;
            text-align: center;
            margin-bottom: 10px;
        }
        
        /* 腳本框 */
        .script-box { 
            background: #0d1117; 
            padding: 20px; 
            border-radius: 6px; 
            margin: 15px 0; 
            border: 1px solid #30363D;
            color: #C9D1D9 !important;
            font-family: monospace;
        }

        /* 按鈕 (扁平化) */
        button[kind="primary"] {
            background-color: #FF4B4B !important;
            border: 1px solid #FF4B4B !important;
            color: white !important;
            font-weight: bold !important;
            box-shadow: none !important; /* 移除發光 */
        }
        button[kind="primary"]:hover {
            background-color: #D93E3E !important;
            border-color: #D93E3E !important;
        }

        /* 隱藏選單 */
        #MainMenu, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名/口頭禪", "安慰", "鼓勵", "詼諧", "完成"]
    st.markdown('<div style="display:flex; justify-content:space-between; margin:20px 0;">', unsafe_allow_html=True)
    cols = st.columns(len(steps))
    for i, (col, name) in enumerate(zip(cols, steps)):
        # 扁平化顏色：紅色 vs 深灰
        bg_color = "#FF4B4B" if i + 1 <= current_step else "#30363D"
        text_color = "#FFF" if i + 1 <= current_step else "#8B949E"
        
        col.markdown(f"""
        <div style="text-align:center;">
            <div style="width:30px; height:30px; border-radius:50%; background:{bg_color}; margin:0 auto 8px; display:flex; align-items:center; justify-content:center; color:#FFF; font-weight:bold;">
                {i+1}
            </div>
            <div style="font-size:12px; color:{text_color};">{name}</div>
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
    
    xp_html = f'<span class="status-item">XP: <b style="color:#FFD700">{xp}</b></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-size:16px; font-weight:bold; color:#E0E0E0;">{user_label}</div>
        <div style="text-align:right;">
            <span class="status-item">電量: <b style="color:#FF4B4B">{energy}</b></span>
            {xp_html}
            <span class="status-item">| {engine_name}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""
    <div class="question-card-active">
        <div style="color:#8B949E; font-size:12px; margin-bottom:5px; text-transform:uppercase;">Processing {index}/{total}</div>
        <div class="q-text">{question}</div>
        <div style="font-size:13px; color:#8B949E; margin-top:10px;">🎙️ 點擊下方按鈕錄音...</div>
    </div>
    """, unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""
    <div class="history-card">
        <b style="color:#58A6FF;">Q: {q}</b><br>
        <span style="color:#C9D1D9; font-size:13px;">{a[:40]}...</span>
    </div>
    """, unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""
    <div class="dashboard-card">
        <div style="color:#8B949E; font-size:12px; margin-bottom:5px;">{title}</div>
        <div style="font-size:24px; font-weight:bold; color:#FAFAFA;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
