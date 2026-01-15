import streamlit as st

def get_google_auth_url(supabase):
    """取得 Google 登入網址"""
    try:
        redirect_url = st.secrets.get("CURRENT_URL", "https://missyou-test.streamlit.app")
        if redirect_url.endswith("/"): redirect_url = redirect_url[:-1]

        res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect_url, "skip_browser_redirect": True}
        })
        return res.url
    except Exception as e:
        print(f"Auth Error: {e}")
        return None

def get_google_btn_html(auth_url):
    """
    生成強制在當前分頁開啟的 HTML 按鈕
    樣式模仿 Streamlit 原生 Primary Button
    """
    return f"""
    <a href="{auth_url}" target="_self" style="text-decoration: none;">
        <div style="
            width: 100%;
            background: linear-gradient(135deg, #FF4B4B 0%, #FF2B2B 100%);
            color: white;
            padding: 0.6rem;
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
            font-family: 'Source Sans Pro', sans-serif;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: transform 0.1s;
        " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
            G 使用 Google 帳號繼續
        </div>
    </a>
    """

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
