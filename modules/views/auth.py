import streamlit as st
import datetime
from modules import auth, database

def render(supabase, cookie_manager):
    # 讀取 Cookie
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    
    # 左右分欄
    col1, col2 = st.columns([6, 4], gap="large")
    
    # --- 左側：品牌形象區 (Brand) ---
    with col1:
        # 【關鍵修正】這裡的 HTML 字串全部靠左對齊，不能有任何縮排
        html_content = """
<div style="padding-top: 20px;">
<h1 style="font-size: 56px !important; font-weight: 800; background: linear-gradient(135deg, #FFFFFF 0%, #A78BFA 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0px; line-height: 1.2;">
元宇宙・聲紋 ID
</h1>
<h3 style="color: #94A3B8 !important; font-size: 24px !important; font-weight: 400; margin-top: 0; margin-bottom: 40px; letter-spacing: 1px;">
複製一個你，活在元宇宙
</h3>
<div style="background: rgba(255, 255, 255, 0.05); border-left: 5px solid #FF4B4B; padding: 25px; border-radius: 0 16px 16px 0; margin-bottom: 40px; backdrop-filter: blur(10px);">
<p style="font-size: 22px; font-weight: bold; color: #FFF !important; margin: 0; line-height: 1.5;">
「現在錄音，3 分鐘生成你的 AI 數位分身。」
</p>
</div>
<div style="font-size: 18px; line-height: 1.8; color: #CCC; font-weight: 300;">
<p style="margin-bottom: 10px;">這是你在元宇宙的入門儀式。</p>
<p style="margin-bottom: 10px;">透過聲紋鎸刻技術，創造一個能說、能思考、擁有你回憶的 AI。</p>
<p style="margin-top: 20px; color: #818CF8; font-weight: 500;">先拿朋友試試看？還是留給最愛的家人？由你決定。</p>
</div>
</div>
"""
        st.markdown(html_content, unsafe_allow_html=True)

    # --- 右側：會員登入區 (Login) ---
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # 這裡移除了 border=True
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
                        st.session_state.user = res
                        st.success("註冊成功！")
                        st.rerun()
                    else:
                        st.error("註冊失敗，Email 可能已被使用")

            st.markdown("""
            <div style="margin-top: 20px; font-size: 12px; color: #666; text-align: center; border-top: 1px solid #333; padding-top: 10px;">
                點擊註冊即代表您同意 
                <a href="/服務條款" target="_self" style="color: #888; text-decoration: none;">服務條款</a> 與 
                <a href="/隱私權政策" target="_self" style="color: #888; text-decoration: none;">隱私權政策</a>
            </div>
            """, unsafe_allow_html=True)
