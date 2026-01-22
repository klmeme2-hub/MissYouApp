import streamlit as st
from modules import ui, database, audio, config, gamification
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory

def render(supabase, client, question_db):
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    user_id = st.session_state.user.user.id
    
    # ==========================================
    # 1. Header (僅標題)
    # ==========================================
    
    title_html = """
<h1 style="
    font-size: 42px !important; 
    font-weight: 800; 
    margin: 0 !important; 
    padding: 0 !important; 
    line-height: 1.2 !important; 
    background: linear-gradient(90deg, #FFFFFF, #A78BFA, #22D3EE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
">
聲紋ID刻錄室
</h1>
<p style="
    font-size: 15px !important; 
    color: #94A3B8 !important; 
    margin: 8px 0 0 0 !important; 
    font-weight: 500; 
    line-height: 1.6 !important;
    letter-spacing: 0.5px;
">
這不僅僅是錄音，這是將你的聲紋數據化，作為你在數位世界唯一的身份識別
</p>
"""
    st.markdown(title_html, unsafe_allow_html=True)

    # ==========================================
    # 2. 控制台 (角色選擇 + 生成按鈕)
    # ==========================================
    
    # 為了計算狀態列的分數，我們先渲染控制台來確定 target_role
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    # 使用玻璃擬態容器包裹控制區

    
    c_role, c_btn = st.columns([7, 3], vertical_alignment="bottom")
    
    with c_role:
        st.markdown("<div style='color:#A78BFA; font-size:14px; font-weight:600; margin-bottom:5px;'>選擇對話/錄製對象</div>", unsafe_allow_html=True)
        disp_role = st.selectbox("選擇對象", allowed, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[disp_role]
    
    with c_btn:
        if st.button("🎁 生成邀請卡", type="primary", use_container_width=True):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True

    # 閉合玻璃擬態容器


    # ==========================================
    # 3. 狀態列 (放在控制台下方)
    # ==========================================
    
    # 計算相似度
    sim_score, sim_hint, sim_gain = gamification.calculate_similarity(supabase, user_id, target_role)
    
    # 顯示狀態列
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile), sim_score, sim_hint, sim_gain)
    
    # 提示訊息
    has_op = audio.get_audio_bytes(supabase, target_role, "opening")
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

    # ==========================================
    # 4. Tab 分頁
    # ==========================================
    t1, t2, t3, t4 = st.tabs(["🧬 聲紋訓練", "📝 人設補完", "🧠 回憶補完", "💎 等級說明"])

    with t1: 
        tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, tier)
    with t2: 
        tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t3: 
        tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
    with t4: 
        tab_store.render(supabase, st.session_state.user.user.id, xp)

    # ==========================================
    # 5. 底部登出區
    # ==========================================
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.divider()
    
    c_email, c_logout = st.columns([8, 2], vertical_alignment="center")
    
    with c_email:
        st.markdown(f"<div style='text-align:right; color:#666; font-size:14px;'>目前登入：{st.session_state.user.user.email}</div>", unsafe_allow_html=True)
        
    with c_logout:
        if st.button("登出", key="footer_logout", use_container_width=True):
            st.session_state.logout_clicked = True
            st.rerun()
