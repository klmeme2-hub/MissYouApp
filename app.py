import streamlit as st
import json
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
cookie_manager = stx.CookieManager()
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

# ==========================================
# 處理 Google 登入回調 (OAuth Callback)
# ==========================================
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        
        # 嘗試交換 Session
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        
        if res and res.user:
            st.session_state.user = res
            
            # 初始化用戶資料
            database.get_user_profile(supabase, res.user.id)
            
            # 成功後，強制清除網址參數，避免重新整理時重複送 code 導致報錯
            st.query_params.clear()
            st.rerun()
            
    except Exception as e:
        # 【關鍵修改】如果報錯，先檢查是否其實已經登入了 (Session已建立)
        # 很多時候是因為 code 只能用一次，第二次刷新就會報錯，但其實 user 已經在庫裡了
        session = supabase.auth.get_session()
        if session:
            st.session_state.user = session
            st.query_params.clear()
            st.rerun()
        else:
            # 真的失敗才顯示錯誤，但用 toast 取代 error 比較不嚇人
            st.toast(f"登入重試中... ({str(e)})", icon="⚠️")
            # 不清除參數，讓用戶可以手動再試一次或按上一頁

# B. 處理訪客連結
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
# 介面渲染
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

