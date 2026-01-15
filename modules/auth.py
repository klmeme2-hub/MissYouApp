import streamlit as st

def get_google_auth_url(supabase):
    """取得 Google 登入網址"""
    try:
        # 優先讀取 Secrets 設定的網址
        # 如果沒設定，才用預設值 (這樣可以避免本地端和雲端網址混亂)
        redirect_url = st.secrets.get("CURRENT_URL", "https://missyou-test.streamlit.app")
        
        # 移除尾部的斜線，避免 Supabase 驗證失敗
        if redirect_url.endswith("/"):
            redirect_url = redirect_url[:-1]

        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url
            }
        })
        return res.url
    except Exception as e:
        print(f"Auth Error: {e}")
        return None

def login_user(supabase, email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except: return None

def signup_user(supabase, email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response
    except: return None

def get_current_user_id():
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.user.id
    if "guest_data" in st.session_state and st.session_state.guest_data:
        return st.session_state.guest_data['owner_id']
    return None
