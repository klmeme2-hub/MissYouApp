import streamlit as st

def load_css():
    st.markdown("""
    <style>
        .stApp, p, h1, h2, h3, label, div, span, button { color: #333333 !important; }
        div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #333333 !important; }
        div[data-baseweb="popover"] li { background-color: #FFFFFF !important; color: #333333 !important; }
        
        .ai-bubble {
            background-color: #FFFFFF; padding: 20px; border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 5px solid #4A90E2;
            margin: 10px 0; color: #333333; font-size: 16px; line-height: 1.6;
        }
        
        /* 狀態列 (會員/訪客通用) */
        .status-bar {
            background-color: #263238; color: white !important;
            padding: 12px 20px; border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 20px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        .status-item { margin-left: 15px; font-size: 14px; }
        .badge { background: #FF9800; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; }
        
        .question-card { background: #E3F2FD; padding: 20px; border-radius: 12px; border: 2px solid #2196F3; text-align: center; margin-bottom: 20px; }
        .q-text { font-size: 18px; color: #1565C0 !important; font-weight: bold; }
        .history-card { background: white; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 8px; }
        
        #MainMenu, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def render_status_bar(tier, energy, xp, is_guest=False):
    tier_map = {
        "basic": "🔰 初級練習生", "intermediate": "🛡️ 中級守護者", 
        "advanced": "🔥 高級刻錄師", "eternal": "♾️ 永恆上鏈"
    }
    tier_name = tier_map.get(tier, tier)
    
    # 判斷引擎
    if tier in ['advanced', 'eternal']:
        engine_info = "🚀 Gemini Pro + 擬真語音"
    else:
        engine_info = "⚡ Gemini Flash + 標準語音"

    user_label = "👋 親友訪客" if is_guest else f"👤 {tier_name}"
    
    st.markdown(f"""
    <div class="status-bar">
        <div>{user_label}</div>
        <div>
            <span class="status-item">❤️ 心靈電量: {energy}</span>
            {f'<span class="status-item">⭐ 共鳴值: {xp}</span>' if not is_guest else ''}
            <span class="status-item" style="opacity:0.8; font-weight:normal;">| {engine_info}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_question_card(question, index, total):
    st.markdown(f"""
    <div class="question-card">
        <div style="color:#666; font-size:12px; margin-bottom:5px;">進度 {index}/{total}</div>
        <div class="q-text">{question}</div>
        <div style="font-size:13px; color:#555; margin-top:10px;">請按下錄音，自然地回答...</div>
    </div>
    """, unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f'<div class="history-card"><b>Q: {q}</b><br><span style="color:#666; font-size:13px;">{a[:40]}...</span></div>', unsafe_allow_html=True)
