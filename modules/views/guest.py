import streamlit as st
from modules import ui, database, audio, brain

def render(supabase, client):
    owner_data = st.session_state.guest_data
    role_key = owner_data['role'] 
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    # 1. 取得資料
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    persona_data = database.load_persona(supabase, role_key)
    display_name = persona_data.get('member_nickname', url_name) if persona_data else url_name

    # --- 【修正1】 加入品牌 Header (與會員後台一致) ---
    st.markdown("""
    <div class="brand-header">
        <div style="font-size: 40px;">♾️</div>
        <div>
            <div class="header-title">EchoSoul · 聲紋ID刻錄室</div>
            <div class="header-subtitle">這不僅僅是錄音，這是將你的聲紋數據化，作為你在數位世界唯一的身份識別</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 自動執行每日簽到
    if "daily_checked" not in st.session_state:
        database.check_daily_interaction(supabase, owner_id)
        st.session_state.daily_checked = True

    # 3. 準備開場白音訊 (先準備資料，暫不播放)
    audio_to_play = None
    
    if "opening_played" not in st.session_state:
        op_bytes = audio.get_audio_bytes(supabase, role_key, "opening")
        if not op_bytes and role_key != "friend":
            op_bytes = audio.get_audio_bytes(supabase, role_key, "nickname")
            
        if role_key == "friend":
            ai_ask = "你覺得這個AI分身，跟我本尊有幾分像呢？幫我打個分數，拜託了。"
            ai_wav = audio.generate_speech(ai_ask, tier)
            final = audio.merge_audio_clips(op_bytes, ai_wav) if op_bytes else ai_wav
        else:
            ai_greet = audio.generate_speech("想我嗎？", tier)
            final = audio.merge_audio_clips(op_bytes, ai_greet) if op_bytes else ai_greet
        
        audio_to_play = final
        st.session_state.opening_played = True

    # --- 【修正2】 先顯示狀態列 ---
    engine_type = "elevenlabs" # 訪客端統一顯示
    ui.render_status_bar(tier, energy, 0, engine_type, is_guest=True, member_name=display_name)

    # --- 【修正2】 再顯示播放器 (這樣就會在狀態列下方) ---
    if audio_to_play: 
        st.audio(audio_to_play, format="audio/mp3", autoplay=True)
    
    # 顯示對話標題
    st.markdown(f"<h3 style='text-align:center;'>與 {display_name} 通話中...</h3>", unsafe_allow_html=True)
    
    if role_key == "friend":
        parrot_mode = st.toggle("🦜 九官鳥模式 (我說什麼他學什麼)")
        cost = 0
    else:
        parrot_mode = False
        use_high = st.toggle("👑 高傳真線路 (消耗2電量)", value=True)
        cost = 2 if use_high else 1

    if energy <= 0:
        st.error("💔 電量耗盡")
        if st.button(f"🔋 幫 {display_name} 儲值 $88"):
            database.update_profile_stats(supabase, owner_id, energy_delta=100)
            st.rerun()
    else:
        audio_val = st.audio_input("請說話...", key="guest_rec")
        if audio_val:
            try:
                database.update_profile_stats(supabase, owner_id, energy_delta=-cost)
                user_text = brain.transcribe_audio(audio_val)
                if len(user_text.strip()) > 0:
                    with st.spinner("..."):
                        if parrot_mode:
                            ai_text = user_text
                        else:
                            mems = database.get_all_memories_text(supabase, role_key)
                            has_nick = audio.get_audio_bytes(supabase, role_key, "nickname") is not None
                            ai_text = brain.think_and_reply(tier, persona_data, mems, user_text, has_nick)
                        
                        forced_tier = 'advanced' if (role_key!="friend" and use_high) else 'basic'
                        wav = audio.generate_speech(ai_text, forced_tier)
                        
                        final = wav
                        if not parrot_mode and has_nick and wav:
                            nb = audio.get_audio_bytes(supabase, role_key, "nickname")
                            if nb: final = audio.merge_audio_clips(nb, wav)
                        
                        st.audio(final, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
            except: st.error("連線不穩")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- 【修正3】 已移除「離開」按鈕 ---
    
    if role_key == "friend":
        st.info("😲 覺得像嗎？註冊免費獲得您的 AI 分身 👇")
        if st.button("👉 點此註冊"):
            st.session_state.guest_data = None
            st.query_params.clear()
            st.rerun()
