import streamlit as st
import json
import time
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config
import extra_streamlit_components as stx

st.set_page_config(page_title="想念", page_icon="📞", layout="wide")
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
# 新增：導航控制
if "active_tab" not in st.session_state: st.session_state.active_tab = "🧬 聲紋訓練"
# 訪客狀態
if "call_status" not in st.session_state: st.session_state.call_status = "ringing"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen" # listen, rating, interact

# ==========================================
# 1. 網址攔截
# ==========================================
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

# ==========================================
# 2. 邏輯路由
# ==========================================

# 情境 A: 訪客模式
if st.session_state.guest_data:
    owner_id = st.session_state.guest_data['owner_id']
    role_key = st.session_state.guest_data['role'] # friend, partner...
    url_name = st.session_state.guest_data.get('display_name', '朋友')
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    
    # 決定語音模型 (若為家人可切換)
    use_high_res = st.toggle("👑 高傳真線路 (消耗2電量)", value=False) if role_key != "friend" else False
    engine_type = "elevenlabs" if use_high_res else "openai"
    cost = 2 if use_high_res else 1

    # 顯示來電介面
    if st.session_state.call_status == "ringing":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(f"<div style='text-align:center; padding-top:50px;'><div style='font-size:80px;'>👤</div><h1>{url_name}</h1><p style='font-size:20px;'>📞 來電中...</p></div>", unsafe_allow_html=True)
            if st.button("🟢 接聽", use_container_width=True, type="primary"):
                st.session_state.call_status = "connected"
                # 每日簽到
                database.check_daily_interaction(supabase, owner_id)
                st.rerun()

    # 接通後
    elif st.session_state.call_status == "connected":
        
        # 🟢 軌道 A: 朋友/死黨 (裂變流程)
        if role_key == "friend":
            # 1. 強制播放開場 (真實口頭禪 + AI 求評分)
            if "opening_played" not in st.session_state:
                op_bytes = audio.get_audio_bytes(supabase, role_key, "opening")
                # AI 求評分文案
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
                if c1.button("🤖 不像"): rate=1
                if c2.button("🤔 有點像"): rate=3
                if c3.button("😱 像到發毛"): rate=5
                
                if 'rate' in locals():
                    database.submit_feedback(supabase, owner_id, rate, "朋友評分")
                    st.session_state.friend_stage = "interact"
                    
                    # 播放感謝語音
                    thx_audio = audio.generate_speech("太感謝你啦！幫我加了1積分。你可以試試下面的九官鳥模式，我會學你講話喔！", tier)
                    st.audio(thx_audio, format="audio/mp3", autoplay=True)
                    st.rerun()

            # 3. 互動區 (九官鳥 + 轉化)
            elif st.session_state.friend_stage == "interact":
                st.success("✅ 已解鎖互動功能")
                parrot = st.toggle("🦜 九官鳥模式", value=True)
                
                audio_val = st.audio_input("試試看說：我是大豬頭", key="p_rec")
                if audio_val:
                    txt = brain.transcribe_audio(audio_val)
                    if txt:
                        # 朋友模式不扣電量，或扣很少
                        ai_say = txt if parrot else "我是朋友模式AI，目前只支援九官鳥喔！"
                        wav = audio.generate_speech(ai_say, tier) # 這裡可視情況強制用 ElevenLabs 讓朋友驚艷
                        st.audio(wav, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_say}</div>', unsafe_allow_html=True)

                st.markdown("---")
                st.info("😲 被嚇到了嗎？")
                if st.button("👉 免費製作你的 AI 分身"):
                    st.session_state.guest_data = None
                    st.query_params.clear()
                    st.rerun()

        # ❤️ 軌道 B: 家人 (情感消耗流程)
        else:
            # 1. 溫馨開場
            if "opening_played" not in st.session_state:
                nick_bytes = audio.get_audio_bytes(supabase, role_key, "opening") # 這裡其實是暱稱
                # 這裡假設家人開場白是用暱稱錄音代替，或另外錄製
                ai_greet = audio.generate_speech("想我嗎？", tier)
                final = audio.merge_audio_clips(nick_bytes, ai_greet) if nick_bytes else ai_greet
                st.audio(final, format="audio/mp3", autoplay=True)
                st.session_state.opening_played = True

            # 2. 電子雞儀表板
            ui.render_status_bar(tier, energy, 0, engine_type="elevenlabs" if use_high_res else "openai", is_guest=True)
            
            # 3. 正常對話
            if energy <= 0:
                st.error("💔 電量耗盡")
                if st.button(f"🔋 幫他儲值 $88"):
                    database.update_profile_stats(supabase, owner_id, energy_delta=100)
                    st.rerun()
            else:
                audio_val = st.audio_input("請說話...", key="fam_rec")
                if audio_val:
                    # 扣點
                    database.update_profile_stats(supabase, owner_id, energy_delta=-cost)
                    
                    user_text = brain.transcribe_audio(audio_val)
                    if user_text:
                        # RAG
                        mems = database.get_all_memories_text(supabase, role_key)
                        persona = database.load_persona(supabase, role_key)
                        ai_text = brain.think_and_reply(tier, persona, mems, user_text, False)
                        
                        # TTS (根據開關決定引擎)
                        engine = "elevenlabs" if use_high_res else "openai"
                        # 這裡需要微調 audio.generate_speech 支援直接傳 engine 參數
                        # 為簡化，假設 audio.generate_speech 內部會判斷，我們這裡傳 tier 騙它
                        # 更好的做法是修改 audio.generate_speech 接受 engine 參數
                        # 暫時 Hack: 如果選高傳真，傳 'advanced' 給 generate_speech
                        hack_tier = 'advanced' if use_high_res else 'basic'
                        wav = audio.generate_speech(ai_text, hack_tier)
                        
                        st.audio(wav, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)

    if st.button("🔴 掛斷"):
        st.session_state.guest_data = None
        st.session_state.call_status = "ringing"
        if "opening_played" in st.session_state: del st.session_state["opening_played"]
        st.rerun()

# 情境 B: 未登入 (略，請複製前版)
elif not st.session_state.user:
    # ... (請貼上 SaaS Beta 3.3 的登入區塊) ...
    # 為了節省篇幅，這裡省略，請務必補上
    pass

# 情境 C: 會員後台
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
    
    # 頂部導航 (替代 st.tabs，實現程式化跳轉)
    # 使用 radio 模擬 tabs
    tabs = ["🧬 聲紋訓練", "💎 分享解鎖", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"]
    
    # 如果有指定跳轉，更新 radio 的 index
    if "nav_target" in st.session_state:
        try:
            default_index = tabs.index(st.session_state.nav_target)
        except: default_index = 0
        del st.session_state.nav_target # 用完即丟
    else:
        default_index = 0
        
    selected_tab = st.radio("功能選單", tabs, index=default_index, horizontal=True, label_visibility="collapsed")

    # 角色選擇 (共用)
    c_role, c_btn = st.columns([7, 3])
    with c_role:
        disp_role = st.selectbox("選擇對象", list(config.ROLE_MAPPING.keys()))
        target_role = config.ROLE_MAPPING[disp_role]
    with c_btn:
        # 檢查開場白
        has_op = audio.check_audio_exists(supabase, target_role, "opening")
        if st.button("🎁 生成邀請卡", type="primary"):
            if not has_op and target_role == "friend":
                st.error("⚠️ 請先完成聲紋訓練 (錄製口頭禪)")
                st.session_state.nav_target = "🧬 聲紋訓練" # 設定跳轉目標
                st.rerun()
            else:
                token = database.create_share_token(supabase, target_role)
                st.session_state.current_token = token
                st.session_state.show_invite = True

    # 邀請卡彈窗 (略，請複製前版)
    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        st.success(f"邀請連結：{url}")
        if st.button("關閉"): st.session_state.show_invite = False

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
