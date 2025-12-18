import streamlit as st
from modules import audio
from modules.config import ROLE_MAPPING

def render(supabase, tier, xp):
    """
    Tab 5: 完美暱稱 & 身分設定
    """
    if tier == 'basic' and xp < 20:
        st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        return

    st.subheader("🎯 完美暱稱與身分設定")
    st.info("設定親友聽到的稱呼，並錄製一段真實呼喚，讓 AI 在開頭直接播放這段錄音。")
    
    # 1. 選擇角色
    nick_role = st.selectbox("設定哪位親友？", list(ROLE_MAPPING.keys()), key="nr_select")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 步驟 1：身分設定 (文字)")
        st.caption("當這位親友登入時，他會看到誰？")
        
        # 這裡從資料庫讀取舊的設定 (如果有的話)
        # 為了簡化，我們先不讀取舊值顯示在框框(需要額外查詢)，直接讓用戶輸入更新
        my_nick = st.text_input(f"請輸入 {nick_role} 平常怎麼叫您？", placeholder="例如：老公、阿強、爸爸", key="my_nick_input")
        
        if st.button("💾 儲存身分稱呼"):
            if my_nick:
                from modules import database # 延遲引用避免循環
                # 這裡我們只更新 member_nickname，content (人設) 暫時保留原樣或讀取後更新
                # 為了方便，我們假設人設已存在。如果不存在，這個動作會新建一個空白人設只存暱稱
                current_persona = database.load_persona(supabase, nick_role)
                content = current_persona['content'] if current_persona else "尚未設定人設"
                
                database.save_persona_summary(supabase, nick_role, content, member_nickname=my_nick)
                st.success(f"已更新！當 {nick_role} 登入時，會顯示「與 [{my_nick}] 通話中」。")
            else:
                st.error("請輸入稱呼")

    with col2:
        st.markdown("#### 步驟 2：完美暱稱 (聲音)")
        st.caption(f"錄下您平常呼喚 {nick_role} 的聲音 (Audio Injection)")
        
        st.markdown(f"請按下錄音，喊一聲：**「{nick_role}～」** (建議 2-3 秒)")
        real_nick_audio = st.audio_input("錄製", key="real_nick_rec_tab5")
        
        if real_nick_audio:
            if st.button("💾 上傳真實聲音"):
                with st.spinner("處理中..."):
                    if audio.upload_nickname_audio(supabase, nick_role, real_nick_audio.read()):
                        st.success("成功！AI 將使用這段錄音作為開場。")
