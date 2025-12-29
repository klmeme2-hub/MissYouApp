import streamlit as st
import json
import time
import datetime
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config
import extra_streamlit_components as stx

# ==========================================
# 應用程式：MetaVoice (SaaS Stable - UI Fix)
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

# 狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False
if "current_token" not in st.session_state: st.session_state.current_token = None
if "call_status" not in st.session_state: st.session_state.call_status = "ringing"
if "friend_stage" not in st.session_state: st.session_state.friend_stage = "listen"

# 1. 網址攔截 (略，維持原樣)
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
# 情境 A: 訪客模式 (UI 微調)
# ------------------------------------------
if st.session_state.guest_data:
    # (此處與上一版相同，為節省篇幅省略)
    # 請直接複製上一版的情境 A 邏輯
    pass # 記得補回代碼

# ------------------------------------------
# 情境 B: 未登入
# ------------------------------------------
elif not st.session_state.user:
    # (此處與上一版相同，為節省篇幅省略)
    pass # 記得補回代碼

# ------------------------------------------
# 情境 C: 會員後台 (重點修正區)
# ------------------------------------------
else:
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    
    # --- 1. Header 區塊 (修正圖示與對齊) ---
    c_head, c_user = st.columns([7, 3])
    
    with c_head:
        # 使用 Emoji 代替圖片，解決白方塊問題
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="font-size: 40px;">🌌</div>
            <div>
                <div class="header-title">元宇宙聲紋站</div>
                <div class="header-subtitle">元宇宙的第一張通行證：鎸刻你的數位聲紋</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_user:
        # 使用 ui.py 定義的 .user-info-box 進行對齊
        st.markdown(f"""
        <div class="user-info-box">
            <div class="user-email">{st.session_state.user.user.email}</div>
        </div>
        """, unsafe_allow_html=True)
        # 按鈕獨立放在下面，透過 CSS user-info-box 的 flex-end 靠右對齊有點難，
        # 這裡改用 columns 硬排比較穩
        c_null, c_btn = st.columns([1, 1])
        with c_btn:
            if st.button("登出", use_container_width=True):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()

    # --- 2. 狀態列 ---
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile))
    
    # --- 3. 控制台 (對齊修正) ---
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    c_role, c_btn = st.columns([7, 3], vertical_alignment="bottom") # 關鍵：底部對齊
    
    with c_role:
        disp_role = st.selectbox("選擇對象", allowed)
        target_role = config.ROLE_MAPPING[disp_role]
    
    has_op = audio.get_audio_bytes(supabase, target_role, "opening")
    
    with c_btn:
        if st.button("🎁 生成邀請卡", type="primary", use_container_width=True):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True

    if not has_op and target_role == "friend": st.caption("⚠️ 尚未錄製口頭禪")

    if st.session_state.show_invite:
        # (邀請卡顯示邏輯同前，略)
        pass

    # --- 4. Tab 分頁 (修正 Stepper 顯示) ---
    t1, t2, t3, t4 = st.tabs(["🧬 聲紋訓練", "💎 等級說明", "📝 人設補完", "🧠 回憶補完"])

    with t1: tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, tier)
    with t2: tab_store.render(supabase, st.session_state.user.user.id, xp)
    with t3: tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t4: tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
