import streamlit as st
import json
import time
import datetime
from openai import OpenAI
import extra_streamlit_components as stx

# 引入模組 (保持架構乾淨)
from modules import ui, auth, database, audio, brain, config
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory, tab_config

# ==========================================
# 應用程式：想念 (SaaS Modular V3 - 精簡路由版)
# ==========================================

st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="🤍", layout="wide")
ui.load_css()

# 1. 初始化 Cookie 管理器
cookie_manager = stx.CookieManager()

# 2. 系統檢查 & 初始化
if "SUPABASE_URL" not in st.secrets: st.stop()
supabase = database.init_supabase()
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}
question_db = load_questions()

# 3. 狀態初始化
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1
if "show_invite" not in st.session_state: st.session_state.show_invite = False # 控制邀請卡開關

# ==========================================
# 邏輯路由
# ==========================================

# ------------------------------------------
# 情境 A: 親友訪客模式
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_key = owner_data['role']
    owner_id = owner_data['owner_id']
    
    # 讀取資料
    profile = database.get_user_profile(supabase, user_id=owner_id)
    daily_msg = database.check_daily_interaction(supabase, owner_id)
    if daily_msg: st.toast(daily_msg, icon="📅")
    
    # 顯示狀態列
    ui.render_status_bar(profile.get('tier'), profile.get('energy'), 0, audio.get_tts_engine_type(profile), is_guest=True)
    
    # 讀取顯示名稱 (修正：顯示會員設定的暱稱，而非角色名)
    persona_data = database.load_persona(supabase, role_key)
    display_name = persona_data.get('member_nickname', "會員") if persona_data else "會員"
    
    if profile.get('energy') <= 0:
        st.error("💔 心靈電量已耗盡...")
        # (此處省略儲值按鈕UI代碼，保持精簡)
    else:
        st.markdown(f"<h2 style='text-align:center;'>📞 與 [{display_name}] 通話中...</h2>", unsafe_allow_html=True)
        if not persona_data:
            st.warning("對方尚未設定資料。")
        else:
            # 這裡簡單處理，實際對話邏輯建議也封裝
            col_c1, col_c2 = st.columns([1, 2])
            with col_c1: st.image("https://cdn-icons-png.flaticon.com/512/607/607414.png", width=150)
            with col_c2: st.info(f"這是 {display_name} 留給您的聲音。\n每次對話消耗 1 點電量。")
            
            # (對話錄音區塊 - 略，請參考上一版或封裝至 modules/chat.py)
            # 為了讓程式能跑，這裡放個佔位符
            st.info("🎙️ [對話功能運作中...]") 

    st.divider()
    if st.button("🚪 離開"):
        st.session_state.guest_data = None
        st.rerun()

# ------------------------------------------
# 情境 B: 未登入 (首頁)
# ------------------------------------------
elif not st.session_state.user:
    # 讀取 Cookie
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    saved_token = cookies.get("guest_token", "")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    # 左：親友
    with col1:
        st.markdown("## 👋 我是親友")
        token_input = st.text_input("通行碼", value=saved_token, placeholder="A8K29")
        if st.button("🚀 開始對話", type="primary", use_container_width=True):
            data = database.validate_token(supabase, token_input.strip())
            if data:
                cookie_manager.set("guest_token", token_input.strip(), expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                st.rerun()
            else: st.error("無效通行碼")

    # 右：會員
    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        with tab_l:
            with st.form("login_form"):
                l_e = st.text_input("Email", value=saved_email)
                l_p = st.text_input("密碼", type="password")
                if st.form_submit_button("登入", use_container_width=True):
                    res = auth.login_user(supabase, l_e, l_p)
                    if res and res.user:
                        cookie_manager.set("member_email", l_e, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                        st.session_state.user = res
                        st.rerun()
                    else: st.error("登入失敗")
        # (註冊區塊省略，同上版)

# ------------------------------------------
# 情境 C: 會員後台 (加入新佈局與文案)
# ------------------------------------------
else:
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    
    with st.sidebar:
        st.write(f"👤 {st.session_state.user.user.email}")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    ui.render_status_bar(tier, profile.get('energy'), xp, audio.get_tts_engine_type(profile))
    
    # 權限判斷
    is_unlocked = True
    if tier == 'basic' and xp < 20: is_unlocked = False
    
    # ==========================================
    # 【重點修改】頂部控制台 (7:3 佈局 + 邀請卡)
    # ==========================================
    c_role, c_btn = st.columns([7, 3])
    
    with c_role:
        role_options = list(config.ROLE_MAPPING.keys())
        selected_role_display = st.selectbox("選擇對象", role_options, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[selected_role_display] # 轉成英文代號
    
    with c_btn:
        if st.button("🎁 生成邀請卡", type="primary", use_container_width=True):
            # 生成 Token 並展開區塊
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True

    # 鎖定提示
    if not is_unlocked and target_role != "friend":
        st.info("🔒 累積 **20 點 XP** 或 **付費升級**，即可解鎖此角色。")

    # --- 數位邀請卡 (動態展開) ---
    if st.session_state.show_invite:
        token = st.session_state.get("current_token", "LOADING")
        app_url = "https://missyou.streamlit.app"
        
        # 【重點修改】四套感性文案邏輯
        if target_role == "friend":
            title = "嘿！賭你分不出來！"
            body = f"欸，最近 AI 真的太誇張了！🤯\n我訓練了一個我的「數位分身」，連我的口頭禪都學會了。\n你去聽聽看，打個分數，看能不能騙過你的耳朵？"
            ps = "(進去記得選「不像」不要給我面子 😂)"
        elif target_role == "partner":
            title = "給親愛的你：一個永遠的承諾"
            body = f"親愛的，有些話如果不說，我怕以後沒機會說。\n我在這裡留下了一些聲音和回憶，這裡住著一部分的我。\n如果哪天我不在身邊，隨時打開這裡，我會一直陪著你。"
            ps = "(這是我給你的，專屬禮物 ❤️)"
        elif target_role == "junior":
            title = "給寶貝：老爸/老媽永遠都在"
            body = f"孩子，世界很大，有時候會很累對吧？\n我把我的經驗和聲音都存在這裡了。\n無論你長多大，遇到什麼困難，這裡永遠有一個聲音願意聽你說話，永遠為你加油。"
            ps = "(記得，家永遠是你的後盾 💪)"
        elif target_role == "elder":
            title = "給親愛的長輩：換我來陪您"
            body = f"謝謝您們辛苦把我養大。\n我知道我有時候工作忙，沒辦法天天陪在您身邊。\n所以我用現在的科技，把我的聲音留在了這裡。\n想我的時候，只要點開這裡，我就會像在家一樣，陪您聊天。"
            ps = "(您只要負責講話就好，我會聽 ❤️)"
        else:
            title = "來自我的數位分身"
            body = "我在這裡留下了一些聲音，希望能陪你聊聊天。"
            ps = ""

        full_copy = f"""【{title}】\n\n{body}\n\n🔗 傳送門：{app_url}\n🔑 通關密碼：{token}\n\n{ps}"""

        st.markdown("---")
        with st.container():
            st.success(f"### 💌 您的數位邀請卡已生成 ({selected_role_display})")
            c_text, c_copy = st.columns([4, 1])
            with c_text:
                st.code(full_copy, language="text")
            with c_copy:
                st.button("❌ 關閉", on_click=lambda: st.session_state.update({"show_invite": False}))
                st.caption("👆 點擊右上角複製")
        st.markdown("---")

    # ==========================================
    # 下方功能 Tab (完全模組化調用)
    # ==========================================
    st.divider()
    t1, t2, t3, t4, t5 = st.tabs(["🧬 聲紋訓練", "💎 分享解鎖", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"])

    with t1: tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, st.secrets['VOICE_ID'], st.secrets['ELEVENLABS_API_KEY'])
    with t2: tab_store.render(supabase, st.session_state.user.user.id, xp)
    with t3: tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t4: tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
    with t5: tab_config.render(supabase, tier, xp)
