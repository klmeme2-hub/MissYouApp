import streamlit as st
import requests
from openai import OpenAI
import os

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="想念 - 數位人格預備系統", page_icon="🤍", layout="centered")

# 隱藏不需要的選單，保持介面乾淨
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stApp {background-color: #fafafa;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. 讀取金鑰 (從 Secrets 或側邊欄) ---
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

# --- 3. 初始化「多重人格」資料庫 ---
# 在真實產品中，這些資料會存在雲端資料庫。
# 在 MVP 中，我們先存在 Session 裡，會員設定完後可以複製保存。

if "personas" not in st.session_state:
    st.session_state.personas = {
        "妻子": """你現在扮演我的丈夫。請用溫柔、依賴的語氣對我說話。
        關鍵記憶：結婚紀念日是 10/15，喜歡叫我「寶貝」。""",
        
        "兒子": """你現在扮演我的父親。請用慈祥但帶點嚴厲的長輩口吻。
        關鍵記憶：希望你要腳踏實地工作，不要太晚睡。""",
        
        "朋友": """你現在扮演我的死黨。語氣要輕鬆、幽默，可以開玩笑。
        關鍵記憶：我們以前常去打籃球，喜歡互虧。"""
    }

# --- 4. 介面分流：建立模式 vs 對話模式 ---
st.title("🤍 想念 (Miss You)")
st.caption("數位人格傳承系統")

tab1, tab2 = st.tabs(["⚙️ 會員設定 (建立靈魂)", "💬 親友互動 (預覽對話)"])

# ==========================================
# TAB 1: 會員設定區 (Soul Studio)
# 會員在這裡上傳不同對象的對話紀錄
# ==========================================
with tab1:
    st.header("1. 建立您的數位分身")
    st.info("請針對不同的親友關係，分別訓練 AI 的說話方式。")

    # 選擇要訓練的對象
    target_role = st.selectbox("您想設定對誰的說話語氣？", ["妻子", "兒子", "朋友", "其他"], key="train_role")
    
    # 上傳該對象的 LINE 紀錄
    uploaded_file = st.file_uploader(f"上傳您與【{target_role}】的 LINE 紀錄 (.txt)", type="txt", key="uploader")
    
    # 輸入會員在對話中的名字 (讓 AI 知道誰是主人)
    member_name = st.text_input("您在對話紀錄裡的名字是？", placeholder="例如：Ken、爸爸", key="member_name")

    if st.button("開始分析並生成人設"):
        if not uploaded_file or not member_name or not client:
            st.error("請確認檔案已上傳、名字已輸入，且 API Key 正確。")
        else:
            with st.spinner(f"AI 正在學習您對【{target_role}】的說話方式..."):
                try:
                    # 讀取檔案 (取最後 30,000 字)
                    string_data = uploaded_file.read().decode("utf-8")
                    slice_data = string_data[-30000:]

                    # 靈魂萃取 Prompt
                    analysis_prompt = f"""
                    這是一段 LINE 對話紀錄。
                    其中名為「{member_name}」的人是【會員本人】。
                    對話的另一方是會員的【{target_role}】。

                    請分析【會員本人】在這段關係中的：
                    1. 說話語氣（是對平輩、晚輩還是伴侶？）。
                    2. 特殊的暱稱或口頭禪。
                    3. 共同的關鍵回憶或關注點。

                    最後，請生成一段「System Prompt」，格式如下：
                    "你現在扮演【會員本人】。正在與你的【{target_role}】對話。
                    語氣指導：...
                    關鍵記憶：..."
                    
                    對話內容：
                    {slice_data}
                    """

                    response = client.chat.completions.create(
                        model="gpt-4o", # 分析用強模型
                        messages=[{"role": "user", "content": analysis_prompt}]
                    )
                    
                    # 更新該角色的人設
                    new_persona = response.choices[0].message.content
                    st.session_state.personas[target_role] = new_persona
                    st.success(f"成功！已建立對【{target_role}】的專屬人格。")
                    
                except Exception as e:
                    st.error(f"分析失敗: {e}")

    # 顯示目前所有的人設 (讓會員檢查)
    with st.expander("檢視目前的靈魂設定 (可手動修改)"):
        for role, persona_text in st.session_state.personas.items():
            st.text_area(f"對【{role}】的人設：", value=persona_text, height=150, key=f"text_{role}")

# ==========================================
# TAB 2: 親友互動區 (Interaction Mode)
# 未來親友打開 APP 主要看到的介面
# ==========================================
with tab2:
    st.header("2. 跨越時空的對話")
    
    # 1. 身分選擇 (關鍵功能)
    selected_identity = st.selectbox("請問您是我的...?", list(st.session_state.personas.keys()), key="user_identity")
    
    # 載入對應人設
    current_persona = st.session_state.personas[selected_identity]
    
    # 顯示照片 (如果有)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("photo.jpg"):
            st.image("photo.jpg", use_container_width=True)
        else:
            st.write("🤍")

    st.markdown(f"<p style='text-align: center;'>正在使用【{selected_identity}】模式與您對話</p>", unsafe_allow_html=True)

    # 初始化對話紀錄
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 處理音訊
    def process_audio(audio_file):
        try:
            # A. 轉錄
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file
            )
            user_text = transcript.text

            # B. 思考 (注入當前選定的人設)
            # 取最近 10 句對話
            recent_history = st.session_state.chat_history[-10:] 
            
            messages_for_ai = [{"role": "system", "content": current_persona}] + recent_history
            messages_for_ai.append({"role": "user", "content": user_text})
            
            # 額外叮嚀 (省錢 + 自然)
            messages_for_ai.append({"role": "system", "content": "請保持回答簡短(50字內)，語氣自然像家人。"})

            response = client.chat.completions.create(
                model="gpt-4o-mini", # 對話用省錢模型
                messages=messages_for_ai
            )
            ai_text = response.choices[0].message.content

            # 存紀錄
            st.session_state.chat_history.append({"role": "user", "content": user_text})
            st.session_state.chat_history.append({"role": "assistant", "content": ai_text})

            # C. 發聲
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
            st.error(f"Error: {e}")

    # 錄音按鈕
    audio_val = st.audio_input("開始說話...", key="chat_recorder")
    if audio_val:
        process_audio(audio_val)

    # 顯示字幕
    if len(st.session_state.chat_history) > 0:
        last_msg = st.session_state.chat_history[-1]
        if last_msg["role"] == "assistant":
            st.info(f"祂說：{last_msg['content']}")