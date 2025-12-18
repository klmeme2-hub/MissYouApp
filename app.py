import streamlit as st
import json
import requests
import io
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
# import extra_streamlit_components as stx  <-- 暫時註解掉這個元兇

# ==========================================
# 應用程式：想念 (SaaS 救援版)
# 更新內容：移除 Cookie Manager，確保程式能順利啟動
# ==========================================

st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="🤍", layout="wide")

# 暫時不載入 CSS，先確認功能正常 (您可以稍後取消註解)
ui.load_css() 

# 2. 系統檢查
if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ Secrets 設定缺失")
    st.stop()

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

# ==========================================
# 邏輯路由
# ==========================================

# ------------------------------------------
# 情境 A: 親友訪客模式
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    
    # 取得資料 (加上容錯)
    profile = database.get_user_profile(supabase, user_id=owner_id)
    if not profile: profile = {"tier": "basic", "energy": 0, "xp": 0}
    
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    
    daily_msg = database.check_daily_interaction(supabase, owner_id)
    if daily_msg: st.toast(daily_msg, icon="📅")
    
    engine_type = audio.get_tts_engine_type(profile)
    ui.render_status_bar(tier, energy, profile.get('xp',0), engine_type, is_guest=True)
    
    if energy <= 0:
        st.error("💔 心靈電量已耗盡...")
        # ... (儲值按鈕邏輯)
    else:
        # 讀取人設與稱呼
        persona_data = database.load_persona(supabase, role_name)
        display_name = "會員"
        if persona_data and persona_data.get('member_nickname'):
            display_name = persona_data['member_nickname']
            
        st.markdown(f"<h2 style='text-align:center;'>📞 與 [{display_name}] 通話中...</h2>", unsafe_allow_html=True)
        
        if not persona_data:
            st.warning("對方尚未設定資料。")
        else:
            col_c1, col_c2 = st.columns([1, 2])
            with col_c1: st.image("https://cdn-icons-png.flaticon.com/512/607/607414.png", width=150)
            with col_c2: st.info(f"這是 {display_name} 留給您的聲音。\n每次對話消耗 1 點電量。")

            if "chat_history" not in st.session_state: st.session_state.chat_history = []

            audio_val = st.audio_input("請按此說話...", key="guest_rec")
            if audio_val:
                try:
                    database.update_profile_stats(supabase, owner_id, energy_delta=-1)
                    user_text = brain.transcribe_audio(audio_val)
                    if len(user_text.strip()) > 1:
                        with st.spinner("思考中..."):
                            memories = database.get_all_memories_text(supabase, role_name)
                            has_nick = audio.get_nickname_audio_bytes(supabase, role_name) is not None
                            ai_text = brain.think_and_reply(tier, persona_data, memories, user_text, has_nick)
                            raw_audio = audio.generate_speech(ai_text, tier)
                            
                            final_audio = raw_audio
                            if has_nick and raw_audio:
                                nick_bytes = audio.get_nickname_audio_bytes(supabase, role_name)
                                if nick_bytes: final_audio = audio.merge_audio_clips(nick_bytes, raw_audio)
                            
                            st.session_state.chat_history.append({"role": "user", "content": user_text})
                            st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                            
                            if final_audio: st.audio(final_audio, format="audio/mp3", autoplay=True)
                            st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
                except Exception as e: st.error(f"Error: {e}")

    st.divider()
    if st.button("🚪 離開通話"):
        st.session_state.guest_data = None
        st.rerun()

# ------------------------------------------
# 情境 B: 首頁 (訪客驗證 / 會員登入)
# ------------------------------------------
elif not st.session_state.user:
    col1, col2 = st.columns([1, 1], gap="large")
    
    # 左側：親友入口
    with col1:
        st.markdown("## 👋 我是親友")
        st.caption("輸入家人分享給您的邀請碼")
        
        token_input = st.text_input("通行碼", placeholder="例如：A8K29", label_visibility="collapsed")
        
        if st.button("🚀 開始對話", type="primary", use_container_width=True):
            data = database.validate_token(supabase, token_input.strip())
            if data:
                st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                st.success("驗證成功！")
                st.rerun()
            else: st.error("無效的通行碼")

    # 右側：會員入口 (標準版)
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
    # 防呆：如果 profile 是 None，給預設值
    if not profile: profile = {"tier": "basic", "energy": 30, "xp": 0}
    
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
    
    engine_type = audio.get_tts_engine_type(profile)
    ui.render_status_bar(tier, energy, xp, engine_type)
    
    allowed = ["朋友"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1: target_role = st.selectbox("選擇對象", allowed)
    
    if target_role == "朋友" and len(allowed) == 1:
        st.info("🔒 累積 **20 點 XP** 或 **付費升級**，即可解鎖「家人」角色。")

    st.divider()

    # 引入 Tab 模組
    from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧬 聲紋訓練", "💎 分享解鎖完整版", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"])

    with tab1: tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, st.secrets['VOICE_ID'], st.secrets['ELEVENLABS_API_KEY'])
    with tab2: tab_store.render(supabase, st.session_state.user.user.id, xp)
    with tab3: tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with tab4: tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
    with tab5: tab_config.render(supabase, tier, xp)
