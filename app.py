import streamlit as st
import json
import time
import datetime
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config
import extra_streamlit_components as stx

# ==========================================
# 應用程式：MetaVoice (SaaS Beta 4.2 - 視覺升級版)
# ==========================================

# 1. UI 設定 (更換新標題)
st.set_page_config(page_title="MetaVoice - 元宇宙聲紋站", page_icon="🌌", layout="centered")
ui.load_css()

# 2. 初始化 Cookie 與 系統
cookie_manager = stx.CookieManager()

if "SUPABASE_URL" not in st.secrets:
    st.error("⚠️ Secrets 設定缺失")
    st.stop()

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

# ==========================================
# 邏輯路由
# ==========================================

# 1. 網址參數攔截
if "token" in st.query_params and not st.session_state.user and not st.session_state.guest_data:
    try:
        raw_token = st.query_params["token"]
        real_token = raw_token.split("_")[0] if "_" in raw_token else raw_token
        display_name_from_url = raw_token.split("_")[1] if "_" in raw_token else "朋友"
        
        data = database.validate_token(supabase, real_token)
        if data:
            st.session_state.guest_data = {
                'owner_id': data['user_id'], 
                'role': data['role'], 
                'display_name': display_name_from_url
            }
            st.rerun()
        else:
            st.error("連結無效")
            st.query_params.clear()
    except: pass

# ------------------------------------------
# 情境 A: 訪客模式
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    
    persona_data = database.load_persona(supabase, role_name)
    display_name = url_name
    if persona_data and persona_data.get('member_nickname'):
        display_name = persona_data['member_nickname']

    # 階段 1: 來電模擬
    if st.session_state.call_status == "ringing":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(f"""
            <div style='text-align:center; padding-top:50px;'>
                <div style='font-size:80px;'>👤</div>
                <h1 style='color:#FAFAFA;'>{display_name}</h1>
                <p style='color:#CCC; font-size:20px; animation: blink 1.5s infinite;'>📞 來電中...</p>
            </div>
            <style>@keyframes blink {{ 0% {{opacity: 1;}} 50% {{opacity: 0.5;}} 100% {{opacity: 1;}} }}</style>
            """, unsafe_allow_html=True)
            
            if st.button("🟢 接聽", use_container_width=True, type="primary"):
                st.session_state.call_status = "connected"
                database.check_daily_interaction(supabase, owner_id)
                st.rerun()

    # 階段 2: 通話中
    elif st.session_state.call_status == "connected":
        if "opening_played" not in st.session_state:
            op_bytes = audio.get_audio_bytes(supabase, role_name, "opening")
            
            # 決定 AI 接話內容 (根據軌道)
            if role_name == "friend":
                ai_ask = "你覺得這個AI分身，跟我本尊有幾分像呢？幫我打個分數，拜託了。"
                ai_wav = audio.generate_speech(ai_ask, tier)
                final = audio.merge_audio_clips(op_bytes, ai_wav) if op_bytes else ai_wav
            else:
                ai_greet = audio.generate_speech("想我嗎？", tier)
                # 家人模式：若有 opening (其實是 nickname)，則拼接
                # 若無 opening，直接播放 AI
                final = audio.merge_audio_clips(op_bytes, ai_greet) if op_bytes else ai_greet
            
            if final: st.audio(final, format="audio
