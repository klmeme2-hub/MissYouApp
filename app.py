import streamlit as st
import requests
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# --- 1. 頁面設定 ---
st.set_page_config(page_title="想念", page_icon="🤍", layout="centered")

# --- 2. 讀取金鑰 (從雲端保險箱) ---
# 這裡會自動去抓你在 Streamlit 後台設定的 Secrets
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

# --- 3. 初始化 OpenAI ---
client = None
if openai_key:
    client = OpenAI(api_key=openai_key)

# --- 4. 定義「靈魂」 (請在這裡修改你親人的設定) ---
# 把這裡的文字改成你想念的那個人的特徵，這段文字使用者看不到，是給 AI 看的
SYSTEM_PERSONA = """
你現在扮演我的【父親】。
你的名字叫【李國榮】。
關係：我是你的孩子。
語氣風格：
- 說話溫暖、沈穩，語速中等。
- 喜歡用「傻孩子」、「別太累了」來關心我。
- 遇到我難過時，你會講一些小時候帶我去泡溫泉的回憶來安慰我。
- 不需要太過客套，要像家人一樣自然。
記憶庫：
1. 我們家以前養過一隻狗叫「小狗」。
2. 你最拿手的一道菜是「三杯雞」。
3. 你的願望是希望我能快樂健康，不要為了寫功課.考試壞了身體。
請一定要維持這個角色，不要承認自己是 AI。
"""

# --- 5. 介面設計 (極簡化) ---
st.title("🤍 想念")
st.write("按住錄音，說說你的心裡話...")

# 初始化聊天紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示歷史對話
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. 核心處理函數 ---
def process_conversation(user_text):
    # 顯示使用者文字
    with st.chat_message("user"):
        st.markdown(user_text)
    st.session_state.messages.append({"role": "user", "content": user_text})

    if client and elevenlabs_key and voice_id:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                # 組合 Prompt
                messages_for_ai = [{"role": "system", "content": SYSTEM_PERSONA}] + st.session_state.messages
                
                # AI 思考
                with st.spinner("..."): # 顯示簡單的等待符號
                    response = client.chat.completions.create(
                        model="gpt-4o", 
                        messages=messages_for_ai
                    )
                    ai_text = response.choices[0].message.content
                    message_placeholder.markdown(ai_text)
                    st.session_state.messages.append({"role": "assistant", "content": ai_text})

                # AI 說話
                # 這裡不顯示 Spinner，讓聲音自然出現
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
                st.error(f"發生錯誤: {e}")
    else:
        st.warning("系統尚未設定完成，請聯絡開發者。")

# --- 7. 輸入區 (錄音優先) ---
st.divider()

# 調整按鈕置中
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    audio = mic_recorder(
        start_prompt="🎙️ 按此說話",
        stop_prompt="⏹️ 說完了", 
        key='recorder',
        format="mp3"
    )

# 處理錄音
if audio:
    if "last_audio_id" not in st.session_state:
        st.session_state.last_audio_id = None
    
    if audio['id'] != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio['id']
        
        if client:
            audio_file = io.BytesIO(audio['bytes'])
            audio_file.name = "voice.mp3"
            try:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file
                )
                process_conversation(transcript.text)
            except Exception as e:
                st.error("聽不清楚，請再說一次")

# 隱藏的文字輸入框 (為了排版美觀，放在最下面Expander裡，以備不時之需)
with st.expander("或者使用文字輸入"):
    text_input = st.chat_input("輸入文字...")
    if text_input:
        process_conversation(text_input)