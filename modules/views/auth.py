import streamlit as st
import datetime
import os
import base64
from modules import auth, database
import extra_streamlit_components as stx

def get_base64_encoded_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except:
        return None

def render(supabase, cookie_manager, current_cookies):
    # 【關鍵修復 1】建立一個獨立的 Cookie 管理器，專門用於寫入
    # 使用 key="auth_writer" 避免與 app.py 的 key="main_cookie_mgr" 衝突
    cookie_writer = stx.CookieManager(key="auth_writer")

    saved_email = ""
    if current_cookies:
        saved_email = current_cookies.get("member_email", "")
    
    col1, col2 = st.columns([6, 4], gap="large")
    
    # --- 左側：品牌形象區 ---
    with col1:
        
        logo_html = ""
        if os.path.exists("logo.png"):
            img_b64 = get_base64_encoded_image("logo.png")
            if img_b64:
                logo_html = f'<img src="data:image/png;base64,{img_b64}" style="width: 80%; height: auto; object-fit: contain;">'
        
        if not logo_html:
            logo_html = '<span style="font-size: 50px;">♾️</span>'

        # 【關鍵修復 2】HTML 字串內容完全靠左，移除所有縮排
        # 請確保從 <div... 到 .../div> 都是貼在編輯器的最左邊
        html_content = f"""
<div style="padding-top: 40px; padding-right: 20px;">
<div style="display: flex; gap: 25px; align-items: center; margin-bottom: 40px;">
<div style="background: white; width: 110px; height: 110px; border-radius: 24px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 30px rgba(167, 139, 250, 0.2); flex-shrink: 0;">
{logo_html}
</div>
<div style="display: flex; flex-direction: column; justify-content: center;">
<h3 style="color: #FFFFFF !important; font-size: 32px !important; font-weight: 700; margin: 0; line-height: 1.2; letter-spacing: 1px;">
複刻你的數位聲紋
</h3>
<p style="font-family: 'Courier New', monospace; color: #A78BFA; font-weight: 600; font-size: 16px; margin-top: 8px; letter-spacing: 1px;">
Voice remains, Soul echoes.
</p>
</div>
</div>
<div style="font-size: 18px; line-height: 2.0; color: #E2E8F0; font-weight: 300; background: rgba(255, 255, 255, 0.03); padding: 30px; border-radius: 16px; border-left: 4px solid #A78BFA;">
<p>EchoSoul 利用最新的 AI 技術，為您鎸刻聲紋，將這份溫暖永久保存在元宇宙中。</p>
<p style="margin-top: 15px;">無論距離多遠，無論時間多久，只要點開，我就在。</p>
</div>
</div>
"""
        st.markdown(html_content, unsafe_allow_html=True)

    # --- 右側：登入註冊區 ---
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        with st.container():
            st.subheader("👤 會員登入")
            
            auth_url = auth.get_google_auth_url(supabase)
            
            tab_l, tab_s = st.tabs(["登入", "註冊"])
            
            with tab_l:
                with st.form("login_form"):
                    le = st.text_input("Email", value=saved_email)
                    lp = st.text_input("密碼", type="password")
                    
                    if st.form_submit_button("登入", use_container_width=True):
                        res = auth.login_user(supabase, le, lp)
                        if res and res.user:
                            # 【關鍵修復 3】使用 cookie_writer 寫入，而非 cookie_manager
                            expires = datetime.datetime.now() + datetime.timedelta(days=30)
                            cookie_writer.set("member_email", le, expires_at=expires)
                            cookie_writer.set("sb_access_token", res.session.access_token, expires_at=expires)
                            cookie_writer.set("sb_refresh_token", res.session.refresh_token, expires_at=expires)
                            
                            st.session_state.user = res
                            st.success("登入成功！")
                            st.rerun()
                        else:
                            st.error("登入失敗")

                st.markdown("""<div style="text-align:center; margin: 15px 0; color:#666; font-size:12px;">- OR -</div>""", unsafe_allow_html=True)
                
                if auth_url:
                    st.link_button("G 使用 Google 帳號繼續", auth_url, type="primary", use_container_width=True)
                else:
                    st.error("Google 登入設定未完成")

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
                        st.error("註冊失敗，Email 可能已被使用")

            st.markdown("""
            <div style="margin-top: 30px; font-size: 12px; color: #666; text-align: center; border-top: 1px solid #333; padding-top: 15px;">
                點擊登入即代表您同意 
                <a href="/服務條款" target="_self" style="color: #888; text-decoration: none;">服務條款</a> 與 
                <a href="/隱私權政策" target="_self" style="color: #888; text-decoration: none;">隱私權政策</a>
                <div style="margin-top: 20px; font-family: monospace; color: #555;">
                © 2026 EchoSoul. All rights reserved.
                </div>
            </div>
            """, unsafe_allow_html=True)
