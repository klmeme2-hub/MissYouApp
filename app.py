import streamlit as st
import json
import time
import datetime
from openai import OpenAI
from modules import ui, auth, database
from modules.views import auth as view_auth
from modules.views import member as view_member
from modules.views import guest as view_guest
import extra_streamlit_components as stx

# 1. UI 設定
st.set_page_config(page_title="EchoSoul", page_icon="♾️", layout="centered")
ui.load_css()

# 2. 系統初始化
cookie_manager = stx.CookieManager(key="main_cookies")
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
# 4. 自動登入邏輯 (Auto Login) - 關鍵新增
# ==========================================
# 如果現在沒登入，且網址沒有要處理 Token 或 Code，就檢查 Cookie
if not st.session_state.user and "code" not in st.query_params and "token" not in st.query_params:
    try:
        # 稍微延遲確保 Cookie Manager 載入
        time.sleep(0.1)
        cookies = cookie_manager.get_all()
        access_token = cookies.get("sb_access_token")
        refresh_token = cookies.get("sb_refresh_token")
        
        if access_token and refresh_token:
            # 嘗試用 Cookie 恢復 Session
            res = supabase.auth.set_session(access_token, refresh_token)
            if res and res.user:
                st.session_state.user = res
                database.get_user_profile(supabase, res.user.id)
                st.rerun() # 成功恢復，刷新頁面
    except:
        pass # Cookie 無效或過期，忽略

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
            
            # 【關鍵】登入成功，寫入 Cookie (30天)
            expires = datetime.datetime.now() + datetime.timedelta(days=30)
            cookie_manager.set("sb_access_token", res.session.access_token, expires_at=expires)
            cookie_manager.set("sb_refresh_token", res.session.refresh_token, expires_at=expires)
            
            st.success("Google 登入成功！")
            st.query_params.clear()
            st.rerun()
            
    except Exception as e:
        err_msg = str(e).lower()
        if "code verifier" in err_msg:
            st.toast("⚠️ 連線逾時，請重新點擊登入", icon="🔄")
            st.query_params.clear()
            time.sleep(2)
            st.rerun()
        else:
            st.error(f"登入異常: {e}")
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
# 6. 介面渲染
# ==========================================

if st.session_state.guest_data:
    view_guest.render(supabase, client, teaser_db)

elif not st.session_state.user:
    # 這裡要把 cookie_manager 傳進去，讓 Email 登入也能寫 Cookie
    view_auth.render(supabase, cookie_manager)

else:
    # 這裡要把 cookie_manager 傳進去，讓登出時能刪除 Cookie
    view_member.render(supabase, client, question_db, cookie_manager)
