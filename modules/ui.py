import streamlit as st

def load_css():
    """載入 EchoSoul 專屬：深藍與琥珀金視覺系統"""
    st.markdown("""
    <style>
        /* 1. 全域背景與文字基礎 */
        .stApp {
            background-color: #001F3F !important; /* 深藍底 */
            color: #E2E8F0 !important; /* 淺灰白文字 */
        }

        /* 2. 側邊欄優化 */
        [data-testid="stSidebar"] {
            background-color: #00152B !important;
            border-right: 1px solid rgba(255, 191, 0, 0.2);
        }

        /* 3. 琥珀金標題與品牌字 */
        h1, h2, h3, .brand-text {
            color: #FFBF00 !important;
            font-family: 'Noto Serif TC', serif;
            text-shadow: 0px 0px 10px rgba(255, 191, 0, 0.3);
        }

        /* 4. 按鈕視覺：琥珀金實心 */
        .stButton>button {
            background-color: #FFBF00 !important;
            color: #001F3F !important;
            border-radius: 20px !important;
            border: none !important;
            font-weight: 700 !important;
            padding: 0.5rem 2rem !important;
            transition: all 0.3s ease !important;
        }
        .stButton>button:hover {
            box-shadow: 0px 0px 15px rgba(255, 191, 0, 0.6) !important;
            transform: translateY(-2px);
        }

        /* 5. 卡片容器：模擬琥珀質感 */
        [data-testid="stVerticalBlock"] > div > div > div[data-testid="stVerticalBlock"] {
            background-color: rgba(255, 191, 0, 0.03);
            border: 1px solid rgba(255, 191, 0, 0.1);
            border-radius: 12px;
            padding: 20px;
        }

        /* 6. 輸入框對焦顏色 */
        textarea, input {
            background-color: #002B55 !important;
            color: white !important;
            border: 1px solid rgba(255, 191, 0, 0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, engine_type, similarity=0, sim_hint="", sim_gain=0, is_guest=False, member_name=""):
    tier_map = {"basic": "初級練習生", "intermediate": "中級守護者", "advanced": "高級刻錄師", "eternal": "永恆上鏈"}
    tier_name = tier_map.get(tier, tier)
    engine_name = "Gemini Pro" if engine_type == "elevenlabs" else "Gemini Flash"
    
    icon = "🚀" if tier == "basic" else "🛡️"
    if tier == "advanced": icon = "🔥"
    if tier == "eternal": icon = "♾️"

    left_content = f"👉 正在與 <span style='color:#FFD700;'>{member_name}</span> 對話..." if is_guest else f"{icon} {tier_name}"
    
    xp_part = ""
    if not is_guest:
        tooltip = f"下一步：{sim_hint} (+{sim_gain}%)" if sim_gain > 0 else "已達目前等級上限"
        sim_part = f"""<div class="tooltip-container"><span style="color:#BBB">相似度 <span class="sim-score">{similarity}%</span></span><span class="tooltip-text">{tooltip}</span></div>"""
        xp_part = f"""{sim_part}&nbsp;&nbsp;<span style="color:#FFD700">⭐ XP: {xp}</span>"""

    engine_display = "" if is_guest else f"""<span style='margin-left:15px; color:#888; border-left:1px solid #444; padding-left:10px;'>| {engine_name}</span>"""
    
    # 這裡的 HTML 結構更加嚴謹，避免換行造成的解析錯誤
    html = f"""<div class="status-bar"><div class="status-left">{left_content}</div><div class="status-right"><div class="tooltip-container"><span>❤️ 電量: <span class="val-energy">{energy}</span></span><span class="tooltip-text">約還可對話 {energy} 句</span></div>{xp_part}{engine_display}</div></div>"""
    
    st.markdown(html, unsafe_allow_html=True)

def render_question_card(question, index, total): st.info(f"🎙️ **Q{index}/{total}: {question}**")
def render_history_card(q, a): st.markdown(f"> **Q:** {q}\n> **A:** {a[:30]}...")
def render_dashboard_card(title, content): st.metric(label=title, value=content)
