import streamlit as st
from modules import audio, database

def render(supabase, client, user_id, target_role, tier):
    
    # 顯示圓形進度條
    from modules.ui import render_stepper
    render_stepper(st.session_state.step)
    
    st.markdown("---")

    # ==========================================
    # STEP 1: 核心人設 (喚名/口頭禪/身分)
    # ==========================================
    if st.session_state.step == 1:
        
        # --- 情境 A: 朋友/死黨 (維持原案) ---
        if target_role == "friend":
            st.subheader("STEP 1: 口頭禪炸彈 💣")
            
            st.markdown("##### 1. 設定身分")
            st.caption("請輸入 朋友/死黨 平常 **怎麼叫您**？")
            member_nick = st.text_input("標籤", placeholder="例如：阿強、東哥", label_visibility="collapsed", key="step1_fr_mn")
            
            st.markdown("##### 2. 錄製開場白")
            st.info("留一句話給換帖的，讓他接起電話寒毛直豎。建議錄製：「喂～買霸未？」")
            
            rec = st.audio_input("錄音 (2-3秒)", key="step1_fr_rec")
            
            # 朋友模式：這段錄音主要當作 Opening
            file_type_to_save = "opening"
            ai_demo_text = "你覺得這個AI分身，跟我本尊有幾分像呢？"

        # --- 情境 B: 家人/伴侶 (新版整合邏輯) ---
        else:
            st.subheader("STEP 1: 輕輕喚你的名 ❤️")
            
            st.markdown("##### 1. 設定身分")
            st.caption(f"請輸入 {target_role} 平常 **怎麼叫您**？(這會顯示在邀請連結與通話畫面上)")
            member_nick = st.text_input("身分稱呼", placeholder="例如：老公、黑狗爸、老媽", label_visibility="collapsed", key="step1_fam_mn")
            
            st.markdown("##### 2. 錄製完美暱稱")
            st.info(f"請用最溫柔、自然的語氣，呼喚對方的名字或小名。這段聲音會用在每次對話的開頭。")
            st.markdown(f"👉 **建議錄製：** 「老婆～」 或 「寶貝女兒～」")
            
            rec = st.audio_input("錄音 (2-3秒)", key="step1_fam_rec")
            
            # 家人模式：這段錄音既是 Nickname (拼接用) 也是 Opening (開場用)
            # 我們稍後在存檔時會做雙重處理
            ai_demo_text = "想我嗎？"

        # --- 共用存檔邏輯 ---
        # 條件：必須有錄音 + 必須有輸入名字
        if rec and member_nick:
            if st.button("💾 上傳並試聽", type="primary"):
                with st.spinner("處理中..."):
                    audio_bytes = rec.read()
                    
                    # 1. 儲存身分 (member_nickname)
                    # 先讀取舊人設避免覆蓋 content
                    p = database.load_persona(supabase, target_role)
                    content = p['content'] if p else "尚未設定人設"
                    database.save_persona_summary(supabase, target_role, content, member_nickname=member_nick)

                    # 2. 儲存音檔 (關鍵修改)
                    if target_role == "friend":
                        # 朋友模式：只存為 opening
                        audio.upload_audio_file(supabase, target_role, audio_bytes, "opening")
                    else:
                        # 家人模式：同時存為 nickname (對話拼接用) 和 opening (開場檢查用)
                        # 這樣既能滿足「完美暱稱」，又能解鎖「生成邀請卡」按鈕
                        audio.upload_audio_file(supabase, target_role, audio_bytes, "nickname")
                        audio.upload_audio_file(supabase, target_role, audio_bytes, "opening")
                    
                    # 3. 訓練 AI Voice ID
                    rec.seek(0)
                    audio.train_voice_sample(rec.read())
                    
                    # 4. 獎勵積分
                    database.update_profile_stats(supabase, user_id, xp_delta=1, log_reason="完成Step1")
                    
                    # 5. 試聽拼接
                    ai_wav = audio.generate_speech(ai_demo_text, tier)
                    final = audio.merge_audio_clips(audio_bytes, ai_wav)
                    
                    st.audio(final, format="audio/mp3")
                    st.success("設定已儲存！獲得 1 點共鳴值")

        if st.button("下一步 →"):
            st.session_state.step = 2
            st.rerun()

    # ==========================================
    # STEP 2-4: 情緒腳本 (維持不變)
    # ==========================================
    elif st.session_state.step in [2, 3, 4]:
        scripts = {
            2: ("刻錄「安慰語氣」", "欸，我知道你現在心裡一定超悶的啦，感覺是不是付出的心血都白費了？吼，沒關係啦，真的沒關係，讓我抱一下。你看你齁，把自己逼得那麼緊，早就累壞了。我們又不是機器人，偶爾搞砸一下是很正常的，誰沒有低潮的時候？失敗就失敗啊，它只是在提醒你：你該休息了。我們現在什麼都不要想，先找個地方坐下來。我會在這裡陪著你，等你準備好了，我們再一起慢慢來，好不好？你已經做得很好了。"),
            3: ("刻錄「鼓勵語氣」", "哇塞！你真的決定要開始學那個東西了喔？超酷的啦！我知道一開始會很難、很煩，那介面看起來像外星文，沒錯啦！但你想想看，等你真的學會了，那個成就感會有多爆炸？不要去想還有多少東西沒學，就先專心搞定眼前這個小任務就好。每天進步一點點，慢慢累積起來就會是超巨大的力量！相信我，你的腦袋比你想像中靈光多了！衝啊！我等你做出第一個成品，我請客，隨便你點！"),
            4: ("刻錄「輕鬆詼諧語氣」", "我跟你說，我昨天去圖書館 K 書，真的糗死了啦！我把水壺放在桌上，想說要裝一下文青對不對？結果我一個不小心，那個金屬水壺直接滾到地上，發出那種「匡啷匡啷匡啷」超大聲的聲音！整個圖書館的人，你知道嗎？全部都抬頭看著我！我當時真的超想假裝是睡著了，然後從地上爬起來！那個聲音迴盪了五秒鐘欸！搞得我後來待不下去，我就直接收東西逃走了！")
        }
        
        title, content = scripts.get(st.session_state.step, ("標題", "內容"))
        st.subheader(f"STEP {st.session_state.step}: {title}")
        st.markdown(f'<div class="script-box">{content}</div>', unsafe_allow_html=True)
        
        rec = st.audio_input("請朗讀上方文字", key=f"step{st.session_state.step}_rec")
        if rec:
            if st.button("💾 上傳訓練"):
                with st.spinner("訓練 Voice ID 中..."):
                    audio.train_voice_sample(rec.read())
                    database.update_profile_stats(supabase, user_id, xp_delta=1, log_reason=f"Step{st.session_state.step}")
                    st.success("已上傳 (+1 XP)")
        
        col_prev, col_next = st.columns(2)
        with col_prev: 
            if st.button("← 上一步"): 
                st.session_state.step -= 1
                st.rerun()
        with col_next: 
            btn_txt = "下一步 →" if st.session_state.step < 4 else "完成訓練 →"
            if st.button(btn_txt): 
                st.session_state.step += 1
                st.rerun()

    # ==========================================
    # STEP 5: 完成與引導
    # ==========================================
    elif st.session_state.step == 5:
        st.balloons()
        
        # 根據角色顯示不同文案
        if target_role == "friend":
            msg = "恭喜！惡作劇分身已完成。"
        else:
            msg = "恭喜！您已為家人留下了最珍貴的聲音。"
            
        st.markdown(f"""
        <div style='text-align:center; padding:30px; background-color:#262730; border:1px solid #4CAF50; border-radius:15px;'>
            <h2 style='color:#4CAF50;'>🎉 {msg}</h2>
            <p>您現在可以點擊上方的 <b>「🎁 生成邀請卡」</b> 分享給對方了。</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("← 返回 Step 1 重錄"):
            st.session_state.step = 1
            st.rerun()
