import streamlit as st
import json
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
# 引入新的 Tab 模組 (請確保您已建立這些檔案，若還沒，請先建立空檔案)
from modules.tabs import tab_config 
# from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory (之後補齊)

# 1. UI 設定
st.set_page_config(page_title="想念", page_icon="🤍", layout="wide")
ui.load_css()

# 2. 系統初始化
if "SUPABASE_URL" not in st.secrets: st.stop()
supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 3. 狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None

# ==========================================
# 邏輯路由
# ==========================================

# 情境 A: 親友訪客模式
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    
    # 取得資料
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    
    # 【關鍵修正】讀取人設資料 (包含 member_nickname)
    persona_data = database.load_persona(supabase, role_name)
    
    # 決定顯示名稱
    display_name = "會員" # 預設
    if persona_data and persona_data.get('member_nickname'):
        display_name = persona_data['member_nickname']
    
    # 顯示正確的標題
    st.markdown(f"<h2 style='text-align:center;'>📞 與 [{display_name}] 通話中...</h2>", unsafe_allow_html=True)
    
    # 電子雞邏輯 & 狀態列
    daily_msg = database.check_daily_interaction(supabase, owner_id)
    if daily_msg: st.toast(daily_msg)
    engine_type = audio.get_tts_engine_type(profile)
    ui.render_status_bar(tier, energy, 0, engine_type, is_guest=True)
    
    if energy <= 0:
        st.error("💔 電量耗盡...")
        # ... (儲值按鈕邏輯)
    else:
        if not persona_data:
            st.warning("對方尚未設定資料。")
        else:
            col_c1, col_c2 = st.columns([1, 2])
            with col_c1: st.image("https://cdn-icons-png.flaticon.com/512/607/607414.png", width=150)
            with col_c2: st.info(f"這是 {display_name} 留給您的聲音。\n每次對話消耗 1 點電量。")

            # ... (對話錄音與生成邏輯，與之前相同，略) ...
            # 這裡之後可以把 對話邏輯 也封裝進 modules/chat.py 會更乾淨

    st.divider()
    if st.button("🚪 離開"):
        st.session_state.guest_data = None
        st.rerun()

# 情境 B: 首頁 (登入/註冊)
elif not st.session_state.user:
    # ... (維持之前的登入/註冊/Cookie邏輯) ...
    # 為了節省篇幅，請保留原有的登入代碼
    pass 

# 情境 C: 會員後台
else:
    # ... (側邊欄與標題) ...
    
    # 分頁管理
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧬 聲紋訓練", "💎 分享解鎖", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"])
    
    # 使用模組呼叫 (乾淨！)
    with tab1:
        st.write("聲紋訓練模組 (請建立 modules/tabs/tab_voice.py)")
        # tab_voice.render(...) 
        
    with tab5:
        # 呼叫我們剛剛寫好的新模組
        tab_config.render(supabase, tier, xp=0) # 傳入 xp 參數
