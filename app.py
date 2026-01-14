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

# A. 處理 Google 登入回調 (OAuth Callback)
# 當網址有 ?code= 時，代表剛從 Google 回來
if "code" in st.query_params:
    try:
        code = st.query_params["code"]
        # 用 code 交換 session
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        if res and res.user:
            st.session_state.user = res
            
            # 初始化用戶資料
            database.get_user_profile(supabase, res.user.id)
            
            # 【重要】檢查是否有綁定任務 (從 Cookie 讀取暫存的 Voice ID)
            # cookies = cookie_manager.get_all() # 這裡 stx 可能讀不到剛寫入的，暫時略過複雜綁定邏輯
            # 未來可在此處將 Cookie 中的 pending_voice_id 寫入資料庫
            
            st.success("Google 登入成功！")
            # 清除網址參數，避免重新整理又跑一次
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.error(f"登入驗證失敗: {e}")
        st.query_params.clear()

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
