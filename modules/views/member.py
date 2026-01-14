import streamlit as st
from modules import ui, database, audio, config, gamification
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory

def render(supabase, client, question_db):
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    user_id = st.session_state.user.user.id
    
    # 1. Header
    col_head_main, col_head_info = st.columns([7, 3], vertical_alignment="bottom")
    with col_head_main:
        st.markdown("""<div class="header-title">EchoSoul · 聲紋ID刻錄室</div><div class="header-subtitle">這不僅僅是錄音，這是將你的聲紋數據化，作為你在數位世界唯一的身份識別</div>""", unsafe_allow_html=True)
    with col_head_info:
        st.markdown(f"<div class='user-info-box'><div class='user-email'>{st.session_state.user.user.email}</div></div>", unsafe_allow_html=True)

    # 2. 角色選擇 (必須在狀態列之前，因為要計算該角色的相似度)
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    # 為了版面，這裡先不顯示 Selectbox，但邏輯上我們需要知道現在選誰
    # 我們使用 session state 來暫存選擇，或者直接在這裡渲染 Selectbox
    # 為了對齊，我們把 Selectbox 放在下面，但預設值先取出來算分數
    
    # 這裡有點 tricky，為了算出分數傳給 status bar，我們需要先知道 target_role
    # 解決方案：先渲染狀態列下面的控制區，取得 target_role，再重新渲染狀態列 (不推薦)
    # 更好的方案：狀態列不依賴 target_role，或者預設顯示朋友的分數
    # 這裡我們採取：先渲染 Selectbox 區塊 (順序交換一下)
    
    # --- 控制台區塊 (提前) ---
    c_role, c_btn = st.columns([7, 3], vertical_alignment="bottom")
    with c_role:
        disp_role = st.selectbox("選擇對象", allowed, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[disp_role]
    with c_btn:
        if st.button("🎁 生成邀請卡", type="primary", use_container_width=True):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True

    # 3. 計算相似度
    sim_score, sim_hint, sim_gain = gamification.calculate_similarity(supabase, user_id, target_role)

    # 4. 狀態列 (現在有數據了)
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile), sim_score, sim_hint, sim_gain)
    
    # --- 繼續顯示其他內容 ---
    has_op = audio.get_audio_bytes(supabase, target_role, "opening")
    if not has_op and target_role == "friend": st.caption("⚠️ 尚未錄製口頭禪")

    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        st.markdown('<div style="margin:20px 0;"></div>', unsafe_allow_html=True)
        st.success(f"💌 邀請連結 ({disp_role})")
        copy_text = f"欸！點這個連結打電話給我：\n{url}"
        st.code(url)
        st.text_area("建議文案", value=copy_text)
        if st.button("❌ 關閉"): st.session_state.show_invite = False
    
    st.markdown('<div style="margin:20px 0;"></div>', unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["🧬 聲紋訓練", "📝 人設補完", "🧠 回憶補完", "💎 等級說明"])

    with t1: tab_voice.render(supabase, client, user_id, target_role, tier)
    with t2: tab_persona.render(supabase, client, user_id, target_role, tier, xp)
    with t3: tab_memory.render(supabase, client, user_id, target_role, tier, xp, question_db)
    with t4: tab_store.render(supabase, st.session_state.user.user.id, xp)

    # 5. 底部登出
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.divider()
    c_null, c_logout = st.columns([8, 2])
    with c_logout:
        if st.button("登出", key="footer_logout", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
