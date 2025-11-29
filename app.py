import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import numpy as np
import os
import json
import io
from pydub import AudioSegment
import time

# ==========================================
# 版本資訊：SaaS Beta 1.0 (多人連線版)
# 更新內容：Supabase Auth 登入、資料隔離(RLS)、檔案路徑分流
# ==========================================

# --- 1. 頁面與 UI 設定 ---
st.set_page_config(page_title="想念 - 數位分身平台", page_icon="🤍", layout="wide")

custom_css = """
<style>
    .stApp, p, h1, h2, h3, label, div, span, button { color: #333333 !important; }
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li:hover { background-color: #E3F2FD !important; }
    
    /* 登入區塊美化 */
    .login-box {
        background-color: #FFFFFF;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        text-align: center;
        max-width: 400px;
        margin: 0 auto;
    }

    /* 對話氣泡 */
    .ai-bubble {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #4A90E2;
        margin: 10px 0;
        color: #333333;
    }
    
    /* 題目卡片 */
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
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 2. 初始化與設定 ---
if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ 請先設定 Secrets")
    st.stop()

# 平台提供的 API Key (SaaS 模式 - 方案 B)
openai_key = st.secrets["OPENAI_API_KEY"]
elevenlabs_key = st.secrets["ELEVENLABS_API_KEY"]
voice_id = st.secrets["VOICE_ID"]
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

client = OpenAI(api_key=openai_key)

# 初始化 Supabase (注意：這只是初始化，尚未登入)
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
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

question_db = load_questions_from_file()

# --- 4. Authentication (登入/註冊邏輯) ---

def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        return None

def signup_user(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response
    except Exception as e:
        return None

# --- 5. 核心功能函數 (已加入 user_id 處理) ---

def get_current_user_id():
    """取得目前登入者的 UUID"""
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user.user.id
    return None

def get_embedding(text):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def get_memories_by_role(role):
    """取得該角色所有的回憶 (RLS 會自動過濾，但我們這邊直接調用)"""
    try:
        # RLS 開啟後，必須帶有 session 資訊，這裡我們依靠 supabase client 的狀態
        response = supabase.table("memories").select("*").eq("role", role).order('id', desc=True).execute()
        return response.data
    except Exception as e:
        return []

def save_memory_fragment(role, question, answer):
    user_id = get_current_user_id()
    if not user_id: return False
    
    full_content = f"【關於{question}】：{answer}"
    
    # 1. 刪除舊的 (邏輯層刪除，確保不重複)
    try:
        existing = get_memories_by_role(role)
        for mem in existing:
            if mem['content'].startswith(f"【關於{question}】"):
                supabase.table("memories").delete().eq("id", mem['id']).execute()
    except: pass
    
    # 2. 插入新的 (必須包含 user_id)
    embedding = get_embedding(full_content)
    data = {
        "user_id": user_id,
        "role": role, 
        "content": full_content, 
        "embedding": embedding
    }
    supabase.table("memories").insert(data).execute()
    return True

def search_relevant_memories(role, query_text):
    # 注意：Supabase 的 match_memories 函數我們之前寫的時候沒有加 user_id 過濾
    # 但因為開啟了 RLS，所以資料庫層面只會搜尋到自己的資料，這是安全的。
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
    
    # 注意：Upsert 需要確保 user_id + role 是唯一的
    # 我們之前建立表時可能沒設複合主鍵，這裡用簡單的先刪後增，或者依賴 RLS
    try:
        # 先檢查是否存在
        res = supabase.table("personas").select("id").eq("role", role).execute()
        if res.data:
            # Update
            supabase.table("personas").update({"content": content}).eq("id", res.data[0]['id']).execute()
        else:
            # Insert
            data = {"user_id": user_id, "role": role, "content": content}
            supabase.table("personas").insert(data).execute()
    except Exception as e:
        print(f"Persona Save Error: {e}")

def load_all_roles():
    try:
        res = supabase.table("personas").select("role").execute()
        return [i['role'] for i in res.data]
    except: return []

def load_persona(role):
    try:
        res = supabase.table("personas").select("content").eq("role", role).execute()
        return res.data[0]['content'] if res.data else None
    except: return None

# --- 音訊相關 (路徑隔離) ---
def upload_nickname_audio(role, audio_bytes):
    user_id = get_current_user_id()
    if not user_id: return False
    
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        # 關鍵修改：路徑包含 user_id
        file_path = f"{user_id}/nickname_{safe_role}.mp3"
        
        supabase.storage.from_("audio_clips").upload(
            file_path, 
            audio_bytes, 
            file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        return True
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        return False

def get_nickname_audio_bytes(role):
    user_id = get_current_user_id()
    if not user_id: return None
    
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        # 關鍵修改：從 user_id 資料夾讀取
        file_path = f"{user_id}/nickname_{safe_role}.mp3"
        response = supabase.storage.from_("audio_clips").download(file_path)
        return response
    except: return None

def train_voice_sample(audio_bytes):
    # 這裡目前是共用同一個 Voice ID (SaaS 模式下，這會導致所有人的聲音混在一起)
    # 未來進階版需要為每個會員建立獨立的 Voice ID
    # Step 1 暫時維持現狀，或者您可以考慮這裡先 disable 訓練功能以免混淆
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/edit"
        headers = {"xi-api-key": elevenlabs_key}
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        data = {'name': 'My Digital Clone'} 
        response = requests.post(url, headers=headers, data=data, files=files)
        return response.status_code == 200
    except Exception as e: return False

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
    except Exception as e: return main_bytes

# --- 6. 狀態管理與登入檢查 ---

if "user" not in st.session_state:
    st.session_state.user = None

# --- 7. 主程式邏輯 (路由) ---

if not st.session_state.user:
    # === 訪客狀態：顯示登入/註冊 ===
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br><br><h1 style='text-align: center;'>🤍 想念</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>為愛留聲，讓回憶永存。<br>SaaS 多人連線預覽版</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            tab_login, tab_signup = st.tabs(["登入", "註冊新會員"])
            
            with tab_login:
                email = st.text_input("電子郵件", key="l_email")
                password = st.text_input("密碼", type="password", key="l_pass")
                if st.button("登入", use_container_width=True, type="primary"):
                    with st.spinner("驗證中..."):
                        res = login_user(email, password)
                        if res and res.user:
                            st.session_state.user = res
                            st.success("登入成功！")
                            st.rerun()
                        else:
                            st.error("登入失敗，請檢查帳號密碼")

            with tab_signup:
                new_email = st.text_input("電子郵件", key="s_email")
                new_password = st.text_input("設定密碼", type="password", key="s_pass")
                if st.button("註冊", use_container_width=True):
                    with st.spinner("建立帳戶中..."):
                        res = signup_user(new_email, new_password)
                        if res and res.user:
                            st.success("註冊成功！系統已自動登入。")
                            st.session_state.user = res
                            st.rerun()
                        else:
                            st.error("註冊失敗，請稍後再試")

else:
    # === 已登入狀態：顯示完整 APP ===
    
    # 側邊欄：導航與用戶資訊
    with st.sidebar:
        st.write(f"👤 會員：{st.session_state.user.user.email}")
        
        # 導航選單
        app_mode = st.radio("選擇模式", ["💬 對話模式", "⚙️ 設定與訓練", "📊 帳戶狀態"])
        
        st.divider()
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    if app_mode == "💬 對話模式":
        # 這裡是原本的「前台」邏輯
        st.title("💬 跨時空對話")
        
        roles = load_all_roles()
        if not roles:
            st.info("☁️ 您尚未建立任何數位人格。請前往「⚙️ 設定與訓練」建立。")
        else:
            col_sel, col_pic = st.columns([2, 1])
            with col_sel:
                st.markdown("#### 👋 您好，請問您是我的...？")
                sel_role = st.selectbox("身分", roles, label_visibility="collapsed")
                persona_summary = load_persona(sel_role)
                if persona_summary: st.success(f"已連結：{sel_role}模式")
            with col_pic:
                if os.path.exists("photo.jpg"): st.image("photo.jpg", use_container_width=True)

            if "chat_history" not in st.session_state: st.session_state.chat_history = []

            def process_chat(audio_file):
                try:
                    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                    user_text = transcript.text
                    if not user_text or len(user_text.strip()) < 2:
                        st.warning("👂 請再說一次..."); return

                    with st.spinner("思考與檢索中..."):
                        relevant_memory = search_relevant_memories(sel_role, user_text)
                        has_nickname_audio = get_nickname_audio_bytes(sel_role) is not None
                        
                        nickname_instruction = ""
                        if has_nickname_audio:
                            nickname_instruction = "【特殊指令】：回應中**絕對不要**包含對方的暱稱，直接講內容。因為系統會自動播放真實暱稱。"
                        else:
                            nickname_instruction = "請在開頭自然呼喚對方的暱稱。"

                        system_instruction = f"""
                        {persona_summary}
                        【深層記憶】：{relevant_memory}
                        {nickname_instruction}
                        語氣要自然。
                        """
                        
                        msgs = [{"role": "system", "content": system_instruction}] + st.session_state.chat_history[-6:]
                        msgs.append({"role": "user", "content": user_text})

                        res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                        ai_text = res.choices[0].message.content
                        
                        st.session_state.chat_history.append({"role": "user", "content": user_text})
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_text})

                        final_audio_bytes = b""
                        ai_audio_bytes = b""

                        if ai_text:
                            tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                            headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                            data = {"text": ai_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}}
                            tts_res = requests.post(tts_url, json=data, headers=headers)
                            if tts_res.status_code == 200: ai_audio_bytes = tts_res.content

                        if has_nickname_audio and ai_audio_bytes:
                            nickname_bytes = get_nickname_audio_bytes(sel_role)
                            if nickname_bytes: final_audio_bytes = merge_audio_clips(nickname_bytes, ai_audio_bytes)
                            else: final_audio_bytes = ai_audio_bytes
                        else: final_audio_bytes = ai_audio_bytes

                        if final_audio_bytes:
                            st.audio(final_audio_bytes, format="audio/mp3", autoplay=True)

                except Exception as e: st.error(f"Error: {e}")

            st.divider()
            st.markdown("##### 🎙️ 按下錄音跟我說話：")
            val = st.audio_input("錄音", key="rec_pub")
            if val and persona_summary: process_chat(val)
            if st.session_state.chat_history:
                last = st.session_state.chat_history[-1]
                if last["role"] == "assistant":
                    st.markdown(f'<div class="ai-bubble"><b>祂說：</b><br>{last["content"]}</div>', unsafe_allow_html=True)

    elif app_mode == "⚙️ 設定與訓練":
        # 這裡是原本的「後台」邏輯
        st.title("⚙️ 靈魂刻錄室")
        
        tab1, tab2, tab3 = st.tabs(["📝 基礎人設", "🧠 回憶補完", "🎯 完美暱稱"])

        with tab1:
            st.caption("設定對話語氣與基礎資訊")
            c1, c2 = st.columns(2)
            with c1: t_role = st.selectbox("對象", list(ROLE_MAPPING.keys()), key="tr")
            with c2: member_name = st.text_input("您的名字 (供AI識別)", value="爸爸", key="mn")
            nickname = st.text_input("專屬暱稱", placeholder="例如：寶貝", key="nk")
            up_file = st.file_uploader(f"上傳與【{t_role}】的紀錄", type="txt")
            if st.button("✨ 生成基礎人設"):
                if up_file and member_name:
                    with st.spinner("分析中..."):
                        raw = up_file.read().decode("utf-8")
                        prompt = f"分析對話。主角(我):{member_name}。對象:{t_role}。暱稱:{nickname}。生成System Prompt，重點：模仿主角語氣，對象是{t_role}時務必使用暱稱{nickname}。資料：{raw[-20000:]}"
                        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                        save_persona_summary(t_role, res.choices[0].message.content)
                        st.success("更新完成")

        with tab2:
            st.caption("回憶補完計畫")
            q_role = st.selectbox("補充對象回憶", list(question_db.keys()), key="q_role")
            q_list = question_db.get(q_role, [])
            memories = get_memories_by_role(q_role)
            answered_qs = set()
            for m in memories:
                if "【關於" in m['content'] and "】：" in m['content']:
                    q_part = m['content'].split("【關於")[1].split("】：")[0]
                    answered_qs.add(q_part)

            if "edit_target" not in st.session_state: st.session_state.edit_target = None
            current_q = None
            if st.session_state.edit_target:
                current_q = st.session_state.edit_target
                st.info(f"✏️ 正在重新錄製：{current_q}")
            else:
                for q in q_list:
                    if q not in answered_qs:
                        current_q = q
                        break
            
            if len(q_list) > 0:
                progress = len(answered_qs) / len(q_list)
                st.progress(progress, text=f"進度：{len(answered_qs)} / {len(q_list)}")

            col_left, col_right = st.columns([1.5, 1], gap="medium")
            with col_left:
                st.markdown("### 🎙️ 進行中任務")
                if current_q:
                    st.markdown(f"""<div class="question-card-active"><div class="q-text">{current_q}</div></div>""", unsafe_allow_html=True)
                    audio_ans = st.audio_input("錄音回答", key=f"ans_{current_q}")
                    if "transcribed_text" not in st.session_state: st.session_state.transcribed_text = ""
                    if audio_ans:
                        trans = client.audio.transcriptions.create(model="whisper-1", file=audio_ans)
                        st.session_state.transcribed_text = trans.text
                        st.text_area("文字修改", value=st.session_state.transcribed_text, key="edit_text_area")
                        c_act1, c_act2 = st.columns(2)
                        with c_act1:
                            if st.button("🔊 試聽"):
                                if st.session_state.transcribed_text:
                                    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                                    headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                                    data = {"text": st.session_state.transcribed_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}}
                                    r = requests.post(tts_url, json=data, headers=headers)
                                    if r.status_code == 200: st.audio(r.content, format="audio/mp3", autoplay=True)
                        with c_act2:
                            if st.button("💾 存入並訓練", type="primary"):
                                final_text = st.session_state.edit_text_area
                                save_memory_fragment(q_role, current_q, final_text)
                                audio_ans.seek(0)
                                train_voice_sample(audio_ans.read())
                                st.success("已儲存")
                                st.session_state.edit_target = None
                                st.session_state.transcribed_text = ""
                                st.rerun()
                    if st.button("⏭️ 跳過"):
                        save_memory_fragment(q_role, current_q, "(已略過)")
                        st.rerun()
                else: st.success("🎉 題目已全部完成")

            with col_right:
                st.markdown("### 📜 回憶存摺")
                with st.container(height=500):
                    for mem in memories:
                        if "【關於" in mem['content']:
                            try:
                                q_part = mem['content'].split("【關於")[1].split("】：")[0]
                                a_part = mem['content'].split("】：")[1]
                                st.markdown(f"""<div class="history-card"><div class="history-q">Q: {q_part}</div><div class="history-a">A: {a_part[:30]}...</div></div>""", unsafe_allow_html=True)
                                if st.button("🔄 重錄", key=f"re_{mem['id']}"):
                                    st.session_state.edit_target = q_part
                                    st.rerun()
                            except: pass

        with tab3:
            st.subheader("🎯 完美暱稱重現")
            st.info("錄製一段真實的呼喚，AI 會在開頭直接播放這段錄音。")
            nick_role = st.selectbox("錄製給誰聽？", list(ROLE_MAPPING.keys()), key="nick_role")
            st.markdown(f"請按下錄音，喊一聲給【{nick_role}】聽的暱稱：")
            real_nick_audio = st.audio_input("錄製", key="real_nick_rec")
            if real_nick_audio:
                if st.button("💾 上傳真實聲音"):
                    with st.spinner("處理中..."):
                        if upload_nickname_audio(nick_role, real_nick_audio.read()):
                            st.success("成功！")

    elif app_mode == "📊 帳戶狀態":
        st.title("📊 帳戶狀態")
        st.info(f"目前登入帳號：{st.session_state.user.user.email}")
        st.caption("以下顯示系統資源使用量（由平台提供算力）")
        
        # 這裡未來可以顯示會員等級、每日剩餘額度等
        # 目前先顯示平台總量
        try:
            url = "https://api.elevenlabs.io/v1/user/subscription"
            headers = {"xi-api-key": elevenlabs_key}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                used = data['character_count']
                limit = data['character_limit']
                st.metric("平台聲音額度使用量", f"{used:,} / {limit:,}")
                st.progress(used/limit)
        except: pass