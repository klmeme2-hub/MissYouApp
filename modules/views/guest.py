import streamlit as st
import random
import time
from modules import ui, database, audio, brain

def render(supabase, client, teaser_db):
    owner_data = st.session_state.guest_data
    role_key = owner_data['role'] 
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    persona_data = database.load_persona(supabase, role_key)
    display_name = persona_data.get('member_nickname', url_name) if persona_data else url_name

    # Header
    st.markdown("""<div class="brand-header"><div style="font-size: 30px;">♾️</div><div><div class="header-title" style="font-size: 24px !important;">EchoSoul · 聲紋ID刻錄室</div></div></div>""", unsafe_allow_html=True)

    # 狀態管理
    if "has_rated" not in st.session_state: st.session_state.has_rated = False
    if "teaser_idx" not in st.session_state: st.session_state.teaser_idx = 0
    if "guest_voice_id" not in st.session_state: st.session_state.guest_voice_id = None
    if "crosstalk_audio" not in st.session_state: st.session_state.crosstalk_audio = None
    if "teaser_stage" not in st.session_state: st.session_state.teaser_stage = "answer"
    
    teasers = teaser_db.get("brain_teasers", [])

    # 1. 開場白 & 評分門檻
    if not st.session_state.has_rated and role_key == "friend":
        if "opening_played" not in st.session_state:
            op_bytes = audio.get_audio_bytes(supabase, role_key, "opening")
            ai_ask = audio.generate_speech("你覺得這個AI分身像不像？幫我打個分數。", tier)
            final = audio.merge_audio_clips(op_bytes, ai_ask) if op_bytes else ai_ask
            if final: st.audio(final, format="audio/mp3", autoplay=True)
            st.session_state.opening_played = True
            
        ui.render_status_bar(tier, energy, 0, "elevenlabs", is_guest=True, member_name=display_name)
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
            
            thx_text = "謝啦！... 幫我等級加了1分。... 現在解鎖腦筋急轉彎模式！... 答對有彩蛋！！..."
            thx = audio.generate_speech(thx_text, tier)
            
            st.audio(thx, format="audio/mp3", autoplay=True)
            time.sleep(5) 
            st.rerun()
            
    # 2. 已評分 -> 顯示主要功能
    else:
        # 狀態列
        ui.render_status_bar(tier, energy, 0, "elevenlabs", is_guest=True, member_name=display_name)
        
        if role_key != "friend":
            # 家人模式 (維持原樣)
            st.markdown(f"<h3 style='text-align:center;'>與 {display_name} 通話中...</h3>", unsafe_allow_html=True)
            # ... (家人邏輯省略，維持原樣) ...
            pass
        else:
            # 朋友模式：腦筋急轉彎 + 九官鳥
            tab_teaser, tab_parrot = st.tabs(["🧠 腦力激盪", "🦜 九官鳥"])
            
            with tab_teaser:
                if not teasers:
                    st.error("題庫讀取失敗")
                else:
                    # 循環出題
                    current_q = teasers[st.session_state.teaser_idx % len(teasers)]
                    
                    # 渲染題目卡
                    ui.render_question_card(current_q['q'], st.session_state.teaser_idx + 1, len(teasers), hint=current_q['hint'])

                    # 階段一：播放題目 & 等待回答
                    if st.session_state.teaser_stage == "answer":
                        if f"q_played_{st.session_state.teaser_idx}" not in st.session_state:
                            q_text = f"...請問!...{current_q['q']}，猜猜看是什麼？"
                            q_audio = audio.generate_speech(q_text, tier)
                            st.audio(q_audio, format="audio/mp3", autoplay=True)
                            st.session_state[f"q_played_{st.session_state.teaser_idx}"] = True
                        
                        st.caption("不知道答案嗎? 請說: 天靈靈地靈靈...谷哥大神幫助我解題")
                        st.caption("知道答案嗎? 請說: 這題我會! 答案是 XXX 對不對?")
                        
                        ans_audio = st.audio_input("按住回答 (請說完整句子)", key=f"rec_ans_{st.session_state.teaser_idx}")
                        
                        if ans_audio:
                            st.session_state.teaser_stage = "retry"
                            st.rerun()

                    # 階段二：假裝沒聽清楚
                    elif st.session_state.teaser_stage == "retry":
                        if "retry_played" not in st.session_state:
                            retry_text = "哎呀... 訊號不好，我沒聽清楚。... 麻煩你幫我唸這句測試一下：... 『我是宇宙無敵大聰明，這題難不倒我！』"
                            retry_audio = audio.generate_speech(retry_text, tier)
                            st.audio(retry_audio, format="audio/mp3", autoplay=True)
                            st.session_state.retry_played = True
                        
                        st.info("🎤 請跟著唸：**「我是宇宙無敵大聰明，這題難不倒我！」**")
                        spell_audio = st.audio_input("唸出測試語句", key=f"rec_spell_{st.session_state.teaser_idx}")
                        
                        if spell_audio:
                            with st.spinner("🔄 正在分析聲紋特徵... 生成雙人相聲中... (需約 10 秒)"):
                                # 2. 複製聲音
                                if not st.session_state.guest_voice_id:
                                    spell_audio.seek(0)
                                    st.session_state.guest_voice_id = audio.clone_guest_voice(spell_audio.read())
                                
                                # 3. 生成劇本
                                script = brain.generate_crosstalk_script(current_q['q'], "我是大聰明", display_name)
                                
                                # 4. 生成語音
                                audio_clips = []
                                for line in script:
                                    spk = st.session_state.guest_voice_id if line['speaker'] == 'guest' else None
                                    clip = audio.generate_speech(line['text'], tier, specific_voice_id=spk)
                                    audio_clips.append(clip)
                                
                                full_audio = audio.merge_dialogue(audio_clips)
                                st.session_state.crosstalk_audio = full_audio
                                database.update_profile_stats(supabase, owner_id, xp_delta=1)
                                
                                time.sleep(3)
                                st.session_state.teaser_stage = "result"
                                st.rerun()

                    # 階段三：播放結果 (這裡做了按鈕修改)
                    elif st.session_state.teaser_stage == "result":
                        if st.session_state.crosstalk_audio:
                            st.markdown("### 🎭 AI 脫口秀：阿強 vs 你")
                            st.audio(st.session_state.crosstalk_audio, format="audio/mp3", autoplay=True)
                            
                            st.warning("⚠️ 您的 AI 聲紋 ID 已暫時生成 (離開即銷毀)")
                            
                            # 【修改】按鈕更新 & 移除下一題
                            # 使用 use_container_width 讓按鈕大一點
                            if st.button(f"🔥 註冊綁定 (幫{display_name} +10 XP)", type="primary", use_container_width=True):
                                if st.session_state.guest_voice_id: audio.delete_voice(st.session_state.guest_voice_id)
                                st.session_state.guest_data = None
                                st.rerun()

            with tab_parrot:
                parrot = st.toggle("🦜 九官鳥模式", value=True)
                p_rec = st.audio_input("請說話...", key="parrot_rec")
                if p_rec:
                    txt = brain.transcribe_audio(p_rec)
                    if txt:
                        wav = audio.generate_speech(txt, tier)
                        st.audio(wav, format="audio/mp3", autoplay=True)
                        st.info(f"AI: {txt}")

    # 底部按鈕
    st.divider()
    if st.button("🚪 離開"):
        if st.session_state.guest_voice_id: audio.delete_voice(st.session_state.guest_voice_id)
        st.session_state.guest_data = None
        st.query_params.clear()
        st.rerun()
    
    # 【修改】移除了底部的「註冊免費獲得」區塊，因為上面已經有大按鈕了
