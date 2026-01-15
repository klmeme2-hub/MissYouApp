import streamlit as st
import datetime
import time # 補上
from modules import auth, database

def render(supabase, cookie_manager, current_cookies):
    
    saved_email = ""
    if current_cookies:
        saved_email = current_cookies.get("member_email", "")
    
    col1, col2 = st.columns([6, 4], gap="large")
    
    # 左側
    with col1:
        html_content = """
<div style="padding-top: 40px; padding-right: 20px;">
<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
<span style="font-size: 48px;">♾️</span> 
<h1 style="font-size: 48px !important; font-weight: 800; background: linear-gradient(135deg, #FFFFFF 0%, #A78BFA 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0px; line-height: 1.2;">
EchoSoul
</h1>
</div>
<h3 style="color: #94A3B8 !important; font-size: 24px !important; font-weight: 400; margin-top: 0; margin-bottom: 40px; letter-spacing: 2px;">
複刻你的數位聲紋
</h3>
<div style="font-size: 18px; line-height: 2.0; color: #E2E8F0; font-weight: 300; background: rgba(255, 255, 255, 0.05); padding: 30px; border-radius: 16px; border-left: 4px solid #A78BFA;">
<p>EchoSoul 利用最新的 AI 技術，為您鎸刻聲紋，將這份溫暖永久保存在元宇宙中。</p>
<p>無論距離多遠，無論時間多久，只要點開，我就在。</p>
<p style="margin-top: 25px; color: #A78BFA; font-weight: 600; font-family: 'Courier New', monospace;">
Voice remains, Soul echoes.
</p>
</div>
</div>
"""
        st.markdown(html_content, unsafe_allow_html=True)

    # 右側
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container():
            st.subheader("👤 會員登入")
            
            # Google 按鈕
            auth_url = auth.get_google_auth_url(supabase)
            if auth_url:
                st.link_button("G 使用 Google 帳號繼續", auth_url, type="primary", use_container_width=True)
            else:
                st.error("Google 登入設定未完成")

            st.markdown("""<div style="text-align:center; margin: 20px 0; color:#666; font-size:12px;">- OR -</div>""", unsafe_allow_html=True)
            
            tab_l, tab_s = st.tabs(["登入", "註冊"])
            
            with tab_l:
                with st.form("login_form"):
                    le = st.text_input("Email", value=saved_email)
                    lp = st.text_input("密碼", type="password")
                    if st.form_submit_button("登入", use_container_width=True):
                        res = auth.login_user(supabase, le, lp)
                        if res and res.user:
                            # 【關鍵修復】存入 Cookie 並等待
                            expires = datetime.datetime.now() + datetime.timedelta(days=30)
                            cookie_manager.set("member_email", le, expires_at=expires)
                            cookie_manager.set("sb_access_token", res.session.access_token, expires_at=expires)
                            cookie_manager.set("sb_refresh_token", res.session.refresh_token, expires_at=expires)
                            
                            st.success("登入成功！")
                            time.sleep(2) # 等待寫入
                            
                            st.session_state.user = res
                            st.rerun()
                        else:
                            st.error("登入失敗")
            
            with tab_s:
                st.caption("✨ 註冊即送 **免費體驗點數**")
                se = st.text_input("Email", key="s_e")
                sp = st.text_input("設定密碼", type="password", key="s_p")
                if st.button("註冊", use_container_width=True):
                    res = auth.signup_user(supabase, se, sp)
                    if res and res.user:
                        database.get_user_profile(supabase, res.user.id)
                        st.session_state.user = res
                        st.success("註冊成功！")
                        st.rerun()
                    else:
                        st.error("註冊失敗")

            st.markdown("""<div style="margin-top:20px; font-size:12px; color:#666; text-align:center;">© 2026 EchoSoul. All rights reserved.</div>""", unsafe_allow_html=True)
