import streamlit as st
import requests
from openai import OpenAI
from supabase import create_client, Client
import numpy as np
import os
import json
import io
from pydub import AudioSegment

# ==========================================
# 版本資訊：A 版 (Master)
# 更新內容：補回進度條、雙欄佈局、試聽功能、完美暱稱拼接
# ==========================================

# --- 1. 頁面與 UI 設定 ---
st.set_page_config(page_title="想念", page_icon="🤍", layout="wide") # 寬螢幕模式

custom_css = """
<style>
    /* 全局配色鎖定 */
    .stApp, p, h1, h2, h3, label, div, span, button { color: #333333 !important; }
    
    /* 下拉選單修復 */
    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li { background-color: #FFFFFF !important; color: #333333 !important; }
    div[data-baseweb="popover"] li:hover { background-color: #E3F2FD !important; }

    /* AI 對話氣泡 */
    .ai-bubble {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #4A90E2;
        margin: 10px 0;
        color: #333333;
    }
    
    /* 題目卡片 (Active) */
    .question-card-active {
        background-color: #E3F2FD;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 2px solid #2196F3;
        text-align: center;
    }
    .q-text {
        font-size: 20px;
        font-weight: bold;
        color: #1565C0 !important;
        margin-bottom: 10px;
    }

    /* 歷史回憶卡片 */
    .history-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        margin-bottom: 10px;
        font-size: 14px;
    }
    .history-q { font-weight: bold; color: #555 !important; }
    .history-a { color: #333 !important; margin-top: 5px; }
    
    /* 儀表板卡片 */
    .dashboard-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E0E0E0;
        margin-bottom: 20px;
    }

    /* 隱藏 Streamlit 選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 2. 初始化與設定 ---
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

ROLE_MAPPING = {
    "妻子": "wife",
    "丈夫": "husband",
    "兒子": "son",
    "女兒": "daughter",
    "朋友": "friend",
    "孫子": "grandson",
    "其他": "others"
}

# --- 3. 讀取外部題庫 ---
@st.cache_data
def load_questions_from_file():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

question_db = load_questions_from_file()

# --- 4. 核心功能函數 ---

def get_elevenlabs_usage():
    try:
        url = "https://api.elevenlabs.io/v1/user/subscription"
        headers = {"xi-api-key": elevenlabs_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['character_count'], data['character_limit']
        return 0, 0
    except: return 0, 0

def get_embedding(text):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def get_memories_by_role(role):
    """取得該角色所有的回憶"""
    try:
        response = supabase.table("memories").select("*").eq("role", role).order('id', desc=True).execute()
        return response.data
    except: return []

def save_memory_fragment(role, question, answer):
    """儲存記憶 (含覆寫邏輯：刪除舊的相同題目)"""
    full_content = f"【關於{question}】：{answer}"
    
    # 1. 刪除舊的
    try:
        existing = get_memories_by_role(role)
        for mem in existing:
            # 簡單比對題目
            if mem['content'].startswith(f"【關於{question}】"):
                supabase.table("memories").delete().eq("id", mem['id']).execute()
    except: pass
    
    # 2. 插入新的
    embedding = get_embedding(full_content)
    data = {"role": role, "content": full_content, "embedding": embedding}
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

# --- 音訊相關函數 ---
def upload_nickname_audio(role, audio_bytes):
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"nickname_{safe_role}.mp3"
        supabase.storage.from_("audio_clips").upload(
            file_path, audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        return True
    except Exception as e:
        st.error(f"儲存音檔失敗: {e}")
        return False

def get_nickname_audio_bytes(role):
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"nickname_{safe_role}.mp3"
        response = supabase.storage.from_("audio_clips").download(file_path)
        return response
    except: return None

def train_voice_sample(audio_bytes):
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/edit"
        headers = {"xi-api-key": elevenlabs_key}
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        data = {'name': 'My Digital Clone'} 
        response = requests.post(url, headers=headers, data=data, files=files)
        return response.status_code == 200
    except Exception as e:
        print(f"訓練上傳失敗: {e}")
        return False

def merge_audio_clips(intro_bytes, main_bytes):
    try:
        if not intro_bytes or len(intro_bytes) < 100: return main_bytes
        intro = AudioSegment.from_file(io.BytesIO(intro_bytes))
        main = AudioSegment.from_file(io.BytesIO(main_bytes))
        silence = AudioSegment.silent(duration=200)
        combined = intro + silence + main
        buffer = io.BytesIO()
        combined.export(buffer, format="mp3")
        return buffer.getvalue()
    except Exception as e:
        print(f"音訊合併失敗: {e}")
        return main_bytes

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
    # === 親友前台 (User Mode) ===
    roles = load_all_roles()
    
    # 限制前台寬度
    st.markdown("""<style>.block-container {max_width: 700px; padding-top: 2rem;}</style>""", unsafe_allow_html=True)

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
                # 1. 語音轉字
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                user_text = transcript.text
                if not user_text or len(user_text.strip()) < 2:
                    st.warning("👂 請再說一次..."); return

                # 2. 檢索記憶
                with st.spinner("思考與檢索中..."):
                    relevant_memory = search_relevant_memories(sel_role, user_text)
                    has_nickname_audio = get_nickname_audio_bytes(sel_role) is not None
                    
                    nickname_instruction = ""
                    if has_nickname_audio:
                        nickname_instruction = "【特殊指令】：回應中**絕對不要**包含對方的暱稱或打招呼，直接講內容。因為系統會自動播放真實暱稱。"
                    else:
                        nickname_instruction = "請在開頭自然呼喚對方的暱稱。"

                    system_instruction = f"""
                    {persona_summary}
                    【深層記憶】：{relevant_memory}
                    {nickname_instruction}
                    語氣要自然，包含呼吸感。
                    """
                    
                    msgs = [{"role": "system", "content": system_instruction}] + st.session_state.chat_history[-6:]
                    msgs.append({"role": "user", "content": user_text})

                    res = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
                    ai_text = res.choices[0].message.content
                    
                    st.session_state.chat_history.append({"role": "user", "content": user_text})
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_text})

                    final_audio_bytes = b""
                    ai_audio_bytes = b""

                    if ai_text:
                        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                        headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                        data = {
                            "text": ai_text, 
                            "model_id": "eleven_multilingual_v2", 
                            "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}
                        }
                        tts_res = requests.post(tts_url, json=data, headers=headers)
                        if tts_res.status_code == 200:
                            ai_audio_bytes = tts_res.content

                    if has_nickname_audio and ai_audio_bytes:
                        nickname_bytes = get_nickname_audio_bytes(sel_role)
                        if nickname_bytes:
                            final_audio_bytes = merge_audio_clips(nickname_bytes, ai_audio_bytes)
                        else: final_audio_bytes = ai_audio_bytes
                    else: final_audio_bytes = ai_audio_bytes

                    if final_audio_bytes:
                        st.audio(final_audio_bytes, format="audio/mp3", autoplay=True)

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
    # === 管理員後台 (Admin Mode) ===
    st.success("🔓 管理員模式")
    if st.button("登出"):
        st.session_state.is_admin = False
        st.rerun()

    # 儀表板
    st.markdown("### 📊 系統健康儀表板")
    c_sys1, c_sys2 = st.columns(2)
    with c_sys1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.caption("🗣️ 聲音合成額度")
        used, limit = get_elevenlabs_usage()
        if limit > 0:
            st.progress(used / limit)
            st.write(f"**{used:,}** / {limit:,}")
        else: st.warning("無法讀取")
        st.markdown('</div>', unsafe_allow_html=True)
    with c_sys2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.caption("🧠 大腦餘額")
        st.markdown("""<a href="https://platform.openai.com/settings/organization/billing/overview" target="_blank"><button style="width:100%;">🔗 查看帳單</button></a>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 基礎人設", "🧠 回憶補完", "🎯 完美暱稱"])

    # TAB 1: 基礎人設
    with tab1:
        st.caption("設定對話語氣與基礎資訊")
        c1, c2 = st.columns(2)
        with c1: t_role = st.selectbox("對象", list(ROLE_MAPPING.keys()), key="tr")
        with c2: member_name = st.text_input("您的名字 (供AI識別)", value="爸爸", key="mn")
        nickname = st.text_input("專屬暱稱", placeholder="例如：寶貝", key="nk")
        up_file = st.file_uploader(f"上傳與【{t_role}】的紀錄", type="txt")
        if st.button("✨ 生成基礎人設"):
            if up_file and member_name:
                with st.spinner("分析中..."):
                    raw = up_file.read().decode("utf-8")
                    prompt = f"分析對話。主角(我):{member_name}。對象:{t_role}。暱稱:{nickname}。生成System Prompt，重點：模仿主角語氣，對象是{t_role}時務必使用暱稱{nickname}。資料：{raw[-20000:]}"
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    save_persona_summary(t_role, res.choices[0].message.content)
                    st.success("更新完成")

    # TAB 2: 回憶補完 (雙欄 + 進度條)
    with tab2:
        # 1. 準備資料
        q_role = st.selectbox("補充對象回憶", list(question_db.keys()), key="q_role")
        q_list = question_db.get(q_role, [])
        
        # 取得已回答的歷史
        memories = get_memories_by_role(q_role)
        answered_qs = set()
        for m in memories:
            if "【關於" in m['content'] and "】：" in m['content']:
                q_part = m['content'].split("【關於")[1].split("】：")[0]
                answered_qs.add(q_part)

        # 狀態管理
        if "edit_target" not in st.session_state: st.session_state.edit_target = None

        # 決定當前題目
        current_q = None
        if st.session_state.edit_target:
            current_q = st.session_state.edit_target
            st.info(f"✏️ 正在重新錄製：{current_q}")
        else:
            for q in q_list:
                if q not in answered_qs:
                    current_q = q
                    break
        
        # 【進度條 - 功能回歸】
        if len(q_list) > 0:
            progress = len(answered_qs) / len(q_list)
            st.progress(progress, text=f"回憶補完進度：{len(answered_qs)} / {len(q_list)}")

        # 介面分欄
        col_left, col_right = st.columns([1.5, 1], gap="medium")
        
        # --- 左欄：操作區 ---
        with col_left:
            st.markdown("### 🎙️ 進行中任務")
            if current_q:
                st.markdown(f"""
                <div class="question-card-active">
                    <div class="q-text">{current_q}</div>
                    <div style="font-size:14px; color:#555;">請按下錄音，自然地講述這段回憶...</div>
                </div>
                """, unsafe_allow_html=True)
                
                audio_ans = st.audio_input("錄音回答", key=f"ans_{current_q}")
                
                if "transcribed_text" not in st.session_state: st.session_state.transcribed_text = ""
                
                if audio_ans:
                    trans = client.audio.transcriptions.create(model="whisper-1", file=audio_ans)
                    st.session_state.transcribed_text = trans.text
                    
                    st.text_area("📝 識別文字 (可手動修改)", value=st.session_state.transcribed_text, key="edit_text_area")
                    
                    c_act1, c_act2 = st.columns(2)
                    with c_act1:
                        if st.button("🔊 試聽 AI 唸一遍", use_container_width=True):
                            if st.session_state.transcribed_text:
                                with st.spinner("生成試聽中..."):
                                    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                                    headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
                                    data = {"text": st.session_state.transcribed_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.65}}
                                    r = requests.post(tts_url, json=data, headers=headers)
                                    if r.status_code == 200:
                                        st.audio(r.content, format="audio/mp3", autoplay=True)
                    
                    with c_act2:
                        if st.button("💾 確認無誤，存入並訓練", type="primary", use_container_width=True):
                            final_text = st.session_state.edit_text_area
                            with st.spinner("存入並訓練..."):
                                save_memory_fragment(q_role, current_q, final_text)
                                audio_ans.seek(0)
                                train_voice_sample(audio_ans.read())
                                st.success("已儲存！")
                                st.session_state.edit_target = None
                                st.session_state.transcribed_text = ""
                                st.rerun()

                if st.button("⏭️ 跳過此題"):
                    save_memory_fragment(q_role, current_q, "(已略過)")
                    st.rerun()
            else:
                st.success("🎉 太棒了！此角色的題庫已全部完成。")

        # --- 右欄：歷史紀錄 ---
        with col_right:
            st.markdown("### 📜 回憶存摺")
            st.caption("已完成 (點擊重錄)")
            with st.container(height=500):
                for mem in memories:
                    if "【關於" in mem['content']:
                        try:
                            q_part = mem['content'].split("【關於")[1].split("】：")[0]
                            a_part = mem['content'].split("】：")[1]
                            st.markdown(f"""
                            <div class="history-card">
                                <div class="history-q">Q: {q_part}</div>
                                <div class="history-a">A: {a_part[:30]}...</div>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button("🔄 重錄", key=f"re_{mem['id']}"):
                                st.session_state.edit_target = q_part
                                st.rerun()
                        except: pass

    # TAB 3: 完美暱稱
    with tab3:
        st.subheader("🎯 完美暱稱重現")
        st.info("錄製一段真實的呼喚，AI 會在開頭直接播放這段錄音。")
        nick_role = st.selectbox("錄製給誰聽？", list(ROLE_MAPPING.keys()), key="nick_role")
        st.markdown(f"請按下錄音，喊一聲給【{nick_role}】聽的暱稱：")
        real_nick_audio = st.audio_input("錄製", key="real_nick_rec")
        if real_nick_audio:
            if st.button("💾 上傳真實聲音"):
                with st.spinner("處理中..."):
                    if upload_nickname_audio(nick_role, real_nick_audio.read()):
                        st.success("成功！")