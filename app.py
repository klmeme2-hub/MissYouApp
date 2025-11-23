import streamlit as st
import requests
from openai import OpenAI
import os

# --- 1. 頁面設定 (隱藏預設選單) ---
st.set_page_config(page_title="想念", page_icon="🤍", layout="centered")

# 隱藏 Streamlit 預設的右上角選單和下方 Footer，讓介面更乾淨
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stApp {
    background-color: #f9f9f9;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. 讀取金鑰 ---
if "OPENAI_API_KEY" in st.secrets:
    openai_key = st.secrets["OPENAI_API_KEY"]
else:
    openai_key = st.sidebar.text_input("OpenAI Key", type="password")

if "ELEVENLABS_API_KEY" in st.secrets:
    elevenlabs_key = st.secrets["ELEVENLABS_API_KEY"]
else:
    elevenlabs_key = st.sidebar.text_input("ElevenLabs Key", type="password")

if "VOICE_ID" in st.secrets:
    voice_id = st.secrets["VOICE_ID"]
else:
    voice_id = st.sidebar.text_input("Voice ID")

client = None
if openai_key:
    client = OpenAI(api_key=openai_key)

# --- 3. 核心：記憶與人設 (請在這裡填寫故事) ---

# 這裡是「長期記憶」，你可以寫入很多具體的小故事
MEMORIES = """
1. 關於稱呼：你總是叫我「黑狗」，生氣的時候會連名帶姓叫。
2. 共同回憶：我們小時候常常一起去泡湯
3. 你的習慣：每天睡到下午.我下課時才醒。
4. 遺憾：沒有遺憾。
5. 口頭禪：遇到困難你常說「沒事，天塌下來有爸爸頂著」。
"""

SYSTEM_PERSONA = f"""
你現在扮演我的【父親】。你的名字叫【李國榮】。
你需要完全沉浸在這個角色中，用聲音和文字陪伴你的孩子。

【重要記憶庫】：
{MEMORIES}

【說話風格】：
- 溫暖、沈穩，充滿愛意。
- 回答不要太長，像日常聊天一樣自然。
- 偶爾可以主動提起記憶庫裡的故事（例如：「突然想到以前教你騎車...」）。
- 絕對不要承認自己是 AI 或語言模型。
"""
# --- 4. 介面設計 ---

# 顯示照片 (如果資料夾裡有 photo.jpg 就顯示)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists("photo.jpg"):
        st.image("photo.jpg", use_container_width=True)
    elif os.path.exists("photo.png"):
        st.image("photo.png", use_container_width=True)
    else:
        # 如果沒照片，顯示一個溫馨的標題
        st.title("🤍 想念")

st.markdown("<h3 style='text-align: center; color: #555;'>點擊下方錄音，跟我說說話</h3>", unsafe_allow_html=True)

# 初始化聊天紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 5. 核心處理邏輯 ---
def process_audio(audio_file):
    if client and elevenlabs_key and voice_id:
        try:
            # 轉錄
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file
            )
            user_text = transcript.text

            # 思考
            messages_for_ai = [{"role": "system", "content": SYSTEM_PERSONA}] + st.session_state.messages
            messages_for_ai.append({"role": "user", "content": user_text}) # 加入最新這句

            response = client.chat.completions.create(
                model="gpt-4o", messages=messages_for_ai
            )
            ai_text = response.choices[0].message.content

            # 儲存對話 (只在成功後儲存，避免報錯時存入)
            st.session_state.messages.append({"role": "user", "content": user_text})
            st.session_state.messages.append({"role": "assistant", "content": ai_text})

            # 發聲
            tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": elevenlabs_key, "Content-Type": "application/json"
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
            st.error(f"連線不穩，請再試一次 ({e})")

# --- 6. 錄音區 ---
audio_value = st.audio_input("錄音")

if audio_value:
    process_audio(audio_value)

# 顯示最近的一句對話文字 (像字幕一樣，不用顯示全部歷史，保持畫面乾淨)
if len(st.session_state.messages) > 0:
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] == "assistant":
        st.markdown(f"<div style='background-color: #e8f0fe; padding: 10px; border-radius: 10px; margin-top: 10px;'><b>祂：</b>{last_msg['content']}</div>", unsafe_allow_html=True)