import streamlit as st
import json
import time
import datetime
from openai import OpenAI
import extra_streamlit_components as stx

# 引入模組
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config

# ==========================================
# 應用程式：想念 (SaaS Beta 3.3 - 解鎖分享限制版)
# 更新內容：移除生成邀請卡的強制錄音限制，讓測試更順暢
# ==========================================

st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="📞", layout="wide")
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

# ==========================================
# 1. 網址參數攔截
# ==========================================
if "token" in st.query_params and not st.session_state.user and not st.session_state.guest_data:
    try:
        raw_token = st.query_params["token"]
        if "_" in raw_token:
            real_token = raw_token.split("_")[0]
            display_name_from_url = raw_token.split("_")[1]
        else:
            real_token = raw_token
            display_name_from_url = "朋友"
        
        data = database.validate_token(supabase, real_token)
        if data:
            st.session_state.guest_data = {
                'owner_id': data['user_id'], 
                'role': data['role'], 
                'display_name': display_name_from_url
            }
            st.rerun()
        else:
            st.error(f"連結無效 (Token: {real_token})")
            st.query_params.clear()
    except Exception as e: st.error(f"連結解析錯誤: {e}")

# ==========================================
# 2. 邏輯路由
# ==========================================

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
    engine_type = audio.get_tts_engine_type(profile)
    
    persona_data = database.load_persona(supabase, role_name)
    display_name = url_name
    if persona_data and persona_data.get('member_nickname'):
        display_name = persona_data['member_nickname']

    # 階段 1: 來電模擬
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

    # 階段 2: 通話中
    elif st.session_state.call_status == "connected":
        if "opening_played" not in st.session_state:
            op_bytes = audio.get_audio_bytes(supabase, role_name, "opening")
            if op_bytes: 
                st.audio(op_bytes, format="audio/mp3", autoplay=True)
            else: 
                # AI 候補開場白 (解決沒錄音就不能用的問題)
                fb = audio.generate_speech("喂？你終於來啦！等你好久了。", tier)
                st.audio(fb, format="audio/mp3", autoplay=True)
            st.session_state.opening_played = True

        ui.render_status_bar(tier, energy, 0, engine_type, is_guest=True)
        st.markdown(f"<h3 style='text-align:center;'>與 {display_name} 通話中...</h3>", unsafe_allow_html=True)
        
        parrot_mode = st.toggle("🦜 九官鳥模式")

        if energy <= 0:
            st.error("💔 訊號中斷 (電量耗盡)")
            if st.button("🔋 幫他儲值 $88"):
                database.update_profile_stats(supabase, owner_id, energy_delta=100)
                st.rerun()
        else:
            audio_val = st.audio_input("請說話...", key="guest_rec")
            if audio_val:
                try:
                    database.update_profile_stats(supabase, owner_id, energy_delta=-1)
                    user_text = brain.transcribe_audio(audio_val)
                    
                    if len(user_text.strip()) > 0:
                        with st.spinner("..."):
                            if parrot_mode:
                                ai_text = user_text
                            else:
                                memories = database.get_all_memories_text(supabase, role_name)
                                has_nick = audio.get_audio_bytes(supabase, role_name, "nickname") is not None
                                ai_text = brain.think_and_reply(tier, persona_data, memories, user_text, has_nick)
                            
                            raw_audio = audio.generate_speech(ai_text, tier)
                            final_audio = raw_audio
                            
                            if not parrot_mode and raw_audio:
                                nb = audio.get_audio_bytes(supabase, role_name, "nickname")
                                if nb: final_audio = audio.merge_audio_clips(nb, raw_audio)
                            
                            if final_audio: st.audio(final_audio, format="audio/mp3", autoplay=True)
                            st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
                except: st.error("連線不穩")

        st.divider()
        if st.button("🔴 掛斷"):
            st.session_state.guest_data = None
            st.session_state.call_status = "ringing"
            if "opening_played" in st.session_state: del st.session_state["opening_played"]
            st.query_params.clear()
            st.rerun()
            
        st.info("😲 被嚇到了嗎？註冊免費獲得您的 AI 分身 👇")
        if st.button("👉 點此註冊"):
            st.session_state.guest_data = None
            st.query_params.clear()
            st.rerun()

# ------------------------------------------
# 情境 B: 首頁
# ------------------------------------------
elif not st.session_state.user:
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    saved_token = cookies.get("guest_token", "")
    
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("## 👋 我是親友")
        token_input = st.text_input("通行碼", value=saved_token, placeholder="A8K29")
        if st.button("🚀 開始對話", type="primary"):
            d = database.validate_token(supabase, token_input.strip())
            if d:
                cookie_manager.set("guest_token", token_input.strip(), expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.session_state.guest_data = {'owner_id': d['user_id'], 'role': d['role']}
                st.rerun()
            else: st.error("無效")

    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        with tab_l:
            with st.form("login"):
                le = st.text_input("Email", value=saved_email)
                lp = st.text_input("密碼", type="password")
                if st.form_submit_button("登入"):
                    r = auth.login_user(supabase, le, lp)
                    if r and r.user:
                        cookie_manager.set("member_email", le, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                        st.session_state.user = r
                        st.rerun()
                    else: st.error("失敗")
        with tab_s:
            se = st.text_input("Email", key="se")
            sp = st.text_input("設定密碼", type="password", key="sp")
            if st.button("註冊"):
                r = auth.signup_user(supabase, se, sp)
                if r and r.user:
                    database.get_user_profile(supabase, r.user.id)
                    st.session_state.user = r
                    st.success("成功")
                    st.rerun()
                else: st.error("失敗")

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
    ui.render_status_bar(tier, profile.get('energy'), xp, audio.get_tts_engine_type(profile))
    
    # 權限鎖定：初級會員且 XP 不足時，只開放「朋友」
    allowed = ["朋友/死黨"] # 預設只開放朋友
    if tier != 'basic' or xp >= 20: 
        allowed = list(config.ROLE_MAPPING.keys()) # 解鎖全部
    
    # 頂部控制台 (角色選擇 + 分享)
    c_role, c_btn = st.columns([7, 3])
    with c_role:
        disp_role = st.selectbox("選擇對象", allowed, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[disp_role]
    with c_btn:
        # 【修正】移除強制錄音檢查，讓中級會員能直接測試
        has_op = audio.get_audio_bytes(supabase, target_role, "opening")
        
        # 即使沒有錄音，也允許生成，訪客端會自動用 AI 聲音候補
        if st.button("🎁 生成邀請卡", type="primary"):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True
    
    if not has_op and target_role == "friend":
        st.caption("⚠️ 尚未錄製惡作劇開場白，朋友將會聽到 AI 語音 (建議去聲紋訓練錄製以達最佳效果)")

    if target_role == "friend" and len(allowed) == 1:
        st.info("🔒 累積 **20 點 XP** 或 **付費升級**，即可解鎖「家人」角色。")

    # 邀請卡彈窗
    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERROR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        
        st.markdown("---")
        st.success(f"💌 邀請連結 ({disp_role})")
        
        # 文案邏輯
        if target_role == "friend":
            copy_text = f"欸！我做了一個AI分身超像的，點這個連結打電話給我：\n{url}\n\n(記得開聲音喔)"
        elif target_role == "partner":
            copy_text = f"親愛的，這裡有我留給你的專屬聲音：\n{url}\n\n想我的時候就點開來聽聽。"
        elif target_role == "junior":
            copy_text = f"孩子，這是爸媽留給你的時光膠囊：\n{url}\n\n無論在哪裡，我們都陪著你。"
        elif target_role == "elder":
            copy_text = f"爸/媽，這是我弄的一個小程式，您可以點開來跟我講講話：\n{url}\n\n就像打電話一樣簡單喔。"
        else:
            copy_text = f"點擊連結開始對話：\n{url}"

        st.code(url)
        st.text_area("建議文案 (可直接複製)", value=copy_text)
        
        if st.button("❌ 關閉"): st.session_state.show_invite = False
        st.markdown("---")

    st.divider()

    # 引入模組 Tab
    from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config

    t1, t2, t3, t4, t5 = st.tabs(["🧬 聲紋訓練", "💎 分享解鎖", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"])

    with t1: tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, st.secrets['VOICE_ID'], st.secrets['ELEVENLABS_API_KEY'])
    with t2: tab_store.render(supabase, st.session_state.user.user.id, xp)
    with t3: tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t4: tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
    with t5: tab_config.render(supabase, tier, xp)
