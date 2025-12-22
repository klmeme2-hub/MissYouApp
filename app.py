import streamlit as st
import json
import time
import datetime
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config
import extra_streamlit_components as stx

# ==========================================
# 應用程式：想念 (SaaS Beta 4.0 - 完整版)
# ==========================================

# 1. UI 設定 (寬螢幕 + 深色模式)
st.set_page_config(page_title="想念", page_icon="📞", layout="wide")
ui.load_css()

# 2. 初始化 Cookie 與 系統
cookie_manager = stx.CookieManager()

if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ Secrets 未設定")
    st.stop()

supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}
question_db = load_questions()

# 3. 狀態變數初始化
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None
if "call_status" not in st.session_state: st.session_state.call_status = "ringing"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen" # listen, rating, interact

# ==========================================
# 邏輯路由
# ==========================================

# ------------------------------------------
# 檢查網址參數 (直連邏輯)
# ------------------------------------------
if "token" in st.query_params and not st.session_state.user and not st.session_state.guest_data:
    try:
        raw_token = st.query_params["token"]
        # 解析 Token (例如: A8K29_阿強)
        if "_" in raw_token:
            real_token = raw_token.split("_")[0]
            display_name_from_url = raw_token.split("_")[1]
        else:
            real_token = raw_token
            display_name_from_url = "朋友"
        
        # 驗證
        data = database.validate_token(supabase, real_token)
        if data:
            st.session_state.guest_data = {
                'owner_id': data['user_id'], 
                'role': data['role'], 
                'display_name': display_name_from_url
            }
            st.rerun()
        else:
            st.error("無效連結")
            st.query_params.clear()
    except: pass

# ------------------------------------------
# 情境 A: 訪客模式 (雙軌道體驗)
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_key = owner_data['role'] # friend, partner...
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    # 取得資料
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    
    # 讀取人設與暱稱
    persona_data = database.load_persona(supabase, role_key)
    display_name = url_name
    if persona_data and persona_data.get('member_nickname'):
        display_name = persona_data['member_nickname']

    # --- 階段 1: 來電模擬 (共通) ---
    if st.session_state.call_status == "ringing":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(f"""
            <div style='text-align:center; padding-top:50px;'>
                <div style='font-size:80px;'>👤</div>
                <h1 style='color:#FAFAFA;'>{display_name}</h1>
                <p style='color:#CCC; font-size:20px; animation: blink 1.5s infinite;'>📞 來電中...</p>
            </div>
            <style>@keyframes blink {{ 0% {{opacity: 1;}} 50% {{opacity: 0.5;}} 100% {{opacity: 1;}} }}</style>
            """, unsafe_allow_html=True)
            
            if st.button("🟢 接聽", use_container_width=True, type="primary"):
                st.session_state.call_status = "connected"
                database.check_daily_interaction(supabase, owner_id)
                st.rerun()

    # --- 階段 2: 通話中 (雙軌道) ---
    elif st.session_state.call_status == "connected":
        
        # 🟢 軌道 A: 朋友 (裂變流程)
        if role_key == "friend":
            # 1. 強制播放開場 (口頭禪 + 求評分)
            if "opening_played" not in st.session_state:
                # 真實口頭禪
                op_bytes = audio.get_audio_bytes(supabase, role_key, "opening")
                # AI 求評分
                ask_rate = "你覺得這個AI分身，跟我本尊有幾分像呢？幫我打個分數，拜託了。"
                ai_ask = audio.generate_speech(ask_rate, tier)
                
                final = audio.merge_audio_clips(op_bytes, ai_ask) if op_bytes else ai_ask
                if final: st.audio(final, format="audio/mp3", autoplay=True)
                st.session_state.opening_played = True
            
            # 2. 強制評分彈窗
            if st.session_state.friend_stage == "listen":
                st.info("🔊 請先聽完上面的聲音...")
                st.markdown("### 🤔 老實說，像不像？")
                c1, c2, c3 = st.columns(3)
                rating = 0
                if c1.button("🤖 不像"): rating=1
                if c2.button("🤔 有點像"): rating=3
                if c3.button("😱 像到發毛"): rating=5
                
                if rating > 0:
                    database.submit_feedback(supabase, owner_id, rating, "朋友評分")
                    st.session_state.friend_stage = "interact"
                    
                    # 播放感謝
                    thx_audio = audio.generate_speech("太感謝你啦！幫我加了1積分。你可以試試下面的九官鳥模式，我會學你講話喔！", tier)
                    st.audio(thx_audio, format="audio/mp3", autoplay=True)
                    st.rerun()

            # 3. 互動區 (九官鳥 + 轉化)
            elif st.session_state.friend_stage == "interact":
                st.success("✅ 已解鎖互動功能")
                parrot_mode = st.toggle("🦜 九官鳥模式 (我說什麼他學什麼)", value=True)
                
                audio_val = st.audio_input("試試看說：我是大豬頭", key="p_rec")
                if audio_val:
                    txt = brain.transcribe_audio(audio_val)
                    if txt:
                        ai_say = txt if parrot_mode else "我是朋友模式AI，目前建議使用九官鳥功能喔！"
                        # 這裡強制用高級語音 (如果有的話) 來驚艷朋友
                        wav = audio.generate_speech(ai_say, tier) 
                        st.audio(wav, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_say}</div>', unsafe_allow_html=True)

                st.markdown("---")
                st.info("😲 被嚇到了嗎？")
                if st.button("👉 免費製作你的 AI 分身", use_container_width=True):
                    st.session_state.guest_data = None
                    st.query_params.clear()
                    st.rerun()

        # ❤️ 軌道 B: 家人 (情感消耗)
        else:
            # 1. 溫馨開場 (真實暱稱 + AI問候)
            if "opening_played" not in st.session_state:
                nick_bytes = audio.get_audio_bytes(supabase, role_key, "nickname") # 使用 Tab 5 的暱稱
                ai_greet = audio.generate_speech("想我嗎？", tier)
                final = audio.merge_audio_clips(nick_bytes, ai_greet) if nick_bytes else ai_greet
                st.audio(final, format="audio/mp3", autoplay=True)
                st.session_state.opening_played = True

            # 2. 電子雞儀表板 (模型切換)
            use_high_res = st.toggle("👑 高傳真線路 (消耗2電量)", value=False)
            current_cost = 2 if use_high_res else 1
            
            # 傳遞 engine 給 status bar 顯示
            eng_display = "elevenlabs" if use_high_res else "openai"
            ui.render_status_bar(tier, energy, 0, eng_display, is_guest=True)
            
            if energy <= 0:
                st.error("💔 電量耗盡")
                if st.button(f"🔋 幫 {display_name} 儲值 $88"):
                    database.update_profile_stats(supabase, owner_id, energy_delta=100)
                    st.rerun()
            else:
                audio_val = st.audio_input("請說話...", key="fam_rec")
                if audio_val:
                    try:
                        # 扣點
                        database.update_profile_stats(supabase, owner_id, energy_delta=-current_cost)
                        
                        user_text = brain.transcribe_audio(audio_val)
                        if user_text:
                            # RAG + Brain
                            mems = database.get_all_memories_text(supabase, role_key)
                            has_nick = audio.get_audio_bytes(supabase, role_key, "nickname") is not None
                            
                            # 思考
                            ai_text = brain.think_and_reply(tier, persona_data, mems, user_text, False)
                            
                            # 語音 (強制指定引擎)
                            forced_tier = 'advanced' if use_high_res else 'basic'
                            wav = audio.generate_speech(ai_text, forced_tier)
                            
                            # 拼接
                            final = wav
                            if has_nick and wav:
                                nb = audio.get_audio_bytes(supabase, role_key, "nickname")
                                if nb: final = audio.merge_audio_clips(nb, wav)
                            
                            st.audio(final, format="audio/mp3", autoplay=True)
                            st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
                            st.toast(f"剩餘電量: {energy - current_cost}")
                            
                    except Exception as e: st.error(f"Error: {e}")

    # 掛斷按鈕
    st.divider()
    if st.button("🔴 掛斷"):
        st.session_state.guest_data = None
        st.session_state.call_status = "ringing"
        if "opening_played" in st.session_state: del st.session_state["opening_played"]
        if "friend_stage" in st.session_state: del st.session_state["friend_stage"]
        st.query_params.clear()
        st.rerun()

# ------------------------------------------
# 情境 B: 未登入 (首頁)
# ------------------------------------------
elif not st.session_state.user:
    
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    saved_token = cookies.get("guest_token", "")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    # 左側：親友入口
    with col1:
        st.markdown("## 👋 我是親友")
        st.caption("輸入家人分享給您的邀請碼")
        token_input = st.text_input("通行碼", value=saved_token, placeholder="A8K29")
        if st.button("🚀 開始對話", type="primary", use_container_width=True):
            data = database.validate_token(supabase, token_input.strip())
            if data:
                cookie_manager.set("guest_token", token_input.strip(), expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                st.success("驗證成功！")
                time.sleep(0.5)
                st.rerun()
            else: st.error("無效的通行碼")

    # 右側：會員入口
    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        
        with tab_l:
            with st.form("login_form"):
                l_e = st.text_input("Email", value=saved_email)
                l_p = st.text_input("密碼", type="password")
                submitted = st.form_submit_button("登入", use_container_width=True)
                if submitted:
                    res = auth.login_user(supabase, l_e, l_p)
                    if res and res.user: 
                        cookie_manager.set("member_email", l_e, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                        st.session_state.user = res
                        st.success("登入成功")
                        time.sleep(0.5)
                        st.rerun()
                    else: st.error("登入失敗")
        
        with tab_s:
            s_e = st.text_input("Email", key="s_e")
            s_p = st.text_input("設定密碼", type="password", key="s_p")
            if st.button("註冊", use_container_width=True):
                res = auth.signup_user(supabase, s_e, s_p)
                if res and res.user:
                    database.get_user_profile(supabase, res.user.id)
                    st.session_state.user = res
                    st.success("註冊成功！")
                    st.rerun()
                else: st.error("註冊失敗")

# ------------------------------------------
# 情境 C: 會員後台
# ------------------------------------------
else:
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
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile))
    
    # 頂部控制台 (使用 radio 實現分頁跳轉)
    tabs_list = ["🧬 聲紋訓練", "💎 分享解鎖", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"]
    
    # 如果有跳轉指令
    idx = 0
    if "nav_target" in st.session_state:
        try: idx = tabs_list.index(st.session_state.nav_target)
        except: pass
        del st.session_state.nav_target
        
    selected_tab = st.radio("功能選單", tabs_list, index=idx, horizontal=True, label_visibility="collapsed")

    # 角色選擇與生成邀請卡 (獨立一列)
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    c_role, c_btn = st.columns([7, 3])
    with c_role:
        disp_role = st.selectbox("選擇對象", allowed, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[disp_role]
    with c_btn:
        # 生成邀請卡邏輯
        has_op = audio.get_audio_bytes(supabase, target_role, "opening")
        
        # 即使沒錄音也允許生成，系統會用 AI Fallback
        if st.button("🎁 生成邀請卡", type="primary", use_container_width=True):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True
            
    if not has_op and target_role == "friend":
        st.caption("⚠️ 尚未錄製口頭禪，朋友將聽到 AI 語音 (建議去聲紋訓練錄製)")

    if target_role == "friend" and len(allowed) == 1:
        st.info("🔒 累積 20 XP 或升級，即可解鎖「家人」角色。")

    # 邀請卡彈窗
    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        
        st.markdown("---")
        st.success(f"💌 邀請連結 ({disp_role})")
        
        # 文案
        copy_text = f"欸！我做了一個AI分身超像的，點這個連結打電話給我：\n{url}"
        if target_role == "partner": copy_text = f"親愛的，這是我留給你的聲音：\n{url}"
        elif target_role == "junior": copy_text = f"孩子，這是爸媽的時光膠囊：\n{url}"
        elif target_role == "elder": copy_text = f"爸/媽，您可以點開來跟我講講話：\n{url}"

        st.code(url)
        st.text_area("建議文案", value=copy_text)
        if st.button("❌ 關閉"): st.session_state.show_invite = False
        st.markdown("---")

    st.divider()

    # 渲染對應 Tab
    if selected_tab == "🧬 聲紋訓練":
        tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, tier)
    elif selected_tab == "💎 分享解鎖":
        tab_store.render(supabase, st.session_state.user.user.id, xp)
    elif selected_tab == "📝 人設補完":
        tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    elif selected_tab == "🧠 回憶補完":
        tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
    elif selected_tab == "🎯 完美暱稱":
        tab_config.render(supabase, tier, xp)
