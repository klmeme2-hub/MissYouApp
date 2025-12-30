import streamlit as st
from modules import ui, database, audio, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory

def render(supabase, client):
    user = st.session_state.user
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    
    # 1. Header (使用您確認過的穩定排版)
    col_head_main, col_head_info = st.columns([7, 3], vertical_alignment="bottom")
    
    with col_head_main:
        st.markdown("""
        <div class="header-title">🌌 元宇宙聲紋站</div>
        <div class="header-subtitle">元宇宙的第一張通行證：鎸刻你的數位聲紋</div>
        """, unsafe_allow_html=True)
        
    with col_head_info:
        # 這裡不使用複雜 CSS，直接顯示登出鈕，簡單整齊
        st.markdown(f"<div style='text-align:right; font-size:12px; color:#888; margin-bottom:5px;'>{user.user.email}</div>", unsafe_allow_html=True)
        # 您想要登出鈕移到下面，這裡我就只保留 Email 顯示
        # 登出按鈕移至頁面最底端

    # 2. 狀態列
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile))
    
    # 3. 角色與分享
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    c_role, c_btn = st.columns([7, 3], vertical_alignment="bottom")
    with c_role:
        disp_role = st.selectbox("選擇對象", allowed, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[disp_role]
    
    has_op = audio.get_audio_bytes(supabase, target_role, "opening")
    
    with c_btn:
        if st.button("🎁 生成邀請卡", type="primary", use_container_width=True):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True

    if not has_op and target_role == "friend": st.caption("⚠️ 尚未錄製口頭禪")

    # 邀請卡彈窗
    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        
        st.markdown('<div class="compact-divider"></div>', unsafe_allow_html=True)
        st.success(f"💌 邀請連結 ({disp_role})")
        copy_text = f"欸！點這個連結打電話給我：\n{url}"
        st.code(url)
        st.text_area("建議文案", value=copy_text)
        if st.button("❌ 關閉"): st.session_state.show_invite = False
    
    st.markdown('<div class="compact-divider"></div>', unsafe_allow_html=True)

    # 4. Tab 分頁
    t1, t2, t3, t4 = st.tabs(["🧬 聲紋訓練", "💎 等級說明", "📝 人設補完", "🧠 回憶補完"])

    with t1: tab_voice.render(supabase, client, user.user.id, target_role, tier)
    with t2: tab_store.render(supabase, user.user.id, xp)
    with t3: tab_persona.render(supabase, client, user.user.id, target_role, tier, xp)
    with t4: tab_memory.render(supabase, client, user.user.id, target_role, tier, xp, question_db) # 需傳入 question_db

    # 5. 底部登出
    st.divider()
    c_i, c_o = st.columns([8, 2], vertical_alignment="center")
    with c_i: st.caption("系統版本：SaaS Beta 4.12")
    with c_o:
        if st.button("登出", key="footer_logout", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
