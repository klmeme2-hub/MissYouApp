import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import numpy as np
import os
import json

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

# --- 3. 讀取外部題庫 (JSON) ---
@st.cache_data
def load_questions_from_file():
    """讀取 questions.json 檔案"""
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"錯誤": ["找不到 questions.json 題庫檔，請確認已上傳至 GitHub"]}
    except Exception as e:
        return {"錯誤": [f"讀取失敗: {e}"]}

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

# --- 上傳錄音到 ElevenLabs (含標籤) ---
def train_voice_sample(audio_bytes, label="General"):
    """
    將錄音檔傳送給 ElevenLabs
    label: 用來標記這是什麼錄音 (例如: Nickname_Wife)
    """
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/edit"
        headers = {"xi-api-key": elevenlabs_key}
        
        # 準備檔案
        files = {
            'files': (f'{label}.mp3', audio_bytes, 'audio/mpeg')
        }
        data = {'name': 'My Digital Clone'} 
        
        response = requests.post(url, headers=headers, data=data, files=files)
        return response.status_code == 200
    except Exception as e:
        st.error(f"上傳失敗: {e}")
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

                with st.spinner("回憶檢索中..."):
                    relevant_memory = search_relevant_memories(sel_role, user_text)
                
                # Prompt 優化：強調暱稱使用
                system_instruction = f"""
                {persona_summary}
                
                【深層記憶與細節】：
                {relevant_memory}
                
                【絕對指令】：
                1. 必須使用我對【{sel_role}】的專屬暱稱。
                2. 語氣要自然，包含呼吸感。
                3. 如果記憶中有具體細節，請自然地帶入。
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
                data = {
                    "text": ai_text, 
                    "model_id": "eleven_multilingual_v2", 
                    "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}
                }
                tts_res = requests.post(tts_url, json=data, headers=headers)
                if tts_res.status_code == 200:
                    st.audio(tts_res.content, format="audio/mp3", autoplay=True)
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

    tab1, tab2, tab3 = st.tabs(["📝 基礎人設", "🧠 回憶補完 (題庫)", "🎙️ 聲音特訓 (暱稱)"])

    # --- TAB 1: 基礎檔案 (保持不變) ---
    with tab1:
        st.caption("設定對話語氣與基礎資訊")
        c1, c2 = st.columns(2)
        with c1: t_role = st.selectbox("對象", ["妻子", "丈夫", "兒子", "女兒", "朋友"], key="tr")
        with c2: nickname = st.text_input("您對他/她的專屬暱稱", placeholder="例如：寶貝、小胖", key="nk")
        
        up_file = st.file_uploader(f"上傳與【{t_role}】的紀錄", type="txt")

        if st.button("✨ 生成基礎人設"):
            if up_file:
                with st.spinner("分析中..."):
                    raw = up_file.read().decode("utf-8")
                    prompt = f"分析對話。主角對{t_role}的說話風格。專屬暱稱是「{nickname}」。請生成System Prompt，強調必須使用暱稱「{nickname}」稱呼對方。資料：{raw[-20000:]}"
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    save_persona_summary(t_role, res.choices[0].message.content)
                    st.success("基礎人設已更新！")

    # --- TAB 2: 回憶補完 (讀取 JSON) ---
    with tab2:
        st.caption("每天回答幾題，讓 AI 的記憶更完整")
        
        q_role = st.selectbox("您想補充關於誰的回憶？", list(question_db.keys()), key="q_role")
        
        # 從 JSON 讀取題目列表
        q_list = question_db.get(q_role, ["(無題目資料)"])
        
        # 隨機按鈕
        if st.button("🎲 隨機換一題"):
             question = np.random.choice(q_list)
             st.session_state.current_q = question
        elif "current_q" not in st.session_state:
             st.session_state.current_q = q_list[0]
            
        st.markdown(f'<div class="question-card"><b>APP 提問：</b><br>{st.session_state.current_q}</div>', unsafe_allow_html=True)
        
        ans_method = st.radio("回答方式", ["語音口述", "文字輸入"], horizontal=True)
        answer_content = ""
        if ans_method == "語音口述":
            audio_ans = st.audio_input("按此回答問題", key="ans_rec")
            if audio_ans:
                trans = client.audio.transcriptions.create(model="whisper-1", file=audio_ans)
                answer_content = trans.text
        else:
            answer_content = st.text_area("輸入您的回答...")

        if st.button("💾 存入大腦"):
            if answer_content:
                full_memory = f"【關於{st.session_state.current_q}】：{answer_content}"
                save_memory_fragment(q_role, full_memory)
                st.success("已存入深層記憶！")
                st.balloons()

    # --- TAB 3: 聲音特訓 (暱稱優化) ---
    with tab3:
        st.subheader("🎯 專屬暱稱定錨")
        st.info("為了讓 AI 叫喚親人的名字更像您，請在這裡特別錄製該暱稱。")
        
        target_nick = st.text_input("輸入您要錄製的暱稱文字", placeholder="例如：老婆～")
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("##### 步驟 1：錄製暱稱")
            st.caption("請只錄製那個稱呼，語氣要像平常叫她一樣。建議錄 3-5 秒。")
            nick_audio = st.audio_input("錄製暱稱", key="nick_rec")
            
        with col_t2:
            st.markdown("##### 步驟 2：上傳定錨")
            if nick_audio and target_nick:
                if st.button("🚀 上傳暱稱樣本"):
                    with st.spinner("正在進行權重微調..."):
                        # 使用特殊的 label 標記
                        success = train_voice_sample(nick_audio, label=f"Nickname_{target_nick}")
                        if success:
                            st.success(f"成功！已讓 AI 記住「{target_nick}」的發音方式。")
                        else:
                            st.error("上傳失敗")
            else:
                st.caption("請先輸入文字並錄音")
        
        st.divider()
        st.subheader("🎙️ 一般情緒訓練")
        st.caption("錄製長句（開心、生氣、安慰）以豐富語調。")
        gen_audio = st.audio_input("錄製長句", key="gen_rec")
        if gen_audio:
            if st.button("上傳情緒樣本"):
                if train_voice_sample(gen_audio, label="Emotion_Sample"):
                    st.success("訓練成功")