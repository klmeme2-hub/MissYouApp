import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* 全局設定 */
        .stApp, p, h1, h2, h3, label, div, span, button { color: #FAFAFA !important; }
        div[data-baseweb="select"] > div, div[data-baseweb="popover"] li { 
            background-color: #262730 !important; color: #FAFAFA !important; border-color: #444 !important;
        }
        
        /* 圓形進度條 (Stepper) */
        .step-wrapper { display: flex; justify-content: space-between; margin: 20px 0; }
        .step-item { text-align: center; position: relative; width: 100%; }
        .step-circle {
            width: 30px; height: 30px; border-radius: 50%; background: #444; margin: 0 auto 5px;
            display: flex; align-items: center; justify-content: center; font-weight: bold; color: #888;
            border: 2px solid #666; transition: all 0.3s;
        }
        .step-active .step-circle { background: #FF4B4B; color: white; border-color: #FF4B4B; box-shadow: 0 0 10px rgba(255, 75, 75, 0.5); }
        .step-label { font-size: 12px; color: #888; }
        .step-active .step-label { color: #FF4B4B; font-weight: bold; }
        
        /* 狀態列 */
        .status-bar {
            background: linear-gradient(90deg, #1E1E1E 0%, #2D2D2D 100%);
            border: 1px solid #444; padding: 12px 20px; border-radius: 10px;
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;
        }
        
        /* 評分彈窗 (模擬) */
        .rating-box {
            background-color: #1E1E1E; padding: 30px; border-radius: 15px; text-align: center;
            border: 2px solid #FFD700; margin: 20px 0; animation: popup 0.5s ease-out;
        }
        @keyframes popup { from {transform: scale(0.8); opacity: 0;} to {transform: scale(1); opacity: 1;} }
        
        /* 按鈕與卡片 */
        .ai-bubble { background: #262730; padding: 15px; border-radius: 10px; border-left: 4px solid #FF4B4B; margin: 10px 0; }
        
        /* 隱藏預設元件 */
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
    tier_map = {"basic": "🔰 初級", "intermediate": "🛡️ 中級", "advanced": "🔥 高級", "eternal": "♾️ 永恆"}
    engine_name = "🚀 ElevenLabs" if engine_type == "elevenlabs" else "⚡ OpenAI"
    user_label = "👋 親友訪客" if is_guest else f"👤 {tier_map.get(tier, tier)}"
    
    xp_html = f'<span style="margin-left:15px">⭐ XP: <b style="color:#FFD700">{xp}</b></span>' if not is_guest else ''
    
    st.markdown(f"""
    <div class="status-bar">
        <div>{user_label}</div>
        <div>
            <span>❤️ 電量: <b style="color:#FF4B4B">{energy}</b></span>
            {xp_html}
            <span style="margin-left:15px; opacity:0.7">| {engine_name}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
