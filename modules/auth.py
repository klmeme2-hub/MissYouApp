# modules/auth.py
import streamlit as st

def login_user(supabase, email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        return None

def signup_user(supabase, email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response
    except Exception as e:
        return None

def check_admin_pass(input_pass):
    # 從 secrets 讀取管理員密碼
    if input_pass == st.secrets["ADMIN_PASSWORD"]:
        return True
    return False

def get_current_user_id():
    """取得目前登入者的 UUID"""
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.user.id
    if "guest_data" in st.session_state and st.session_state.guest_data:
        return st.session_state.guest_data['owner_id']
    return None
