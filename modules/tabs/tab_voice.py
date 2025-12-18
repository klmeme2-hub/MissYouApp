import streamlit as st
import requests
from modules import audio, database

def render(supabase, client, user_id, target_role, voice_id, elevenlabs_key):
    # 進度指示器
    cols = st.columns(5)
    steps = ["❶ 喚名", "❷ 安慰", "❸ 鼓勵", "❹ 詼諧", "❺ 完成"]
    for i, s in enumerate(steps):
        if i + 1 == st.session_state.step:
            cols[i].markdown(f"**<span style='color:#FF4B4B; font-size:18px;'>{s}</span>**", unsafe_allow_html=True)
        else:
            cols[i].markdown(f"<span style='color:#666'>{s}</span>", unsafe_allow_html=True)
    st.markdown("---")

    # STEP 1: 輕輕喚你的名
    if st.session_state.step == 1:
        st.subheader("STEP 1: 輕輕喚你的名")
        
        lbl = "錄下您的招牌口頭禪" if target_role == "朋友" else "錄下您呼喚對方的暱稱"
        hint = "例如：搞什麼鬼～" if target_role == "朋友" else "例如：老婆～"
        
        nickname_text = st.text_input(lbl, placeholder=hint, key="wiz_nick")
        rec = st.audio_input("錄音 (建議 2-3 秒)", key="wiz_rec_1")
        
        if rec and nickname_text:
            if st.button("💾 上傳並試聽"):
                with st.spinner("處理中..."):
                    audio_bytes = rec.read()
                    # 1. 存入 Storage (作為真實拼接素材)
                    audio.upload_nickname_audio(supabase, target_role, audio_bytes)
                    
                    # 2. 訓練 AI Voice ID
                    rec.seek(0)
                    audio.train_voice_sample(audio_bytes)
                    
                    # 獎勵積分
                    database.update_profile_stats(supabase, user_id, xp_delta=1, log_reason="完成Step1")
                    
                    # 3. 試聽 (AI 不唸暱稱，只唸問候語，避免重複)
                    # 這裡需要傳入 tier，為簡化我們假設訓練時用標準版試聽，或傳入 'basic'
                    ai_audio = audio.generate_speech("最近好嗎？", "basic") 
                    
                    # 4. 拼接
                    final = audio.merge_audio_clips(audio_bytes, ai_audio)
                    st.audio(final, format="audio/mp3")
                    st.success("聲紋已建立！獲得 1 點共鳴值 (XP)")

        if st.button("下一步 →"):
            st.session_state.step = 2
            st.rerun()

    # STEP 2-4: 情緒腳本朗讀
    elif st.session_state.step in [2, 3, 4]:
        scripts = {
            2: ("刻錄「安慰語氣」", "欸，我知道你現在心裡一定超悶的啦，感覺是不是付出的心血都白費了？吼，沒關係啦，真的沒關係，讓我抱一下。你看你齁，把自己逼得那麼緊，早就累壞了。我們又不是機器人，偶爾搞砸一下是很正常的，誰沒有低潮的時候？失敗就失敗啊，它只是在提醒你：你該休息了。我們現在什麼都不要想，先找個地方坐下來。我會在這裡陪著你，等你準備好了，我們再一起慢慢來，好不好？你已經做得很好了。"),
            3: ("刻錄「鼓勵語氣」", "哇塞！你真的決定要開始學那個東西了喔？超酷的啦！我知道一開始會很難、很煩，那介面看起來像外星文，沒錯啦！但你想想看，等你真的學會了，那個成就感會有多爆炸？不要去想還有多少東西沒學，就先專心搞定眼前這個小任務就好。每天進步一點點，慢慢累積起來就會是超巨大的力量！相信我，你的腦袋比你想像中靈光多了！衝啊！我等你做出第一個成品，我請客，隨便你點！"),
            4: ("刻錄「輕鬆詼諧語氣」", "我跟你說，我昨天去圖書館 K 書，真的糗死了啦！我把水壺放在桌上，想說要裝一下文青對不對？結果我一個不小心，那個金屬水壺直接滾到地上，發出那種「匡啷匡啷匡啷」超大聲的聲音！整個圖書館的人，你知道嗎？全部都抬頭看著我！我當時真的超想假裝是睡著了，然後從地上爬起來！那個聲音迴盪了五秒鐘欸！搞得我後來待不下去，我就直接收東西逃走了！")
        }
        
        title, content = scripts[st.session_state.step]
        st.subheader(title)
        st.markdown(f'<div class="script-box">{content}</div>', unsafe_allow_html=True)
        
        rec = st.audio_input("請朗讀上方文字", key=f"wiz_rec_{st.session_state.step}")
        if rec:
            if st.button("💾 上傳訓練"):
                with st.spinner("訓練 Voice ID 中..."):
                    audio.train_voice_sample(rec.read())
                    database.update_profile_stats(supabase, user_id, xp_delta=1, log_reason=f"Step{st.session_state.step}")
                    st.success("已上傳 (+1 XP)")
        
        c1, c2 = st.columns(2)
        with c1: 
            if st.button("← 上一步"): st.session_state.step -= 1; st.rerun()
        with c2: 
            if st.button("下一步 →" if st.session_state.step < 4 else "完成訓練 →"): 
                st.session_state.step += 1
                st.rerun()

    # STEP 5: 完結與分享
    elif st.session_state.step == 5:
        st.balloons()
        st.markdown(f"""
        <div style='text-align:center; padding:30px; background-color:#262730; border:1px solid #4CAF50; border-radius:15px;'>
            <h2 style='color:#4CAF50;'>🎉 恭喜！您的初級語氣刻錄模型已完成。</h2>
            <p>您現在可以生成邀請碼，分享給您的【{target_role}】。</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # 生成 Token
        if "share_token" not in st.session_state or st.session_state.get("share_role") != target_role:
            st.session_state.share_token = database.create_share_token(supabase, target_role)
            st.session_state.share_role = target_role
        
        token = st.session_state.share_token
        app_url = "https://missyou.streamlit.app" # 請記得替換
        
        share_text = f"""現在AI太厲害了
我的聲音語氣模型已經刻錄在這裡
{app_url}

你的邀請碼
{token}

一定要來幫我打個分數喔~
看看跟我的聲音有幾成像?"""

        st.code(share_text, language="text")
        st.caption("👆 點擊右上角複製文案")
        
        if st.button("← 返回重錄"):
            st.session_state.step = 1
            st.rerun()
