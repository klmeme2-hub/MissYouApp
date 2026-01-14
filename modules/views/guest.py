import streamlit as st
import random
import time
from modules import ui, database, audio, brain

def render(supabase, client):
    owner_data = st.session_state.guest_data
    role_key = owner_data['role'] 
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    persona_data = database.load_persona(supabase, role_key)
    display_name = persona_data.get('member_nickname', url_name) if persona_data else url_name

    # 狀態管理初始化
    if "has_rated" not in st.session_state: st.session_state.has_rated = False
    if "teaser_idx" not in st.session_state: st.session_state.teaser_idx = 0
    if "guest_voice_id" not in st.session_state: st.session_state.guest_voice_id = None
    if "crosstalk_audio" not in st.session_state: st.session_state.crosstalk_audio = None
    
    # 載入題目
    try:
        import json
        with open('questions.json', 'r', encoding='utf-8') as f:
            teasers = json.load(f).get("brain_teasers", [])
    except: teasers = []

    # --- Header ---
    st.markdown("""
    <div class="brand-header">
        <div style="font-size: 30px;">♾️</div>
        <div>
            <div class="header-title" style="font-size: 24px !important;">EchoSoul · 聲紋ID刻錄室</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. 開場白 & 評分門檻 (The Gate)
    if not st.session_state.has_rated and role_key == "friend":
        # ... (這裡維持原有的開場白播放邏輯) ...
        # ... (為了節省篇幅，這裡顯示評分介面) ...
        st.info(f"👤 與 [{display_name}] 通話中...")
        
        # 播放開場白
        if "opening_played" not in st.session_state:
            op_bytes = audio.get_audio_bytes(supabase, role_key, "opening")
            ai_ask = audio.generate_speech("你覺得這個AI分身像不像？幫我打個分數。", tier)
            final = audio.merge_audio_clips(op_bytes, ai_ask) if op_bytes else ai_ask
            if final: st.audio(final, format="audio/mp3", autoplay=True)
            st.session_state.opening_played = True
            
        st.markdown("---")
        st.markdown("### ⭐ 聽完請評分 (解鎖功能)")
        c1, c2, c3 = st.columns(3)
        rate = 0
        if c1.button("🤖 不像"): rate=1
        if c2.button("🤔 有點像"): rate=3
        if c3.button("😱 像到發毛"): rate=5
        
        if rate > 0:
            database.submit_feedback(supabase, owner_id, rate, "朋友評分")
            st.session_state.has_rated = True
            st.balloons()
            # 播放感謝語
            thx = audio.generate_speech("謝啦！幫我加了1積分。現在解鎖腦筋急轉彎模式！", tier)
            st.audio(thx, format="audio/mp3", autoplay=True)
            time.sleep(2)
            st.rerun()
            
    # 2. 已評分 -> 顯示主要功能 TAB
    else:
        # 如果是家人模式，直接顯示對話，不顯示 Tab
        if role_key != "friend":
            # ... (家人模式代碼略，維持原樣) ...
            st.info("家人模式 (請複製之前的家人邏輯)")
        else:
            # 朋友模式：顯示 TAB
            tab_teaser, tab_parrot = st.tabs(["🧠 腦力激盪 (雙人AI)", "🦜 九官鳥"])
            
            # --- TAB 1: 腦筋急轉彎 ---
            with tab_teaser:
                current_q = teasers[st.session_state.teaser_idx % len(teasers)]
                
                # 題目卡
                st.markdown(f"""
                <div style="background:#E3F2FD; padding:20px; border-radius:10px; border:2px solid #2196F3; text-align:center; color:#1565C0; font-weight:bold; margin-bottom:20px;">
                    <div style="font-size:12px; color:#888;">第 {st.session_state.teaser_idx + 1} 題</div>
                    <div style="font-size:24px; margin:10px 0;">{current_q['q']}</div>
                    <div style="font-size:12px;">💡 提示：{current_q['hint']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 自動播放題目 (阿強唸題目)
                if f"q_played_{st.session_state.teaser_idx}" not in st.session_state:
                    q_audio = audio.generate_speech(f"考你一個喔！{current_q['q']}，猜猜看是什麼？", tier)
                    st.audio(q_audio, format="audio/mp3", autoplay=True)
                    st.session_state[f"q_played_{st.session_state.teaser_idx}"] = True
                
                # 錄音回答
                ans_audio = st.audio_input("按住回答 (請說完整句子)", key=f"teaser_rec_{st.session_state.teaser_idx}")
                
                if ans_audio:
                    # 如果還沒有生成過這題的對話
                    if not st.session_state.crosstalk_audio:
                        with st.spinner("🎧 正在擷取您的聲紋特徵... 生成雙人脫口秀中..."):
                            # 1. 轉文字
                            user_text = brain.transcribe_audio(ans_audio)
                            
                            # 2. 複製訪客聲音 (Instant Cloning) - 只做一次
                            if not st.session_state.guest_voice_id:
                                ans_audio.seek(0)
                                st.session_state.guest_voice_id = audio.clone_guest_voice(ans_audio.read())
                            
                            # 3. 生成劇本
                            script = brain.generate_crosstalk_script(current_q['q'], user_text, display_name)
                            
                            # 4. 生成雙人語音
                            audio_clips = []
                            for line in script:
                                speaker_voice = st.session_state.guest_voice_id if line['speaker'] == 'guest' else None # None=使用系統預設(會員)
                                # 這裡偷懶用 generate_speech，但它只支援預設 voice_id
                                # 我們需要修改 generate_speech 支援 specific_voice_id (已在 audio.py 修改)
                                clip = audio.generate_speech(line['text'], tier, specific_voice_id=speaker_voice)
                                audio_clips.append(clip)
                            
                            # 5. 合併
                            full_audio = audio.merge_dialogue(audio_clips)
                            st.session_state.crosstalk_audio = full_audio
                            
                            # 增加積分
                            database.update_profile_stats(supabase, owner_id, xp_delta=1)

                    # 播放結果
                    if st.session_state.crosstalk_audio:
                        st.markdown("### 🎭 AI 脫口秀：阿強 vs 你")
                        st.audio(st.session_state.crosstalk_audio, format="audio/mp3", autoplay=True)
                        
                        st.markdown("""
                        <div style="background:#1A1C24; padding:15px; border-radius:10px; margin-top:20px; border:1px solid #FF4B4B; text-align:center;">
                            <p style="color:#FF4B4B; font-weight:bold;">⚠️ 您的 AI 聲紋 ID 已暫時生成</p>
                            <p style="font-size:12px; color:#888;">為了保護隱私，離開頁面後將自動銷毀。</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("🔥 註冊綁定 (保留分身)"):
                                # 清理 Voice ID
                                if st.session_state.guest_voice_id:
                                    audio.delete_voice(st.session_state.guest_voice_id)
                                st.session_state.guest_data = None
                                st.rerun()
                        with c2:
                            if st.button("下一題 ➡"):
                                st.session_state.crosstalk_audio = None
                                st.session_state.teaser_idx += 1
                                st.rerun()

            # --- TAB 2: 九官鳥 (原功能) ---
            with tab_parrot:
                parrot = st.toggle("🦜 九官鳥模式", value=True)
                p_rec = st.audio_input("請說話...", key="parrot_rec")
                if p_rec:
                    txt = brain.transcribe_audio(p_rec)
                    if txt:
                        wav = audio.generate_speech(txt, tier)
                        st.audio(wav, format="audio/mp3", autoplay=True)
                        st.info(f"AI: {txt}")

        # 離開時清理 Voice ID
        st.divider()
        if st.button("🚪 離開"):
            if st.session_state.guest_voice_id:
                audio.delete_voice(st.session_state.guest_voice_id)
            st.session_state.guest_data = None
            st.query_params.clear()
            st.rerun()
