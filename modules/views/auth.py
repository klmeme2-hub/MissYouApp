import streamlit as st
import datetime
from modules import auth, database

def render(supabase, cookie_manager):
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    
    col1, col2 = st.columns([6, 4], gap="large")
    
    # 左側：品牌形象區
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
<div style="font-size: 18px; line-height: 2.0; color: #E2E8F0; font-weight: 300; background: rgba(255, 255, 255, 0.03); padding: 30px; border-radius: 16px; border-left: 4px solid #A78BFA;">
<p>EchoSoul 利用最新的 AI 技術，為您鎸刻聲紋，將這份溫暖永久保存在元宇宙中。</p>
<p>無論距離多遠，無論時間多久，只要點開，我就在。</p>
<p style="margin-top: 25px; color: #A78BFA; font-weight: 600; font-family: 'Courier New', monospace;">
Voice remains, Soul echoes.
</p>
</div>
</div>
"""
        st.markdown(html_content, unsafe_allow_html=True)

    # 右側：會員登入區
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        with st.container():
            st.subheader("👤 會員登入")
            
            tab_l, tab_s = st.tabs(["登入", "註冊"])
            
            with tab_l:
                with st.form("login_form"):
                    le = st.text_input("Email", value=saved_email)
                    lp = st.text_input("密碼", type="password")
                    
                    if st.form_submit_button("登入", use_container_width=True, type="primary"):
                        res = auth.login_user(supabase, le, lp)
                        if res and res.user:
                            cookie_manager.set("member_email", le, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                            st.session_state.user = res
                            st.rerun()
                        else:
                            st.error("登入失敗，請檢查帳號密碼")
            
            with tab_s:
                st.caption("✨ 註冊即送 **免費體驗點數**")
                se = st.text_input("Email", key="s_e")
                sp = st.text_input("設定密碼", type="password", key="s_p")
                
                if st.button("註冊", use_container_width=True):
                    res = auth.signup_user(supabase, se, sp)
                    if res and res.user:
                        # 初始化新用戶資料
                        database.get_user_profile(supabase, res.user.id)
                        
                        # 【關鍵修改】檢查是否有推薦人 (guest_data)
                        if st.session_state.guest_data:
                            referrer_id = st.session_state.guest_data['owner_id']
                            # 給邀請人 +10 XP
                            database.reward_referrer(supabase, referrer_id, se)
                        
                        st.session_state.user = res
                        st.success("註冊成功！")
                        st.rerun()
                    else:
                        st.error("註冊失敗，Email 可能已被使用")

            st.markdown("""
            <div style="margin-top: 20px; font-size: 12px; color: #666; text-align: center; border-top: 1px solid #333; padding-top: 15px;">
                點擊註冊即代表您同意 
                <a href="/服務條款" target="_self" style="color: #888; text-decoration: none;">服務條款</a> 與 
                <a href="/隱私權政策" target="_self" style="color: #888; text-decoration: none;">隱私權政策</a>
                <div style="margin-top: 20px; font-family: monospace; color: #555;">
                © 2026 EchoSoul. All rights reserved.
                </div>
            </div>
            """, unsafe_allow_html=True)
