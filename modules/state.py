import streamlit as st

def init_session_state():
    defaults = {
        "user": None,
        "guest_data": None,
        "step": 1,
        "show_invite": False,
        "current_token": None,
        "call_status": "ringing",
        "friend_stage": "listen",
        "opening_played": False, # 防止重複播放
        "trans_text": "" # 語音轉文字暫存
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
