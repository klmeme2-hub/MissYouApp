import streamlit as st
import json
import requests
from openai import OpenAI

# 引入模組
from modules import ui, auth, database, audio, config

# ==========================================
# 主程式：想念 (SaaS Modular Version)
# ==========================================

# 1. 載入 UI 設定 (CSS 與頁面配置)
st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="🤍", layout="wide")
ui.load_css()

# 2. 初始化系統檢查
if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ 請先在 Streamlit Secrets 設定 SUPABASE_URL 與 API Keys")
    st.stop()

# 3. 初始化客戶端
# Supabase 用於資料庫與認證，OpenAI 用於語音轉字與生成
supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 4. 讀取外部題庫 (questions.json)
@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

question_db = load_questions()

# 5. 全域狀態管理 (Session State)
if "user" not in st.session_state:
    st.session_state.user = None
if "guest_data" not in st.session_state:
    st.session_state.guest_data = None
if "step" not in st.session_state:
    st.session_state.step = 1  # 用於靈魂刻錄室的步驟控制

# ==========================================
# 邏輯路由 (Router)
# ==========================================

# ------------------------------------------
# 情境 A: 訪客模式 (親友已輸入 Token 進入)
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id'] # 這裡雖然抓到了 owner_id，但目前的 database 模組函式通常會去抓當前登入者
    # 注意：在訪客模式下，database 層的 get_current_user_id 會抓到 guest_data 裡的 owner_id (請確保 modules/auth.py 有寫這段邏輯)
    
    st.markdown(f"<h2 style='text-align:center;'>📞 與 [{role_name}] 通話中...</h2>", unsafe_allow_html=True)
    
    # 讀取該角色的人設
    persona_summary = database.load_persona(supabase, role_name)
    
    if not persona_summary:
        st.warning("對方尚未設定此角色的靈魂資料，無法進行對話。")
    else:
        # 顯示頭像與提示
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1:
            st.image("https://cdn-icons-png.flaticon.com/512/607/607414.png", width=150)
        with col_c2:
            st.info(f"這是 {role_name} 留給您的聲音。\n請按下錄音，開始跨時空的對話。")

        # 初始化對話紀錄
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # 錄音輸入
        audio_val = st.audio_input("請按此說話...", key="guest_rec")
        
        if audio_val:
            try:
                # 1. 語音轉文字 (Whisper)
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_val)
                user_text = transcript.text
                
                if len(user_text.strip()) > 1:
                    with st.spinner("正在思考與回憶..."):
                        # 2. RAG 深層記憶檢索
                        mem = database.search_relevant_memories(supabase, role_name, user_text)
                        
                        # 3. 檢查是否有真實暱稱錄音
                        has_nick = audio.get_nickname_audio_bytes(supabase, role_name) is not None
                        
                        # 4. 設定指令 (若有真實錄音，AI 開頭就不說暱稱)
                        nick_instr = "【指令】回應開頭不要包含暱稱或問候語，直接講內容。" if has_nick else "請在開頭自然呼喚對方的暱稱。"
                        
                        # 5. 組合 Prompt
                        prompt = f"{persona_summary}\n【相關回憶】{mem}\n{nick_instr}\n語氣要自然，包含呼吸感。"
                        
                        msgs = [{"role": "system", "content": prompt}] + st.session_state.chat_history[-4:]
                        msgs.append({"role": "user", "content": user_text})
                        
                        # 6. GPT 生成文字
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                        ai_text = res.choices[0].message.content
                        
                        # 儲存對話
                        st.session_state.chat_history.append({"role": "user", "content": user_text})
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                        
                        # 7. 聲音合成 (ElevenLabs)
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
                        data = {
                            "text": ai_text, 
                            "model_id": "eleven_multilingual_v2", 
                            "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}
                        }
                        tts_res = requests.post(tts_url, json=data, headers=headers)
                        
                        # 8. 音訊拼接 (真實暱稱 + AI 語音)
                        final_audio = tts_res.content
                        if has_nick:
                            nick_bytes = audio.get_nickname_audio_bytes(supabase, role_name)
                            if nick_bytes:
                                final_audio = audio.merge_audio_clips(nick_bytes, final_audio)
                        
                        # 9. 播放與顯示
                        st.audio(final_audio, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"連線發生錯誤: {e}")

    st.divider()
    if st.button("🚪 離開通話"):
        st.session_state.guest_data = None
        st.rerun()
    
    # 裂變廣告區 (Growth Loop)
    st.markdown("""
    <div style='background-color:#F5F5F5; padding:20px; border-radius:10px; text-align:center; margin-top:30px;'>
        <p>您也想為家人留下這樣的聲音嗎？</p>
        <p style='font-size:12px; color:#666;'>現在註冊，免費建立您的數位分身</p>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------
# 情境 B: 未登入狀態 (首頁：訪客驗證 OR 會員登入)
# ------------------------------------------
elif not st.session_state.user:
    
    # 左右分流佈局
    col1, col2 = st.columns([1, 1], gap="large")
    
    # 左側：親友入口
    with col1:
        st.markdown("## 👋 我是親友")
        st.caption("請輸入家人分享給您的 6 位數通行碼")
        
        token_input = st.text_input("通行碼 (Token)", placeholder="例如：A8K29", label_visibility="collapsed")
        
        if st.button("🚀 開始對話", type="primary", use_container_width=True):
            with st.spinner("驗證中..."):
                data = database.validate_token(supabase, token_input.strip())
                if data:
                    # 驗證成功，將資訊寫入 Session
                    st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                    st.success("驗證成功！正在連線...")
                    st.rerun()
                else:
                    st.error("無效的通行碼，請確認大小寫。")

    # 右側：會員入口
    with col2:
        st.markdown("## 👤 我是會員")
        tab_login, tab_signup = st.tabs(["登入", "註冊新帳號"])
        
        with tab_login:
            l_email = st.text_input("Email", key="login_email")
            l_pwd = st.text_input("密碼", type="password", key="login_pwd")
            if st.button("登入", use_container_width=True):
                with st.spinner("登入中..."):
                    res = auth.login_user(supabase, l_email, l_pwd)
                    if res and res.user: 
                        st.session_state.user = res
                        st.success("登入成功")
                        st.rerun()
                    else:
                        st.error("登入失敗，請檢查帳號密碼。")
                        
        with tab_signup:
            s_email = st.text_input("Email", key="signup_email")
            s_pwd = st.text_input("設定密碼", type="password", key="signup_pwd")
            if st.button("註冊", use_container_width=True):
                with st.spinner("建立帳戶中..."):
                    res = auth.signup_user(supabase, s_email, s_pwd)
                    if res and res.user:
                        st.success("註冊成功！系統已自動登入。")
                        st.session_state.user = res
                        st.rerun()
                    else:
                        st.error("註冊失敗，請稍後再試。")

# ------------------------------------------
# 情境 C: 會員後台 (Member Dashboard)
# ------------------------------------------
else:
    # 側邊欄資訊
    with st.sidebar:
        st.write(f"👤 {st.session_state.user.user.email}")
        st.caption("會員等級：初級 (免費版)")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    
    # 頂部儀表板：顯示餘額 (SaaS 提供算力)
    with st.expander("📊 系統資源狀態 (由平台提供算力)", expanded=False):
        c_sys1, c_sys2 = st.columns(2)
        with c_sys1:
            ui.render_dashboard_card("ElevenLabs 聲音合成額度", "載入中...") 
            # 這裡簡單處理，實際可呼叫 audio.get_elevenlabs_usage()
            used, limit = audio.get_elevenlabs_usage()
            if limit > 0:
                st.progress(used / limit)
                st.caption(f"已用 {used:,} / {limit:,} 字元")
        with c_sys2:
            ui.render_dashboard_card("OpenAI 大腦狀態", "運作中 🟢")
            st.caption("智慧模型：GPT-4o-mini")

    # 角色選擇 (全域影響)
    st.markdown("### 第一步：您想要將你的聲音留給誰?")
    target_role = st.selectbox("選擇對象", list(config.ROLE_MAPPING.keys()), label_visibility="collapsed")
    
    st.divider()

    # 主要功能分頁
    tab1, tab2, tab3 = st.tabs(["🧬 複製聲紋 (步驟引導)", "📝 人設補完 (LINE紀錄)", "🧠 回憶補完 (題庫)"])

    # ==========================================
    # TAB 1: 複製聲紋 (闖關模式)
    # ==========================================
    with tab1:
        # 進度指示器
        cols = st.columns(5)
        steps = ["❶ 喚名", "❷ 安慰", "❸ 鼓勵", "❹ 詼諧", "❺ 完成"]
        for i, s in enumerate(steps):
            if i + 1 == st.session_state.step:
                cols[i].markdown(f"**<span style='color:#1565C0; font-size:18px;'>{s}</span>**", unsafe_allow_html=True)
            else:
                cols[i].markdown(f"<span style='color:#ccc'>{s}</span>", unsafe_allow_html=True)
        st.markdown("---")

        # STEP 1: 輕輕喚你的名
        if st.session_state.step == 1:
            st.subheader("STEP 1: 輕輕喚你的名")
            st.info("請錄下您平常呼喚對方暱稱的聲音，這將成為每次對話的開頭。")
            
            nickname_text = st.text_input("請輸入暱稱文字 (例如：老婆～)", key="s1_nick")
            rec = st.audio_input("錄音 (建議 2-3 秒)", key="s1_rec")
            
            if rec and nickname_text:
                if st.button("💾 上傳並試聽"):
                    with st.spinner("處理中..."):
                        audio_bytes = rec.read()
                        # 1. 存入 Storage (作為真實拼接素材)
                        audio.upload_nickname_audio(supabase, target_role, audio_bytes)
                        # 2. 訓練 AI Voice ID
                        rec.seek(0)
                        audio.train_voice_sample(rec.read())
                        
                        # 3. 試聽拼接 (修正：AI 不說暱稱)
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
                        # 這裡只讓 AI 講 "最近好嗎？"
                        data = {"text": "最近好嗎？", "model_id": "eleven_multilingual_v2"}
                        r = requests.post(tts_url, json=data, headers=headers)
                        
                        # 合併：真人暱稱 + AI問候
                        final = audio.merge_audio_clips(audio_bytes, r.content)
                        st.audio(final, format="audio/mp3")
                        st.success("聲紋已建立！請點擊下一步。")

            if st.button("下一步 →"):
                st.session_state.step = 2
                st.rerun()

        # STEP 2-4: 情緒腳本朗讀
        elif st.session_state.step in [2, 3, 4]:
            scripts = {
                2: ("刻錄「安慰語氣」", "欸，我知道你現在心裡一定超悶的啦，感覺是不是付出的心血都白費了？吼，沒關係啦，真的沒關係，讓我抱一下。你看你齁，把自己逼得那麼緊，早就累壞了。我們又不是機器人，偶爾搞砸一下是很正常的，誰沒有低潮的時候？失敗就失敗啊，它只是在提醒你：你該休息了。我們現在什麼都不要想，先找個地方坐下來。我會在這裡陪著你，等你準備好了，我們再一起慢慢來，好不好？你已經做得很好了。"),
                3: ("刻錄「鼓勵語氣」", "哇塞！你真的決定要開始學那個東西了喔？超酷的啦！我知道一開始會很難、很煩，那介面看起來像外星文，沒錯啦！但你想想看，等你真的學會了，那個成就感會有多爆炸？不要去想還有多少東西沒學，就先專心搞定眼前這個小任務就好。每天進步一點點，慢慢累積起來就會是超巨大的力量！相信我，你的腦袋比你想像中靈光多了！衝啊！我等你做出第一個成品，我請客，隨便你點！"),
                4: ("刻錄「輕鬆詼諧語氣」", "我跟你說，我昨天去圖書館 K 書，真的糗死了啦！我把水壺放在桌上，想說要裝一下文青對不對？結果我一個不小心，那個金屬水壺直接滾到地上，發出那種「匡啷匡啷匡啷」超大聲的聲音！整個圖書館的人，你知道嗎？全部都抬頭看著我！我當時真的超想假裝是睡著了，然後從地上爬起來！那個聲音迴盪了五秒鐘欸！搞得我後來待不下去，我就直接收東西逃走了！")
            }
            
            title, script_content = scripts[st.session_state.step]
            st.subheader(f"STEP {st.session_state.step}: {title}")
            st.markdown(f'<div class="script-box">{script_content}</div>', unsafe_allow_html=True)
            
            rec = st.audio_input("請朗讀上方文字", key=f"s{st.session_state.step}_rec")
            if rec:
                if st.button("💾 上傳訓練"):
                    with st.spinner("訓練 Voice ID 中..."):
                        audio.train_voice_sample(rec.read())
                        st.success("訓練成功！AI 語氣已更新。")
                        
                        # 簡單試聽
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
                        data = {"text": "最近好嗎？", "model_id": "eleven_multilingual_v2"}
                        r = requests.post(tts_url, json=data, headers=headers)
                        
                        # 嘗試拼接真實暱稱 (如果有錄的話)
                        nick_bytes = audio.get_nickname_audio_bytes(supabase, target_role)
                        final = audio.merge_audio_clips(nick_bytes, r.content) if nick_bytes else r.content
                        st.audio(final, format="audio/mp3")
            
            # 導航按鈕
            c_prev, c_next = st.columns(2)
            with c_prev:
                if st.button("← 上一步"):
                    st.session_state.step -= 1
                    st.rerun()
            with c_next:
                if st.session_state.step < 4:
                    if st.button("下一步 →"):
                        st.session_state.step += 1
                        st.rerun()
                else:
                    # Step 4 的下一步 -> 跳轉 Step 5 完結頁
                    if st.button("完成訓練，前往分享頁 →"):
                        st.session_state.step = 5
                        st.rerun()

        # STEP 5: 完結與分享 (裂變機制)
        elif st.session_state.step == 5:
            st.balloons()
            st.markdown(f"""
            <div style='text-align:center; padding:30px; background-color:#F1F8E9; border-radius:15px;'>
                <h2 style='color:#2E7D32;'>🎉 恭喜！您的初級語氣刻錄模型已完成。</h2>
                <p>您現在可以將這個聲音分享給您的【{target_role}】。</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # 生成 Token
            # 使用 session_state 防止重新整理時 token 消失或改變
            if "share_token" not in st.session_state or st.session_state.get("share_role") != target_role:
                st.session_state.share_token = database.create_share_token(supabase, target_role)
                st.session_state.share_role = target_role
            
            token = st.session_state.share_token
            app_url = "https://missyou.streamlit.app" # 請替換成真實網址
            
            # 分享文案
            share_text = f"""現在AI太厲害了
我的聲音語氣模型已經刻錄在這裡
{app_url}

你的邀請碼
{token}

一定要來幫我打個分數喔~
看看跟我的聲音有幾成像?"""

            st.subheader("📤 您的數位邀請卡")
            st.code(share_text, language="text")
            st.caption("👆 點擊右上角的複製按鈕，直接傳送給親友。")
            
            st.divider()
            if st.button("← 返回 Step 1 重新錄製"):
                st.session_state.step = 1
                st.rerun()

    # ==========================================
    # TAB 2: 人設補完 (LINE紀錄)
    # ==========================================
    with tab2:
        st.info("上傳 LINE 對話紀錄 (.txt)，讓 AI 學習您的口頭禪與用詞習慣。")
        
        c1, c2 = st.columns(2)
        with c1:
            member_name = st.text_input("您的名字 (在LINE對話中的顯示名稱)", value="爸爸")
        with c2:
            nickname = st.text_input("專屬暱稱 (請輸入您呼喚對方的發音，如：寶貝、豬頭)", placeholder="例如：寶貝")
            
        up_file = st.file_uploader("上傳紀錄檔", type="txt")
        
        if st.button("✨ 分析並更新人設"):
            if up_file and member_name:
                with st.spinner("AI 正在閱讀並分析語氣特徵..."):
                    raw = up_file.read().decode("utf-8")
                    prompt = f"""
                    分析對話紀錄。
                    主角(我)：{member_name}
                    對象：{target_role}
                    專屬暱稱：{nickname}
                    
                    任務：
                    1. 分析【主角】的說話風格（口頭禪、語氣助詞、長短句習慣）。
                    2. 生成 System Prompt 指令。
                    3. 強制要求：對象是{target_role}時，必須使用暱稱「{nickname}」稱呼對方。
                    
                    資料片段：{raw[-20000:]}
                    """
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    
                    # 存入資料庫
                    database.save_persona_summary(supabase, target_role, res.choices[0].message.content)
                    st.success(f"成功！已建立對【{target_role}】的專屬人設。")
            else:
                st.warning("請填寫完整資訊並上傳檔案")

    # ==========================================
    # TAB 3: 回憶補完 (雙欄 + 試聽 + 語音訓練)
    # ==========================================
    with tab3:
        st.caption("透過回答問題，補充生活細節，同時訓練 AI 的聲音。")
        
        # 1. 準備資料
        q_role = st.selectbox("補充對象回憶", list(question_db.keys()), key="q_role")
        q_list = question_db.get(q_role, [])
        
        # 取得已回答的歷史
        memories = database.get_memories_by_role(supabase, q_role)
        answered_qs = set()
        for m in memories:
            # 解析題目：【關於xxx】：ooo
            if "【關於" in m['content'] and "】：" in m['content']:
                q_part = m['content'].split("【關於")[1].split("】：")[0]
                answered_qs.add(q_part)

        # 狀態管理：是否在編輯模式
        if "edit_target" not in st.session_state: st.session_state.edit_target = None

        # 決定當前題目
        current_q = None
        if st.session_state.edit_target:
            current_q = st.session_state.edit_target
            st.info(f"✏️ 正在重新錄製：{current_q}")
        else:
            # 找第一個沒回答的
            for q in q_list:
                if q not in answered_qs:
                    current_q = q
                    break
        
        # 進度條
        if len(q_list) > 0:
            progress = len(answered_qs) / len(q_list)
            st.progress(progress, text=f"回憶補完進度：{len(answered_qs)} / {len(q_list)}")

        # 介面分欄
        col_left, col_right = st.columns([1.5, 1], gap="medium")
        
        # --- 左欄：操作區 ---
        with col_left:
            st.markdown("### 🎙️ 進行中任務")
            if current_q:
                # 題目卡片
                ui.render_question_card(current_q)
                
                # 錄音
                audio_ans = st.audio_input("錄音回答", key=f"ans_{current_q}")
                
                # 識別結果緩存
                if "transcribed_text" not in st.session_state: st.session_state.transcribed_text = ""
                
                if audio_ans:
                    # 轉文字
                    trans = client.audio.transcriptions.create(model="whisper-1", file=audio_ans)
                    st.session_state.transcribed_text = trans.text
                    
                    st.text_area("📝 識別文字 (可手動修改)", value=st.session_state.transcribed_text, key="edit_text_area")
                    
                    c_act1, c_act2 = st.columns(2)
                    with c_act1:
                        # 試聽功能
                        if st.button("🔊 試聽 AI 唸一遍", use_container_width=True):
                            if st.session_state.transcribed_text:
                                with st.spinner("生成試聽中..."):
                                    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                                    headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
                                    data = {"text": st.session_state.transcribed_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}}
                                    r = requests.post(tts_url, json=data, headers=headers)
                                    if r.status_code == 200:
                                        st.audio(r.content, format="audio/mp3", autoplay=True)
                    
                    with c_act2:
                        # 提交功能
                        if st.button("💾 確認無誤，存入並訓練", type="primary", use_container_width=True):
                            final_text = st.session_state.edit_text_area
                            with st.spinner("存入記憶並訓練 Voice ID..."):
                                # 存入資料庫
                                database.save_memory_fragment(supabase, q_role, current_q, final_text)
                                # 訓練聲音
                                audio_ans.seek(0)
                                audio.train_voice_sample(audio_ans.read())
                                
                                st.success("已儲存！")
                                # 重置狀態
                                st.session_state.edit_target = None
                                st.session_state.transcribed_text = ""
                                st.rerun()

                # 跳過按鈕
                if st.button("⏭️ 跳過此題"):
                    database.save_memory_fragment(supabase, q_role, current_q, "(已略過)")
                    st.rerun()
            else:
                st.success("🎉 太棒了！此角色的題庫已全部完成。")

        # --- 右欄：歷史紀錄 ---
        with col_right:
            st.markdown("### 📜 回憶存摺")
            st.caption("已完成 (點擊可重錄)")
            
            with st.container(height=500):
                for mem in memories:
                    if "【關於" in mem['content']:
                        try:
                            q_part = mem['content'].split("【關於")[1].split("】：")[0]
                            a_part = mem['content'].split("】：")[1]
                            
                            ui.render_history_card(q_part, a_part)
                            
                            if st.button("🔄 重錄", key=f"re_{mem['id']}"):
                                st.session_state.edit_target = q_part
                                st.rerun()
                        except: pass
