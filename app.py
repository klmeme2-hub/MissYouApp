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
    /* 全局配色鎖定 */
    .stApp, p, h1, h2, h3, label, div, span, button { color: #333333 !important; }
    
    /* 下拉選單修復 */
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li:hover { background-color: #E3F2FD !important; }

    /* AI 對話氣泡 */
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
    .question-card {
        background-color: #E3F2FD;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #BBDEFB;
        text-align: center;
    }
    .q-text {
        font-size: 20px;
        font-weight: bold;
        color: #1565C0 !important;
        margin-bottom: 10px;
    }
    
    /* 隱藏 Streamlit 選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 2. 初始化與設定 ---
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

# --- 關鍵修正：角色中英對照表 (解決檔名報錯) ---
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
    except:
        return {} # 若讀取失敗回傳空字典

question_db = load_questions_from_file()

# --- 4. 核心功能函數 ---

def get_embedding(text):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def save_memory_fragment(role, text_content):
    """儲存單條記憶片段"""
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

# --- 音訊相關函數 ---

def upload_nickname_audio(role, audio_bytes):
    """上傳真實暱稱音檔 (用於拼接)"""
    try:
        # 轉碼：把中文角色轉成英文檔名
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"nickname_{safe_role}.mp3"
        
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
    """下載真實暱稱音檔"""
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"nickname_{safe_role}.mp3"
        response = supabase.storage.from_("audio_clips").download(file_path)
        return response
    except:
        return None

def train_voice_sample(audio_bytes):
    """上傳音檔至 ElevenLabs 進行訓練"""
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/edit"
        headers = {"xi-api-key": elevenlabs_key}
        # 這裡不改變 Voice Name，只上傳樣本
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        data = {'name': 'My Digital Clone'} 
        response = requests.post(url, headers=headers, data=data, files=files)
        return response.status_code == 200
    except Exception as e:
        print(f"訓練上傳失敗: {e}") # 訓練失敗不阻擋流程，僅後台印出
        return False

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
    # === 親友前台 (User Mode) ===
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
                # 1. 語音轉字
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                user_text = transcript.text
                if not user_text or len(user_text.strip()) < 2:
                    st.warning("👂 請再說一次..."); return

                # 2. 檢索記憶
                with st.spinner("思考與檢索中..."):
                    relevant_memory = search_relevant_memories(sel_role, user_text)
                    
                    # 檢查真實暱稱
                    has_nickname_audio = get_nickname_audio_bytes(sel_role) is not None
                    
                    nickname_instruction = ""
                    if has_nickname_audio:
                        nickname_instruction = "【特殊指令】：回應開頭必須加上 `[PLAY_NICKNAME]` 標籤。"
                    else:
                        nickname_instruction = "請在開頭自然呼喚對方的暱稱。"

                    # 3. 生成回應
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
                    
                    # 隱藏標籤
                    display_text = ai_text.replace("[PLAY_NICKNAME]", "").strip()
                    if display_text.startswith((",", "，")): display_text = display_text[1:].strip()

                    st.session_state.chat_history.append({"role": "user", "content": user_text})
                    st.session_state.chat_history.append({"role": "assistant", "content": display_text})

                    # 4. 音訊拼接
                    final_audio_bytes = b""
                    
                    # A. 真實暱稱
                    if "[PLAY_NICKNAME]" in ai_text and has_nickname_audio:
                        nickname_bytes = get_nickname_audio_bytes(sel_role)
                        if nickname_bytes:
                            final_audio_bytes += nickname_bytes
                            # 增加一點點靜音 (padding) 讓拼接更自然 (這裡用空bytes模擬，實際需要音訊處理庫，為求穩定暫略)
                            ai_text = ai_text.replace("[PLAY_NICKNAME]", "").strip()
                            if ai_text.startswith((",", "，")): ai_text = ai_text[1:].strip()

                    # B. AI 語音
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

                    # C. 播放
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
    # === 管理員後台 (Admin Mode) ===
    st.success("🔓 管理員模式")
    if st.button("登出"):
        st.session_state.is_admin = False
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📝 基礎人設", "🧠 回憶補完 (引導)", "🎯 完美暱稱"])

    # --- TAB 1: 基礎檔案 (修復欄位) ---
    with tab1:
        st.caption("設定對話語氣與基礎資訊")
        c1, c2 = st.columns(2)
        with c1: 
            t_role = st.selectbox("對象", list(ROLE_MAPPING.keys()), key="tr")
        with c2: 
            # 欄位回歸：會員名字
            member_name = st.text_input("您在對話紀錄中的名字", placeholder="例如：Ken", key="mn")
            
        nickname = st.text_input("您對他/她的專屬暱稱", placeholder="例如：寶貝、小胖", key="nk")
        
        up_file = st.file_uploader(f"上傳與【{t_role}】的紀錄", type="txt")

        if st.button("✨ 生成基礎人設"):
            if up_file and member_name:
                with st.spinner("AI 正在分析您的語氣..."):
                    raw = up_file.read().decode("utf-8")
                    prompt = f"""
                    分析對話紀錄。
                    主角(我)：{member_name}
                    對象：{t_role}
                    專屬暱稱：{nickname}
                    
                    請分析【主角】的說話風格。
                    生成 System Prompt，重點：
                    1. 必須模仿主角的語氣。
                    2. 對象是{t_role}，請務必使用暱稱「{nickname}」稱呼對方。
                    資料：{raw[-20000:]}
                    """
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    save_persona_summary(t_role, res.choices[0].message.content)
                    st.success(f"已建立對【{t_role}】的專屬人設！")
            else:
                st.warning("請填寫完整資訊")

    # --- TAB 2: 回憶補完計畫 (順序 + 語音訓練) ---
    with tab2:
        st.info("💡 這裡的回答會變成深層記憶，且您的錄音會同步用於訓練 AI 聲音。")
        
        q_role = st.selectbox("補充關於誰的回憶？", list(question_db.keys()), key="q_role")
        q_list = question_db.get(q_role, ["(無題目)"])
        
        # 初始化題目索引
        if "q_index" not in st.session_state: st.session_state.q_index = 0
        if "current_role_q" not in st.session_state: st.session_state.current_role_q = q_role
        
        # 如果切換了角色，索引歸零
        if st.session_state.current_role_q != q_role:
            st.session_state.q_index = 0
            st.session_state.current_role_q = q_role

        # 確保索引不超標
        if st.session_state.q_index >= len(q_list):
            st.success("🎉 太棒了！您已回答完此角色的所有題目。")
            if st.button("重新開始"):
                st.session_state.q_index = 0
                st.rerun()
        else:
            current_q = q_list[st.session_state.q_index]
            
            # 進度顯示
            st.progress((st.session_state.q_index + 1) / len(q_list), text=f"進度：{st.session_state.q_index + 1} / {len(q_list)}")
            
            # 顯示題目卡片
            st.markdown(f"""
            <div class="question-card">
                <div class="q-text">Q{st.session_state.q_index + 1}: {current_q}</div>
                <div style="font-size:14px; color:#666;">請按下錄音，自然地回答這個問題...</div>
            </div>
            """, unsafe_allow_html=True)

            # 語音回答區
            audio_ans = st.audio_input("錄音回答", key=f"ans_rec_{st.session_state.q_index}")
            
            col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
            
            with col_b1:
                if st.button("✅ 提交並訓練聲音", type="primary", use_container_width=True):
                    if audio_ans:
                        with st.spinner("正在存入記憶並訓練聲音..."):
                            # 1. 轉文字
                            trans = client.audio.transcriptions.create(model="whisper-1", file=audio_ans)
                            content = trans.text
                            
                            # 2. 存入記憶庫
                            full_memory = f"【關於{current_q}】：{content}"
                            save_memory_fragment(q_role, full_memory)
                            
                            # 3. 傳送錄音去訓練
                            # 將 bytes 指針歸零以便重複讀取
                            audio_ans.seek(0)
                            audio_bytes = audio_ans.read()
                            train_voice_sample(audio_bytes)
                            
                            st.success("已儲存！")
                            # 跳下一題
                            st.session_state.q_index += 1
                            st.rerun()
                    else:
                        st.warning("請先錄音")

            with col_b2:
                if st.button("跳過", use_container_width=True):
                    st.session_state.q_index += 1
                    st.rerun()
                    
            with col_b3:
                # 簡單實作「以後不答」：邏輯上就是永久跳過，這裡暫時用跳過處理，未來可加資料庫欄位紀錄
                if st.button("不再問", use_container_width=True):
                    st.session_state.q_index += 1
                    st.rerun()

    # --- TAB 3: 完美暱稱 (Audio Injection) ---
    with tab3:
        st.subheader("🎯 完美暱稱重現")
        st.caption("錄製一段真實的呼喚，AI 會在開頭直接播放這段錄音。")
        
        nick_role = st.selectbox("錄製給誰聽？", list(ROLE_MAPPING.keys()), key="nick_role")
        
        st.markdown(f"請按下錄音，喊一聲給【{nick_role}】聽的暱稱（2-3秒）：")
        real_nick_audio = st.audio_input("錄製", key="real_nick_rec")
        
        if real_nick_audio:
            if st.button("💾 上傳真實聲音"):
                with st.spinner("處理中..."):
                    audio_bytes = real_nick_audio.read()
                    if upload_nickname_audio(nick_role, audio_bytes):
                        st.success(f"成功！對【{nick_role}】說話時，將使用這段真實錄音開頭。")