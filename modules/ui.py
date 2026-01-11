import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* =============================================
           1. 全局基礎設定 (緊湊版)
           ============================================= */
        .stApp {
            background-color: #050505;
            background-image: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #050505 40%);
            color: #E2E8F0;
            font-family: 'Inter', sans-serif;
        }
        
        /* 【關鍵修改】全局行高縮小 (1.6 -> 1.35) */
        p, label, span, div, li, .stMarkdown, button {
            color: #E2E8F0 !important;
            font-size: 15px !important; /* 字體稍微縮小一點點 */
            line-height: 1.35 !important; /* 讓行距更緊湊 */
        }
        
        /* 標題層級設定 */
        h1 { font-size: 32px !important; font-weight: 800 !important; line-height: 1.2 !important; margin-bottom: 5px !important; }
        h2 { font-size: 26px !important; font-weight: 700 !important; margin-top: 20px !important; }
        h3 { font-size: 20px !important; font-weight: 600 !important; }
        
        /* 調整主容器 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 1000px !important;
        }
        
        /* 移除預設分隔線與間距 */
        hr { display: none !important; }
        .stElementContainer { margin-bottom: 0.8rem !important; }

        /* =============================================
           2. Header 樣式
           ============================================= */
        .brand-container {
            display: flex;
            align-items: center;
            gap: 15px;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .brand-icon { font-size: 40px; }
        .brand-text h1 {
            background: linear-gradient(90deg, #FFFFFF, #A78BFA);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-subtitle {
            font-size: 14px !important;
            color: #94A3B8 !important;
            font-weight: 400;
            margin-top: 0 !important;
        }

        /* =============================================
           3. 按鈕優化 (針對導航列按鈕)
           ============================================= */
        div.stButton > button {
            font-size: 14px !important; /* 字體縮小 */
            padding: 0.4rem 0.8rem !important; /* 內距縮小 */
            height: auto !important;
            min-height: 0px !important;
            white-space: nowrap !important; /* 【關鍵】強制不換行 */
            border-radius: 6px !important;
        }

        /* Primary 按鈕 (生成邀請卡) */
        button[kind="primary"] {
            background: linear-gradient(135deg, #FF4B4B 0%, #FF2B2B 100%) !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
        }
        
        /* Secondary 按鈕 (導航頁籤) */
        button[kind="secondary"] {
            background-color: #1A1C24 !important;
            color: #BBB !important;
            border: 1px solid #333 !important;
        }
        button[kind="secondary"]:hover {
            border-color: #666 !important;
            color: white !important;
        }
        /* 當按鈕被選中時 (Active) - 透過 Python 控制 style */

        /* =============================================
           4. 卡片與容器
           ============================================= */
        /* 狀態列 */
        .status-bar {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 10px 20px;
            border-radius: 12px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px;
        }
        .status-item { margin-left: 20px; color: #94A3B8 !important; font-size: 13px !important; }
        .status-value { color: #FCD34D !important; font-weight: 700; }

        /* 題目卡片 */
        .question-card-active {
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 17, 21, 0.5) 100%);
            border: 1px solid #3B82F6;
            padding: 20px; border-radius: 16px;
            text-align: center; margin-bottom: 15px;
        }
        .q-text { font-size: 20px !important; color: #FFF !important; font-weight: 700; margin: 10px 0; }

        /* 輸入框與選單 */
        input, textarea, .stSelectbox > div > div {
            background-color: #0F1115 !important;
            color: #F8FAFC !important;
            border: 1px solid #2D3039 !important;
            border-radius: 8px !important;
            min-height: 40px !important;
        }
        
        /* 隱藏 */
        #MainMenu, footer {visibility: hidden;}

        /* 手機適配 */
        @media (max-width: 600px) {
            .brand-container { flex-direction: column; text-align: center; align-items: center; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 5px; }
            .status-item { margin-left: 0; }
        }
    </style>
    """, unsafe_allow_html=True)

# 保留其他 render 函數 (dashboard card, question card...) 
# 為了節省篇幅，這裡省略，請保留原有的 render 函數定義
def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    icon = "🌱" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"
    user_label = "👋 訪客" if is_guest else f"{icon} {tier_name}"
    xp_html = f'<span class="status-item">⭐ XP <span class="status-value">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-weight:600; font-size:15px; color:#FFF;">{user_label}</div>
        <div>
            <span class="status-item">❤️ 電量 <span class="status-value" style="color:#F472B6!important;">{energy}</span></span>
            {xp_html}
            <span class="status-item" style="border-left:1px solid #444; padding-left:15px;">{engine_name}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""<div class="question-card-active"><div style="color:#94A3B8; font-size:11px; margin-bottom:5px;">PROGRESS {index}/{total}</div><div class="q-text">{question}</div><div style="font-size:13px; color:#64748B; margin-top:10px;">🎙️ 點擊下方錄音...</div></div>""", unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""<div class="history-card" style="background:#0F1115; padding:12px; border:1px solid #333; border-radius:8px; margin-bottom:8px;"><b style="color:#A78BFA;">Q: {q}</b><br><span style="color:#94A3B8; font-size:13px;">{a[:40]}...</span></div>""", unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""<div class="dashboard-card" style="background:#0F1115; padding:15px; border:1px solid #333; border-radius:8px; text-align:center; margin-bottom:10px;"><div style="color:#94A3B8; font-size:12px;">{title}</div><div style="font-size:20px; font-weight:700; color:#F8FAFC;">{content}</div></div>""", unsafe_allow_html=True)
