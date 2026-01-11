import streamlit as st
from modules import ui, database, audio, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory

def render(supabase, client, question_db):
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    
    # 1. Header (自定義 HTML 結構)
    # 這裡將標題、圖示、Email 整合在一個 Flexbox 容器中，確保對齊
    st.markdown(f"""
    <div class="brand-container">
        <div class="brand-icon">♾️</div>
        <div class="brand-text" style="flex-grow: 1;">
            <h1>EchoSoul · 聲紋ID刻錄室</h1>
            <p class="brand-subtitle">這不僅僅是錄音，這是將你的聲紋數據化，作為你在數位世界唯一的身份識別</p>
        </div>
        <div class="user-pill">
            {st.session_state.user.user.email}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 狀態列
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile))
    
    # 3. 角色與分享控制台
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    # 使用 columns 的 bottom 對齊參數
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

    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        
        st.success(f"💌 邀請連結 ({disp_role})")
        st.code(url)
        if st.button("❌ 關閉"): st.session_state.show_invite = False
    
    # 增加一點間距
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 4. Tab 分頁
    t1, t2, t3, t4 = st.tabs(["🧬 聲紋訓練", "📝 人設補完", "🧠 回憶補完", "💎 等級說明"])

    with t1: tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, tier)
    with t2: tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t3: tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
    with t4: tab_store.render(supabase, st.session_state.user.user.id, xp)

    # 5. 底部登出區
    st.markdown("<br><br><br>", unsafe_allow_html=True) # 增加底部留白
    c_null, c_logout = st.columns([8, 2])
    with c_logout:
        if st.button("登出", key="footer_logout", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
