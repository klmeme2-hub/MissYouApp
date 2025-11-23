import streamlit as st
import requests
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder # 引入錄音套件
import io

# --- 頁面設定 ---
st.set_page_config(page_title="想念 - 語音對話版", page_icon="🤍")
st.title("🤍 想念 (Miss You)")
st.subheader("第三階段：裝上耳朵")

# --- 側邊欄：核心設定 ---
with st.sidebar:
    st.header("🔑 金鑰設定")
    elevenlabs_key = st.text_input("ElevenLabs API Key", type="password")
    openai_key = st.text_input("OpenAI API Key", type="password")
    
    st.divider()
    st.header("🧠 靈魂設定")
    default_prompt = """你現在扮演我的父親。
你的名字叫張志明。
個性：溫柔、沈穩，偶爾會講冷笑話。
說話習慣：喜歡用「傻孩子」、「對吧」結尾。
請用溫暖、像父親一樣的口吻回覆我。"""
    system_prompt = st.text_area("設定人設：", default_prompt, height=250)

    # 聲音 ID 設定
    st.divider()
    voice_id_input = st.text_input("ElevenLabs Voice ID", "")

# --- 初始化 OpenAI ---
client = None
if openai_key:
    client = OpenAI(api_key=openai_key)

# --- 初始化聊天紀錄 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 顯示歷史對話 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 核心邏輯區 ---
# 我們定義一個處理對話的函數，無論是打字還是語音都走這裡
def process_conversation(user_text):
    # 1. 顯示並儲存使用者的話
    with st.chat_message("user"):
        st.markdown(user_text)
    st.session_state.messages.append({"role": "user", "content": user_text})

    # 2. AI 思考 & 說話
    if client and elevenlabs_key and voice_id_input:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            try:
                # 組合對話紀錄
                messages_for_ai = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                
                # 呼叫 GPT
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=messages_for_ai
                )
                ai_text = response.choices[0].message.content
                message_placeholder.markdown(ai_text)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})

                # 呼叫 ElevenLabs TTS
                tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id_input}"
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
                else:
                    st.error(f"聲音生成失敗: {tts_response.text}")

            except Exception as e:
                st.error(f"發生錯誤: {e}")
    else:
        st.error("請檢查 Key 是否都已填寫")

# --- 輸入區域 (語音 + 文字) ---
st.divider()
col1, col2 = st.columns([1, 4])

with col1:
    st.write("🎙️ 按下說話：")
    # 錄音按鈕
    audio = mic_recorder(
        start_prompt="開始錄音",
        stop_prompt="結束並發送", 
        key='recorder'
    )

with col2:
    # 傳統文字輸入框
    text_input = st.chat_input("或用打字的...")

# --- 處理輸入邏輯 ---

# 情況 A: 使用者用了錄音
if audio:
    # 為了避免重複發送，我們檢查這個音檔是否剛被處理過
    if "last_audio_id" not in st.session_state:
        st.session_state.last_audio_id = None
    
    # 只有當這是新的錄音時才執行
    if audio['id'] != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio['id']
        
        if client:
            with st.spinner("正在聽你說話..."):
                # 將錄音資料轉為 OpenAI Whisper 能讀的格式
                audio_bytes = audio['bytes']
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = "voice.mp3" # 偽裝成檔案
                
                # 呼叫 Whisper (語音轉文字)
                try:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                    user_voice_text = transcript.text
                    # 執行對話流程
                    process_conversation(user_voice_text)
                    
                except Exception as e:
                    st.error(f"聽不懂你的聲音: {e}")

# 情況 B: 使用者用了打字
if text_input:
    process_conversation(text_input)