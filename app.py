import streamlit as st
import json
from openai import OpenAI
from modules import ui, database, state
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

# 3. 狀態初始化 (呼叫模組)
state.init_session_state()

# 4. 網址攔截邏輯
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
    # 進入訪客畫面
    view_guest.render(supabase, client)

elif not st.session_state.user:
    # 進入登入畫面
    view_auth.render(supabase, cookie_manager)

else:
    # 進入會員後台
    view_member.render(supabase, client)
