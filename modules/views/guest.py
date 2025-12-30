import streamlit as st
from modules import ui, database, audio, brain

def render(supabase, client):
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    persona_data = database.load_persona(supabase, role_name)
    display_name = persona_data.get('member_nickname', url_name) if persona_data else url_name

    # 階段 1: 來電模擬
    if st.session_state.call_status == "ringing":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(f"<div style='text-align:center; padding-top:50px;'><div style='font-size:80px;'>👤</div><h1>{display_name}</h1><p style='color:#CCC; animation:blink 1.5s infinite;'>📞 來電中...</p></div><style>@keyframes blink {{0%{{opacity:1}} 50%{{opacity:0.5}} 100%{{opacity:1}}}}</style>", unsafe_allow_html=True)
            if st.button("🟢 接聽", use_container_width=True, type="primary"):
                st.session_state.call_status = "connected"
                database.check_daily_interaction(supabase, owner_id)
                st.rerun()

    # 階段 2: 通話中
    elif st.session_state.call_status == "connected":
        # 開場白邏輯
        if "opening_played" not in st.session_state:
            op_bytes = audio.get_audio_bytes(supabase, role_name, "opening")
            # 如果是家人且沒開場白，嘗試找暱稱
            if not op_bytes and role_name != "friend": 
                op_bytes = audio.get_audio_bytes(supabase, role_name, "nickname")
            
            if role_name == "friend":
                ai_ask = "你覺得這個AI分身，跟我本尊有幾分像呢？幫我打個分數，拜託了。"
                ai_wav = audio.generate_speech(ai_ask, tier)
                final = audio.merge_audio_clips(op_bytes, ai_wav) if op_bytes else ai_wav
            else:
                ai_greet = audio.generate_speech("想我嗎？", tier)
                final = audio.merge_audio_clips(op_bytes, ai_greet) if op_bytes else ai_greet
            
            if final: st.audio(final, format="audio/mp3", autoplay=True)
            st.session_state.opening_played = True

        ui.render_status_bar(tier, energy, 0, audio.get_tts_engine_type(profile), is_guest=True)
        st.markdown(f"<h4 style='text-align:center;'>與 {display_name} 通話中...</h4>", unsafe_allow_html=True)
        
        # 模式開關
        if role_name == "friend":
            parrot_mode = st.toggle("🦜 九官鳥模式")
            cost = 0
        else:
            parrot_mode = False
            use_high = st.toggle("👑 高傳真線路 (消耗2電量)", value=False)
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
                            if parrot_mode: ai_text = user_text
                            else:
                                mems = database.get_all_memories_text(supabase, role_name)
                                has_nick = audio.get_audio_bytes(supabase, role_name, "nickname") is not None
                                ai_text = brain.think_and_reply(tier, persona_data, mems, user_text, has_nick)
                            
                            forced_tier = 'advanced' if (role_name!="friend" and use_high) else 'basic'
                            wav = audio.generate_speech(ai_text, forced_tier)
                            
                            final = wav
                            if not parrot_mode and has_nick and wav:
                                nb = audio.get_audio_bytes(supabase, role_name, "nickname")
                                if nb: final = audio.merge_audio_clips(nb, wav)
                            
                            st.audio(final, format="audio/mp3", autoplay=True)
                            st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
                except: st.error("連線不穩")

    st.divider()
    if st.button("🔴 掛斷"):
        st.session_state.guest_data = None
        st.session_state.call_status = "ringing"
        if "opening_played" in st.session_state: del st.session_state["opening_played"]
        st.query_params.clear()
        st.rerun()
    
    if role_name == "friend":
        st.info("😲 覺得像嗎？註冊免費獲得您的 AI 分身 👇")
        if st.button("👉 點此註冊"):
            st.session_state.guest_data = None
            st.query_params.clear()
            st.rerun()
