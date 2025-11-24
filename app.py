import streamlit as st
import requests
from openai import OpenAI
import os

# --- 1. 頁面設定 ---
st.set_page_config(page_title="想念", page_icon="🤍", layout="centered")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stApp {background-color: #f9f9f9;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. 讀取金鑰 ---
if "OPENAI_API_KEY" in st.secrets:
    openai_key = st.secrets["OPENAI_API_KEY"]
else:
    st.error("請先在 Streamlit Secrets 設定 API Key")
    st.stop()

if "ELEVENLABS_API_KEY" in st.secrets:
    elevenlabs_key = st.secrets["ELEVENLABS_API_KEY"]
else:
    st.stop()

if "VOICE_ID" in st.secrets:
    voice_id = st.secrets["VOICE_ID"]
else:
    st.stop()

client = OpenAI(api_key=openai_key)

# --- 3. 記憶與人設 (加入省錢指令) ---
# 請記得填回你自己的回憶故事
MEMORIES = """
1. 關於稱呼：你總是叫我「黑狗」，生氣的時候會連名帶姓叫。
2. 共同回憶：我們小時候常常一起去泡湯
3. 你的習慣：每天睡到下午.我下課時才醒。
4. 遺憾：沒有遺憾。
5. 口頭禪：遇到困難你常說「個性決定命運」。
"""

SYSTEM_PERSONA = f"""
你現在扮演我的【父親】。你的名字叫【李國榮】。
你需要完全沉浸在這個角色中，用聲音和文字陪伴你的孩子。

【重要】：
1. 你的回應必須簡短，盡量控制在 50 字以內，這很關鍵。
2. 說話像家人一樣口語，不要長篇大論。
3. 記憶庫：{MEMORIES}
"""

# --- 4. 介面 ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists("photo.jpg"):
        st.image("photo.jpg", use_container_width=True)
    else:
        st.title("🤍 想念")

st.markdown("<h3 style='text-align: center; color: #555;'>點擊下方錄音</h3>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. 核心處理 (省錢優化版) ---
def process_audio(audio_file):
    try:
        # 1. 轉錄 (Whisper Model) - 價格很便宜，不用省
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
        user_text = transcript.text

        # 2. 思考 (換成 gpt-4o-mini + 限制記憶長度)
        # 只取最近 10 條對話紀錄，避免 Token 爆炸
        recent_history = st.session_state.messages[-10:] 
        
        messages_for_ai = [{"role": "system", "content": SYSTEM_PERSONA}] + recent_history
        messages_for_ai.append({"role": "user", "content": user_text})

        response = client.chat.completions.create(
            model="gpt-4o-mini", # <--- 這裡換成了便宜 20 倍的模型
            messages=messages_for_ai
        )
        ai_text = response.choices[0].message.content

        # 寫入 Session State
        st.session_state.messages.append({"role": "user", "content": user_text})
        st.session_state.messages.append({"role": "assistant", "content": ai_text})

        # 3. 發聲 (ElevenLabs)
        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": elevenlabs_key, 
            "Content-Type": "application/json"
        }
        data = {
            "text": ai_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
        }
        tts_response = requests.post(tts_url, json=data, headers=headers)
        
        if tts_response.status_code == 200:
            st.audio(tts_response.content, format="audio/mp3", autoplay=True)
        
    except Exception as e:
        st.error(f"系統忙碌中: {e}")

# --- 6. 錄音 ---
audio_value = st.audio_input("錄音")
if audio_value:
    process_audio(audio_value)

# 顯示最近對話
if len(st.session_state.messages) > 0:
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] == "assistant":
        st.markdown(f"<div style='background-color: #e8f0fe; padding: 10px; border-radius: 10px; margin-top: 10px;'><b>祂：</b>{last_msg['content']}</div>", unsafe_allow_html=True)