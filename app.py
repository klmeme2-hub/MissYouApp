import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import os

# --- 1. 頁面設定 ---
st.set_page_config(page_title="想念 - 數位人格", page_icon="🤍", layout="centered")

# --- 2. CSS 美化工程 (解決文字看不見的問題) ---
# 這裡強制設定了文字顏色 (#333333) 和背景顏色 (#F7F9FB)
custom_css = """
<style>
    /* 1. 全局背景與文字顏色鎖定 */
    .stApp {
        background-color: #F7F9FB;
    }
    
    /* 強制所有標題與內文變為深灰色，解決看不見的問題 */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {
        color: #333333 !important;
    }

    /* 2. 按鈕美化 */
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

    /* 3. 對話氣泡樣式 (AI 的回應) */
    .ai-bubble {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #4A90E2; /* 左邊那條藍線 */
        margin-top: 15px;
        margin-bottom: 15px;
        font-size: 16px;
        line-height: 1.6;
        color: #333333;
    }

    /* 4. 隱藏預設選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 5. 分頁標籤美化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        color: #555555 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E3F2FD;
        color: #000000 !important;
        font-weight: bold;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 3. 讀取金鑰 & 初始化 Supabase ---
# 為了避免初次設定報錯，我們加一個簡單的檢查
if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ 尚未設定 Secrets！請先去 Streamlit 後台設定 API Keys。")
    st.stop()

openai_key = st.secrets["OPENAI_API_KEY"]
elevenlabs_key = st.secrets["ELEVENLABS_API_KEY"]
voice_id = st.secrets["VOICE_ID"]
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

client = OpenAI(api_key=openai_key)

@st.cache_resource
def init_supabase():
    return create_client(supabase_url, supabase_key)

supabase = init_supabase()

# --- 4. 資料庫操作函數 ---

def save_persona_to_cloud(role, content):
    """儲存人設"""
    try:
        data = {"role": role, "content": content}
        supabase.table("personas").upsert(data).execute()
        return True
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        return False

def load_all_roles_from_cloud():
    """讀取所有角色"""
    try:
        response = supabase.table("personas").select("role").execute()
        return [item['role'] for item in response.data]
    except Exception as e:
        # 如果資料表還沒建，回傳空列表
        return []

def load_persona_content(role):
    """讀取特定內容"""
    try:
        response = supabase.table("personas").select("content").eq("role", role).execute()
        if response.data:
            return response.data[0]['content']
        return None
    except Exception as e:
        return None

# --- 5. 主介面邏輯 ---

st.title("🤍 想念")
st.caption("跨越時空的數位對話")

tab1, tab2 = st.tabs(["⚙️ 會員設定 (後台)", "💬 親友互動 (前台)"])

# ==========================================
# TAB 1: 會員設定區
# ==========================================
with tab1:
    with st.container(border=True): # 加一個外框讓它像卡片
        st.subheader("📝 建立數位分身")
        st.info("請上傳與不同親友的對話紀錄，AI 將學習您的語氣並存入雲端。")

        col1, col2 = st.columns(2)
        with col1:
            target_role = st.selectbox("設定對象身分", ["妻子", "丈夫", "兒子", "女兒", "朋友", "孫子"], key="train_role")
        with col2:
            member_name = st.text_input("您在對話中的名字", placeholder="例如：爸爸", key="member_name")
        
        uploaded_file = st.file_uploader(f"上傳與【{target_role}】的 LINE 紀錄 (.txt)", type="txt")

        if st.button("✨ 開始分析並儲存", use_container_width=True):
            if not uploaded_file or not member_name:
                st.warning("請上傳檔案並輸入名字")
            else:
                with st.spinner("AI 正在閱讀回憶、提取靈魂特徵..."):
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
                        3. 限制：回答簡短(50字內)，不承認是AI，語氣自然。
                        
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
                            st.success(f"✅ 成功！對【{target_role}】的人設已永久保存。")
                            st.balloons()
                            
                    except Exception as e:
                        st.error(f"發生錯誤: {e}")

    # 檢視資料庫內容
    with st.expander("🔍 查看目前雲端儲存的角色"):
        try:
            db_data = supabase.table("personas").select("role", "created_at").execute()
            if db_data.data:
                st.table(db_data.data)
            else:
                st.write("目前雲端是空的")
        except:
            st.write("連線資料庫讀取中...")

# ==========================================
# TAB 2: 親友互動區
# ==========================================
with tab2:
    # 1. 從雲端抓取有哪些角色可用
    available_roles = load_all_roles_from_cloud()
    
    if not available_roles:
        st.warning("☁️ 雲端還沒有任何回憶資料，請先切換到「會員設定」分頁上傳資料。")
    else:
        # 身分選擇區
        col_sel, col_pic = st.columns([2, 1])
        
        with col_sel:
            st.markdown("#### 👋 您好，請問您是我的...？")
            selected_identity = st.selectbox("請選擇您的身分", available_roles, key="user_identity", label_visibility="collapsed")
            
            # 2. 抓取該角色的靈魂
            current_persona = load_persona_content(selected_identity)
            st.caption(f"已載入對【{selected_identity}】的專屬記憶模式")

        with col_pic:
            # 照片圓角處理
            if os.path.exists("photo.jpg"):
                st.image("photo.jpg", use_container_width=True)
            else:
                st.markdown("<div style='font-size:50px; text-align:center;'>👤</div>", unsafe_allow_html=True)

        st.divider()

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

        # 錄音區 (放在最顯眼的位置)
        st.markdown("##### 🎙️ 按下錄音跟我說話：")
        audio_val = st.audio_input("錄音", key="chat_recorder")
        if audio_val:
            process_audio(audio_val)

        # 顯示最後一句 AI 的回應 (使用漂亮的氣泡樣式)
        if len(st.session_state.chat_history) > 0:
            last_msg = st.session_state.chat_history[-1]
            if last_msg["role"] == "assistant":
                st.markdown(f"""
                <div class="ai-bubble">
                    <b>祂說：</b><br>{last_msg['content']}
                </div>
                """, unsafe_allow_html=True)