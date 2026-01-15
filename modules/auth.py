import streamlit as st

def get_google_auth_url(supabase):
    """取得 Google 登入網址"""
    try:
        # 讀取 Secrets
        redirect_url = st.secrets.get("CURRENT_URL", "https://missyou.streamlit.app")
        
        # 去除尾部斜線 (防呆)
        if redirect_url.endswith("/"):
            redirect_url = redirect_url[:-1]

        # 這裡不使用 skip_browser_redirect，讓它生成標準網址
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url,
            }
        })
        return res.url
    except Exception as e:
        print(f"Auth Error: {e}")
        return None

def login_user(supabase, email, password):
    try:
        return supabase.auth.sign_in_with_password({"email": email, "password": password})
    except: return None

def signup_user(supabase, email, password):
    try:
        return supabase.auth.sign_up({"email": email, "password": password})
    except: return None

def get_current_user_id():
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.user.id
    if "guest_data" in st.session_state and st.session_state.guest_data:
        return st.session_state.guest_data['owner_id']
    return None
