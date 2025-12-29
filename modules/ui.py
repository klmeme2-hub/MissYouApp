import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* --- 1. 全局基礎 (回歸標準) --- */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* 修正主容器寬度與邊距 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 1100px !important;
        }
        
        /* 隱藏預設分隔線 */
        hr { display: none !important; }
        
        /* 全局文字顏色 */
        h1, h2, h3, h4, h5, h6, p, div, span, label, li, button {
            color: #FAFAFA !important;
            font-family: "Source Sans Pro", sans-serif;
        }

        /* --- 2. 頂部標題區 --- */
        .header-title {
            font-size: 34px !important;
            font-weight: 700 !important;
            margin-bottom: 5px !important;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .header-subtitle {
            font-size: 16px !important;
            color: #B0B0B0 !important;
            font-weight: 400;
            margin-top: 0 !important;
        }

        /* --- 3. 右上角用戶資訊 (修復對齊) --- */
        .user-info-box {
            display: flex;
            flex-direction: column;
            align-items: flex-end; /* 靠右對齊 */
            justify-content: center;
            height: 100%;
            margin-top: 10px;
        }
        .user-email {
            font-size: 14px !important;
            color: #888 !important;
            margin-bottom: 5px;
        }

        /* --- 4. 圓形進度條 (修復 HTML 顯示錯誤) --- */
        .step-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 30px 0;
            position: relative;
            width: 100%;
        }
        .step-item {
            text-align: center;
            position: relative;
            z-index: 2;
            padding: 0 30px; /* 圓圈間距 */
        }
        .step-circle {
            width: 32px; height: 32px;
            border-radius: 50%;
            background: #1E1E1E;
            border: 2px solid #444;
            color: #666;
            display: flex; align-items: center; justify-content: center;
            font-weight: bold;
            font-size: 14px;
            margin: 0 auto 8px;
            transition: all 0.3s;
        }
        .step-label {
            font-size: 14px;
            color: #888;
            font-weight: 500;
        }
        /* 連接線 */
        .step-line-bg {
            position: absolute;
            top: 16px; /* 圓圈的一半高度 */
            left: 10%;
            right: 10%;
            height: 2px;
            background: #333;
            z-index: 1;
        }
        /* 激活狀態 */
        .step-active .step-circle {
            background: #FF4B4B;
            border-color: #FF4B4B;
            color: white;
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
        }
        .step-active .step-label {
            color: #FF4B4B !important;
            font-weight: bold;
        }

        /* --- 5. 狀態列 --- */
        .status-bar {
            background: #1A1C24;
            border: 1px solid #333;
            padding: 12px 20px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        .status-text { font-size: 15px; font-weight: 500; }
        .status-highlight { color: #FFD700 !important; font-weight: bold; }

        /* --- 6. 輸入框與按鈕 --- */
        .stSelectbox > div > div {
            background-color: #1F2229 !important;
            border: 1px solid #444 !important;
            color: white !important;
        }
        .stTextInput > div > div > input {
            background-color: #1F2229 !important;
            border: 1px solid #444 !important;
            color: white !important;
        }
        button[kind="primary"] {
            background-color: #FF4B4B !important;
            color: white !important;
            border: none;
            font-weight: bold;
            padding: 0.5rem 1rem;
            font-size: 16px;
        }

        /* 手機版適配 */
        @media (max-width: 600px) {
            .step-wrapper { transform: scale(0.8); width: 110%; margin-left: -5%; }
            .step-line-bg { display: none; } /* 手機隱藏線條 */
            .step-item { padding: 0 5px; }
            .user-info-box { display: none; } /* 手機隱藏右上角資訊 */
        }
    </style>
    """, unsafe_allow_html=True)

def render_stepper(current_step):
    steps = ["喚名", "安慰", "鼓勵", "詼諧", "完成"]
    
    # 【關鍵修復】將 HTML 壓縮為單行字串，避免 Python 的 f-string 換行被 Markdown 誤判
    items_html = ""
    for i, name in enumerate(steps):
        is_active = "step-active" if i + 1 == current_step else ""
        # 注意：這裡不換行，全部擠在一起
        items_html += f'<div class="step-item {is_active}"><div class="step-circle">{i+1}</div><div class="step-label">{name}</div></div>'
    
    # 組合
    final_html = f'<div class="step-wrapper"><div class="step-line-bg"></div>{items_html}</div>'
    
    st.markdown(final_html, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, is_guest=False):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    
    # 圖示
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"

    left_content = f"{'👋 訪客' if is_guest else f'{icon} {tier_name}'}"
    xp_html = f'<span style="margin-left:15px">⭐ XP: <span class="status-highlight">{xp}</span></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-text" style="color:#FFF !important;">{left_content}</div>
        <div class="status-text">
            <span>❤️ 電量: <span style="color:#FF4081; font-weight:bold;">{energy}</span></span>
            {xp_html}
            <span style="margin-left:15px; color:#888;">| {engine}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 其他卡片維持簡單樣式
def render_question_card(question, index, total):
    st.info(f"🎙️ **Q{index}/{total}: {question}**\n\n請按下錄音回答...")

def render_history_card(q, a):
    st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")

def render_dashboard_card(title, content):
    st.metric(label=title, value=content)
