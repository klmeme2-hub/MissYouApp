import streamlit as st
import json
import time
import datetime
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory
import extra_streamlit_components as stx

# ==========================================
# 應用程式：MetaVoice (SaaS Beta 4.3 - UI 緊湊優化版)
# ==========================================

st.set_page_config(page_title="MetaVoice", page_icon="🌌", layout="centered") # 保持置中
ui.load_css()

cookie_manager = stx.CookieManager()

if "SUPABASE_URL" not in st.secrets: st.stop()
supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None
if "call_status" not in st.session_state: st.session_state.call_status = "ringing"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen"

# 1. 網址參數攔截
if "token" in st.query_params and not st.session_state.user and not st.session_state.guest_data:
    try:
        raw = st.query_params["token"]
        real_tk = raw.split("_")[0] if "_" in raw else raw
        d_name = raw.split("_")[1] if "_" in raw else "朋友"
        data = database.validate_token(supabase, real_tk)
        if data:
            st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role'], 'display_name': d_name}
            st.rerun()
    except: pass

# ------------------------------------------
# 情境 A: 訪客模式
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    
    persona_data = database.load_persona(supabase, role_name)
    display_name = persona_data.get('member_nickname', url_name) if persona_data else url_name

    # 階段 1: 來電
    if st.session_state.call_status == "ringing":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(f"<div style='text-align:center; padding-top:30px;'><div style='font-size:60px;'>👤</div><h3>{display_name}</h3><p style='color:#CCC; animation:blink 1.5s infinite;'>📞 來電中...</p></div><style>@keyframes blink {{0%{{opacity:1}} 50%{{opacity:0.5}} 100%{{opacity:1}}}}</style>", unsafe_allow_html=True)
            if st.button("🟢 接聽", use_container_width=True, type="primary"):
                st.session_state.call_status = "connected"
                database.check_daily_interaction(supabase, owner_id)
                st.rerun()

    # 階段 2: 通話
    elif st.session_state.call_status == "connected":
        if "opening_played" not in st.session_state:
            # 優先找開場白 -> 其次找暱稱 -> 最後用 AI
            op_bytes = audio.get_audio_bytes(supabase, role_name, "opening")
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
                            if parrot_mode:
                                ai_text = user_text
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

# ------------------------------------------
# 情境 B: 未登入
# ------------------------------------------
elif not st.session_state.user:
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    
    # 這裡因為是置中佈局，直接顯示登入框
    st.markdown("<h1 style='text-align:center;'>🌌 元宇宙聲紋站</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>元宇宙的第一張通行證：鎸刻你的數位聲紋</p>", unsafe_allow_html=True)
    
    tab_l, tab_s = st.tabs(["會員登入", "免費註冊"])
    with tab_l:
        with st.form("login"):
            le = st.text_input("Email", value=saved_email)
            lp = st.text_input("密碼", type="password")
            if st.form_submit_button("登入", use_container_width=True):
                r = auth.login_user(supabase, le, lp)
                if r and r.user:
                    cookie_manager.set("member_email", le, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                    st.session_state.user = r
                    st.rerun()
                else: st.error("失敗")
    with tab_s:
        se = st.text_input("Email", key="se")
        sp = st.text_input("密碼", type="password", key="sp")
        if st.button("註冊", use_container_width=True):
            r = auth.signup_user(supabase, se, sp)
            if r and r.user:
                database.get_user_profile(supabase, r.user.id)
                st.session_state.user = r
                st.success("成功")
                st.rerun()
            else: st.error("失敗")

# ------------------------------------------
# 情境 C: 會員後台 (UI 大改版)
# ------------------------------------------
else:
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    
    # --- 新版 Header 佈局 ---
    # 左 7 : 右 3
    col_head_main, col_head_info = st.columns([7, 3])
    
    with col_head_main:
        st.markdown("""
        <div>
            <h1 style='font-size: 28px; margin-bottom:0;'>🌌 元宇宙聲紋站</h1>
            <p class='subtitle'>元宇宙的第一張通行證：鎸刻你的數位聲紋</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_head_info:
        # 右上角緊湊的使用者資訊框
        st.markdown(f"""
        <div class="user-info-box">
            <div class="user-email">{st.session_state.user.user.email}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("登出", key="logout_btn"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # 狀態列
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile))
    
    # 角色選擇與分享區
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    c_role, c_btn = st.columns([7, 3])
    with c_role:
        disp_role = st.selectbox("選擇對象", allowed, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[disp_role]
    with c_btn:
        has_op = audio.get_audio_bytes(supabase, target_role, "opening")
        
        # 按鈕提示邏輯
        btn_label = "🎁 生成邀請卡"
        if target_role != "friend": 
            # 如果不是朋友，提示升級
            # 這裡只改 tooltip, 不改按鈕文字以免太長
            help_txt = "分享給親友賺取 XP，升級高級聲音模型"
        else:
            help_txt = "生成惡作劇連結分享給朋友"

        if st.button(btn_label, type="primary", use_container_width=True, help=help_txt):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True
            
    # 提示訊息
    if not has_op and target_role == "friend":
        st.caption("⚠️ 尚未錄製口頭禪，朋友將聽到 AI 語音。建議至「聲紋訓練」Step 1 錄製。")
    if target_role == "friend" and len(allowed) == 1:
        st.info("🔓 累積 **20 點 XP** 或 **付費升級**，即可解鎖「家人」角色。")

    # 邀請卡彈窗
    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        
        st.markdown("---")
        st.success(f"💌 {disp_role} 的邀請連結已生成！")
        
        copy_text = f"欸！我做了一個AI分身超像的，點這個連結打電話給我：\n{url}"
        if target_role == "partner": copy_text = f"親愛的，這是我留給你的聲音：\n{url}"
        elif target_role == "junior": copy_text = f"孩子，這是爸媽的時光膠囊：\n{url}"
        elif target_role == "elder": copy_text = f"爸/媽，您可以點開來跟我講講話：\n{url}"

        st.code(url)
        st.text_area("建議文案 (可直接複製)", value=copy_text)
        if st.button("❌ 關閉"): st.session_state.show_invite = False
        st.markdown("---")

    st.divider()

    # --- TAB 分頁結構 (4 Tabs) ---
    t1, t2, t3, t4 = st.tabs(["🧬 聲紋訓練", "💎 等級說明", "📝 人設補完", "🧠 回憶補完"])

    with t1: tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, tier)
    with t2: tab_store.render(supabase, st.session_state.user.user.id, xp)
    with t3: tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t4: tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
