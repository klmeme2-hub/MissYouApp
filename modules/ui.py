# modules/ui.py
import streamlit as st

def load_css():
    custom_css = """
    <style>
        /* 全局配色鎖定 */
        .stApp, p, h1, h2, h3, label, div, span, button { color: #333333 !important; }
        
        /* 下拉選單修復 */
        div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #333333 !important; }
        div[data-baseweb="popover"] li { background-color: #FFFFFF !important; color: #333333 !important; }
        div[data-baseweb="popover"] li:hover { background-color: #E3F2FD !important; }

        /* AI 對話氣泡 */
        .ai-bubble {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            border-left: 5px solid #4A90E2;
            margin: 10px 0;
            color: #333333;
        }
        
        /* 題目卡片 */
        .question-card-active {
            background-color: #E3F2FD;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 2px solid #2196F3;
            text-align: center;
        }
        .q-text { font-size: 20px; font-weight: bold; color: #1565C0 !important; margin-bottom: 10px; }

        /* 歷史回憶卡片 */
        .history-card {
            background-color: #FFFFFF;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #E0E0E0;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        /* 儀表板卡片 */
        .dashboard-card {
            background-color: #FFFFFF;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #E0E0E0;
            margin-bottom: 20px;
        }
        
        /* 隱藏 Streamlit 選單 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def render_question_card(question):
    st.markdown(f"""
    <div class="question-card-active">
        <div class="q-text">{question}</div>
        <div style="font-size:14px; color:#555;">請按下錄音，自然地講述這段回憶...</div>
    </div>
    """, unsafe_allow_html=True)

def render_history_card(q, a):
    st.markdown(f"""
    <div class="history-card">
        <div class="history-q">Q: {q}</div>
        <div class="history-a">A: {a[:30]}...</div>
    </div>
    """, unsafe_allow_html=True)

def render_dashboard_card(title, content):
    st.markdown(f"""
    <div class="dashboard-card">
        <div style="color:#888; font-size:12px;">{title}</div>
        <div style="font-size:18px; font-weight:bold;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
