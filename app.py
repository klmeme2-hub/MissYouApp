import streamlit as st
import json
import time
import datetime
import random
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config
import extra_streamlit_components as stx

# ==========================================
# 應用程式：EchoSoul (SaaS Stable - Fix TeaserDB)
# ==========================================

# 1. UI 設定
st.set_page_config(page_title="EchoSoul", page_icon="♾️", layout="centered")
ui.load_css()

# 2. 初始化
cookie_manager = stx.CookieManager()
if "SUPABASE_URL" not in st.secrets: st.stop()
supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 3. 讀取題庫 (關鍵修復：補回 teaser_db) ---
@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

@st.cache_data
def load_brain_teasers():
    try:
        with open('questions2.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"brain_teasers": []}

question_db = load_questions()
teaser_db = load_brain_teasers() # 這行是修正重點

# 4. 狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None
if "call_status" not in st.session_state: st.session_state.call_status = "ringing"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen"

# 初始化隨機題號
if "teaser_idx" not in st.session_state:
    t_list = teaser_db.get("brain_teasers", [])
    if t_list:
        st.session_state.teaser_idx = random.randint(0, len(t_list) - 1)
    else:
        st.session_state.teaser_idx = 0

# 5. 網址參數攔截
if "token" in st.query_params and not st.session_state.user and not st.session_state.guest_data:
    try:
        raw = st.query_params["token"]
        real_tk = raw.split("_")[0] if "_" in raw else raw
        d_name = raw.split("_")[1] if "_" in raw else "朋友"
        data = database.validate_token(supabase, real_tk)
        if data:
            st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role'], 'display_name': d_name}
            st.rerun()
    except: pass

# ==========================================
# 路由控制
# ==========================================

# 情境 A: 訪客模式
if st.session_state.guest_data:
    from modules.views import guest as view_guest
    # 這裡傳入 teaser_db 就不會報錯了
    view_guest.render(supabase, client, teaser_db)

# 情境 B: 未登入
elif not st.session_state.user:
    from modules.views import auth as view_auth
    view_auth.render(supabase, cookie_manager)

# 情境 C: 會員後台
else:
    from modules.views import member as view_member
    view_member.render(supabase, client, question_db)
