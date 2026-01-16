import streamlit as st
import base64
import os
from modules import ui, database, audio, config, gamification
from modules.tabs import tab_voice, tab_store, tab_persona, tab_memory

def get_base64_encoded_image(image_path):
    """將圖片轉為 Base64 (用於 HTML 顯示)"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except: return None

def render(supabase, client, question_db):
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    user_id = st.session_state.user.user.id
    
    # ==========================================
    # 1. Header (Logo + 標題)
    # ==========================================
    
    # 準備 Logo
    logo_html = ""
    if os.path.exists("logo.png"):
        img_b64 = get_base64_encoded_image("logo.png")
        if img_b64:
            # Logo 大小設定為 50px
            logo_html = f'<img src="data:image/png;base64,{img_b64}" style="width: 50px; height: 50px; object-fit: contain; margin-right: 15px;">'
    if not logo_html:
        logo_html = '<span style="font-size: 40px; margin-right: 15px;">♾️</span>'

    # 使用 HTML 佈局標題，不使用 columns，避免對齊問題
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        {logo_html}
        <div>
            <div style="font-size: 32px; font-weight: 700; color: #FFF; line-height: 1.2;">聲紋ID刻錄室</div>
            <div style="font-size: 14px; color: #B0B0B0; font-weight: 400;">這不僅僅是錄音，這是將你的聲紋數據化，作為你在數位世界唯一的身份識別</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 【已移除右上角 Email】

    # ==========================================
    # 2. 控制台 (角色選擇 + 生成按鈕)
    # ==========================================
    
    # 為了計算相似度傳給狀態列，我們需要先知道目前選了誰
    # 這裡調整順序：先渲染選擇器，再渲染狀態列
    
    allowed = ["朋友/死黨"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    # 使用 columns 排版控制台
    c_role, c_btn = st.columns([7, 3], vertical_alignment="bottom")
    
    with c_role:
        disp_role = st.selectbox("選擇對象", allowed, label_visibility="collapsed")
        target_role = config.ROLE_MAPPING[disp_role]
    
    with c_btn:
        # 生成邀請卡按鈕
        if st.button("🎁 生成邀請卡", type="primary", use_container_width=True):
            token = database.create_share_token(supabase, target_role)
            st.session_state.current_token = token
            st.session_state.show_invite = True

    # ==========================================
    # 3. 狀態列 (現在可以正確計算相似度了)
    # ==========================================
    
    # 計算相似度
    sim_score, sim_hint, sim_gain = gamification.calculate_similarity(supabase, user_id, target_role)
    
    # 顯示狀態列 (相似度已移至左側)
    ui.render_status_bar(tier, energy, xp, audio.get_tts_engine_type(profile), sim_score, sim_hint, sim_gain)
    
    # 提示訊息
    has_op = audio.get_audio_bytes(supabase, target_role, "opening")
    if not has_op and target_role == "friend": st.caption("⚠️ 尚未錄製口頭禪")

    # 邀請卡彈窗
    if st.session_state.show_invite:
        tk = st.session_state.get("current_token", "ERR")
        pd = database.load_persona(supabase, target_role)
        mn = pd.get('member_nickname', '我') if pd else '我'
        url = f"https://missyou.streamlit.app/?token={tk}_{mn}"
        
        st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
        st.success(f"💌 邀請連結 ({disp_role})")
        copy_text = f"欸！點這個連結打電話給我：\n{url}"
        st.code(url)
        st.text_area("建議文案", value=copy_text)
        if st.button("❌ 關閉"): st.session_state.show_invite = False
    
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)

    # ==========================================
    # 4. Tab 分頁
    # ==========================================
    t1, t2, t3, t4 = st.tabs(["🧬 聲紋訓練", "📝 人設補完", "🧠 回憶補完", "💎 等級說明"])

    with t1: 
        tab_voice.render(supabase, client, st.session_state.user.user.id, target_role, tier)
    with t2: 
        tab_persona.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp)
    with t3: 
        tab_memory.render(supabase, client, st.session_state.user.user.id, target_role, tier, xp, question_db)
    with t4: 
        tab_store.render(supabase, st.session_state.user.user.id, xp)

    # ==========================================
    # 5. 底部登出區
    # ==========================================
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.divider()
    
    c_email, c_logout = st.columns([8, 2], vertical_alignment="center")
    
    with c_email:
        # Email 顯示在這裡
        st.markdown(f"<div style='text-align:right; color:#666; font-size:14px;'>目前登入：{st.session_state.user.user.email}</div>", unsafe_allow_html=True)
        
    with c_logout:
        if st.button("登出", key="footer_logout", use_container_width=True):
            # 這裡只設定狀態，由 app.py 執行登出
            st.session_state.logout_clicked = True
            st.rerun()
