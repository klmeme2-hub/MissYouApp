import streamlit as st
import json
from openai import OpenAI
import requests

# 引入我們拆分好的模組
from modules import ui, auth, database, audio
from modules.config import ROLE_MAPPING

# 1. 載入 UI 設定
st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="🤍", layout="wide")
ui.load_css()

# 2. 初始化系統
if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ 請先設定 Secrets")
    st.stop()

supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 3. 讀取題庫
@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}
question_db = load_questions()

# 4. 狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1

# ==========================================
# 主程式邏輯路由
# ==========================================

# 情境 A: 訪客模式 (親友已輸入 Token)
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    st.markdown(f"<h2 style='text-align:center;'>📞 與 [{role_name}] 通話中...</h2>", unsafe_allow_html=True)
    
    persona_summary = database.load_persona(supabase, role_name)
    if not persona_summary:
        st.warning("對方尚未設定此角色的靈魂資料。")
    else:
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1: st.image("https://cdn-icons-png.flaticon.com/512/607/607414.png", width=150)
        with col_c2: st.info(f"這是 {role_name} 留給您的聲音。")

        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        
        audio_val = st.audio_input("請按此說話...", key="guest_rec")
        if audio_val:
            try:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_val)
                user_text = transcript.text
                if len(user_text.strip()) > 1:
                    with st.spinner("..."):
                        mem = database.search_relevant_memories(supabase, role_name, user_text)
                        has_nick = audio.get_nickname_audio_bytes(supabase, role_name) is not None
                        nick_instr = "【指令】回應開頭不要包含暱稱。" if has_nick else "請在開頭呼喚暱稱。"
                        prompt = f"{persona_summary}\n【回憶】{mem}\n{nick_instr}\n語氣自然。"
                        
                        msgs = [{"role": "system", "content": prompt}] + st.session_state.chat_history[-4:]
                        msgs.append({"role": "user", "content": user_text})
                        
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                        ai_text = res.choices[0].message.content
                        
                        st.session_state.chat_history.append({"role": "user", "content": user_text})
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                        
                        # TTS
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
                        data = {"text": ai_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}}
                        tts_res = requests.post(tts_url, json=data, headers=headers)
                        
                        final_audio = tts_res.content
                        if has_nick:
                            nick_bytes = audio.get_nickname_audio_bytes(supabase, role_name)
                            if nick_bytes: final_audio = audio.merge_audio_clips(nick_bytes, final_audio)
                        
                        st.audio(final_audio, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
            except Exception as e: st.error("連線不穩")

    st.divider()
    if st.button("離開通話"):
        st.session_state.guest_data = None
        st.rerun()

# 情境 B: 未登入 (首頁)
elif not st.session_state.user:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("## 👋 我是親友")
        token_input = st.text_input("通行碼 (Token)", placeholder="例如：A8K29", label_visibility="collapsed")
        if st.button("開始對話", type="primary", use_container_width=True):
            data = database.validate_token(supabase, token_input.strip())
            if data:
                st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                st.success("驗證成功！")
                st.rerun()
            else: st.error("無效的通行碼")

    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        with tab_l:
            email = st.text_input("Email", key="l_e")
            pwd = st.text_input("密碼", type="password", key="l_p")
            if st.button("登入", use_container_width=True):
                res = auth.login_user(supabase, email, pwd)
                if res and res.user: 
                    st.session_state.user = res
                    st.rerun()
                else: st.error("錯誤")
        with tab_s:
            s_email = st.text_input("Email", key="s_e")
            s_pwd = st.text_input("設定密碼", type="password", key="s_p")
            if st.button("註冊", use_container_width=True):
                res = auth.signup_user(supabase, s_email, s_pwd)
                if res and res.user:
                    st.success("成功！")
                    st.session_state.user = res
                    st.rerun()
                else: st.error("失敗")

# 情境 C: 會員後台
else:
    with st.sidebar:
        st.write(f"👤 {st.session_state.user.user.email}")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1: target_role = st.selectbox("您想要將你的聲音留給誰?", list(ROLE_MAPPING.keys()))
    
    tab1, tab2, tab3 = st.tabs(["🧬 複製聲紋 (步驟引導)", "📝 人設補完", "🧠 回憶補完"])

    # TAB 1: 複製聲紋
    with tab1:
        cols = st.columns(5)
        steps = ["❶ 喚名", "❷ 安慰", "❸ 鼓勵", "❹ 詼諧", "❺ 完成"]
        for i, s in enumerate(steps):
            if i + 1 == st.session_state.step: cols[i].markdown(f"**<span style='color:#1565C0'>{s}</span>**", unsafe_allow_html=True)
            else: cols[i].markdown(f"<span style='color:#ccc'>{s}</span>", unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.step == 1:
            st.subheader("STEP 1: 輕輕喚你的名")
            st.info("請錄下您平常呼喚對方暱稱的聲音，這將成為每次對話的開頭。")
            nickname_text = st.text_input("請輸入暱稱文字", placeholder="例如：老婆～")
            rec = st.audio_input("錄音 (建議 2-3 秒)")
            if rec and nickname_text:
                if st.button("💾 上傳並試聽"):
                    with st.spinner("處理中..."):
                        audio_bytes = rec.read()
                        audio.upload_nickname_audio(supabase, target_role, audio_bytes)
                        rec.seek(0)
                        audio.train_voice_sample(rec.read())
                        
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
                        data = {"text": "最近好嗎？", "model_id": "eleven_multilingual_v2"}
                        r = requests.post(tts_url, json=data, headers=headers)
                        
                        final = audio.merge_audio_clips(audio_bytes, r.content)
                        st.audio(final, format="audio/mp3")
                        st.success("聲紋已建立！")
            if st.button("下一步 →"): st.session_state.step = 2; st.rerun()

        elif st.session_state.step in [2, 3, 4]:
            # (這裡放腳本邏輯，為節省篇幅省略，請直接複製上一版代碼的腳本部分即可，只需記得呼叫 audio.train_voice_sample)
            scripts = {2: ("刻錄「安慰語氣」", "腳本內容..."), 3: ("刻錄「鼓勵語氣」", "腳本內容..."), 4: ("刻錄「輕鬆詼諧語氣」", "腳本內容...")} # 請填入完整內容
            # ... (這裡邏輯與上一版相同，只是函數改為呼叫 module)
            # 範例： audio.train_voice_sample(rec.read())
            pass # 請填入完整邏輯
            
        elif st.session_state.step == 5:
            st.balloons()
            st.success("🎉 刻錄完成！")
            if "share_token" not in st.session_state:
                st.session_state.share_token = database.create_share_token(supabase, target_role)
            token = st.session_state.share_token
            st.markdown(f"### 您的專屬分享碼：`{token}`")
            if st.button("← 返回"): st.session_state.step = 1; st.rerun()

    # TAB 2 & 3: 使用 database 模組的函數即可
    # ... (請將上一版的 TAB 2 和 TAB 3 邏輯複製過來，並將 save_memory_fragment 等函數改為 database.save_memory_fragment)