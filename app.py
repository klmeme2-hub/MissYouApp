import streamlit as st
import json
from openai import OpenAI
from modules import ui, database
from modules.views import auth as view_auth
from modules.views import member as view_member
from modules.views import guest as view_guest
import extra_streamlit_components as stx

# 1. UI 設定
st.set_page_config(page_title="MetaVoice", page_icon="🌌", layout="centered")
ui.load_css()

# 2. 系統初始化
cookie_manager = stx.CookieManager()
if "SUPABASE_URL" not in st.secrets: st.stop()
supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}
question_db = load_questions()

# 3. 狀態初始化
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None
if "call_status" not in st.session_state: st.session_state.call_status = "ringing"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen"

# 4. 網址參數攔截
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
# 路由控制 (Controller)
# ==========================================

if st.session_state.guest_data:
    # A. 訪客模式
    view_guest.render(supabase, client)

elif not st.session_state.user:
    # B. 登入畫面
    view_auth.render(supabase, cookie_manager)

else:
    # C. 會員後台
    view_member.render(supabase, client, question_db)
