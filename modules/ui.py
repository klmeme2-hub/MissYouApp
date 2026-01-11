import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* =============================================
           1. 全局重置 (Global Reset)
           ============================================= */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        .stApp {
            background-color: #050505; /* 純粹深黑 */
            background-image: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #050505 40%); /* 頂部極微弱紫光 */
            color: #E2E8F0;
            font-family: 'Inter', sans-serif;
        }
        
        /* 讓文字好讀的通用設定 */
        p, label, span, div, li, .stMarkdown {
            color: #E2E8F0 !important;
            font-size: 16px !important;
            line-height: 1.6 !important; /* 修正行高，讓字不會擠在一起 */
        }
        
        /* 標題層級設定 */
        h1 { font-size: 36px !important; font-weight: 800 !important; line-height: 1.3 !important; letter-spacing: -0.5px; }
        h2 { font-size: 28px !important; font-weight: 700 !important; margin-top: 30px !important; }
        h3 { font-size: 22px !important; font-weight: 600 !important; }
        
        /* 調整主容器寬度與邊距 (給予足夠呼吸空間) */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 5rem !important;
            max-width: 1000px !important;
        }
        
        /* 移除預設分隔線 */
        hr { display: none !important; }
        
        /* 修正 Streamlit 元件間距 (不再使用負值，改用適當的間隙) */
        .stElementContainer {
            margin-bottom: 1rem !important;
        }

        /* =============================================
           2. 品牌標題區 (Hero Header)
           ============================================= */
        .brand-container {
            display: flex;
            align-items: center;
            gap: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }
        .brand-icon {
            font-size: 48px;
            filter: drop-shadow(0 0 15px rgba(124, 77, 255, 0.5));
        }
        .brand-text h1 {
            margin: 0 !important;
            background: linear-gradient(90deg, #FFFFFF, #A78BFA);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-subtitle {
            font-size: 16px !important;
            color: #94A3B8 !important;
            margin: 5px 0 0 0 !important;
            font-weight: 400;
        }
        
        /* 右上角用戶資訊 */
        .user-pill {
            background: rgba(255,255,255,0.05);
            padding: 5px 15px;
            border-radius: 50px;
            font-size: 13px !important;
            color: #94A3B8 !important;
            border: 1px solid rgba(255,255,255,0.1);
        }

        /* =============================================
           3. 現代化元件樣式
           ============================================= */
        
        /* 狀態列 */
        .status-bar {
            background: #0F1115;
            border: 1px solid #2D3039;
            padding: 15px 25px;
            border-radius: 12px;
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            margin-bottom: 30px;
        }
        .status-item { margin-left: 20px; font-weight: 500; font-size: 15px !important; }
        
        /* 輸入框與下拉選單 */
        .stTextInput > div > div > input, .stSelectbox > div > div {
            background-color: #0F1115 !important;
            color: white !important;
            border: 1px solid #333 !important;
            border-radius: 8px !important;
            height: 45px; /* 增加高度，更好點擊 */
        }
        
        /* 按鈕 (Primary) - 生成邀請卡 */
        button[kind="primary"] {
            background: linear-gradient(135deg, #FF4B4B 0%, #FF2B2B 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 600 !important;
            font-size: 16px !important;
            box-shadow: 0 4px 12px rgba(255, 75, 75, 0.3);
            transition: all 0.2s;
        }
        button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 6px 15px rgba(255, 75, 75, 0.5); }

        /* 按鈕 (Secondary) - 導航按鈕 */
        button[kind="secondary"] {
            background-color: #1A1C24 !important;
            color: #BBB !important;
            border: 1px solid #333 !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
        }
        button[kind="secondary"]:hover {
            border-color: #666 !important;
            color: white !important;
        }
        /* 當按鈕被選中時 (Active Tab) - 需要配合 Python session state */
        /* 這裡我們主要靠 primary/secondary 來區分 */

        /* =============================================
           4. 卡片設計
           ============================================= */
        .question-card-active {
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.5) 100%);
            border: 1px solid #3B82F6;
            padding: 30px; 
            border-radius: 16px; 
            text-align: center; 
            margin-bottom: 20px;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.1);
        }
        .q-text { font-size: 24px !important; color: #FFF !important; font-weight: 700; margin: 15px 0; }
        
        .history-card { 
            background-color: #0F1115; padding: 15px; 
            border: 1px solid #2D3039; border-radius: 10px; margin-bottom: 10px; 
        }
        .dashboard-card {
            background-color: #0F1115; padding: 20px; 
            border-radius: 12px; border: 1px solid #2D3039; 
            text-align: center; margin-bottom: 15px;
        }

        #MainMenu, footer {visibility: hidden;}

        /* 手機適配 */
        @media (max-width: 600px) {
            .brand-container { flex-direction: column; text-align: center; gap: 5px; }
            .user-pill { display: none; }
            .status-bar { flex-direction: column; align-items: flex-start; gap: 10px; }
            .status-item { margin-left: 0; }
        }
    </style>
    """, unsafe_allow_html=True)

# 移除 render_stepper (因為改用按鈕了)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    icon = "🌱" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"

    user_label = "👋 訪客" if is_guest else f"{icon} {tier_name}"
    xp_html = f'<span class="status-item">⭐ XP <span style="color:#F59E0B; font-weight:bold;">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div style="font-weight:600; font-size:16px; color:#FFF;">{user_label}</div>
        <div>
            <span class="status-item">❤️ 電量 <span style="color:#F472B6; font-weight:bold;">{energy}</span></span>
            {xp_html}
            <span class="status-item" style="border-left:1px solid #444; padding-left:15px; color:#94A3B8 !important;">{engine}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""<div class="question-card-active"><div style="color:#94A3B8; font-size:12px; letter-spacing:1px;">PROGRESS {index}/{total}</div><div class="q-text">{question}</div><div style="font-size:14px; color:#64748B;">🎙️ 請按下錄音按鈕開始回答...</div></div>""", unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""<div class="history-card"><b style="color:#A78BFA;">Q: {q}</b><br><span style="color:#94A3B8;">{a[:40]}...</span></div>""", unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""<div class="dashboard-card"><div style="color:#94A3B8; font-size:12px; margin-bottom:5px;">{title}</div><div style="font-size:24px; font-weight:bold; color:#F8FAFC;">{content}</div></div>""", unsafe_allow_html=True)
