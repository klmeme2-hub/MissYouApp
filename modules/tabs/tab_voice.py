import streamlit as st
from modules import audio, database

def render(supabase, user_id, target_role, tier):
    # 顯示圓形進度條
    from modules.ui import render_stepper
    render_stepper(st.session_state.step)
    
    st.markdown("---")

    # STEP 1: 口頭禪炸彈
    if st.session_state.step == 1:
        st.subheader("STEP 1: 口頭禪炸彈 💣")
        if target_role == "friend":
            st.info("留一句話給換帖的拜把兄弟，讓他接起電話寒毛直豎，像到發抖。")
            st.markdown("**建議錄製：** 「喂～大胖，賈霸未？」 或 「搞什麼鬼～」")
        else:
            st.info("錄製最自然的親密呼喚。")
            st.markdown("**建議錄製：** 「老婆～」 或 「親愛的～」")

        rec = st.audio_input("錄製 (建議 2-3 秒)", key="step1_rec")
        
        if rec:
            if st.button("💾 上傳並試聽"):
                with st.spinner("處理中..."):
                    ab = rec.read()
                    # 這裡統一存為 'opening' (開場白)
                    audio.upload_audio_file(supabase, target_role, ab, "opening")
                    
                    # 訓練 AI
                    rec.seek(0)
                    audio.train_voice_sample(rec.read())
                    database.update_profile_stats(supabase, user_id, xp_delta=1, log_reason="Step1完成")
                    
                    # 試聽拼接
                    ai_txt = "你覺得這個AI分身，跟我本尊有幾分像呢？" if target_role == "friend" else "想我嗎？"
                    ai_wav = audio.generate_speech(ai_txt, tier)
                    final = audio.merge_audio_clips(ab, ai_wav)
                    st.audio(final, format="audio/mp3")
                    st.success("口頭禪已裝填完畢！")

        if st.button("下一步 →"):
            st.session_state.step = 2
            st.rerun()

    # STEP 2-4 (保留原腳本邏輯)
    elif st.session_state.step in [2, 3, 4]:
        scripts = {
            2: ("刻錄「安慰語氣」", "欸，我知道你現在心裡一定超悶的啦... (略)"),
            3: ("刻錄「鼓勵語氣」", "哇塞！你真的決定要開始學那個東西了喔？... (略)"),
            4: ("刻錄「輕鬆詼諧語氣」", "我跟你說，我昨天去圖書館 K 書... (略)")
        }
        title, content = scripts.get(st.session_state.step, ("標題", "內容"))
        st.subheader(title)
        st.info(content)
        
        rec = st.audio_input("朗讀")
        if rec and st.button("💾 上傳訓練"):
            with st.spinner("Training..."):
                audio.train_voice_sample(rec.read())
                database.update_profile_stats(supabase, user_id, xp_delta=1)
                st.success("已上傳 (+1 XP)")
        
        c1, c2 = st.columns(2)
        with c1: 
            if st.button("← 上一步"): st.session_state.step -= 1; st.rerun()
        with c2: 
            btn_txt = "下一步 →" if st.session_state.step < 4 else "完成訓練 →"
            if st.button(btn_txt): st.session_state.step += 1; st.rerun()

    # STEP 5: 完成
    elif st.session_state.step == 5:
        st.balloons()
        st.success("🎉 訓練完成！現在可以去生成邀請卡了。")
        if st.button("← 返回重錄"): st.session_state.step = 1; st.rerun()
