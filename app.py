import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import numpy as np
import os

# --- 1. 頁面與 UI 設定 ---
st.set_page_config(page_title="想念", page_icon="🤍", layout="centered")

# CSS 強制美化 (配合 config.toml 達到完美效果)
custom_css = """
<style>
    /* 強制字體顏色 */
    .stApp, p, h1, h2, h3, label, div, span { color: #333333 !important; }
    
    /* 下拉選單修復 */
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li:hover { background-color: #E3F2FD !important; }

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
    
    /* 隱藏選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 2. 初始化與連線 ---
# 檢查 Secrets
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

# --- 3. 核心功能函數 ---

def get_embedding(text):
    """將文字轉為向量"""
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def save_memories_to_vector_db(role, text_data):
    """將長篇對話切碎並存入向量資料庫"""
    supabase.table("memories").delete().eq("role", role).execute()
    
    chunk_size = 500
    overlap = 50
    chunks = []
    
    for i in range(0, len(text_data), chunk_size - overlap):
        chunk = text_data[i:i + chunk_size]
        if len(chunk) > 20:
            chunks.append(chunk)
            
    total_chunks = len(chunks)
    progress_bar = st.progress(0, text=f"正在植入深層記憶 (0/{total_chunks})...")
    
    for idx, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        data = {
            "role": role,
            "content": chunk,
            "embedding": embedding
        }
        supabase.table("memories").insert(data).execute()
        progress_bar.progress((idx + 1) / total_chunks, text=f"正在植入深層記憶 ({idx+1}/{total_chunks})")
    
    progress_bar.empty()
    return True

def search_relevant_memories(role, query_text):
    """搜尋相關記憶"""
    try:
        query_vec = get_embedding(query_text)
        response = supabase.rpc(
            "match_memories",
            {
                "query_embedding": query_vec,
                "match_threshold": 0.5,
                "match_count": 3,
                "search_role": role
            }
        ).execute()
        
        memory_text = "\n".join([item['content'] for item in response.data])
        return memory_text
    except Exception as e:
        print(f"搜尋失敗: {e}")
        return ""

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

# --- 4. 權限管理 ---
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

def check_pass():
    if st.session_state.pwd_input == admin_password:
        st.session_state.is_admin = True
        st.session_state.pwd_input = ""
    else:
        st.error("密碼錯誤")

# --- 5. 主介面 ---
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

        # --- 核心對話函數 (已修正縮排) ---
        def process_chat(audio_file):
            try:
                # 1. 語音轉字
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                user_text = transcript.text

                # 【防呆修正】：這裡縮排對齊了，不會報錯
                if not user_text or len(user_text.strip()) < 2:
                    st.warning("👂 聽不太清楚，請靠近麥克風再說一次...")
                    return

                # 2. 搜尋深層記憶
                with st.spinner("回憶檢索中..."):
                    relevant_memory = search_relevant_memories(sel_role, user_text)
                
                # 3. 組合 Prompt
                system_instruction = f"""
                {persona_summary}
                
                【相關的具體回憶片段】：
                {relevant_memory}
                
                請根據上述的人設與回憶片段來回答。如果回憶片段中有具體細節，請自然地帶入對話中。
                """
                
                recent_history = st.session_state.chat_history[-6:] 
                msgs = [{"role": "system", "content": system_instruction}] + recent_history
                msgs.append({"role": "user", "content": user_text})

                # 4. AI 生成
                res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                ai_text = res.choices[0].message.content

                st.session_state.chat_history.append({"role": "user", "content": user_text})
                st.session_state.chat_history.append({"role": "assistant", "content": ai_text})

                # 5. 語音合成
                tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {"xi-api-key": elevenl