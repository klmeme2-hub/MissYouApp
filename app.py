import streamlit as st
import json
import time
import datetime
from openai import OpenAI

from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config

import extra_streamlit_components as stx

# ==========================================
# 應用程式：EchoSoul (SaaS Stable - Single Cookie Fix)
# ==========================================

# 1. UI 設定
st.set_page_config(page_title="EchoSoul", page_icon="♾️", layout="centered")
ui.load_css()

# 2. 系統初始化
cookie_manager = stx.CookieManager(key="main_cookie_mgr")

# 3. 處理 Cookie 寫入 (代理模式 + 單一 Cookie)
if "pending_login_data" in st.session_state:
    data = st.session_state.pending_login_data
    expires = datetime.datetime.now() + datetime.timedelta(days=30)
    
    # 【關鍵】打包成單一 JSON 字串
    cookie_value = json.dumps({
        "email": data["email"],
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"]
    })
    
    # 只呼叫一次 set，避免 Duplicate Key
    cookie_manager.set("echosoul_session", cookie_value, expires_at=expires)
    
    del st.session_state["pending_login_data"]
    time.sleep(1) # 給瀏覽器一點時間
    st.rerun()

# 4. 處理登出
if st.session_state.get("logout_clicked"):
    # 只需刪除一個 Cookie
    cookie_manager.delete("echosoul_session")
    del st.session_state["logout_clicked"]
    
    # 重新獲取 client
    supabase = database.init_supabase()
    supabase.auth.sign_out()
    
    st.session_state.user = None
    time.sleep(0.5)
    st.rerun()

# 5. 讀取 Cookie 進行自動登入
time.sleep(0.1)
all_cookies = cookie_manager.get_all()
saved_session_json = all_cookies.get("echosoul_session")

# 用於傳遞給 auth view 的預設值
view_cookies = {}

if saved_session_json:
    try:
        session_data = json.loads(saved_session_json)
        view_cookies["member_email"] = session_data.get("email", "")
        
        # 自動登入檢查
        if not st.session_state.user and "code" not in st.query_params and "token" not in st.query_params:
            acc = session_data.get("access_token")
            ref = session_data.get("refresh_token")
            
            if acc and ref:
                supabase = database.init_supabase()
                try:
                    res = supabase.auth.set_session(acc, ref)
                    if res and res.user:
                        st.session_state.user = res
                        database.get_user_profile(supabase, res.user.id)
                        st.rerun()
                except:
                    pass # Token 過期，等待下次登入覆蓋
    except:
        pass # JSON 解析失敗，忽略

# 6. 初始化 AI 與 DB
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

# 7. 狀態初始化
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None

if "call_status" not in st.session_state: st.session_state.call_status = "connected"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen"

# 8. 網址參數攔截
# A. Google 登入回調
if "code" in st.query_params:
    try:
        code = st.query_params["code"]

        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        
        if res and res.user:
            st.session_state.user = res

            database.get_user_profile(supabase, res.user.id)
            
            # 【關鍵】設定 Flag，讓上方邏輯去寫入 Cookie
            st.session_state.pending_login_data = {
                "email": res.user.email,
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token
            }
            
            st.success("Google 登入成功！")
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        if supabase.auth.get_session():
            st.query_params.clear()
            st.rerun()
        else:
            st.toast("⚠️ 驗證逾時，請重新點擊登入", icon="🔄")
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
# 9. 介面渲染
# ==========================================

if st.session_state.guest_data:
    from modules.views import guest as view_guest
    view_guest.render(supabase, client, teaser_db)

elif not st.session_state.user:
    from modules.views import auth as view_auth
    # 傳入 view_cookies 讓它可以預填 Email
    view_auth.render(supabase, cookie_manager, view_cookies)

else:
    from modules.views import member as view_member

    view_member.render(supabase, client, question_db)
