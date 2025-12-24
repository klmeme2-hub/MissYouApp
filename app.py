import streamlit as st
import json
import time
import datetime
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
# 移除已刪除的 Tab
from modules.tabs import tab_voice, tab_persona, tab_memory
import extra_streamlit_components as stx

# ==========================================
# 應用程式：MetaVoice (SaaS Beta 4.3 - 緊湊版)
# ==========================================

# 1. UI 設定 (使用 centered 但 CSS 會強制加寬)
st.set_page_config(page_title="MetaVoice", page_icon="🌌", layout="centered")
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

if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None
if "call_status" not in st.session_state: st.session_state.call_status = "ringing"

# ==========================================
# 1. 網址攔截
# ==========================================
if "token" in st.query_params and not st.session_state.user and not st.session_state.guest_data:
    try:
        raw_token = st.query_params["token"]
        real_token = raw_token.split("_")[0] if "_" in raw_token else raw_token
        d_name = raw_token.split("_")[1] if "_" in raw_token else "朋友"
        
        data = database.validate_token(supabase, real_token)
        if data:
            st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role'], 'display_name': d_name}
            st.rerun()
    except: pass

# ==========================================
# 情境 A: 訪客模式 (維持原樣，篇幅省略)
# ==========================================
if st.session_state.guest_data:
    # ... (請保留原本的訪客模式代碼，為節省空間這裡省略，功能邏輯與上一版完全相同) ...
    # 若需完整代碼，請告知，我會補上
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    engine_type = audio.get_tts_engine_type(profile)
    
    persona_data = database.load_persona(supabase, role_name)
    display_name = persona_data.get('member_nickname', url_name) if persona_data else url_name

    if st.session_state.call_status == "ringing":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(f"<div style='text-align:center; padding-top:50px;'><div style='font-size:80px;'>👤</div><h1>{display_name}</h1><p>📞 來電中...</p></div>", unsafe_allow_html=True)
            if st.button("🟢 接聽", use_container_width=True, type="primary"):
                st.session_state.call_status = "connected"
                database.check_daily_interaction(supabase, owner_id)
                st.rerun()

    elif st.session_state.call_status == "connected":
        if "opening_played" not in st.session_state:
            op_bytes = audio.get_audio_bytes(supabase, role_name, "opening")
            if op_bytes: st.audio(op_bytes, format="audio/mp3", autoplay=True)
            else: 
                fb = audio.generate_speech("喂？你終於來啦！", tier)
                st.audio(fb, format="audio/mp3", autoplay=True)
            st.session_state.opening_played = True

        ui.render_status_bar(tier, energy, 0, engine_type, is_guest=True)
        st.markdown(f"<h3 style='text-align:center;'>與 {display_name} 通話中...</h3>", unsafe_allow_html=True)
        
        parrot_mode = False
        if role_name == "friend": parrot_mode = st.toggle("🦜 九官鳥模式")
        
        if energy <= 0:
            st.error("💔 電量耗盡")
            if st.button("🔋 幫他儲值 $88"):
                database.update_profile_stats(supabase, owner_id, energy_delta=100)
                st.rerun()
        else:
            audio_val = st.audio_input("請說話...", key="g_rec")
            if audio_val:
                try:
                    database.update_profile_stats(supabase, owner_id, energy_delta=-1)
                    user_text = brain.transcribe_audio(audio_val)
                    if len(user_text.strip()) > 0:
                        if parrot_mode: ai_text = user_text
                        else:
                            mems = database.get_all_memories_text(supabase, role_name)
                            has_nick = audio.get_audio_bytes(supabase, role_name, "nickname") is not None
                            ai_text = brain.think_and_reply(tier, persona_data, mems, user_text, has_nick)
                        
                        wav = audio.generate_speech(ai_text, tier)
                        final = wav
                        if not parrot_mode and wav and role_name != "friend":
                            nb = audio.get_audio_bytes(supabase, role_name, "nickname")
                            if nb: final = audio.merge_audio_clips(nb, wav)
                        
                        if final: st.audio(final, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
                except: pass
    
    st.divider()
    if st.button("🔴 掛斷"):
        st.session_state.guest_data = None
        st.query_params.clear()
        st.rerun()

# ------------------------------------------
# 情境 B: 未登入 (登入頁)
# ------------------------------------------
elif not st.session_state.user:
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("## 👋 親友入口")
        token_input = st.text_input("通行碼", placeholder="A8K29")
        if st.button("🚀 開始對話", type="primary"):
            d = database.validate_token(supabase, token_input.strip())
            if d:
                st.session_state.guest_data = {'owner_id': d['user_id'], 'role': d['role']}
                st.rerun()
            else: st.error("無效")

    with col2:
        st.markdown("## 👤 會員登入")
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
        if st.button("註冊新帳號"):
            res = auth.signup_user(supabase, le, lp)
            if res and res.user:
                database.get_user_profile(supabase, res.user.id)
                st.session_state.user = res
                st.rerun()

# ------------------------------------------
# 情境 C: 會員後台 (新版佈局)
# ------------------------------------------
else:
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    
    # 1. 頂部 Header (Logo + 登出)
    c_head1, c_head2 = st.columns([8, 2])
    with c_head1:
        st.markdown("<h1 style='padding-top:0;'>🌌 元宇宙聲紋站</h1>", unsafe_allow_html=True)
    with c_head2:
        st.markdown(f"<div style='text-align:right; font-size:12px; color:#888; margin-bottom:5px;'>{st.session_state.user.user.email}</div>", unsafe_allow_html=True)
        if st.button("登出", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # 2. 狀態列
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile))

    # 3. 會員等級說明 (折疊區塊 - 取代 Tab 2)
    with st.expander("💎 會員等級說明 / 升級 (點擊展開)", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            ui.render_dashboard_card("免費解鎖", "20 XP")
            st.caption("累積 20 XP 解鎖家人角色")
        with c2:
            ui.render_dashboard_card("中級守護者", "$99")
            if st.button("💰 升級中級"):
                database.upgrade_tier(supabase, st.session_state.user.user.id, "intermediate", 99, 20)
                st.rerun()
        with c3:
            ui.render_dashboard_card("高級刻錄師", "$599")
            if st.button("💰 升級高級"):
                database.upgrade_tier(supabase, st.session_state.user.user.id, "advanced", 599, 20)
                st.rerun()
        
        st.info("ℹ️ 分享邀請碼給朋友並獲得評分，可快速賺取 XP！")

    # 4. 角色控制台
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    c_role, c_btn = st.columns([7, 3])
    with c_role:
        disp_role = st.selectbox("選擇對象", allowed, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[disp_role]
    with c_btn:
        # 生成按鈕
        if st.button("🎁 生成邀請卡", type="primary", use_container_width=True):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True

    # 邀請卡彈窗
    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        
        st.success(f"💌 邀請連結 ({disp_role})")
        st.code(url)
        if st.button("❌ 關閉"): st.session_state.show_invite = False

    st.markdown("---")

    # 5. 功能分頁 (只剩 3 個)
    t1, t2, t3 = st.tabs(["🧬 聲紋訓練", "📝 人設補完", "🧠 回憶補完"])

    with t1: tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, tier)
    with t2: tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t3: tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
