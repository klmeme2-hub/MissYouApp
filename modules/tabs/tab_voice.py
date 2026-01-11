import streamlit as st
from modules import audio, database

def render(supabase, client, user_id, target_role, tier):
    
    # ==========================
    # 新版導航列 (按鈕式，可跳轉)
    # ==========================
    
    steps = {
        1: "1.口頭禪/暱稱",
        2: "2.安慰語氣",
        3: "3.鼓勵語氣",
        4: "4.詼諧語氣",
        5: "5.完成"
    }

    # 【調整比例】: 第一欄給 1.5，其他給 1，右邊留白
    # 這樣可以容納較長的文字，同時保持靠左
    cols = st.columns([1.5, 1, 1, 1, 1, 3]) 

    for i in range(1, 6):
        btn_type = "primary" if st.session_state.step == i else "secondary"
        if cols[i-1].button(steps[i], key=f"nav_step_{i}", type=btn_type, use_container_width=True):
            st.session_state.step = i
            st.rerun()

    st.markdown("---")

    # (以下內容維持不變，請保留原有的邏輯)
    # ... 為了確保代碼完整性，我把剩下的邏輯也貼上 ...

    ROLE_DISPLAY_NAMES = {
        "friend": "朋友/死黨", "partner": "妻子/丈夫/伴侶", "son": "兒子",
        "daughter": "女兒", "junior": "兒子/女兒/晚輩", "elder": "長輩/父母", "others": "親友"
    }
    role_zh = ROLE_DISPLAY_NAMES.get(target_role, target_role)

    # STEP 1
    if st.session_state.step == 1:
        if target_role == "friend":
            st.subheader("STEP 1: 口頭禪炸彈 💣")
            ai_demo_text = "你覺得這個AI分身，跟我本尊有幾分像呢？"
            id_label = "1. 設定身分"
            id_help = f"請輸入 {role_zh} 平常 **怎麼叫您**？"
            id_placeholder = "例如：阿強、東哥、小娟"
            sound_label = "2. 錄製開場白"
            sound_desc = "留一句話給換帖的拜把兄弟，讓他接起電話寒毛直豎。"
            sound_hint = "👉 **建議錄製：** 「呷飽未？」 或 「好久不見！！」 或 您的招牌口頭禪"
        else:
            st.subheader("STEP 1: 輕輕喚你的名 ❤️")
            ai_demo_text = "想我嗎？"
            id_label = "1. 設定身分"
            id_help = f"請輸入 {role_zh} 平常 **怎麼叫您**？"
            id_placeholder = "例如：老公、黑狗爸、老媽"
            sound_label = "2. 完美暱稱：錄製最自然親密呼喚"
            sound_desc = "請用最溫柔、自然的語氣，呼喚對方的名字或小名。這段聲音會用在每次對話的開頭。"
            sound_hint = "👉 **建議錄製：** 「老婆～」 或 「親愛的～」"

        st.markdown(f"##### {id_label}")
        st.caption(id_help)
        member_nick = st.text_input("身分", placeholder=id_placeholder, label_visibility="collapsed", key="s1_mn")
        st.markdown("") 
        st.markdown(f"##### {sound_label}")
        st.write(sound_desc)
        st.caption(sound_hint)
        st.warning("📱 **手機用戶注意：** 若無法錄音，請點擊 LINE/FB 右上角選單，選擇**「在瀏覽器開啟」**並允許麥克風權限。")
        rec = st.audio_input("錄音 (2-3秒)", key="s1_rec")

        can_save = rec and member_nick
        if can_save:
            if st.button("💾 上傳並試聽", type="primary"):
                with st.spinner("處理中..."):
                    audio_bytes = rec.read()
                    p = database.load_persona(supabase, target_role)
                    content = p['content'] if p else "尚未設定人設"
                    database.save_persona_summary(supabase, target_role, content, member_nickname=member_nick)

                    if target_role == "friend":
                        audio.upload_audio_file(supabase, target_role, audio_bytes, "opening")
                    else:
                        audio.upload_audio_file(supabase, target_role, audio_bytes, "nickname")
                        audio.upload_audio_file(supabase, target_role, audio_bytes, "opening")
                    
                    rec.seek(0)
                    audio.train_voice_sample(rec.read())
                    database.update_profile_stats(supabase, user_id, xp_delta=1, log_reason="完成Step1")
                    
                    ai_wav = audio.generate_speech(ai_demo_text, tier)
                    final = audio.merge_audio_clips(audio_bytes, ai_wav)
                    st.audio(final, format="audio/mp3")
                    st.success("設定已儲存！獲得 1 點共鳴值")
        if st.button("下一步 →"): st.session_state.step = 2; st.rerun()

    # STEP 2-4
    elif st.session_state.step in [2, 3, 4]:
        scripts = {
            2: ("刻錄「安慰語氣」", "欸，我知道你現在心裡一定超悶的啦，感覺是不是付出的心血都白費了？吼，沒關係啦，真的沒關係，讓我抱一下。你看你齁，把自己逼得那麼緊，早就累壞了。我們又不是機器人，偶爾搞砸一下是很正常的，誰沒有低潮的時候？失敗就失敗啊，它只是在提醒你：你該休息了。我們現在什麼都不要想，先找個地方坐下來。我會在這裡陪著你，等你準備好了，我們再一起慢慢來，好不好？你已經做得很好了。"),
            3: ("刻錄「鼓勵語氣」", "哇塞！你真的決定要開始學那個東西了喔？超酷的啦！我知道一開始會很難、很煩，那介面看起來像外星文，沒錯啦！但你想想看，等你真的學會了，那個成就感會有多爆炸？不要去想還有多少東西沒學，就先專心搞定眼前這個小任務就好。每天進步一點點，慢慢累積起來就會是超巨大的力量！相信我，你的腦袋比你想像中靈光多了！衝啊！我等你做出第一個成品，我請客，隨便你點！"),
            4: ("刻錄「輕鬆詼諧語氣」", "我跟你說，我昨天去圖書館 K 書，真的糗死了啦！我把水壺放在桌上，想說要裝一下文青對不對？結果我一個不小心，那個金屬水壺直接滾到地上，發出那種「匡啷匡啷匡啷」超大聲的聲音！整個圖書館的人，你知道嗎？全部都抬頭看著我！我當時真的超想假裝是睡著了，然後從地上爬起來！那個聲音迴盪了五秒鐘欸！搞得我後來待不下去，我就直接收東西逃走了！")
        }
        title, content = scripts.get(st.session_state.step, ("標題", "內容"))
        st.subheader(f"STEP {st.session_state.step}: {title}")
        st.markdown(f'<div class="script-box">{content}</div>', unsafe_allow_html=True)
        st.warning("📱 手機若無法錄音，請用 Chrome/Safari 開啟。")
        rec = st.audio_input("請朗讀上方文字", key=f"step{st.session_state.step}_rec")
        if rec:
            if st.button("💾 上傳訓練"):
                with st.spinner("訓練 Voice ID 中..."):
                    audio.train_voice_sample(rec.read())
                    database.update_profile_stats(supabase, user_id, xp_delta=1, log_reason=f"Step{st.session_state.step}")
                    st.success("已上傳 (+1 XP)")
        col_prev, col_next = st.columns(2)
        with col_prev: 
            if st.button("← 上一步"): st.session_state.step -= 1; st.rerun()
        with col_next: 
            btn_txt = "下一步 →" if st.session_state.step < 4 else "完成訓練 →"
            if st.button(btn_txt): st.session_state.step += 1; st.rerun()

    # STEP 5
    elif st.session_state.step == 5:
        st.balloons()
        st.markdown(f"""<div style='text-align:center; padding:30px; background-color:#262730; border:1px solid #4CAF50; border-radius:15px;'><h2 style='color:#4CAF50;'>🎉 恭喜！{role_zh} 的初級語氣模型已完成。</h2><p>您現在可以點擊上方的 <b>「🎁 生成邀請卡」</b> 分享給對方了。</p></div>""", unsafe_allow_html=True)
        if st.button("← 返回 Step 1 重錄"): st.session_state.step = 1; st.rerun()
