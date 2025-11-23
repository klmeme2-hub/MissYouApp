import streamlit as st
import requests
from openai import OpenAI

# --- 1. 頁面設定 ---
st.set_page_config(page_title="想念", page_icon="🤍", layout="centered")

# --- 2. 讀取金鑰 (從雲端保險箱) ---
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

# --- 5. 介面設計 ---
st.title("🤍 想念")
st.caption("請點擊下方麥克風，錄完後點擊停止發送")

# 初始化聊天紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示歷史對話
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. 核心處理函數 ---
def process_audio(audio_file):
    if client and elevenlabs_key and voice_id:
        try:
            # 1. 轉錄語音 (Whisper)
            with st.spinner("聽取中..."):
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
                user_text = transcript.text

            # 顯示使用者文字
            with st.chat_message("user"):
                st.markdown(user_text)
            st.session_state.messages.append({"role": "user", "content": user_text})

            # 2. AI 思考 (GPT)
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                messages_for_ai = [{"role": "system", "content": SYSTEM_PERSONA}] + st.session_state.messages
                
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=messages_for_ai
                )
                ai_text = response.choices[0].message.content
                message_placeholder.markdown(ai_text)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})

            # 3. AI 說話 (ElevenLabs)
            # 這裡不顯示轉圈圈，讓聲音在背景生成後自動播放
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
        st.warning("系統尚未設定完成。")

# --- 7. 輸入區 (官方原生錄音) ---
st.divider()

# 這是最新的官方錄音元件
audio_value = st.audio_input("按此錄音")

# 如果有錄音，且這個錄音還沒被處理過 (避免重複發送)
if audio_value:
    # 簡單的防重複機制：檢查是否跟上一次處理的內容一樣（這裡用記憶體位址簡單判斷）
    # 在實際操作中，st.audio_input 每次錄完會觸發一次 rerun
    
    # 直接處理
    process_audio(audio_value)