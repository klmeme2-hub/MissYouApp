import streamlit as st
import json
import requests
import io
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config

# ==========================================
# 應用程式：想念 (Miss You) - SaaS 商業正式版
# 架構：Google Gemini (大腦) + ElevenLabs (嘴巴) + Supabase (記憶/會員)
# ==========================================

# 1. 載入 UI 設定 (深色模式 + 玻璃質感)
st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="🤍", layout="wide")
ui.load_css()

# 2. 系統檢查
if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ 系統設定檔 (Secrets) 缺失，請聯絡管理員。")
    st.stop()

# 3. 初始化客戶端
supabase = database.init_supabase()
# 這裡初始化 OpenAI 僅供 Whisper (聽力) 使用，大腦已移至 brain 模組 (Gemini)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 4. 讀取題庫
@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}
question_db = load_questions()

# 5. 全域狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1

# ==========================================
# 邏輯路由 (Router)
# ==========================================

# ------------------------------------------
# 情境 A: 親友訪客模式 (電子雞養成 + 對話)
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    
    # 1. 取得會員資料與等級
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    xp = profile.get('xp', 0)
    
    # 2. 每日簽到/扣點邏輯 (每次重新整理頁面都會檢查)
    daily_msg = database.check_daily_interaction(supabase, owner_id)
    if daily_msg: st.toast(daily_msg, icon="📅")
    
    # 3. 顯示狀態列 (訪客視角)
    engine_type = audio.get_tts_engine_type(profile)
    ui.render_status_bar(tier, energy, xp, engine_type, is_guest=True)
    
    # 4. 電量檢查 (歸零鎖定)
    if energy <= 0:
        st.error("💔 心靈電量已耗盡，無法連線...")
        st.markdown(f"""
        <div style='text-align:center; padding:30px; background:#262730; border-radius:10px; border:1px solid #FF4B4B;'>
            <h3>⚠️ 訊號中斷</h3>
            <p>請幫 {role_name} 補充能量，恢復連線。</p>
            <button style='background:#FF4B4B; color:white; border:none; padding:12px 24px; border-radius:5px; font-weight:bold; cursor:pointer;'>
                🔋 親友儲值 $88 (送100電量)
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("模擬儲值成功 (測試用)"):
            database.update_profile_stats(supabase, owner_id, energy_delta=100, log_reason="親友儲值")
            st.success("電量已補充！連線恢復。")
            st.rerun()
            
    else:
        # 電量充足，顯示對話介面
        st.markdown(f"<h2 style='text-align:center;'>📞 與 [{role_name}] 通話中...</h2>", unsafe_allow_html=True)
        
        persona = database.load_persona(supabase, role_name)
        
        if not persona:
            st.warning("對方尚未設定此角色的靈魂資料。")
        else:
            col_c1, col_c2 = st.columns([1, 2])
            with col_c1: st.image("https://cdn-icons-png.flaticon.com/512/607/607414.png", width=150)
            with col_c2: st.info(f"這是 {role_name} 留給您的聲音。\n每次對話將消耗 1 點心靈電量。")

            if "chat_history" not in st.session_state: st.session_state.chat_history = []

            audio_val = st.audio_input("請按此說話...", key="guest_rec")
            
            if audio_val:
                try:
                    # 扣除電量
                    database.update_profile_stats(supabase, owner_id, energy_delta=-1, log_reason="對話消耗")
                    
                    # 1. 聽 (Whisper -> Text)
                    # 雖然 Gemini 可以聽，但為了介面顯示文字，我們先轉錄
                    user_text = brain.transcribe_audio(audio_val)
                    
                    if len(user_text.strip()) > 1:
                        with st.spinner("思考中..."):
                            # 2. 讀取記憶 (SaaS升級：直接讀取全量文字給 Gemini)
                            memories = database.get_all_memories_text(supabase, role_name)
                            
                            # 3. 檢查是否有真實暱稱錄音
                            has_nick = audio.get_nickname_audio_bytes(supabase, role_name) is not None
                            
                            # 4. 想 (Gemini 雙引擎：Flash/Pro)
                            ai_text = brain.think_and_reply(tier, persona, memories, user_text, has_nick)
                            
                            # 5. 說 (TTS 雙引擎：OpenAI/ElevenLabs)
                            raw_audio = audio.generate_speech(ai_text, tier)
                            
                            # 6. 拼 (真實暱稱拼接)
                            final_audio = raw_audio
                            if has_nick and raw_audio:
                                nick_bytes = audio.get_nickname_audio_bytes(supabase, role_name)
                                if nick_bytes: final_audio = audio.merge_audio_clips(nick_bytes, raw_audio)
                            
                            # 顯示與播放
                            st.session_state.chat_history.append({"role": "user", "content": user_text})
                            st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                            
                            if final_audio: 
                                st.audio(final_audio, format="audio/mp3", autoplay=True)
                            
                            st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
                            st.toast(f"⚡ 剩餘電量: {energy-1}")
                            
                except Exception as e: st.error(f"連線錯誤: {e}")

    st.divider()
    if st.button("🚪 離開通話"):
        st.session_state.guest_data = None
        st.rerun()
    
    # 裂變廣告 (Growth Loop)
    st.markdown("""
    <div style='background-color:#262730; padding:20px; border-radius:10px; text-align:center; margin-top:30px; border:1px solid #444;'>
        <p>您也想為家人留下這樣的聲音嗎？</p>
        <p style='font-size:12px; color:#888;'>現在註冊，免費建立您的數位分身</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------
# 情境 B: 首頁 (訪客驗證 / 會員登入)
# ------------------------------------------
elif not st.session_state.user:
    col1, col2 = st.columns([1, 1], gap="large")
    
    # 左側：親友入口
    with col1:
        st.markdown("## 👋 我是親友")
        st.caption("請輸入家人分享給您的邀請碼")
        token_input = st.text_input("通行碼 (Token)", placeholder="例如：A8K29", label_visibility="collapsed")
        if st.button("🚀 開始對話", type="primary", use_container_width=True):
            data = database.validate_token(supabase, token_input.strip())
            if data:
                # 首次使用 Token 贈送大禮包 (邏輯可加在 database)
                st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                st.success("驗證成功！")
                st.rerun()
            else: st.error("無效的通行碼")

    # 右側：會員入口
    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        with tab_l:
            l_e = st.text_input("Email", key="l_e")
            l_p = st.text_input("密碼", type="password", key="l_p")
            if st.button("登入", use_container_width=True):
                res = auth.login_user(supabase, l_e, l_p)
                if res and res.user: 
                    st.session_state.user = res
                    st.rerun()
                else: st.error("登入失敗，請檢查帳號密碼。")
        with tab_s:
            s_e = st.text_input("Email", key="s_e")
            s_p = st.text_input("設定密碼", type="password", key="s_p")
            if st.button("註冊 (送 30 點電量)", use_container_width=True):
                res = auth.signup_user(supabase, s_e, s_p)
                if res and res.user:
                    # 初始化 Profile
                    database.get_user_profile(supabase, res.user.id)
                    st.session_state.user = res
                    st.success("註冊成功！")
                    st.rerun()
                else: st.error("註冊失敗，請稍後再試。")

# ------------------------------------------
# 情境 C: 會員後台 (Dashboard)
# ------------------------------------------
else:
    # 讀取會員資料
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    
    # 側邊欄
    with st.sidebar:
        st.write(f"👤 {st.session_state.user.user.email}")
        st.caption(f"ID: {st.session_state.user.user.id[:8]}...")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    
    # 頂部狀態列
    engine_type = audio.get_tts_engine_type(profile)
    ui.render_status_bar(tier, energy, xp, engine_type)
    
    # 角色選擇 (權限鎖定邏輯)
    # 規則：初級會員且 XP<20，只能選「朋友」
    allowed_roles = ["朋友"]
    if tier != 'basic' or xp >= 20:
        allowed_roles = list(config.ROLE_MAPPING.keys())
    
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1:
        target_role = st.selectbox("選擇對象", allowed_roles)
    
    # 鎖定提示
    if target_role == "朋友" and len(allowed_roles) == 1:
        st.info("🔒 累積 **20 點 XP** 或 **付費升級**，即可解鎖「家人」角色。")

    st.divider()

    # 五大功能分頁
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧬 聲紋訓練", "💎 分享解鎖完整版", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"])

    # ==========================================
    # TAB 1: 聲紋訓練 (Wizard 闖關模式)
    # ==========================================
    with tab1:
        # 進度指示
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
            
            nickname_text = st.text_input(lbl, placeholder=hint)
            rec = st.audio_input("錄音 (建議 2-3 秒)")
            
            if rec and nickname_text:
                if st.button("💾 上傳並試聽"):
                    with st.spinner("處理中..."):
                        audio_bytes = rec.read()
                        # 1. 存入 Storage (真實拼接用)
                        audio.upload_nickname_audio(supabase, target_role, audio_bytes)
                        
                        # 2. 訓練 AI Voice ID (若為朋友角色可跳過訓練，這裡統一訓練)
                        rec.seek(0)
                        audio.train_voice_sample(rec.read())
                        
                        # 獎勵積分
                        database.update_profile_stats(supabase, st.session_state.user.user.id, xp_delta=1, log_reason="完成Step1")
                        
                        # 3. 試聽 (AI 不唸暱稱，只唸問候語)
                        ai_content = "最近好嗎？"
                        ai_audio = audio.generate_speech(ai_content, tier)
                        
                        # 4. 拼接
                        final = audio.merge_audio_clips(audio_bytes, ai_audio)
                        st.audio(final, format="audio/mp3")
                        st.success("聲紋已建立！獲得 1 點共鳴值 (XP)")

            if st.button("下一步 →"):
                st.session_state.step = 2
                st.rerun()

        # STEP 2-4: 情緒腳本
        elif st.session_state.step in [2, 3, 4]:
            scripts = {
                2: ("刻錄「安慰語氣」", "欸，我知道你現在心裡一定超悶的啦，感覺是不是付出的心血都白費了？吼，沒關係啦，真的沒關係，讓我抱一下。你看你齁，把自己逼得那麼緊，早就累壞了。我們又不是機器人，偶爾搞砸一下是很正常的，誰沒有低潮的時候？失敗就失敗啊，它只是在提醒你：你該休息了。我們現在什麼都不要想，先找個地方坐下來。我會在這裡陪著你，等你準備好了，我們再一起慢慢來，好不好？你已經做得很好了。"),
                3: ("刻錄「鼓勵語氣」", "哇塞！你真的決定要開始學那個東西了喔？超酷的啦！我知道一開始會很難、很煩，那介面看起來像外星文，沒錯啦！但你想想看，等你真的學會了，那個成就感會有多爆炸？不要去想還有多少東西沒學，就先專心搞定眼前這個小任務就好。每天進步一點點，慢慢累積起來就會是超巨大的力量！相信我，你的腦袋比你想像中靈光多了！衝啊！我等你做出第一個成品，我請客，隨便你點！"),
                4: ("刻錄「輕鬆詼諧語氣」", "我跟你說，我昨天去圖書館 K 書，真的糗死了啦！我把水壺放在桌上，想說要裝一下文青對不對？結果我一個不小心，那個金屬水壺直接滾到地上，發出那種「匡啷匡啷匡啷」超大聲的聲音！整個圖書館的人，你知道嗎？全部都抬頭看著我！我當時真的超想假裝是睡著了，然後從地上爬起來！那個聲音迴盪了五秒鐘欸！搞得我後來待不下去，我就直接收東西逃走了！")
            }
            title, content = scripts[st.session_state.step]
            st.subheader(title)
            st.markdown(f'<div class="script-box">{content}</div>', unsafe_allow_html=True)
            
            rec = st.audio_input("請朗讀上方文字")
            if rec:
                if st.button("💾 上傳訓練"):
                    with st.spinner("訓練 Voice ID 中..."):
                        audio.train_voice_sample(rec.read())
                        database.update_profile_stats(supabase, st.session_state.user.user.id, xp_delta=1, log_reason=f"完成Step{st.session_state.step}")
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
            app_url = "https://missyou.streamlit.app" # 請替換
            
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

    # ==========================================
    # TAB 2: 分享解鎖完整版 (商業變現)
    # ==========================================
    with tab2:
        st.subheader("💎 會員權益與積分規則")
        
        with st.expander("ℹ️ 如何獲得共鳴值 (XP)？", expanded=True):
            st.write("- 🎤 **錄製口頭禪/完成腳本**：各 +1 點")
            st.write("- 🤝 **分享給朋友** (使用邀請碼登入)：+1 點/人")
            st.write("- ⭐ **朋友評分**：+1 點/人")
            st.write("- 👤 **成功邀請註冊**：**+5 點/人** (最強攻略！)")

        st.divider()
        st.subheader("🚀 解鎖方案")

        c1, c2, c3 = st.columns(3)
        with c1:
            ui.render_dashboard_card("免費解鎖", "20 XP")
            st.write("累積滿 20 點 XP，即可免費解鎖「家人角色」權限。")
            if st.button("檢查資格"):
                if xp >= 20: 
                    st.success("您已符合資格！請至上方選單選擇家人角色。")
                else:
                    st.error(f"還差 {20-xp} 點 XP")

        with c2:
            ui.render_dashboard_card("中級守護者", "$99")
            st.write("- **免拉人直接解鎖**")
            st.write("- **贈送 99 點電量**")
            st.write("- **7天 高級語音試用**")
            if st.button("💰 付費解鎖中級"):
                database.upgrade_tier(supabase, st.session_state.user.user.id, "intermediate", energy_bonus=99, xp_bonus=20)
                st.balloons()
                st.success("升級成功！")
                st.rerun()

        with c3:
            ui.render_dashboard_card("高級刻錄師", "$599")
            st.write("- **解鎖 擬真版 (ElevenLabs)**")
            st.write("- **贈送 599 點電量**")
            st.write("- **優先體驗新功能**")
            if st.button("💰 付費解鎖高級"):
                database.upgrade_tier(supabase, st.session_state.user.user.id, "advanced", energy_bonus=599, xp_bonus=20)
                st.success("尊榮升級成功！")
                st.rerun()

        st.divider()
        st.error("♾️ **永恆上鏈 ($2599)**：區塊鏈永久存證 (請洽客服)")

    # ==========================================
    # TAB 3: 人設補完
    # ==========================================
    with tab3:
        if tier == 'basic' and xp < 20:
            st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        else:
            st.info("上傳 LINE 對話紀錄，讓 AI 學習口頭禪。")
            c1, c2 = st.columns(2)
            with c1: member_name = st.text_input("您的名字 (LINE顯示名稱)", value="爸爸")
            with c2: nickname = st.text_input("專屬暱稱 (請輸入發音)", placeholder="例如：寶貝")
            
            up_file = st.file_uploader("上傳紀錄檔", type="txt")
            if st.button("✨ 更新人設"):
                if up_file and member_name:
                    with st.spinner("AI 分析中..."):
                        raw = up_file.read().decode("utf-8")
                        prompt = f"分析主角({member_name})對{target_role}的說話風格。生成System Prompt。重點：模仿語氣，對象是{target_role}時務必使用暱稱{nickname}。資料：{raw[-20000:]}"
                        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                        database.save_persona_summary(supabase, target_role, res.choices[0].message.content)
                        st.success("人設已更新")

    # ==========================================
    # TAB 4: 回憶補完 (雙欄 + 試聽)
    # ==========================================
    with tab4:
        if tier == 'basic' and xp < 20:
            st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        else:
            q_list = question_db.get(target_role, [])
            memories = database.get_memories_by_role(supabase, target_role)
            answered_qs = set()
            for m in memories:
                if "【關於" in m['content'] and "】：" in m['content']:
                    answered_qs.add(m['content'].split("【關於")[1].split("】：")[0])

            if "edit_target" not in st.session_state: st.session_state.edit_target = None
            
            current_q = None
            if st.session_state.edit_target:
                current_q = st.session_state.edit_target
                st.info(f"✏️ 正在重新錄製：{current_q}")
            else:
                for q in q_list:
                    if q not in answered_qs:
                        current_q = q
                        break
            
            if len(q_list) > 0:
                ui.render_dashboard_card("回憶補完進度", f"{len(answered_qs)} / {len(q_list)}")
                st.progress(len(answered_qs) / len(q_list))

            col_l, col_r = st.columns([1.5, 1], gap="medium")
            
            with col_l:
                st.markdown("### 🎙️ 進行中任務")
                if current_q:
                    ui.render_question_card(current_q, len(answered_qs)+1, len(q_list))
                    
                    audio_ans = st.audio_input("錄音回答", key=f"ans_{current_q}")
                    if "trans_text" not in st.session_state: st.session_state.trans_text = ""
                    
                    if audio_ans:
                        trans = client.audio.transcriptions.create(model="whisper-1", file=audio_ans)
                        st.session_state.trans_text = trans.text
                        st.text_area("文字確認", value=st.session_state.trans_text, key="edit_area")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("🔊 試聽 AI 唸"):
                                ai_voice = audio.generate_speech(st.session_state.trans_text, tier)
                                st.audio(ai_voice, format="audio/mp3")
                        with c2:
                            if st.button("💾 存入並訓練", type="primary"):
                                database.save_memory_fragment(supabase, target_role, current_q, st.session_state.edit_area) # 使用修改後的文字
                                audio_ans.seek(0)
                                audio.train_voice_sample(audio_ans.read())
                                st.success("已儲存")
                                st.session_state.edit_target = None
                                st.session_state.trans_text = ""
                                st.rerun()
                    
                    if st.button("⏭️ 跳過"):
                        database.save_memory_fragment(supabase, target_role, current_q, "(已略過)")
                        st.rerun()
                else:
                    st.success("🎉 所有題目已完成！")

            with col_r:
                st.markdown("### 📜 回憶存摺")
                with st.container(height=500):
                    for mem in memories:
                        if "【關於" in mem['content']:
                            try:
                                q = mem['content'].split("【關於")[1].split("】：")[0]
                                a = mem['content'].split("】：")[1]
                                ui.render_history_card(q, a)
                                if st.button("🔄 重錄", key=f"re_{mem['id']}"):
                                    st.session_state.edit_target = q
                                    st.rerun()
                            except: pass

    # ==========================================
    # TAB 5: 完美暱稱 (保留功能)
    # ==========================================
    with tab5:
        if tier == 'basic' and xp < 20:
            st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        else:
            st.subheader("🎯 完美暱稱重現")
            st.info("錄製一段真實的呼喚，AI 會在開頭直接播放這段錄音。")
            nick_role = st.selectbox("錄製給誰聽？", list(config.ROLE_MAPPING.keys()), key="nick_role")
            st.markdown(f"請按下錄音，喊一聲給【{nick_role}】聽的暱稱：")
            real_nick_audio = st.audio_input("錄製", key="real_nick_rec")
            if real_nick_audio:
                if st.button("💾 上傳真實聲音"):
                    with st.spinner("處理中..."):
                        if audio.upload_nickname_audio(supabase, nick_role, real_nick_audio.read()):
                            st.success("成功！")
