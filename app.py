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
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #BBDEFB;
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

# --- 3. 內建題庫 (引導會員輸入) ---
INTERVIEW_QUESTIONS = {
    "妻子": [
        "她的生日是哪一天？你們通常怎麼慶祝？",
        "你們的結婚紀念日是何時？當時求婚的場景是什麼？",
        "她最喜歡的顏色、花朵或食物是什麼？",
        "她有沒有什麼口頭禪或是可愛的小習慣？",
        "你們最難忘的一次旅行是去哪裡？發生了什麼事？",
        "你平常都怎麼稱呼她？(例如：老婆、寶貝、全名？)",
        "家裡有寵物嗎？名字叫什麼？她跟寵物的關係如何？",
        "如果她難過時，你通常會怎麼安慰她？"
    ],
    "丈夫": [
        "他的興趣是什麼？(釣魚、打球、遊戲？)",
        "他最愛吃的一道菜是什麼？",
        "你們之間有沒有什麼只有兩人才懂的笑話？",
        "他平常怎麼稱呼妳？"
    ],
    "兒女": [
        "孩子的小名是什麼？為什麼取這個名字？",
        "他/她幾歲了？現在正在讀書還是工作？",
        "你對他/她最大的期望是什麼？",
        "小時候有沒有發生過什麼讓你印象深刻的糗事？",
        "如果他/她遇到挫折，你通常會跟他說什麼？"
    ],
    "朋友": [
        "你們是怎麼認識的？認識多久了？",
        "你們以前最常一起做什麼蠢事？",
        "他有什麼綽號？"
    ]
}

# --- 4. 核心功能函數 ---

def get_embedding(text):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def save_memory_fragment(role, text_content):
    """儲存單條記憶片段 (用於回答問卷)"""
    embedding = get_embedding(text_content)
    data = {
        "role": role,
        "content": text_content,
        "embedding": embedding
    }
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

# --- 新增功能：上傳錄音到 ElevenLabs 進行訓練 ---
def train_voice_sample(audio_bytes):
    """將錄音檔傳送給 ElevenLabs 增加訓練數據"""
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/edit"
        headers = {"xi-api-key": elevenlabs_key}
        
        # 準備檔案
        files = {
            'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')
        }
        # 這裡不改變名字，只上傳檔案
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
                
                system_instruction = f"""
                {persona_summary}
                【相關的深層記憶】：{relevant_memory}
                請務必使用我對【{sel_role}】的專屬稱呼（例如小名）。語氣要自然，包含呼吸感。
                """
                recent_history = st.session_state.chat_history[-6:] 
                msgs = [{"role": "system", "content": system_instruction}] + recent_history
                msgs.append({"role": "user", "content": user_text})

                res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                ai_text = res.choices[0].message.content

                st.session_state.chat_history.append({"role": "user", "content": user_text})
                st.session_state.chat_history.append({"role": "assistant", "content": ai_text})

                # 聲音參數優化 (更感性)
                tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                data = {
                    "text": ai_text, 
                    "model_id": "eleven_multilingual_v2", 
                    "voice_settings": {"stability": 0.4, "similarity_boost": 0.65} # 參數優化
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
    # === 管理員後台 (三大功能區) ===
    st.success("🔓 管理員模式")
    if st.button("登出"):
        st.session_state.is_admin = False
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📝 基礎人設 (檔案)", "🧠 回憶補完 (訪談)", "🎙️ 聲音特訓 (錄音)"])

    # --- TAB 1: 基礎檔案上傳 (原有功能) ---
    with tab1:
        st.caption("一次性上傳大量對話紀錄")
        c1, c2 = st.columns(2)
        with c1: t_role = st.selectbox("對象", ["妻子", "丈夫", "兒子", "女兒", "朋友"], key="tr")
        with c2: nickname = st.text_input("您對他/她的專屬暱稱", placeholder="例如：寶貝、小胖", key="nk")
        
        up_file = st.file_uploader(f"上傳與【{t_role}】的紀錄", type="txt")

        if st.button("✨ 生成基礎人設"):
            if up_file:
                with st.spinner("分析中..."):
                    raw = up_file.read().decode("utf-8")
                    prompt = f"分析對話。我對{t_role}的說話風格。專屬暱稱是「{nickname}」。請生成System Prompt，強調必須使用暱稱稱呼對方。資料：{raw[-20000:]}"
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    save_persona_summary(t_role, res.choices[0].message.content)
                    st.success("基礎人設已更新！")

    # --- TAB 2: 回憶補完計畫 (新功能) ---
    with tab2:
        st.caption("透過回答問題，補充生活細節，讓 AI 更懂你們")
        
        # 1. 選擇角色
        q_role = st.selectbox("您想補充關於誰的回憶？", list(INTERVIEW_QUESTIONS.keys()), key="q_role")
        
        # 2. 隨機或選擇題目
        q_list = INTERVIEW_QUESTIONS.get(q_role, ["請分享一個關於你們的回憶"])
        question = st.selectbox("請選擇一個話題來回答：", q_list)
        
        st.markdown(f'<div class="question-card"><b>APP 提問：</b><br>{question}</div>', unsafe_allow_html=True)
        
        # 3. 回答區 (可錄音或打字)
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
                # 組合問題與答案存入
                full_memory = f"【關於{question}】：{answer_content}"
                save_memory_fragment(q_role, full_memory)
                st.success("已存入深層記憶！AI 之後會記得這件事。")
                st.balloons()
            else:
                st.warning("請先輸入或錄製回答")

    # --- TAB 3: 聲音特訓室 (新功能) ---
    with tab3:
        st.caption("覺得聲音不像？在這裡多錄幾段不同情緒的聲音上傳，訓練 AI。")
        
        st.info("💡 建議錄製內容：\n1. 用開心的語氣叫喚親人的名字。\n2. 講一段安慰人的話。\n3. 大笑或激動的語氣。")
        
        train_audio = st.audio_input("錄製訓練樣本 (約 1 分鐘)", key="train_rec")
        
        if train_audio:
            if st.button("🚀 上傳並微調模型"):
                with st.spinner("正在傳送至 ElevenLabs 進行微調..."):
                    success = train_voice_sample(train_audio)
                    if success:
                        st.success("訓練成功！請等待幾分鐘讓模型更新，聲音會變得更自然。")
                    else:
                        st.error("上傳失敗，請檢查網路或 API Key 權限。")