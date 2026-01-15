import streamlit as st
import json
import time
import datetime
from openai import OpenAI
import extra_streamlit_components as stx

# 引入模組
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config

# ==========================================
# 應用程式：EchoSoul (SaaS Production - Google Login Ready)
# ==========================================

# 1. UI 設定
st.set_page_config(page_title="EchoSoul", page_icon="♾️", layout="centered")
ui.load_css()

# 2. 系統初始化
# 設定 key 避免重複 reload 導致 cookie 讀取錯誤
cookie_manager = stx.CookieManager(key="main_cookie_mgr")

if "SUPABASE_URL" not in st.secrets: st.stop()
supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
teaser_db = load_brain_teasers()

# 3. 狀態初始化
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None
if "call_status" not in st.session_state: st.session_state.call_status = "connected" # 預設接通
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen"

# ==========================================
# 4. 路由與攔截邏輯 (Router)
# ==========================================

# A. 自動登入檢查 (Auto Login Check)
# 只有在「未登入」且「沒有訪客Token」且「沒有正在處理登入回調」時才檢查
if not st.session_state.user and "token" not in st.query_params and "code" not in st.query_params:
    time.sleep(0.2) # 等待 cookie manager 載入
    cookies = cookie_manager.get_all()
    # 這裡只檢查 session 是否有效，實際 token 驗證交給 supabase client 內部處理
    # 或是依賴 supabase.auth.get_session()
    current_session = supabase.auth.get_session()
    if current_session:
        st.session_state.user = current_session
        st.rerun()

# B. Google 登入回調處理 (OAuth Callback)
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        
        # 交換 Session
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        
        if res and res.user:
            st.session_state.user = res
            
            # 初始化用戶資料
            database.get_user_profile(supabase, res.user.id)
            
            # 檢查是否有暫存的綁定任務 (從 Cookie 讀取 pending_voice_id)
            # cookies = cookie_manager.get_all()
            # pending_vid = cookies.get("pending_voice_id")
            # if pending_vid: ... (綁定邏輯)
            
            st.success("登入成功！")
            st.query_params.clear()
            st.rerun()
            
    except Exception as e:
        # 如果報錯，先檢查是否其實已經登入成功 (Supabase 有時會自動處理)
        session = supabase.auth.get_session()
        if session:
            st.session_state.user = session
            st.query_params.clear()
            st.rerun()
        else:
            st.error(f"登入驗證失敗，請重試。")
            st.query_params.clear()

# C. 處理訪客連結
if "token" in st.query_params and not st.session_state.user and not st.session_state.guest_data:
    try:
        raw = st.query_params["token"]
        # 解析 token_名字
        real_tk = raw.split("_")[0] if "_" in raw else raw
        d_name = raw.split("_")[1] if "_" in raw else "朋友"
        
        data = database.validate_token(supabase, real_tk)
        if data:
            st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role'], 'display_name': d_name}
            st.rerun()
    except: pass

# ==========================================
# 5. 介面渲染
# ==========================================

if st.session_state.guest_data:
    # 訪客模式
    view_guest.render(supabase, client, teaser_db)

elif not st.session_state.user:
    # 登入畫面 (含 Google 按鈕)
    view_auth.render(supabase, cookie_manager)

else:
    # 會員後台
    view_member.render(supabase, client, question_db)
