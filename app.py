import streamlit as st
import json
from modules import ui, auth, database, audio, brain, config

# ==========================================
# SaaS Ver. B: Google Gemini 雙引擎商業版
# ==========================================

st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="🤍", layout="wide")
ui.load_css()

if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ Secrets 設定不完整")
    st.stop()

supabase = database.init_supabase()

@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}
question_db = load_questions()

# 狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1

# ==========================================
# 邏輯路由
# ==========================================

# ------------------------------------------
# 情境 A: 親友訪客 (電子雞模式)
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    
    # 1. 取得狀態與等級
    profile = database.get_user_profile(supabase, owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    
    # 2. 每日簽到檢查
    msg = database.check_daily_interaction(supabase, owner_id)
    if msg: st.toast(msg, icon="📅")
    
    # 3. 顯示狀態列
    ui.render_status_bar(tier, energy, profile.get('xp',0), is_guest=True)
    
    # 4. 電量檢查
    if energy <= 0:
        st.error("💔 心靈電量已耗盡，無法連線...")
        st.markdown(f"""
        <div style='text-align:center; padding:30px; background:#FFEBEE; border-radius:10px;'>
            <h3>訊號中斷</h3>
            <p>請幫 {role_name} 補充能量，恢復連線。</p>
            <button style='background:#FF5252; color:white; border:none; padding:10px 20px; border-radius:5px;'>🔋 親友儲值 $88 (送100電量)</button>
        </div>""", unsafe_allow_html=True)
        
        if st.button("模擬儲值 (測試)"):
            database.update_profile_stats(supabase, owner_id, energy_delta=100, log_reason="親友儲值")
            st.success("電量已補充！")
            st.rerun()
            
    else:
        # 電量充足，開始對話
        st.markdown(f"<h2 style='text-align:center;'>📞 與 [{role_name}] 通話中...</h2>", unsafe_allow_html=True)
        persona = database.load_persona(supabase, role_name)
        
        if not persona:
            st.warning("對方尚未設定此角色的資料。")
        else:
            col_c1, col_c2 = st.columns([1, 2])
            with col_c1: st.image("https://cdn-icons-png.flaticon.com/512/607/607414.png", width=150)
            with col_c2: st.info(f"這是 {role_name} 留給您的聲音。\n每次對話消耗 1 電量。")

            if "chat_history" not in st.session_state: st.session_state.chat_history = []

            audio_val = st.audio_input("請按此說話...", key="g_rec")
            if audio_val:
                try:
                    # 扣點
                    database.update_profile_stats(supabase, owner_id, energy_delta=-1, log_reason="對話消耗")
                    
                    # 1. 聽 (Whisper)
                    user_text = brain.transcribe_audio(audio_val)
                    
                    if len(user_text.strip()) > 1:
                        with st.spinner("思考中..."):
                            # 2. 讀取記憶 (SaaS版：直接讀取所有文字給 Gemini)
                            memories = database.get_all_memories_text(supabase, role_name)
                            
                            # 3. 檢查真實暱稱
                            has_nick = audio.get_nickname_audio_bytes(supabase, role_name) is not None
                            
                            # 4. 想 (Gemini - 根據等級切換 Flash/Pro)
                            ai_text = brain.think_and_reply(tier, persona, memories, user_text, has_nick)
                            
                            # 5. 說 (TTS - 根據等級切換 OpenAI/ElevenLabs)
                            raw_audio = audio.generate_speech(ai_text, tier)
                            
                            # 6. 拼 (真實暱稱拼接)
                            final_audio = raw_audio
                            if has_nick and raw_audio:
                                nick_bytes = audio.get_nickname_audio_bytes(supabase, role_name)
                                if nick_bytes: final_audio = audio.merge_audio_clips(nick_bytes, raw_audio)
                            
                            # 顯示
                            st.session_state.chat_history.append({"role": "user", "content": user_text})
                            st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                            
                            if final_audio: st.audio(final_audio, format="audio/mp3", autoplay=True)
                            st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
                            st.toast(f"剩餘電量: {energy-1}")
                            
                except Exception as e: st.error(f"連線錯誤: {e}")

    st.divider()
    if st.button("🚪 離開通話"):
        st.session_state.guest_data = None
        st.rerun()

# ------------------------------------------
# 情境 B: 未登入
# ------------------------------------------
elif not st.session_state.user:
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("## 👋 我是親友")
        token_input = st.text_input("通行碼", placeholder="例如：A8K29", label_visibility="collapsed")
        if st.button("🚀 開始對話", type="primary", use_container_width=True):
            data = database.validate_token(supabase, token_input.strip())
            if data:
                st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                st.rerun()
            else: st.error("無效的通行碼")

    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        with tab_l:
            e = st.text_input("Email", key="l_e")
            p = st.text_input("密碼", type="password", key="l_p")
            if st.button("登入", use_container_width=True):
                res = auth.login_user(supabase, e, p)
                if res and res.user: 
                    st.session_state.user = res
                    st.rerun()
                else: st.error("登入失敗")
        with tab_s:
            e = st.text_input("Email", key="s_e")
            p = st.text_input("設定密碼", type="password", key="s_p")
            if st.button("註冊", use_container_width=True):
                res = auth.signup_user(supabase, e, p)
                if res and res.user:
                    database.get_user_profile(supabase, res.user.id) # Init profile
                    st.session_state.user = res
                    st.success("註冊成功")
                    st.rerun()
                else: st.error("註冊失敗")

# ------------------------------------------
# 情境 C: 會員後台
# ------------------------------------------
else:
    # 讀取資料
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    
    with st.sidebar:
        st.write(f"👤 {st.session_state.user.user.email}")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    
    # 狀態列
    ui.render_status_bar(tier, energy, xp, is_guest=False)
    
    # 角色選擇 (權限鎖定)
    allowed = ["朋友"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1: target_role = st.selectbox("選擇對象", allowed)
    
    if target_role == "朋友" and len(allowed) == 1:
        st.info("🔒 累積 20 XP 或付費升級，即可解鎖「家人」角色。")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🧬 聲紋訓練", "💎 升級與分享", "📝 人設補完", "🧠 回憶補完"])

    # TAB 1: 聲紋 (維持原案，呼叫新模組)
    with tab1:
        # (這裡省略重複的 Step 1-5 UI 代碼，請直接複製上一版 app.py 的 TAB 1 內容)
        # 唯一的差別是：
        # 1. 訓練呼叫 audio.train_voice_sample
        # 2. 上傳呼叫 audio.upload_nickname_audio
        # 3. 完成任務呼叫 database.update_profile_stats(..., xp_delta=1)
        st.write("請參照上一版代碼填入 Step 引導流程...") 
        # 為了讓代碼能跑，這裡放一個簡單示意：
        if st.button("模擬完成 Step 1 (獲得1XP)"):
            database.update_profile_stats(supabase, st.session_state.user.user.id, xp_delta=1, log_reason="Step1")
            st.success("XP +1")

    # TAB 2: 商業變現
    with tab2:
        st.subheader("💎 會員權益與解鎖")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("🛡️ 中級守護者 ($99)")
            if st.button("付費解鎖中級"):
                database.upgrade_tier(supabase, st.session_state.user.user.id, "intermediate", 99, 20)
                st.balloons()
                st.rerun()
        with c2:
            st.warning("🔥 高級刻錄師 ($599)")
            st.write("✅ 解鎖擬真語音引擎 (ElevenLabs)")
            if st.button("付費解鎖高級"):
                database.upgrade_tier(supabase, st.session_state.user.user.id, "advanced", 599, 20)
                st.rerun()
        with c3:
            st.error("♾️ 永恆上鏈 ($2599)")
            st.write("✅ 區塊鏈存證 + 優先功能")

        st.divider()
        st.markdown("### 📤 分享賺 XP (免費解鎖)")
        if st.button("生成邀請碼"):
            token = database.create_share_token(supabase, target_role)
            st.code(token)

    # TAB 3 & 4 (權限鎖定)
    with tab3:
        if tier == 'basic' and xp < 50: st.warning("🔒 需升級或累積 50 XP 解鎖")
        else: st.write("人設補完區 (已解鎖)")
            # 這裡放原本的人設代碼...

    with tab4:
        if tier == 'basic' and xp < 50: st.warning("🔒 需升級或累積 50 XP 解鎖")
        else: 
            st.write("回憶補完區 (已解鎖)")
            # 這裡放原本的回憶補完代碼...
