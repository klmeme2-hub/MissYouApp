import streamlit as st
from modules import ui, database, audio, brain

def render(supabase, client):
    owner_data = st.session_state.guest_data
    role_key = owner_data['role'] # friend, partner...
    role_name = role_key # 顯示用的角色代號 (可考慮轉中文)
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    
    persona_data = database.load_persona(supabase, role_key)
    display_name = persona_data.get('member_nickname', url_name) if persona_data else url_name

    # --- 自動播放開場白 (只在第一次進入時播放) ---
    if "opening_played" not in st.session_state:
        op_bytes = audio.get_audio_bytes(supabase, role_key, "opening")
        
        # 決定 AI 接話內容
        if role_key == "friend":
            ai_ask = "你覺得這個AI分身，跟我本尊有幾分像呢？幫我打個分數，拜託了。"
            ai_wav = audio.generate_speech(ai_ask, tier)
            final = audio.merge_audio_clips(op_bytes, ai_wav) if op_bytes else ai_wav
        else:
            ai_greet = audio.generate_speech("想我嗎？", tier)
            # 家人模式：若有 opening (其實是 nickname)，則拼接
            if not op_bytes and role_key != "friend":
                op_bytes = audio.get_audio_bytes(supabase, role_key, "nickname")
            final = audio.merge_audio_clips(op_bytes, ai_greet) if op_bytes else ai_greet
        
        if final: st.audio(final, format="audio/mp3", autoplay=True)
        st.session_state.opening_played = True

    # --- 顯示主要介面 ---
    
    # 狀態列
    engine_type = "elevenlabs" # 強制顯示為擬真
    ui.render_status_bar(tier, energy, 0, engine_type, is_guest=True)
    
    st.markdown(f"<h3 style='text-align:center;'>與 {display_name} 通話中...</h3>", unsafe_allow_html=True)
    
    # 分流邏輯：朋友才有九官鳥
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
                        
                        # 生成語音 (朋友模式強制用 ElevenLabs 驚艷對方)
                        forced_tier = 'advanced' if (role_key == "friend" or use_high) else 'basic'
                        wav = audio.generate_speech(ai_text, forced_tier)
                        
                        final = wav
                        if not parrot_mode and has_nick and wav:
                            nb = audio.get_audio_bytes(supabase, role_key, "nickname")
                            if nb: final = audio.merge_audio_clips(nb, wav)
                        
                        st.audio(final, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
            except: st.error("連線不穩")

    st.divider()
    
    # 離開按鈕
    if st.button("🚪 離開"):
        st.session_state.guest_data = None
        if "opening_played" in st.session_state: del st.session_state["opening_played"]
        st.query_params.clear()
        st.rerun()
    
    if role_key == "friend":
        st.info("😲 覺得像嗎？註冊免費獲得您的 AI 分身 👇")
        if st.button("👉 點此註冊"):
            st.session_state.guest_data = None
            st.query_params.clear()
            st.rerun()
