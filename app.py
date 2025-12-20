import streamlit as st
import json
import requests
import io
import time
import datetime
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
import extra_streamlit_components as stx

# ==========================================
# 應用程式：想念 (SaaS Beta 3.0 - 病毒裂變版)
# 更新內容：網址參數攔截、模擬來電介面、強制開場白、九官鳥模式
# ==========================================

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
# 新增：通話狀態
if "call_status" not in st.session_state: st.session_state.call_status = "ringing" # ringing, connected

# ==========================================
# 邏輯路由 (Router)
# ==========================================

# 1. 優先檢查網址參數 (URL Parameters Hook)
# 格式: ?token=TOKEN_名字
params = st.query_params
if "token" in params and not st.session_state.guest_data:
    raw_token = params["token"]
    # 切分 Token 與 名字
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
            'display_name': display_name_from_url # 暫存 URL 上的名字
        }
        st.rerun()

# ------------------------------------------
# 情境 A: 親友訪客模式 (驚喜體驗)
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    # 取得後台資料
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    engine_type = audio.get_tts_engine_type(profile)
    
    # 嘗試讀取會員設定的暱稱 (比 URL 更準)
    persona_data = database.load_persona(supabase, role_name)
    display_name = persona_data.get('member_nickname', url_name) if persona_data else url_name

    # --- 階段 1: 來電模擬 (Ringing) ---
    if st.session_state.call_status == "ringing":
        # 全螢幕置中佈局
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(f"""
            <div style='text-align:center; padding-top:50px;'>
                <div style='font-size:80px;'>👤</div>
                <h1 style='color:#FAFAFA;'>{display_name}</h1>
                <p style='color:#CCC; font-size:20px; animation: blink 1.5s infinite;'>📞 來電中...</p>
            </div>
            <style>
                @keyframes blink {{ 0% {{opacity: 1;}} 50% {{opacity: 0.5;}} 100% {{opacity: 1;}} }}
            </style>
            """, unsafe_allow_html=True)
            
            # 接聽按鈕
            if st.button("🟢 接聽", use_container_width=True, type="primary"):
                st.session_state.call_status = "connected"
                # 每日簽到
                database.check_daily_interaction(supabase, owner_id)
                st.rerun()

    # --- 階段 2: 通話中 (Connected) ---
    elif st.session_state.call_status == "connected":
        
        # 1. 自動播放開場白 (驚嚇點)
        # 檢查是否已播放過 (避免重整頁面重複播)
        if "opening_played" not in st.session_state:
            opening_bytes = audio.get_audio_bytes(supabase, role_name, "opening")
            if opening_bytes:
                st.audio(opening_bytes, format="audio/mp3", autoplay=True)
            else:
                # 如果沒錄開場白，用 AI 生成一句
                fallback = audio.generate_speech("喂？你終於來啦！", tier)
                st.audio(fallback, format="audio/mp3", autoplay=True)
            st.session_state.opening_played = True

        # 2. 顯示通話介面
        ui.render_status_bar(tier, energy, 0, engine_type, is_guest=True)
        
        st.markdown(f"<h3 style='text-align:center;'>正在與 {display_name} 通話...</h3>", unsafe_allow_html=True)
        
        # 九官鳥模式開關
        parrot_mode = st.toggle("🦜 九官鳥模式 (我說什麼，他就學什麼)")

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
                            # 分支邏輯：九官鳥 vs 正常AI
                            if parrot_mode:
                                ai_text = user_text # 直接複誦
                            else:
                                # 正常 AI 思考
                                memories = database.get_all_memories_text(supabase, role_name)
                                has_nick = audio.get_audio_bytes(supabase, role_name, "nickname") is not None
                                ai_text = brain.think_and_reply(tier, persona_data, memories, user_text, has_nick)
                            
                            # 生成語音
                            raw_audio = audio.generate_speech(ai_text, tier)
                            final_audio = raw_audio
                            
                            # 如果是正常模式且有暱稱，進行拼接
                            if not parrot_mode and raw_audio:
                                nick_bytes = audio.get_audio_bytes(supabase, role_name, "nickname")
                                if nick_bytes: final_audio = audio.merge_audio_clips(nick_bytes, raw_audio)
                            
                            # 播放
                            if final_audio: 
                                st.audio(final_audio, format="audio/mp3", autoplay=True)
                            
                            st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
                            
                except Exception as e: st.error("連線不穩")

        st.divider()
        if st.button("🔴 掛斷"):
            st.session_state.guest_data = None
            st.session_state.call_status = "ringing"
            del st.session_state["opening_played"]
            st.rerun()
            
        # 裂變按鈕 (常駐顯示)
        st.markdown("""
        <div style='background-color:#262730; padding:15px; border-radius:10px; text-align:center; margin-top:20px; border:1px solid #FF4B4B;'>
            <p style='margin:0; font-size:14px; color:#CCC;'>😲 被嚇到了嗎？</p>
            <h4 style='color:#FFF; margin:5px 0;'>註冊免費獲得您的 AI 分身</h4>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👉 點此註冊 (送體驗點數)", use_container_width=True):
            st.session_state.guest_data = None # 登出訪客
            st.rerun() # 回首頁註冊

# ------------------------------------------
# 情境 B: 首頁 (會員登入) - 已隱藏訪客輸入框
# ------------------------------------------
elif not st.session_state.user:
    
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    
    # 單欄置中佈局 (因為訪客現在都走網址了)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>🤍 想念</h1>", unsafe_allow_html=True)
        st.caption("請登入管理您的數位分身，或點擊親友分享的連結進入對話。")
        
        tab_l, tab_s = st.tabs(["會員登入", "免費註冊"])
        
        with tab_l:
            with st.form("login_form"):
                l_e = st.text_input("Email", value=saved_email)
                l_p = st.text_input("密碼", type="password")
                if st.form_submit_button("登入", use_container_width=True):
                    res = auth.login_user(supabase, l_e, l_p)
                    if res and res.user: 
                        cookie_manager.set("member_email", l_e, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
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
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    
    with st.sidebar:
        st.write(f"👤 {st.session_state.user.user.email}")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    ui.render_status_bar(tier, profile.get('energy'), xp, audio.get_tts_engine_type(profile))
    
    # 角色選擇
    allowed = ["朋友"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    col_r1, col_r2 = st.columns([7, 3])
    with col_r1:
        selected_role_display = st.selectbox("選擇對象", list(config.ROLE_MAPPING.keys()), label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[selected_role_display]
        
    # 生成連結 (須先檢查開場白)
    with col_r2:
        # 檢查是否已錄製開場白
        has_opening = audio.get_audio_bytes(supabase, target_role, "opening")
        
        if target_role == "friend" and not has_opening:
            st.button("🎁 生成邀請卡", disabled=True, help="請先在 Tab 1 完成「開場白」錄製")
        else:
            if st.button("🎁 生成邀請卡", type="primary"):
                token = database.create_share_token(supabase, target_role)
                st.session_state.current_token = token
                st.session_state.show_invite = True

    if not has_opening and target_role == "friend":
        st.warning("⚠️ 請先至 **「🧬 聲紋訓練」** 錄製惡作劇開場白，才能生成邀請連結！")

    # 邀請卡彈窗
    if st.session_state.show_invite:
        token = st.session_state.get("current_token", "ERROR")
        # 讀取會員設定的名字，若無則用預設
        p_data = database.load_persona(supabase, target_role)
        my_name = p_data.get('member_nickname', '我') if p_data else '我'
        
        # 組合帶參數的連結
        app_url = f"https://missyou.streamlit.app/?token={token}_{my_name}"
        
        st.markdown("---")
        with st.container():
            st.success(f"### 💌 邀請連結已生成")
            st.write("將此連結傳給朋友，點擊即可直接通話 (免輸入代碼)：")
            st.code(app_url, language="text")
            
            # 文案模板
            share_text = f"欸！我做了一個 AI 分身，超像的！\n點這個連結打電話給我：\n{app_url}\n\n(記得開聲音喔)"
            st.text_area("建議文案", value=share_text)
            
            if st.button("❌ 關閉"): st.session_state.show_invite = False
        st.markdown("---")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧬 聲紋訓練", "💎 分享解鎖", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"])

    # TAB 1: 聲紋訓練 (新增開場白錄製)
    with tab1:
        st.subheader("STEP 1: 基礎聲紋")
        # ... (略：原本的暱稱錄製) ...
        # 為了節省篇幅，這裡請放入原本的暱稱錄製代碼
        
        st.markdown("---")
        st.subheader("STEP 2: 惡作劇開場白 (強制)")
        st.info("這段聲音會在朋友「接聽」電話時，第一時間播放。請錄得像真的一樣！")
        
        st.markdown("**請按下錄音，並用自然的語氣說：**")
        st.markdown("> 「喂～你終於來啦！等你好久，剛剛說到哪裡？」")
        
        op_rec = st.audio_input("錄製開場白", key="op_rec")
        if op_rec:
            if st.button("💾 上傳開場白 (解鎖分享功能)"):
                if audio.upload_audio_file(supabase, target_role, op_rec.read(), "opening"):
                    st.success("成功！現在可以生成邀請卡了。")
                    st.session_state.has_opening = True
                    time.sleep(1)
                    st.rerun()

    # 其他 Tab 維持原樣 (請複製上一版的 Tab 2-5 內容)
    # ...
