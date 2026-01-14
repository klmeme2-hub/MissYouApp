import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* =============================================
           1. 全局基礎設定
           ============================================= */
        .stApp {
            background-color: #050505;
            background-image: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #050505 40%);
            color: #E2E8F0;
            font-family: 'Inter', sans-serif;
        }
        
        /* 調整主容器 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 1000px !important;
        }
        
        /* 隱藏預設分隔線 */
        hr { display: none !important; }
        
        /* 全局文字設定 (解決行高問題) */
        p, label, span, div, li, .stMarkdown {
            color: #E2E8F0 !important;
            font-size: 15px !important;
            line-height: 1.6 !important; /* 拉開行高，避免重疊 */
        }
        
        /* 縮小元件間距 */
        .stElementContainer { margin-bottom: -10px !important; }

        /* =============================================
           2. Header 樣式 (修復重疊)
           ============================================= */
        .header-title h1 {
            font-size: 36px !important;
            font-weight: 800 !important;
            margin-bottom: 5px !important;
            padding: 0 !important;
            text-shadow: 0 0 15px rgba(124, 77, 255, 0.6);
            line-height: 1.4 !important; /* 加大行高 */
        }
        .header-subtitle {
            font-size: 16px !important;
            color: #94A3B8 !important;
            font-weight: 400;
            margin-top: 5px !important;
            margin-bottom: 20px !important;
        }

        /* 右上角用戶資訊 */
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
            font-size: 13px; color: #888 !important; white-space: nowrap;
        }

        /* =============================================
           3. 按鈕強制不換行 (修復按鈕跑版)
           ============================================= */
        div.stButton > button {
            font-size: 14px !important;
            padding: 0.4rem 0.8rem !important;
            height: auto !important;
            min-height: 0px !important;
            white-space: nowrap !important; /* 【關鍵】強制文字不換行 */
            border-radius: 6px !important;
            width: auto !important; /* 避免被撐開 */
        }
        
        button[kind="primary"] {
            background: linear-gradient(135deg, #FF4B4B 0%, #FF2B2B 100%) !important;
            color: white !important; border: none !important;
        }
        button[kind="secondary"] {
            background-color: #1A1C24 !important;
            color: #BBB !important; border: 1px solid #333 !important;
        }
        button[kind="secondary"]:hover {
            border-color: #666 !important; color: white !important;
        }

        /* =============================================
           4. 狀態列與卡片
           ============================================= */
        .status-bar {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 12px 20px;
            border-radius: 12px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        .status-item { margin-left: 15px; color: #94A3B8 !important; font-size: 13px !important; white-space: nowrap; }
        .status-value { color: #FCD34D !important; font-weight: 700; }
        .sim-score { color: #00E5FF; font-weight: bold; cursor: help; border-bottom: 1px dashed #00E5FF; }

        /* Tooltip */
        .tooltip-container { position: relative; display: inline-block; }
        .tooltip-container .tooltip-text {
            visibility: hidden; width: 220px; background-color: #333; color: #fff; text-align: center;
            border-radius: 6px; padding: 8px; position: absolute; z-index: 1;
            top: 150%; left: 50%; margin-left: -110px; opacity: 0; transition: opacity 0.3s;
            border: 1px solid #555; box-shadow: 0 4px 10px rgba(0,0,0,0.5); font-size: 12px !important;
        }
        .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

        /* 卡片 */
        .question-card-active {
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 17, 21, 0.5) 100%);
            border: 1px solid #3B82F6; padding: 25px; border-radius: 16px; text-align: center; margin-bottom: 20px;
        }
        .q-text { font-size: 20px; color: #FFF !important; font-weight: 700; margin: 10px 0; }
        .history-card { background-color: #0F1115; padding: 15px; border: 1px solid #2D3039; border-radius: 10px; margin-bottom: 10px; }
        .script-box { background: #1E1E1E; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #FFD700; color: #DDD !important; }
        .ai-bubble { background-color: #262730; padding: 15px; border-radius: 10px; border-left: 3px solid #FF4B4B; margin: 10px 0; color: #E0E0E0 !important; }
        .dashboard-card { background-color: #0F1115; padding: 20px; border-radius: 12px; border: 1px solid #2D3039; text-align: center; margin-bottom: 15px; }

        #MainMenu, footer {visibility: hidden;}

        @media (max-width: 600px) {
            .brand-container { flex-direction: column; }
            .user-info-box { display: none; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 8px; }
            .status-item { margin-left: 0; }
        }
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------------
# 關鍵修復：Render Status Bar (解決代碼外洩問題)
# 使用 f-string 拼接成單行，避免 Markdown 縮排錯誤
# --------------------------------------------------------
def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    
    left = f"👋 訪客" if is_guest else f"{icon} {tier_name}"
    
    # 關鍵修正：將 XP 的 HTML 拼接邏輯簡化，避免 f-string 混亂
    xp_part = ""
    if not is_guest:
        xp_part = f'<span style="margin-left:15px">⭐ XP: <span style="color:#FFD700">{xp}</span></span>'
    
    st.markdown(f"""
    <div style="background:#1A1C24; padding:12px 20px; border-radius:8px; display:flex; justify-content:space-between; border:1px solid #333; margin-bottom:20px;">
        <div style="color:white; font-weight:bold;">{left}</div>
        <div>
            <span style="color:#FF4081; font-weight:bold;">❤️ 電量: {energy}</span>
            {xp_part}
            <span style="margin-left:15px; color:#888;">| {engine}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(final_html, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""<div class="question-card-active"><div style="color:#94A3B8; font-size:12px; margin-bottom:5px;">PROGRESS {index}/{total}</div><div class="q-text">{question}</div><div style="font-size:13px; color:#64748B; margin-top:15px;">🎙️ 請按下錄音...</div></div>""", unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""<div class="history-card"><b style="color:#A78BFA;">Q: {q}</b><br><span style="color:#94A3B8; font-size:13px;">{a[:40]}...</span></div>""", unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""<div class="dashboard-card"><div style="color:#94A3B8; font-size:12px; margin-bottom:5px;">{title}</div><div style="font-size:24px; font-weight:700; color:#F8FAFC;">{content}</div></div>""", unsafe_allow_html=True)
