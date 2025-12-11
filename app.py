import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import numpy as np
import os
import json
import io
import random
import string
from pydub import AudioSegment

# ==========================================
# 版本資訊：SaaS Beta 2.1 (優化分享流程版)
# 更新內容：Step 1 試聽修正、新增 Step 5 完結頁、分享文案一鍵複製
# ==========================================

# --- 1. 頁面與 UI 設定 ---
st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="🤍", layout="wide")

custom_css = """
<style>
    .stApp, p, h1, h2, h3, label, div, span, button { color: #333333 !important; }
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #333333 !important; }
    
    /* 步驟導航條 */
    .step-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
        padding: 10px;
        background-color: #F0F2F6;
        border-radius: 10px;
    }
    
    /* 腳本卡片 */
    .script-box {
        background-color: #FFF3E0;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #FFE0B2;
        font-size: 16px;
        line-height: 1.6;
        margin: 15px 0;
        color: #5D4037 !important;
    }

    /* 題目卡片 (Active) */
    .question-card-active {
        background-color: #E3F2FD;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 2px solid #2196F3;
        text-align: center;
    }
    .q-text { font-size: 20px; font-weight: bold; color: #1565C0 !important; margin-bottom: 10px; }

    /* 歷史回憶卡片 */
    .history-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        margin-bottom: 10px;
        font-size: 14px;
    }
    
    .ai-bubble {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #4A90E2;
        margin: 10px 0;
        color: #333333;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 2. 初始化與設定 ---
if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ 請先設定 Secrets")
    st.stop()

openai_key = st.secrets["OPENAI_API_KEY"]
elevenlabs_key = st.secrets["ELEVENLABS_API_KEY"]
voice_id = st.secrets["VOICE_ID"]
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

client = OpenAI(api_key=openai_key)

@st.cache_resource
def init_supabase():
    return create_client(supabase_url, supabase_key)

supabase = init_supabase()

ROLE_MAPPING = {
    "妻子": "wife",
    "丈夫": "husband",
    "兒子": "son",
    "女兒": "daughter",
    "朋友": "friend",
    "孫子": "grandson",
    "其他": "others"
}

# --- 3. 讀取外部題庫 ---
@st.cache_data
def load_questions_from_file():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

question_db = load_questions_from_file()

# --- 4. 核心功能函數 ---

def get_current_user_id():
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.user.id
    if "guest_data" in st.session_state and st.session_state.guest_data:
        return st.session_state.guest_data['owner_id']
    return None

def get_embedding(text):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def upload_nickname_audio(role, audio_bytes):
    user_id = get_current_user_id()
    if not user_id: return False
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/nickname_{safe_role}.mp3"
        supabase.storage.from_("audio_clips").upload(
            file_path, audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        return True
    except Exception as e:
        print(f"Storage Error: {e}")
        return False

def get_nickname_audio_bytes(role):
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/nickname_{safe_role}.mp3"
        response = supabase.storage.from_("audio_clips").download(file_path)
        return response
    except: return None

def train_voice_sample(audio_bytes):
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/edit"
        headers = {"xi-api-key": elevenlabs_key}
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        data = {'name': 'My Digital Clone'} 
        requests.post(url, headers=headers, data=data, files=files)
        return True
    except: return False

def merge_audio_clips(intro_bytes, main_bytes):
    try:
        if not intro_bytes or len(intro_bytes) < 100: return main_bytes
        intro = AudioSegment.from_file(io.BytesIO(intro_bytes))
        main = AudioSegment.from_file(io.BytesIO(main_bytes))
        silence = AudioSegment.silent(duration=200)
        combined = intro + silence + main
        buffer = io.BytesIO()
        combined.export(buffer, format="mp3")
        return buffer.getvalue()
    except Exception as e: 
        print(f"Merge error: {e}")
        return main_bytes

# --- RLS 與資料庫操作 ---
def save_memory_fragment(role, question, answer):
    user_id = get_current_user_id()
    if not user_id: return False
    full_content = f"【關於{question}】：{answer}"
    try:
        res = supabase.table("memories").select("id, content").eq("user_id", user_id).eq("role", role).execute()
        for mem in res.data:
            if mem['content'].startswith(f"【關於{question}】"):
                supabase.table("memories").delete().eq("id", mem['id']).execute()
    except: pass
    
    embedding = get_embedding(full_content)
    data = {"user_id": user_id, "role": role, "content": full_content, "embedding": embedding}
    supabase.table("memories").insert(data).execute()
    return True

def search_relevant_memories(role, query_text):
    try:
        query_vec = get_embedding(query_text)
        response = supabase.rpc(
            "match_memories",
            {"query_embedding": query_vec, "match_threshold": 0.5, "match_count": 3, "search_role": role}
        ).execute()
        return "\n".join([item['content'] for item in response.data])
    except: return ""

def save_persona_summary(role, content):
    user_id = get_current_user_id()
    if not user_id: return
    try:
        res = supabase.table("personas").select("id").eq("user_id", user_id).eq("role", role).execute()
        if res.data:
            supabase.table("personas").update({"content": content}).eq("id", res.data[0]['id']).execute()
        else:
            data = {"user_id": user_id, "role": role, "content": content}
            supabase.table("personas").insert(data).execute()
    except Exception as e: print(e)

def load_persona(role):
    user_id = get_current_user_id()
    try:
        res = supabase.table("personas").select("content").eq("user_id", user_id).eq("role", role).execute()
        return res.data[0]['content'] if res.data else None
    except: return None

def get_memories_by_role(role):
    user_id = get_current_user_id()
    try:
        res = supabase.table("memories").select("*").eq("user_id", user_id).eq("role", role).order('id', desc=True).execute()
        return res.data
    except: return []

# --- 分享功能 ---
def create_share_token(role):
    user_id = get_current_user_id()
    # 檢查是否已存在
    try:
        exist = supabase.table("share_tokens").select("token").eq("user_id", user_id).eq("role", role).execute()
        if exist.data:
            return exist.data[0]['token']
    except: pass

    # 生成新 Token
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    try:
        data = {"user_id": user_id, "role": role, "token": token}
        supabase.table("share_tokens").insert(data).execute()
        return token
    except Exception as e:
        return None

def validate_token(token):
    try:
        res = supabase.table("share_tokens").select("*").eq("token", token).execute()
        if res.data:
            return res.data[0]
        return None
    except: return None

# --- 5. 狀態管理 ---
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1

# --- 6. 主程式路由 ---

# 情境 A: 訪客模式 (親友已輸入 Token)
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    
    st.markdown(f"<h2 style='text-align:center;'>📞 與 [{role_name}] 通話中...</h2>", unsafe_allow_html=True)
    
    persona_summary = load_persona(role_name)
    if not persona_summary:
        st.warning("對方尚未設定此角色的靈魂資料。")
    else:
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1:
            st.image("https://cdn-icons-png.flaticon.com/512/607/607414.png", width=150)
        with col_c2:
            st.info(f"這是 {role_name} 留給您的聲音。")

        if "chat_history" not in st.session_state: st.session_state.chat_history = []

        audio_val = st.audio_input("請按此說話...", key="guest_rec")
        
        if audio_val:
            try:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_val)
                user_text = transcript.text
                if len(user_text.strip()) > 1:
                    with st.spinner("..."):
                        mem = search_relevant_memories(role_name, user_text)
                        
                        has_nick = get_nickname_audio_bytes(role_name) is not None
                        nick_instr = "【指令】回應開頭不要包含暱稱。" if has_nick else "請在開頭呼喚暱稱。"
                        
                        prompt = f"{persona_summary}\n【回憶】{mem}\n{nick_instr}\n語氣自然。"
                        msgs = [{"role": "system", "content": prompt}] + st.session_state.chat_history[-4:]
                        msgs.append({"role": "user", "content": user_text})
                        
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                        ai_text = res.choices[0].message.content
                        
                        st.session_state.chat_history.append({"role": "user", "content": user_text})
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                        
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                        headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                        data = {"text": ai_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}}
                        tts_res = requests.post(tts_url, json=data, headers=headers)
                        
                        final_audio = tts_res.content
                        if has_nick:
                            nick_bytes = get_nickname_audio_bytes(role_name)
                            if nick_bytes: final_audio = merge_audio_clips(nick_bytes, final_audio)
                        
                        st.audio(final_audio, format="audio/mp3", autoplay=True)
                        st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
            except Exception as e: st.error("連線不穩，請重試")

    st.divider()
    if st.button("離開通話"):
        st.session_state.guest_data = None
        st.rerun()
        
    st.markdown("""
    <div style='background-color:#F5F5F5; padding:20px; border-radius:10px; text-align:center; margin-top:30px;'>
        <p>您也想為家人留下這樣的聲音嗎？</p>
        <a href='#' target='_self'><button style='background-color:#4CAF50; color:white; padding:10px 20px; border:none; border-radius:5px;'>免費建立您的數位分身</button></a>
    </div>
    """, unsafe_allow_html=True)


# 情境 B: 未登入 (首頁)
elif not st.session_state.user:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("## 👋 我是親友")
        st.caption("輸入家人給您的通行碼")
        token_input = st.text_input("通行碼 (Token)", placeholder="例如：A8K29", label_visibility="collapsed")
        if st.button("開始對話", type="primary", use_container_width=True):
            data = validate_token(token_input.strip())
            if data:
                st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                st.success("驗證成功！")
                st.rerun()
            else:
                st.error("無效的通行碼")

    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        with tab_l:
            email = st.text_input("Email", key="l_e")
            pwd = st.text_input("密碼", type="password", key="l_p")
            if st.button("登入", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                    if res.user: 
                        st.session_state.user = res
                        st.rerun()
                except: st.error("帳號密碼錯誤")
        with tab_s:
            s_email = st.text_input("Email", key="s_e")
            s_pwd = st.text_input("設定密碼", type="password", key="s_p")
            if st.button("註冊", use_container_width=True):
                try:
                    res = supabase.auth.sign_up({"email": s_email, "password": s_pwd})
                    if res.user:
                        st.success("註冊成功！")
                        st.session_state.user = res
                        st.rerun()
                except: st.error("註冊失敗")

# 情境 C: 會員後台
else:
    with st.sidebar:
        st.write(f"👤 {st.session_state.user.user.email}")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    
    # 頂部選單：選擇角色
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1:
        target_role = st.selectbox("您想要將你的聲音留給誰?", list(ROLE_MAPPING.keys()))
    
    # 分頁
    tab1, tab2, tab3 = st.tabs(["🧬 複製聲紋 (步驟引導)", "📝 人設補完 (LINE紀錄)", "🧠 回憶補完 (題庫)"])

    # --- TAB 1: 複製聲紋 (Wizard) ---
    with tab1:
        # 進度指示器
        cols = st.columns(5)
        steps = ["❶ 喚名", "❷ 安慰", "❸ 鼓勵", "❹ 詼諧", "❺ 完成"]
        for i, s in enumerate(steps):
            if i + 1 == st.session_state.step:
                cols[i].markdown(f"**<span style='color:#1565C0'>{s}</span>**", unsafe_allow_html=True)
            else:
                cols[i].markdown(f"<span style='color:#ccc'>{s}</span>", unsafe_allow_html=True)
        st.markdown("---")

        # STEP 1: 喚名
        if st.session_state.step == 1:
            st.subheader("STEP 1: 輕輕喚你的名")
            st.info("請錄下您平常呼喚對方暱稱的聲音，這將成為每次對話的開頭。")
            
            nickname_text = st.text_input("請輸入暱稱文字", placeholder="例如：老婆～")
            rec = st.audio_input("錄音 (建議 2-3 秒)")
            
            if rec and nickname_text:
                if st.button("💾 上傳並試聽"):
                    with st.spinner("處理中..."):
                        audio_bytes = rec.read()
                        # 1. 存入 Storage
                        upload_nickname_audio(target_role, audio_bytes)
                        # 2. 訓練 AI
                        rec.seek(0)
                        train_voice_sample(rec.read())
                        
                        # 3. 試聽拼接 (修正：AI 生成內容不包含暱稱，避免重複)
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                        headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                        # 修改點：這裡只讓 AI 講 "最近好嗎？"
                        data = {"text": "最近好嗎？", "model_id": "eleven_multilingual_v2"}
                        r = requests.post(tts_url, json=data, headers=headers)
                        
                        final = merge_audio_clips(audio_bytes, r.content)
                        st.audio(final, format="audio/mp3")
                        st.success("聲紋已建立！")

            if st.button("下一步 →"):
                st.session_state.step = 2
                st.rerun()

        # STEP 2-4: 腳本朗讀
        elif st.session_state.step in [2, 3, 4]:
            scripts = {
                2: ("刻錄「安慰語氣」", "欸，我知道你現在心裡一定超悶的啦，感覺是不是付出的心血都白費了？吼，沒關係啦，真的沒關係，讓我抱一下。你看你齁，把自己逼得那麼緊，早就累壞了。我們又不是機器人，偶爾搞砸一下是很正常的，誰沒有低潮的時候？失敗就失敗啊，它只是在提醒你：你該休息了。我們現在什麼都不要想，先找個地方坐下來。我會在這裡陪著你，等你準備好了，我們再一起慢慢來，好不好？你已經做得很好了。"),
                3: ("刻錄「鼓勵語氣」", "哇塞！你真的決定要開始學那個東西了喔？超酷的啦！我知道一開始會很難、很煩，那介面看起來像外星文，沒錯啦！但你想想看，等你真的學會了，那個成就感會有多爆炸？不要去想還有多少東西沒學，就先專心搞定眼前這個小任務就好。每天進步一點點，慢慢累積起來就會是超巨大的力量！相信我，你的腦袋比你想像中靈光多了！衝啊！我等你做出第一個成品，我請客，隨便你點！"),
                4: ("刻錄「輕鬆詼諧語氣」", "我跟你說，我昨天去圖書館 K 書，真的糗死了啦！我把水壺放在桌上，想說要裝一下文青對不對？結果我一個不小心，那個金屬水壺直接滾到地上，發出那種「匡啷匡啷匡啷」超大聲的聲音！整個圖書館的人，你知道嗎？全部都抬頭看著我！我當時真的超想假裝是睡著了，然後從地上爬起來！那個聲音迴盪了五秒鐘欸！搞得我後來待不下去，我就直接收東西逃走了！")
            }
            
            title, script_content = scripts[st.session_state.step]
            st.subheader(f"STEP {st.session_state.step}: {title}")
            st.markdown(f'<div class="script-box">{script_content}</div>', unsafe_allow_html=True)
            
            rec = st.audio_input("請朗讀上方文字")
            if rec:
                if st.button("💾 上傳訓練"):
                    with st.spinner("訓練 Voice ID 中..."):
                        train_voice_sample(rec.read())
                        st.success("訓練成功！AI 語氣已更新。")
                        
                        # 試聽邏輯 (修正：不重複暱稱)
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                        headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                        data = {"text": "最近好嗎？", "model_id": "eleven_multilingual_v2"}
                        r = requests.post(tts_url, json=data, headers=headers)
                        
                        nick_bytes = get_nickname_audio_bytes(target_role)
                        final = merge_audio_clips(nick_bytes, r.content) if nick_bytes else r.content
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
                    # Step 4 的下一步 -> 跳轉 Step 5
                    if st.button("完成訓練 →"):
                        st.session_state.step = 5
                        st.rerun()

        # STEP 5: 完結與分享 (新增)
        elif st.session_state.step == 5:
            st.balloons()
            st.markdown(f"""
            <div style='text-align:center; padding:30px;'>
                <h2 style='color:#2E7D32;'>🎉 恭喜！您的初級語氣刻錄模型已完成。</h2>
                <p>您現在可以分享這個連接給您的【{target_role}】</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 生成 Token (確保不會一直重複生成，這裡簡化為每次顯示時檢查)
            if "share_token" not in st.session_state:
                st.session_state.share_token = create_share_token(target_role)
            
            # 準備分享文案
            token = st.session_state.share_token
            # 請將下方的網址替換為您的真實 APP 網址
            share_text = f"""現在AI太厲害了
我的聲音語氣模型已經刻錄在這裡
https://missyou.streamlit.app/

你的邀請碼
{token}

一定要來幫我打個分數喔~
看看跟我的聲音有幾成像?"""

            st.info("👇 點擊下方區塊右上角的按鈕即可複製文案")
            st.code(share_text, language="text")
            
            if st.button("← 返回 Step 1 重新錄製"):
                st.session_state.step = 1
                st.rerun()

    # --- TAB 2: 人設補完 (簡化版) ---
    with tab2:
        st.info("上傳 LINE 對話紀錄，讓 AI 學習您的口頭禪。")
        member_name = st.text_input("您的名字 (LINE顯示名稱)", value="爸爸")
        nickname = st.text_input("專屬暱稱 (AI將用此稱呼對方)", placeholder="例如：寶貝")
        up_file = st.file_uploader("上傳 .txt 紀錄檔", type="txt")
        if st.button("✨ 分析並更新人設"):
            if up_file and member_name:
                with st.spinner("分析中..."):
                    raw = up_file.read().decode("utf-8")
                    prompt = f"分析主角(我):{member_name}對{target_role}的說話風格。生成System Prompt，重點：模仿主角語氣，並使用暱稱{nickname}稱呼對方。資料：{raw[-20000:]}"
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    save_persona_summary(target_role, res.choices[0].message.content)
                    st.success("人設已更新")

    # --- TAB 3: 回憶補完 (雙欄) ---
    with tab3:
        q_list = question_db.get(target_role, [])
        memories = get_memories_by_role(target_role)
        answered_qs = set()
        for m in memories:
            if "【關於" in m['content'] and "】：" in m['content']:
                answered_qs.add(m['content'].split("【關於")[1].split("】：")[0])

        if "edit_target" not in st.session_state: st.session_state.edit_target = None
        
        current_q = st.session_state.edit_target
        if not current_q:
            for q in q_list:
                if q not in answered_qs:
                    current_q = q
                    break
        
        col_l, col_r = st.columns([1.5, 1], gap="medium")
        
        with col_l:
            st.markdown("### 🎙️ 進行中任務")
            if current_q:
                st.markdown(f'<div class="question-card-active"><div class="q-text">{current_q}</div></div>', unsafe_allow_html=True)
                audio_ans = st.audio_input("錄音回答", key=f"q_{current_q}")
                
                if "trans_text" not in st.session_state: st.session_state.trans_text = ""
                
                if audio_ans:
                    trans = client.audio.transcriptions.create(model="whisper-1", file=audio_ans)
                    st.session_state.trans_text = trans.text
                    
                    st.text_area("文字確認", value=st.session_state.trans_text)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("🔊 試聽"):
                            tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                            headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                            data = {"text": st.session_state.trans_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}}
                            r = requests.post(tts_url, json=data, headers=headers)
                            st.audio(r.content, format="audio/mp3")
                    with c2:
                        if st.button("💾 存入並訓練", type="primary"):
                            save_memory_fragment(target_role, current_q, st.session_state.trans_text)
                            audio_ans.seek(0)
                            train_voice_sample(audio_ans.read())
                            st.success("已儲存")
                            st.session_state.edit_target = None
                            st.session_state.trans_text = ""
                            st.rerun()
                
                if st.button("⏭️ 跳過"):
                    save_memory_fragment(target_role, current_q, "(已略過)")
                    st.rerun()
            else:
                st.success("題庫已完成")

        with col_r:
            st.markdown("### 📜 已完成")
            with st.container(height=500):
                for mem in memories:
                    if "【關於" in mem['content']:
                        q = mem['content'].split("【關於")[1].split("】：")[0]
                        if st.button(f"🔄 {q}", key=f"h_{mem['id']}"):
                            st.session_state.edit_target = q
                            st.rerun()