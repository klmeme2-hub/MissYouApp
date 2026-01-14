import streamlit as st
import json
import time
import datetime
import random # 補上
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config
import extra_streamlit_components as stx

# ==========================================
# 應用程式：MetaVoice (SaaS Beta 4.12 - 邏輯修復版)
# ==========================================

st.set_page_config(page_title="MetaVoice", page_icon="🌌", layout="centered")
ui.load_css()

cookie_manager = stx.CookieManager()
if "SUPABASE_URL" not in st.secrets: st.stop()
supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- 讀取題庫 (修復) ---
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
teaser_db = load_brain_teasers() # 讀取腦筋急轉彎

# 3. 狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None
if "call_status" not in st.session_state: st.session_state.call_status = "ringing"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen"

# 【修正】初始化隨機題號
if "teaser_idx" not in st.session_state:
    t_list = teaser_db.get("brain_teasers", [])
    if t_list:
        st.session_state.teaser_idx = random.randint(0, len(t_list) - 1)
    else:
        st.session_state.teaser_idx = 0

# 1. 網址參數攔截
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

if st.session_state.guest_data:
    # A. 訪客模式 (傳入 teaser_db)
    view_guest.render(supabase, client, teaser_db)

elif not st.session_state.user:
    # B. 登入畫面
    view_auth.render(supabase, cookie_manager)

else:
    # C. 會員後台
    view_member.render(supabase, client, question_db)
