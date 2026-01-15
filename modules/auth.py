import streamlit as st

def get_google_auth_url(supabase):
    """取得 Google 登入網址"""
    try:
        # 1. 優先從 Secrets 讀取
        # 2. 如果 Secrets 沒設，回退到測試版網址 (Hardcode fallback)
        redirect_url = st.secrets.get("CURRENT_URL", "https://missyou-test.streamlit.app")
        
        # 【關鍵修正】強制移除尾部的斜線 '/'，避免 Supabase 判定不符
        if redirect_url.endswith("/"):
            redirect_url = redirect_url[:-1]

        # 印出網址以便除錯 (可在右下角 Manage app -> Logs 看到)
        print(f"DEBUG: Redirect URL is set to: {redirect_url}")

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
