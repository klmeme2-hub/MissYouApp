import streamlit as st

def get_google_auth_url(supabase):
    """取得 Google 登入網址"""
    try:
        # 讀取 Secrets，預設為測試版
        redirect_url = st.secrets.get("CURRENT_URL", "https://missyou-test.streamlit.app")
        
        # 移除尾部斜線
        if redirect_url.endswith("/"):
            redirect_url = redirect_url[:-1]

        # 使用 PKCE 流程（Supabase 預設）
        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url,
                "skip_browser_redirect": True,
                "queryParams": {
                    "access_type": "offline",
                    "prompt": "consent"
                }
            }
        })
        return res.url
    except Exception as e:
        st.error(f"OAuth 設定錯誤: {e}")
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
    # 優先檢查 session_state
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.user.id
    # 其次檢查 guest_data
    if "guest_data" in st.session_state and st.session_state.guest_data:
        return st.session_state.guest_data['owner_id']
    
    return None
