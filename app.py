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

# 2. 系統初始化 (關鍵：Cookie Manager)
# key="main_cookies" 確保全域唯一
cookie_manager = stx.CookieManager(key="main_cookies")

# 【關鍵修復】: 在最上層讀取一次 Cookie，之後往下傳遞，避免重複呼叫
time.sleep(0.1) # 稍微等待載入
all_cookies = cookie_manager.get_all()

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
if "call_status" not in st.session_state: st.session_state.call_status = "connected"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen"

# ==========================================
# 4. 自動登入邏輯 (Auto Login)
# ==========================================
if not st.session_state.user and "code" not in st.query_params and "token" not in st.query_params:
    if all_cookies:
        access_token = all_cookies.get("sb_access_token")
        refresh_token = all_cookies.get("sb_refresh_token")
        
        if access_token and refresh_token:
            try:
                res = supabase.auth.set_session(access_token, refresh_token)
                if res and res.user:
                    st.session_state.user = res
                    database.get_user_profile(supabase, res.user.id)
                    st.rerun()
            except:
                # 過期則清除
                cookie_manager.delete("sb_access_token")
                cookie_manager.delete("sb_refresh_token")

# ==========================================
# 5. 路由與攔截
# ==========================================

# A. Google 登入回調
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        
        if res and res.user:
            st.session_state.user = res
            database.get_user_profile(supabase, res.user.id)
            
            # 寫入 Cookie (30天)
            expires = datetime.datetime.now() + datetime.timedelta(days=30)
            cookie_manager.set("sb_access_token", res.session.access_token, expires_at=expires)
            cookie_manager.set("sb_refresh_token", res.session.refresh_token, expires_at=expires)
            
            st.success("Google 登入成功！")
            st.query_params.clear()
            st.rerun()
            
    except Exception as e:
        # 容錯處理：如果已經有 Session 就不報錯
        session = supabase.auth.get_session()
        if session:
            st.session_state.user = session
            st.query_params.clear()
            st.rerun()
        else:
            st.toast("⚠️ 連線逾時，請重新點擊登入", icon="🔄")
            st.query_params.clear()
            time.sleep(2)
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
    view_guest.render(supabase, client, teaser_db)

elif not st.session_state.user:
    # 【關鍵修改】傳入 all_cookies，讓 auth.py 使用
    view_auth.render(supabase, cookie_manager, all_cookies)

else:
    view_member.render(supabase, client, question_db, cookie_manager)
