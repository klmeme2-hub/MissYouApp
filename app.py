import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import numpy as np
import os

# --- 1. 頁面與 UI 設定 ---
st.set_page_config(page_title="想念", page_icon="🤍", layout="centered")

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
    
    /* 儀表板卡片 */
    .dashboard-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E0E0E0;
        margin-bottom: 10px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 2. 初始化與連線 ---
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

# --- 3. 系統監控函數 (新增) ---

def get_elevenlabs_usage():
    """查詢 ElevenLabs 剩餘額度"""
    try:
        url = "https://api.elevenlabs.io/v1/user/subscription"
        headers = {"xi-api-key": elevenlabs_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            used = data['character_count']
            limit = data['character_limit']
            return used, limit
        return 0, 0
    except:
        return 0, 0

# --- 4. 核心功能函數 ---

def get_embedding(text):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def save_memories_to_vector_db(role, text_data):
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

# --- 5. 權限管理 ---
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

def check_pass():
    if st.session_state.pwd_input == admin_password:
        st.session_state.is_admin = True
        st.session_state.pwd_input = ""
    else:
        st.error("密碼錯誤")

# --- 6. 主介面 ---
st.title("🤍 想念")

if not st.session_state.is_admin:
    # === 親友前台 (保持不變) ===
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
                    st.warning("👂 聽不太清楚，請靠近麥克風再說一次...")
                    return

                with st.spinner("回憶檢索中..."):
                    relevant_memory = search_relevant_memories(sel_role, user_text)
                
                system_instruction = f"""
                {persona_summary}
                【相關的具體回憶片段】：
                {relevant_memory}
                請根據上述的人設與回憶片段來回答。如果回憶片段中有具體細節，請自然地帶入對話中。
                """
                
                recent_history = st.session_state.chat_history[-6:] 
                msgs = [{"role": "system", "content": system_instruction}] + recent_history
                msgs.append({"role": "user", "content": user_text})

                res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                ai_text = res.choices[0].message.content

                st.session_state.chat_history.append({"role": "user", "content": user_text})
                st.session_state.chat_history.append({"role": "assistant", "content": ai_text})

                tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                data = {"text": ai_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}
                tts_res = requests.post(tts_url, json=data, headers=headers)
                if tts_res.status_code == 200:
                    st.audio(tts_res.content, format="audio/mp3", autoplay=True)

            except Exception as e: 
                st.error(f"Error: {e}")

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
    # === 管理員後台 (新增儀表板) ===
    st.success("🔓 管理員模式")
    if st.button("登出"):
        st.session_state.is_admin = False
        st.rerun()

    # --- 系統健康儀表板 (新增區塊) ---
    st.markdown("### 📊 系統健康儀表板")
    
    col_sys1, col_sys2 = st.columns(2)
    
    # ElevenLabs 狀態
    with col_sys1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.caption("🗣️ 聲音合成額度 (ElevenLabs)")
        used, limit = get_elevenlabs_usage()
        if limit > 0:
            usage_percent = used / limit
            st.progress(usage_percent)
            st.write(f"**{used:,}** / {limit:,} 字元")
            if usage_percent > 0.8:
                st.error("⚠️ 額度即將用完！")
        else:
            st.warning("無法讀取數據")
        st.markdown('</div>', unsafe_allow_html=True)

    # OpenAI 狀態
    with col_sys2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.caption("🧠 大腦餘額 (OpenAI)")
        st.info("OpenAI 不提供餘額查詢 API")
        st.markdown("""
            <a href="https://platform.openai.com/settings/organization/billing/overview" target="_blank">
                <button style="
                    width:100%; 
                    background-color:white; 
                    border:1px solid #ccc; 
                    padding:8px; 
                    border-radius:5px; 
                    cursor:pointer;">
                    🔗 點此查看帳單
                </button>
            </a>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    
    # --- 原本的建立功能 ---
    with st.container(border=True):
        st.subheader("📝 建立/更新全息數位分身")
        c1, c2 = st.columns(2)
        with c1: t_role = st.selectbox("對象身分", ["妻子", "丈夫", "兒子", "女兒", "朋友"], key="tr")
        with c2: m_name = st.text_input("您的名字", value="爸爸", key="mn")
        
        up_file = st.file_uploader(f"上傳與【{t_role}】的 LINE 紀錄", type="txt")

        if st.button("✨ 開始深度刻錄", use_container_width=True):
            if up_file and m_name:
                with st.spinner("正在進行雙重處理..."):
                    try:
                        raw_text = up_file.read().decode("utf-8")
                        
                        prompt = f"分析以下對話。主角：{m_name}，對象：{t_role}。生成語氣指導System Prompt。資料：{raw_text[-20000:]}"
                        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                        summary = res.choices[0].message.content
                        save_persona_summary(t_role, summary)
                        
                        save_memories_to_vector_db(t_role, raw_text)
                        
                        st.success(f"✅ 完成！對【{t_role}】的靈魂與所有細節記憶已永久保存。")
                        st.balloons()
                    except Exception as e: st.error(f"錯誤: {e}")