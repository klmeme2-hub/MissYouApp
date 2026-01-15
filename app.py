import streamlit as st
import json
import time
import datetime
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config
import extra_streamlit_components as stx

# 1. UI 設定
st.set_page_config(page_title="EchoSoul", page_icon="♾️", layout="centered")
ui.load_css()

# 2. 系統初始化
# 這裡必須設定 key，否則 re-run 可能會丟失狀態
cookie_manager = stx.CookieManager(key="main_cookie_mgr")

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

# ==========================================
# 4. 自動登入邏輯 (Auto Login)
# ==========================================
# 只有在「未登入」且「沒有訪客Token」時才檢查
if not st.session_state.user and not "token" in st.query_params:
    time.sleep(0.1) # 等待 cookie manager 載入
    cookies = cookie_manager.get_all()
    access_token = cookies.get("sb_access_token")
    refresh_token = cookies.get("sb_refresh_token")
    
    if access_token and refresh_token:
        try:
            # 嘗試用 Cookie 恢復 Session
            res = supabase.auth.set_session(access_token, refresh_token)
            if res and res.user:
                st.session_state.user = res
                st.rerun() # 成功恢復，重新整理頁面進入後台
        except:
            # 失敗代表 Token 過期，清除 Cookie
            cookie_manager.delete("sb_access_token")
            cookie_manager.delete("sb_refresh_token")

# ==========================================
# 5. 網址攔截邏輯
# ==========================================

# A. Google 登入回調 (?code=...)
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        if res and res.user:
            st.session_state.user = res
            database.get_user_profile(supabase, res.user.id) # Init profile
            
            # 【關鍵】登入成功後，立刻寫入 Cookie (30天)
            cookie_manager.set("sb_access_token", res.session.access_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
            cookie_manager.set("sb_refresh_token", res.session.refresh_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
            
            st.success("登入成功！")
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.toast("登入重試中...", icon="⏳")
        # 嘗試檢查是否已登入
        if supabase.auth.get_session():
            st.query_params.clear()
            st.rerun()

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
# 6. 介面渲染
# ==========================================

if st.session_state.guest_data:
    # 訪客模式
    view_guest.render(supabase, client, None) # 暫時不傳 teaser_db

elif not st.session_state.user:
    # 登入畫面
    view_auth.render(supabase, cookie_manager)

else:
    # 會員後台
    # C.1 登出邏輯：除了登出 Supabase，還要清除 Cookie
    # 為了讓按鈕能操作，我們把登出邏輯封裝在 member 視圖裡，但這裡需要處理 cookie 清除
    # 簡單做法：在 member.py 裡 return 一個訊號，或直接在那裡操作 supabase
    # 這裡我們用一個簡單的 callback check
    if st.session_state.get("logout_clicked"):
        cookie_manager.delete("sb_access_token")
        cookie_manager.delete("sb_refresh_token")
        del st.session_state["logout_clicked"]
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    view_member.render(supabase, client, question_db)
