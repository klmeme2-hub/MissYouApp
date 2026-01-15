import streamlit as st
import json
import time
import datetime
from openai import OpenAI
import extra_streamlit_components as stx

# --- 核心模組 ---
from modules import ui, auth, database, audio, brain, config

# --- 介面視圖 (View) 模組：移到最上方引用，防止 NameError ---
from modules.views import auth as view_auth
from modules.views import member as view_member
from modules.views import guest as view_guest

# --- Tab 模組 ---
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config

# ==========================================
# 應用程式：EchoSoul (Ver. 0115 備份 - 修復版)
# ==========================================

# 1. UI 設定
st.set_page_config(page_title="EchoSoul", page_icon="♾️", layout="centered")
ui.load_css()

# 2. 初始化
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

# 3. 狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None
if "call_status" not in st.session_state: st.session_state.call_status = "ringing"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen"

# 4. 網址參數攔截
# A. Google 登入回調
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        if res and res.user:
            st.session_state.user = res
            database.get_user_profile(supabase, res.user.id) # 初始化資料
            st.success("Google 登入成功！")
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.error(f"登入驗證失敗: {e}")
        st.query_params.clear()

# B. 訪客 Token
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
    # A. 訪客模式
    # 這裡傳入 None 作為 teaser_db (因為這是備份版，尚未整合腦筋急轉彎題庫)
    view_guest.render(supabase, client, None)

elif not st.session_state.user:
    # B. 登入畫面 (現在 view_auth 肯定已經定義了)
    view_auth.render(supabase, cookie_manager)

else:
    # C. 會員後台
    view_member.render(supabase, client, question_db)
