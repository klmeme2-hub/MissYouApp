import streamlit as st
import datetime
from modules import auth, database

def render(supabase, cookie_manager):
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    saved_token = cookies.get("guest_token", "")
    
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("## 👋 我是親友")
        token_input = st.text_input("通行碼", value=saved_token, placeholder="A8K29")
        if st.button("🚀 開始對話", type="primary"):
            d = database.validate_token(supabase, token_input.strip())
            if d:
                cookie_manager.set("guest_token", token_input.strip(), expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.session_state.guest_data = {'owner_id': d['user_id'], 'role': d['role']}
                st.rerun()
            else: st.error("無效")
    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        with tab_l:
            with st.form("login"):
                le = st.text_input("Email", value=saved_email)
                lp = st.text_input("密碼", type="password")
                if st.form_submit_button("登入"):
                    r = auth.login_user(supabase, le, lp)
                    if r and r.user:
                        cookie_manager.set("member_email", le, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                        st.session_state.user = r
                        st.rerun()
                    else: st.error("失敗")
        with tab_s:
            se = st.text_input("Email", key="se")
            sp = st.text_input("密碼", type="password", key="sp")
            if st.button("註冊"):
                r = auth.signup_user(supabase, se, sp)
                if r and r.user:
                    database.get_user_profile(supabase, r.user.id)
                    st.session_state.user = r
                    st.success("成功")
                    st.rerun()
                else: st.error("失敗")
