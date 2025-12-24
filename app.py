import streamlit as st
import json
import time
import datetime
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config
import extra_streamlit_components as stx

# ==========================================
# 應用程式：MetaVoice (SaaS Beta 4.7 - UI 緊湊修正版)
# ==========================================

# 1. UI 設定
st.set_page_config(page_title="MetaVoice", page_icon="🌌", layout="centered")
ui.load_css()

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

# 1. 網址參數攔截
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

# ------------------------------------------
# 情境 A: 訪客模式
# ------------------------------------------
if st.session_state.guest_data:
    # ... (訪客模式維持不變，請複製上一版) ...
    # 為節省篇幅，此處省略
    pass
    # 若需完整代碼請參考上一版

# ------------------------------------------
# 情境 B: 未登入
# ------------------------------------------
elif not st.session_state.user:
    # ... (登入模式維持不變，請複製上一版) ...
    # 為節省篇幅，此處省略
    pass

# ------------------------------------------
# 情境 C: 會員後台 (UI 調整重點)
# ------------------------------------------
else:
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    
    # 1. 頂部 Header (緊湊版)
    col_head_main, col_head_info = st.columns([7, 3])
    
    with col_head_main:
        st.markdown("""
        <div class="header-title">
            <h1>🌌 元宇宙聲紋站</h1>
            <p class="header-subtitle">元宇宙的第一張通行證：鎸刻你的數位聲紋</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_head_info:
        c_email, c_btn = st.columns([2, 1])
        with c_email:
            st.markdown(f"<div class='user-email-text'>{st.session_state.user.user.email}</div>", unsafe_allow_html=True)
        with c_btn:
            if st.button("登出", key="logout_btn", use_container_width=True):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()

    # 2. 狀態列 (已移除小人)
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile))
    
    # 3. 角色與分享 (更緊湊)
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    c_role, c_btn = st.columns([7, 3])
    with c_role:
        disp_role = st.selectbox("選擇對象", allowed, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[disp_role]
    with c_btn:
        has_op = audio.get_audio_bytes(supabase, target_role, "opening")
        if st.button("🎁 生成邀請卡", type="primary", use_container_width=True):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True
            
    # 縮小的提示間距
    if not has_op and target_role == "friend": st.caption("⚠️ 尚未錄製口頭禪")
    if target_role == "friend" and len(allowed) == 1: st.info("🔒 累積 20 XP 解鎖家人角色")

    # 邀請卡彈窗
    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        
        # 使用自定義分隔線代替 st.divider 以縮小間距
        st.markdown('<div class="compact-divider"></div>', unsafe_allow_html=True)
        st.success(f"💌 邀請連結 ({disp_role})")
        
        copy_text = f"欸！我做了一個AI分身超像的，點這個連結打電話給我：\n{url}"
        if target_role != "friend": copy_text = f"這是留給你的聲音：\n{url}"

        st.code(url)
        st.text_area("建議文案", value=copy_text)
        if st.button("❌ 關閉"): st.session_state.show_invite = False
        st.markdown('<div class="compact-divider"></div>', unsafe_allow_html=True)
    
    # 使用 CSS 控制的緊湊分隔線
    if not st.session_state.show_invite:
        st.markdown('<div class="compact-divider"></div>', unsafe_allow_html=True)

    # 4. TAB 分頁 (緊湊化)
    t1, t2, t3, t4 = st.tabs(["🧬 聲紋訓練", "💎 等級說明", "📝 人設補完", "🧠 回憶補完"])

    with t1: tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, tier)
    with t2: tab_store.render(supabase, st.session_state.user.user.id, xp)
    with t3: tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t4: tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
