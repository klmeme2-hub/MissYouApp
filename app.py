import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import numpy as np
import os
import json
import io

# --- 1. 頁面與 UI 設定 ---
st.set_page_config(page_title="想念", page_icon="🤍", layout="centered")

custom_css = """
<style>
    .stApp, p, h1, h2, h3, label, div, span { color: #333333 !important; }
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li:hover { background-color: #E3F2FD !important; }
    .ai-bubble {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #4A90E2;
        margin: 10px 0;
        color: #333333;
    }
    .question-card {
        background-color: #E3F2FD;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #BBDEFB;
        font-size: 18px;
        font-weight: bold;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 2. 初始化 ---
if "SUPABASE_URL" not in st.secrets or "ADMIN_PASSWORD" not in st.secrets:
    st.error("⚠️ 請先設定 Secrets")
    st.stop()

openai_key = st.secrets["OPENAI_API_KEY"]
elevenlabs_key = st.secrets["ELEVENLABS_API_KEY"]
voice_id = st.secrets["VOICE_ID"]
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
admin_password = st.secrets["ADMIN_PASSWORD"]

client = OpenAI(api_key=openai_key)

@st.cache_resource
def init_supabase():
    return create_client(supabase_url, supabase_key)

supabase = init_supabase()

# --- 3. 讀取外部題庫 ---
@st.cache_data
def load_questions_from_file():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

question_db = load_questions_from_file()

# --- 4. 核心功能函數 ---

def get_embedding(text):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def save_memory_fragment(role, text_content):
    embedding = get_embedding(text_content)
    data = {"role": role, "content": text_content, "embedding": embedding}
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
    data = {"role": role, "content": content}
    supabase.table("personas").upsert(data).execute()

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

# --- 新增：處理真實音檔上傳與下載 ---
def upload_nickname_audio(role, audio_bytes):
    """將暱稱音檔上傳到 Supabase Storage"""
    try:
        file_path = f"nickname_{role}.mp3"
        supabase.storage.from_("audio_clips").upload(
            file_path, 
            audio_bytes, 
            file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        return True
    except Exception as e:
        st.error(f"儲存音檔失敗: {e}")
        return False

def get_nickname_audio_bytes(role):
    """從 Supabase 下載暱稱音檔"""
    try:
        file_path = f"nickname_{role}.mp3"
        response = supabase.storage.from_("audio_clips").download(file_path)
        return response
    except:
        return None

# --- 5. 權限管理 ---
if "is_admin" not in st.session_state: st.session_state.is_admin = False

def check_pass():
    if st.session_state.pwd_input == admin_password:
        st.session_state.is_admin = True
        st.session_state.pwd_input = ""
    else: st.error("密碼錯誤")

# --- 6. 主介面 ---
st.title("🤍 想念")

if not st.session_state.is_admin:
    # === 親友前台 ===
    roles = load_all_roles()
    if not roles:
        st.info("☁️ 尚未建立數位人格")
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
                    
                    # 檢查是否有預錄的暱稱音檔
                    has_nickname_audio = get_nickname_audio_bytes(sel_role) is not None
                    
                    nickname_instruction = ""
                    if has_nickname_audio:
                        nickname_instruction = """
                        【特殊指令】：
                        請務必在回應的「最開頭」加上標籤 `[PLAY_NICKNAME]`。
                        例如：`[PLAY_NICKNAME]，今天過得好嗎？`
                        這代表你會先呼喚對方的暱稱。
                        """
                    else:
                        nickname_instruction = "請在開頭自然呼喚對方的暱稱。"

                    system_instruction = f"""
                    {persona_summary}
                    
                    【深層記憶】：{relevant_memory}
                    
                    {nickname_instruction}
                    
                    語氣要自然，包含呼吸感。
                    """
                    
                    msgs = [{"role": "system", "content": system_instruction}] + st.session_state.chat_history[-6:]
                    msgs.append({"role": "user", "content": user_text})

                    res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                    ai_text = res.choices[0].message.content
                    
                    # 處理顯示文字 (把標籤藏起來，不要顯示給使用者看)
                    display_text = ai_text.replace("[PLAY_NICKNAME]", "").strip()
                    if display_text.startswith("，") or display_text.startswith(","):
                        display_text = display_text[1:].strip()

                    st.session_state.chat_history.append({"role": "user", "content": user_text})
                    st.session_state.chat_history.append({"role": "assistant", "content": display_text})

                    # --- 音訊拼接邏輯 ---
                    final_audio_bytes = b""
                    
                    # 1. 如果 AI 決定叫暱稱，且我們有錄音檔 -> 先放入暱稱音檔
                    if "[PLAY_NICKNAME]" in ai_text and has_nickname_audio:
                        nickname_bytes = get_nickname_audio_bytes(sel_role)
                        if nickname_bytes:
                            final_audio_bytes += nickname_bytes
                            # 剩下的文字去生成語音
                            ai_text = ai_text.replace("[PLAY_NICKNAME]", "").strip()
                            # 去掉開頭的標點
                            if ai_text.startswith("，") or ai_text.startswith(","):
                                ai_text = ai_text[1:].strip()

                    # 2. 生成剩下的語音
                    if ai_text:
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                        headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                        data = {
                            "text": ai_text, 
                            "model_id": "eleven_multilingual_v2", 
                            "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}
                        }
                        tts_res = requests.post(tts_url, json=data, headers=headers)
                        if tts_res.status_code == 200:
                            final_audio_bytes += tts_res.content

                    # 3. 播放拼接後的音訊
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

    st.divider()
    with st.expander("🔒 會員登入"):
        st.text_input("密碼", type="password", key="pwd_input", on_change=check_pass)

else:
    # === 管理員後台 ===
    st.success("🔓 管理員模式")
    if st.button("登出"):
        st.session_state.is_admin = False
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📝 基礎人設", "🧠 回憶補完", "🎙️ 聲音特訓 (暱稱)"])

    # TAB 1 & 2 省略詳細代碼，與上一版相同 (請自行保留或複製上一版的 tab1, tab2 內容)
    # 這裡為了完整性，我還是把 Tab 1 和 Tab 2 放進來，以免你複製錯

    with tab1:
        st.caption("設定對話語氣與基礎資訊")
        c1, c2 = st.columns(2)
        with c1: t_role = st.selectbox("對象", ["妻子", "丈夫", "兒子", "女兒", "朋友"], key="tr")
        with c2: nickname = st.text_input("專屬暱稱", placeholder="例如：寶貝", key="nk")
        up_file = st.file_uploader(f"上傳與【{t_role}】的紀錄", type="txt")
        if st.button("✨ 生成基礎人設"):
            if up_file:
                with st.spinner("分析中..."):
                    raw = up_file.read().decode("utf-8")
                    prompt = f"分析對話。主角對{t_role}的說話風格。專屬暱稱是「{nickname}」。請生成System Prompt。資料：{raw[-20000:]}"
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    save_persona_summary(t_role, res.choices[0].message.content)
                    st.success("更新完成")

    with tab2:
        st.caption("回憶補完計畫")
        q_role = st.selectbox("補充對象回憶", list(question_db.keys()), key="q_role")
        q_list = question_db.get(q_role, ["無題目"])
        if st.button("🎲 換一題"): st.session_state.current_q = np.random.choice(q_list)
        elif "current_q" not in st.session_state: st.session_state.current_q = q_list[0]
        st.markdown(f'<div class="question-card">{st.session_state.current_q}</div>', unsafe_allow_html=True)
        ans = st.text_area("輸入回答...")
        if st.button("💾 存入大腦"):
            if ans:
                save_memory_fragment(q_role, f"【關於{st.session_state.current_q}】：{ans}")
                st.success("已存入")

    # --- TAB 3: 聲音特訓 (重點更新) ---
    with tab3:
        st.subheader("🎯 完美暱稱重現 (Audio Injection)")
        st.info("這裡錄製的聲音，將會被「原封不動」地播放，而不是用 AI 合成的。")
        
        # 選擇要錄製給誰聽的暱稱
        nick_target_role = st.selectbox("這是給誰聽的暱稱？", ["妻子", "丈夫", "兒子", "女兒", "朋友"], key="nick_role")
        
        st.markdown(f"請按下錄音，深情地喊一聲給【{nick_target_role}】聽的暱稱（建議 2-3 秒）：")
        st.caption("例如：「老～婆～」、「寶貝女兒～」")
        
        real_nick_audio = st.audio_input("錄製真實暱稱", key="real_nick_rec")
        
        if real_nick_audio:
            # 試聽
            st.audio(real_nick_audio)
            
            if st.button("💾 儲存這個真實聲音"):
                with st.spinner("正在上傳至雲端倉庫..."):
                    # 將音檔讀取為 bytes
                    audio_bytes = real_nick_audio.read()
                    
                    if upload_nickname_audio(nick_target_role, audio_bytes):
                        st.success(f"成功！以後對【{nick_target_role}】說話時，開頭都會直接播放這段錄音。")
                    else:
                        st.error("上傳失敗，請檢查 Supabase Storage 是否已建立 'audio_clips' bucket。")