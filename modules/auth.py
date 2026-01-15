import streamlit as st

def get_google_auth_url(supabase):
    """取得 Google 登入網址"""
    try:
        # 【關鍵修改】優先從 Secrets 讀取當前網址，如果沒設定，才用預設值
        # 這樣 Dev 版和 Prod 版就可以分開設定了
        redirect_url = st.secrets.get("CURRENT_URL", "https://missyou-test.streamlit.app")
        
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
