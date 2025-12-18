import streamlit as st
import json
from openai import OpenAI
# 引入所有模組
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config

# 1. UI 設定
st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="🤍", layout="wide")
ui.load_css()

# 2. 系統初始化
if "SUPABASE_URL" not in st.secrets: st.stop()
supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 3. 讀取題庫
@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}
question_db = load_questions()

# 4. 狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1

# ==========================================
# 邏輯路由
# ==========================================

# 情境 A: 訪客模式
if st.session_state.guest_data:
    owner_id = st.session_state.guest_data['owner_id']
    role_name = st.session_state.guest_data['role']
    
    # 讀取人設與稱呼
    persona_data = database.load_persona(supabase, role_name)
    display_name = "會員"
    if persona_data and persona_data.get('member_nickname'):
        display_name = persona_data['member_nickname']
        
    st.markdown(f"<h2 style='text-align:center;'>📞 與 [{display_name}] 通話中...</h2>", unsafe_allow_html=True)
    
    # 狀態檢查
    profile = database.get_user_profile(supabase, user_id=owner_id)
    msg = database.check_daily_interaction(supabase, owner_id)
    if msg: st.toast(msg)
    
    ui.render_status_bar(profile.get('tier'), profile.get('energy'), 0, audio.get_tts_engine_type(profile), is_guest=True)
    
    if profile.get('energy') <= 0:
        st.error("💔 電量耗盡...")
        # (儲值按鈕略...)
    else:
        if not persona_data:
            st.warning("對方尚未設定資料。")
        else:
            # ... (對話與錄音邏輯，與之前相同) ...
            # 這裡因為代碼太長，建議您可以把「對話邏輯」也封裝到 modules/chat.py
            # 目前先維持原樣，請複製上一版 app.py 的對話邏輯貼過來
            pass 

    if st.button("🚪 離開"):
        st.session_state.guest_data = None
        st.rerun()

# 情境 B: 未登入
elif not st.session_state.user:
    # ... (登入/註冊介面，請複製上一版) ...
    pass

# 情境 C: 會員後台
else:
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    
    with st.sidebar:
        st.write(f"👤 {st.session_state.user.user.email}")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    ui.render_status_bar(tier, profile.get('energy'), xp, audio.get_tts_engine_type(profile))
    
    allowed = ["朋友"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1: target_role = st.selectbox("選擇對象", allowed)
    if target_role == "朋友" and len(allowed) == 1: st.info("🔒 累積 20 XP 解鎖家屬角色")

    st.divider()

    # 這裡就是模組化的威力！主程式只要這幾行：
    t1, t2, t3, t4, t5 = st.tabs(["🧬 聲紋訓練", "💎 分享解鎖", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"])
    
    with t1: tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, st.secrets['VOICE_ID'], st.secrets['ELEVENLABS_API_KEY'])
    with t2: tab_store.render(supabase, st.session_state.user.user.id, xp)
    with t3: tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t4: tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
    with t5: tab_config.render(supabase, tier, xp)
