import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import os

# --- 1. 頁面設定 ---
st.set_page_config(page_title="想念 - 雲端永存版", page_icon="🤍", layout="centered")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stApp {background-color: #fafafa;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. 讀取金鑰 & 初始化 Supabase ---
# 檢查 Secrets 是否都設定好了
required_secrets = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY", "VOICE_ID", "SUPABASE_URL", "SUPABASE_KEY"]
missing_secrets = [key for key in required_secrets if key not in st.secrets]

if missing_secrets:
    st.error(f"缺少設定金鑰，請去 Secrets 補上: {', '.join(missing_secrets)}")
    st.stop()

openai_key = st.secrets["OPENAI_API_KEY"]
elevenlabs_key = st.secrets["ELEVENLABS_API_KEY"]
voice_id = st.secrets["VOICE_ID"]
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

client = OpenAI(api_key=openai_key)

# 初始化 Supabase 連線
@st.cache_resource
def init_supabase():
    return create_client(supabase_url, supabase_key)

supabase = init_supabase()

# --- 3. 定義存取資料庫的函數 (Helper Functions) ---

def save_persona_to_cloud(role, content):
    """將人設儲存到 Supabase"""
    try:
        data = {"role": role, "content": content}
        # 使用 upsert，如果 role 存在就更新，不存在就新增
        supabase.table("personas").upsert(data).execute()
        return True
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        return False

def load_all_roles_from_cloud():
    """從 Supabase 讀取所有已設定的角色"""
    try:
        response = supabase.table("personas").select("role").execute()
        # 回傳一個列表，例如 ['妻子', '兒子']
        return [item['role'] for item in response.data]
    except Exception as e:
        st.error(f"讀取角色失敗: {e}")
        return []

def load_persona_content(role):
    """根據角色讀取具體內容"""
    try:
        response = supabase.table("personas").select("content").eq("role", role).execute()
        if response.data:
            return response.data[0]['content']
        return None
    except Exception as e:
        return None

# --- 4. 介面邏輯 ---

st.title("🤍 想念 (Miss You)")
st.caption("數位人格傳承系統 - Cloud Ver.")

tab1, tab2 = st.tabs(["⚙️ 會員設定 (寫入)", "💬 親友互動 (讀取)"])

# ==========================================
# TAB 1: 會員設定區 (寫入雲端)
# ==========================================
with tab1:
    st.header("1. 建立數位分身")
    st.info("設定完成後，資料將永久儲存在雲端資料庫。")

    target_role = st.selectbox("設定對象身分", ["妻子", "兒子", "女兒", "朋友", "孫子"], key="train_role")
    member_name = st.text_input("您在對話中的名字", placeholder="例如：爸爸", key="member_name")
    uploaded_file = st.file_uploader(f"上傳與【{target_role}】的 LINE 紀錄 (.txt)", type="txt")

    if st.button("生成並儲存到雲端"):
        if not uploaded_file or not member_name:
            st.error("請上傳檔案並輸入名字")
        else:
            with st.spinner("AI 分析中，並同步寫入資料庫..."):
                try:
                    # 1. AI 分析
                    string_data = uploaded_file.read().decode("utf-8")[-30000:]
                    analysis_prompt = f"""
                    請分析以下 LINE 對話紀錄。
                    主角：{member_name} (會員本人)
                    對象：{target_role}
                    
                    請生成一段 System Prompt，包含：
                    1. 語氣指導 (對{target_role}說話的口氣)
                    2. 關鍵記憶與口頭禪
                    3. 限制：回答簡短(50字內)，不承認是AI。
                    
                    對話內容：
                    {string_data}
                    """
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": analysis_prompt}]
                    )
                    persona_content = response.choices[0].message.content
                    
                    # 2. 存入 Supabase
                    if save_persona_to_cloud(target_role, persona_content):
                        st.success(f"成功！對【{target_role}】的人設已永久保存。")
                        # 強制刷新頁面，讓 Tab 2 能讀到新角色
                        st.rerun() 
                        
                except Exception as e:
                    st.error(f"發生錯誤: {e}")

    # 檢視資料庫內容
    with st.expander("查看雲端資料庫目前的狀態"):
        try:
            db_data = supabase.table("personas").select("*").execute()
            st.dataframe(db_data.data)
        except:
            st.write("目前沒有資料")

# ==========================================
# TAB 2: 親友互動區 (從雲端讀取)
# ==========================================
with tab2:
    st.header("2. 跨越時空的對話")
    
    # 1. 從雲端抓取有哪些角色可用
    available_roles = load_all_roles_from_cloud()
    
    if not available_roles:
        st.warning("目前雲端沒有任何資料，請先到「會員設定」建立人設。")
    else:
        selected_identity = st.selectbox("我是...", available_roles, key="user_identity")
        
        # 2. 抓取該角色的靈魂
        current_persona = load_persona_content(selected_identity)
        
        # 顯示照片
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if os.path.exists("photo.jpg"):
                st.image("photo.jpg", use_container_width=True)
            else:
                st.write("🤍")

        # 3. 對話功能
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        def process_audio(audio_file):
            try:
                # 轉錄
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file
                )
                user_text = transcript.text

                # 思考
                recent_history = st.session_state.chat_history[-10:] 
                messages_for_ai = [{"role": "system", "content": current_persona}] + recent_history
                messages_for_ai.append({"role": "user", "content": user_text})
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=messages_for_ai
                )
                ai_text = response.choices[0].message.content

                st.session_state.chat_history.append({"role": "user", "content": user_text})
                st.session_state.chat_history.append({"role": "assistant", "content": ai_text})

                # 發聲
                tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
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

        audio_val = st.audio_input("開始說話...", key="chat_recorder")
        if audio_val:
            process_audio(audio_val)

        if len(st.session_state.chat_history) > 0:
            last_msg = st.session_state.chat_history[-1]
            if last_msg["role"] == "assistant":
                st.info(f"祂說：{last_msg['content']}")