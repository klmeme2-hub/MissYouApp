import streamlit as st
import json
import requests
from openai import OpenAI
from modules import ui, auth, database, audio, config

# ==========================================
# 版本資訊：共鳴 1 版 (Gamification V1)
# 更新內容：積分系統、鎖定機制、朋友評分、口頭禪錄製
# ==========================================

st.set_page_config(page_title="想念 - 惡作劇分身", page_icon="👻", layout="wide")
ui.load_css()

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

if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1

# ==========================================
# 邏輯路由
# ==========================================

# ------------------------------------------
# 情境 A: 訪客模式 (朋友來玩)
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    
    st.markdown(f"<h2 style='text-align:center;'>👻 猜猜我是誰？</h2>", unsafe_allow_html=True)
    st.caption("這是你的朋友訓練出來的 AI 分身，試著跟它聊聊，看像不像！")
    
    persona_summary = database.load_persona(supabase, role_name)
    
    if not persona_summary:
        st.warning("這個分身還在學說話，請叫朋友趕快去訓練！")
    else:
        # 頭像與對話區
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1: st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=150) # 惡作劇頭像
        
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        if "has_rated" not in st.session_state: st.session_state.has_rated = False

        audio_val = st.audio_input("按此對話 (試試問他私密問題)", key="guest_rec")
        
        if audio_val:
            try:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_val)
                user_text = transcript.text
                if len(user_text.strip()) > 1:
                    with st.spinner("AI 正在模仿語氣..."):
                        mem = database.search_relevant_memories(supabase, role_name, user_text)
                        
                        # 檢查口頭禪 (原暱稱功能)
                        has_catchphrase = audio.get_nickname_audio_bytes(supabase, role_name) is not None
                        nick_instr = "【指令】回應開頭不要加口頭禪。" if has_catchphrase else "請在開頭加上你的招牌口頭禪。"
                        
                        prompt = f"{persona_summary}\n【相關記憶】{mem}\n{nick_instr}\n語氣要輕鬆、像朋友一樣閒聊，可以開玩笑。"
                        
                        msgs = [{"role": "system", "content": prompt}] + st.session_state.chat_history[-4:]
                        msgs.append({"role": "user", "content": user_text})
                        
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                        ai_text = res.choices[0].message.content
                        
                        st.session_state.chat_history.append({"role": "user", "content": user_text})
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                        
                        # TTS
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
                        data = {"text": ai_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}} # 朋友語氣可以浮誇一點
                        tts_res = requests.post(tts_url, json=data, headers=headers)
                        
                        final_audio = tts_res.content
                        if has_catchphrase:
                            catch_bytes = audio.get_nickname_audio_bytes(supabase, role_name)
                            if catch_bytes: final_audio = audio.merge_audio_clips(catch_bytes, final_audio)
                        
                        st.audio(final_audio, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
            except Exception as e: st.error("連線錯誤")

        # --- 評分互動區 (裂變核心) ---
        st.divider()
        if not st.session_state.has_rated:
            st.markdown("### ⭐ 覺得像嗎？幫朋友打個分！")
            st.caption("你的評分會增加他的【共鳴值】，幫他解鎖更多功能。")
            
            c_score1, c_score2, c_score3 = st.columns(3)
            rating = 0
            if c_score1.button("🤖 不像 (1分)"): rating = 1
            if c_score2.button("🤔 有點像 (3分)"): rating = 3
            if c_score3.button("😱 像到發毛 (5分)"): rating = 5
            
            if rating > 0:
                database.submit_feedback(supabase, owner_id, rating, "朋友測試回饋")
                st.session_state.has_rated = True
                st.balloons()
                st.success(f"感謝評價！已幫朋友增加 {rating} 點共鳴值。")
                st.rerun()
        else:
            st.success("✅ 您已完成評分，感謝您的參與！")
            # 轉化鉤子
            st.markdown("""
            <div style='background-color:#E8F5E9; padding:20px; border-radius:10px; text-align:center; margin-top:20px;'>
                <h3>😈 想不想也做一個 AI 去騙朋友？</h3>
                <p>現在註冊，免費製作你的惡作劇分身！</p>
            </div>
            """, unsafe_allow_html=True)

    if st.button("離開"):
        st.session_state.guest_data = None
        st.rerun()

# ------------------------------------------
# 情境 B: 首頁 (訪客/登入)
# ------------------------------------------
elif not st.session_state.user:
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.markdown("## 👋 我是朋友")
        st.caption("輸入朋友給你的邀請碼")
        token_input = st.text_input("邀請碼 (Token)", placeholder="例如：A8K29", label_visibility="collapsed")
        if st.button("🚀 開始測試", type="primary", use_container_width=True):
            data = database.validate_token(supabase, token_input.strip())
            if data:
                st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                st.success("驗證成功！")
                st.rerun()
            else: st.error("無效的邀請碼")

    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        with tab_l:
            l_e = st.text_input("Email", key="le")
            l_p = st.text_input("密碼", type="password", key="lp")
            if st.button("登入", use_container_width=True):
                res = auth.login_user(supabase, l_e, l_p)
                if res and res.user: 
                    st.session_state.user = res
                    st.rerun()
                else: st.error("登入失敗")
        with tab_s:
            s_e = st.text_input("Email", key="se")
            s_p = st.text_input("設定密碼", type="password", key="sp")
            if st.button("註冊 (送 5 點共鳴值)", use_container_width=True):
                res = auth.signup_user(supabase, s_e, s_p)
                if res and res.user:
                    # 註冊送初始積分 (邏輯在資料庫或這裡處理)
                    database.add_resonance_score(supabase, res.user.id, 5)
                    st.session_state.user = res
                    st.success("註冊成功！")
                    st.rerun()
                else: st.error("註冊失敗")

# ------------------------------------------
# 情境 C: 會員後台 (Gamified Dashboard)
# ------------------------------------------
else:
    # 取得使用者資料
    profile = database.get_user_profile(supabase)
    score = profile.get('resonance_score', 0)
    
    # 側邊欄
    with st.sidebar:
        st.markdown(f"### ⚡ 共鳴值: {score}")
        st.progress(min(score/50, 1.0))
        st.caption("目標：50 點解鎖核心記憶區")
        
        st.divider()
        st.write(f"👤 {st.session_state.user.user.email}")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    
    # 鎖定邏輯：如果分數 < 10，只能選朋友
    if score < 10:
        st.info(f"📢 目前階段：**惡作劇練習生**。請先完成朋友的訓練並分享，獲得 **10 點共鳴值** 後解鎖家屬角色。")
        target_role = "朋友"
    else:
        st.success("🎉 您已解鎖【摯愛守護者】權限！可以開始錄製給家人的聲音。")
        target_role = st.selectbox("選擇對象", list(config.ROLE_MAPPING.keys()))

    st.divider()

    # 如果選了非朋友角色，但分數不夠 (防呆)
    if target_role != "朋友" and score < 10:
        st.error("🔒 此角色尚未解鎖！請先累積共鳴值。")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(["🧬 聲紋訓練", "📤 分享裂變", "📝 人設補完", "🧠 回憶補完"])

    # --- TAB 1: 聲紋訓練 (惡作劇版/正式版) ---
    with tab1:
        if target_role == "朋友":
            st.subheader("STEP 1: 錄製招牌口頭禪")
            st.caption("這會是朋友打開連結時聽到的第一句話，要夠像！")
            catchphrase = st.text_input("輸入口頭禪", placeholder="例如：搞什麼鬼～、真的假的～")
        else:
            st.subheader("STEP 1: 輕輕喚你的名")
            catchphrase = st.text_input("輸入專屬暱稱", placeholder="例如：老婆～")
            
        rec = st.audio_input("錄音 (建議 2-3 秒)")
        if rec and catchphrase:
            if st.button("💾 上傳並試聽"):
                with st.spinner("處理中..."):
                    audio_bytes = rec.read()
                    audio.upload_nickname_audio(supabase, target_role, audio_bytes)
                    rec.seek(0)
                    audio.train_voice_sample(rec.read())
                    
                    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                    headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
                    # 試聽內容根據角色不同
                    demo_text = "欸借你的錢什麼時候還？" if target_role == "朋友" else "最近好嗎？"
                    data = {"text": demo_text, "model_id": "eleven_multilingual_v2"}
                    r = requests.post(tts_url, json=data, headers=headers)
                    
                    final = audio.merge_audio_clips(audio_bytes, r.content)
                    st.audio(final, format="audio/mp3")
                    st.success("聲紋已建立！")

        # Step 2-4 省略為按鈕示意，請沿用之前的腳本邏輯
        st.markdown("---")
        st.markdown("#### 強化訓練 (建議完成)")
        if st.button("前往情緒腳本訓練 (Step 2-4)"):
            st.info("此功能在共鳴 1 版簡化，請直接點擊上方「分享裂變」邀請朋友測試。")

    # --- TAB 2: 分享裂變 (賺分神器) ---
    with tab2:
        st.subheader("📈 賺取共鳴值")
        st.write("將您的 AI 分享給朋友，請他們評分。每個 5 星好評 +5 點！")
        
        # 顯示目前的評價
        st.markdown("##### 💬 朋友給您的留言")
        feedbacks = database.get_feedbacks(supabase)
        if feedbacks:
            for fb in feedbacks:
                st.info(f"⭐ {fb['score']} 分 | 留言: {fb.get('comment','無')}")
        else:
            st.caption("目前還沒有人評分，趕快分享吧！")

        st.divider()
        if st.button("生成【朋友】專屬邀請碼"):
            token = database.create_share_token(supabase, "朋友")
            st.code(f"https://missyou.streamlit.app\n邀請碼：{token}\n\n欸測一下這是不是我本人？", language="text")

    # --- TAB 3 & 4: 鎖定機制 ---
    with tab3:
        if score < 50:
            st.warning("🔒 需累積 50 點共鳴值解鎖「人設補完」功能。")
        else:
            st.success("👑 已解鎖進階功能")
            # (這裡放原本的 Tab 2 內容)

    with tab4:
        if score < 50:
            st.warning("🔒 需累積 50 點共鳴值解鎖「回憶補完」功能。")
        else:
            st.success("👑 已解鎖進階功能")
            # (這裡放原本的 Tab 3 內容)
