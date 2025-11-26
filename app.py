import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import os

# --- 1. 頁面設定 ---
st.set_page_config(page_title="想念", page_icon="🤍", layout="centered")

# --- 2. CSS 美化 (含下拉選單修復) ---
custom_css = """
<style>
    /* 全局設定：強制淺色背景與深色文字 */
    .stApp {
        background-color: #F7F9FB;
        color: #333333;
    }
    
    /* 強制所有文字變深灰 */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {
        color: #333333 !important;
    }

    /* 關鍵修復：下拉選單 (Selectbox) 的選項文字顏色 */
    div[data-baseweb="select"] > div {
        color: #333333 !important;
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="popover"] li {
        color: #333333 !important; /* 選項列表的文字 */
        background-color: #FFFFFF !important;
    }
    /* 選項滑鼠懸停時的效果 */
    div[data-baseweb="popover"] li:hover {
        background-color: #E3F2FD !important;
    }

    /* 按鈕美化 */
    .stButton>button {
        background-color: #4A90E2;
        color: white !important;
        border-radius: 12px;
        border: none;
        padding: 10px 20px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #357ABD;
        transform: scale(1.02);
    }

    /* AI 對話氣泡 */
    .ai-bubble {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #4A90E2;
        margin-top: 15px;
        margin-bottom: 15px;
        font-size: 16px;
        line-height: 1.6;
        color: #333333;
    }

    /* 隱藏預設選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 3. 讀取金鑰 & 初始化 ---
if "SUPABASE_URL" not in st.secrets or "ADMIN_PASSWORD" not in st.secrets:
    st.error("⚠️ 請先在 Secrets 設定 SUPABASE 資訊與 ADMIN_PASSWORD")
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

# --- 4. 資料庫操作函數 ---
def save_persona_to_cloud(role, content):
    try:
        data = {"role": role, "content": content}
        supabase.table("personas").upsert(data).execute()
        return True
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        return False

def load_all_roles_from_cloud():
    try:
        response = supabase.table("personas").select("role").execute()
        return [item['role'] for item in response.data]
    except Exception as e:
        return []

def load_persona_content(role):
    try:
        response = supabase.table("personas").select("content").eq("role", role).execute()
        if response.data:
            return response.data[0]['content']
        return None
    except Exception as e:
        return None

# --- 5. 權限管理邏輯 (Session State) ---
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

def check_password():
    """驗證密碼"""
    if st.session_state.password_input == admin_password:
        st.session_state.is_admin = True
        st.session_state.password_input = "" # 清空輸入框
    else:
        st.error("密碼錯誤")

# --- 6. 主介面 ---

st.title("🤍 想念")

# 如果還沒登入管理員，只顯示「親友互動」介面，但在最下方留一個「管理員登入」的入口
if not st.session_state.is_admin:
    # === 親友模式 (預設) ===
    st.caption("跨越時空的數位對話")
    
    # 直接載入互動介面 (不顯示 Tabs)
    available_roles = load_all_roles_from_cloud()
    
    if not available_roles:
        st.info("☁️ 目前尚未建立任何數位人格。請會員登入後台進行設定。")
    else:
        col_sel, col_pic = st.columns([2, 1])
        with col_sel:
            st.markdown("#### 👋 您好，請問您是我的...？")
            selected_identity = st.selectbox("請選擇您的身分", available_roles, key="user_identity_public", label_visibility="collapsed")
            current_persona = load_persona_content(selected_identity)
            if current_persona:
                st.success(f"已連結：{selected_identity}模式")

        with col_pic:
            if os.path.exists("photo.jpg"):
                st.image("photo.jpg", use_container_width=True)
            else:
                st.markdown("<div style='font-size:50px; text-align:center;'>👤</div>", unsafe_allow_html=True)

        # 對話邏輯
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        def process_audio_public(audio_file):
            try:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file
                )
                user_text = transcript.text

                recent_history = st.session_state.chat_history[-10:] 
                messages_for_ai = [{"role": "system", "content": current_persona}] + recent_history
                messages_for_ai.append({"role": "user", "content": user_text})
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini", messages=messages_for_ai
                )
                ai_text = response.choices[0].message.content

                st.session_state.chat_history.append({"role": "user", "content": user_text})
                st.session_state.chat_history.append({"role": "assistant", "content": ai_text})

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

        st.divider()
        st.markdown("##### 🎙️ 按下錄音跟我說話：")
        audio_val = st.audio_input("錄音", key="public_recorder")
        if audio_val and current_persona:
            process_audio_public(audio_val)

        if len(st.session_state.chat_history) > 0:
            last_msg = st.session_state.chat_history[-1]
            if last_msg["role"] == "assistant":
                st.markdown(f"""<div class="ai-bubble"><b>祂說：</b><br>{last_msg['content']}</div>""", unsafe_allow_html=True)

    # --- 頁尾：管理員登入區 ---
    st.divider()
    with st.expander("🔒 會員登入 (建立/修改人設)"):
        st.text_input("輸入管理密碼", type="password", key="password_input", on_change=check_password)

else:
    # === 管理員模式 (登入後) ===
    st.success("🔓 已登入管理員模式")
    if st.button("登出"):
        st.session_state.is_admin = False
        st.rerun()

    tab1, tab2 = st.tabs(["⚙️ 靈魂刻錄 (後台)", "💬 對話測試 (前台)"])

    # TAB 1: 後台設定
    with tab1:
        with st.container(border=True):
            st.subheader("📝 建立/更新數位分身")
            col1, col2 = st.columns(2)
            with col1:
                target_role = st.selectbox("設定對象身分", ["妻子", "丈夫", "兒子", "女兒", "朋友", "孫子"], key="train_role")
            with col2:
                member_name = st.text_input("您在對話中的名字", placeholder="例如：爸爸", key="member_name")
            
            uploaded_file = st.file_uploader(f"上傳與【{target_role}】的 LINE 紀錄 (.txt)", type="txt")

            if st.button("✨ 開始分析並儲存", use_container_width=True):
                if not uploaded_file or not member_name:
                    st.warning("請完整填寫資訊")
                else:
                    with st.spinner("AI 分析中..."):
                        try:
                            string_data = uploaded_file.read().decode("utf-8")[-30000:]
                            analysis_prompt = f"""
                            請分析以下 LINE 對話紀錄。主角：{member_name}，對象：{target_role}。
                            請生成 System Prompt，包含語氣指導、關鍵記憶。限制：回答簡短(50字內)，語氣自然。
                            資料：{string_data}
                            """
                            response = client.chat.completions.create(
                                model="gpt-4o", messages=[{"role": "user", "content": analysis_prompt}]
                            )
                            content = response.choices[0].message.content
                            if save_persona_to_cloud(target_role, content):
                                st.success(f"已儲存對【{target_role}】的人設！")
                                st.balloons()
                        except Exception as e:
                            st.error(f"錯誤: {e}")

        # 查看資料庫
        with st.expander("查看雲端資料狀態"):
            try:
                data = supabase.table("personas").select("role", "created_at").execute()
                st.table(data.data)
            except:
                pass

    # TAB 2: 前台預覽 (跟親友看到的一樣)
    with tab2:
        st.info("這是預覽親友會看到的畫面")
        # 這裡重複一次對話邏輯，或是為了代碼簡潔，我們可以只讓管理員去「登出」後使用首頁。
        # 為了方便，這裡顯示一個簡單提示即可。
        st.write("請點擊上方「登出」按鈕，即可回到親友模式進行真實體驗。")