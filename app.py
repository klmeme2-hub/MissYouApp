import streamlit as st
import json
import requests
import io
import time
import datetime # 補上 datetime 模組
from openai import OpenAI
from modules import ui, auth, database, audio, brain, config
import extra_streamlit_components as stx

# ==========================================
# 應用程式：想念 (SaaS Beta 2.3 - 記憶帳密修復版)
# 更新內容：修復 st.cache_resource 參數報錯問題
# ==========================================

st.set_page_config(page_title="想念 - 靈魂刻錄室", page_icon="🤍", layout="wide")
ui.load_css()

# 1. 初始化 Cookie 管理器 (修正版)
# 直接初始化即可，不需要使用 cache_resource 裝飾器，因為 stx 內部已經處理了狀態
cookie_manager = stx.CookieManager()

# 2. 系統檢查
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

# 狀態管理
if "user" not in st.session_state: st.session_state.user = None
if "guest_data" not in st.session_state: st.session_state.guest_data = None
if "step" not in st.session_state: st.session_state.step = 1

# ==========================================
# 邏輯路由
# ==========================================

# ------------------------------------------
# 情境 A: 親友訪客模式
# ------------------------------------------
if st.session_state.guest_data:
    owner_data = st.session_state.guest_data
    role_name = owner_data['role']
    owner_id = owner_data['owner_id']
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    
    daily_msg = database.check_daily_interaction(supabase, owner_id)
    if daily_msg: st.toast(daily_msg, icon="📅")
    
    engine_type = audio.get_tts_engine_type(profile)
    ui.render_status_bar(tier, energy, profile.get('xp',0), engine_type, is_guest=True)
    
    if energy <= 0:
        st.error("💔 心靈電量已耗盡...")
        st.markdown(f"""<div style='text-align:center; padding:30px; background:#262730; border-radius:10px; border:1px solid #FF4B4B;'><h3>⚠️ 訊號中斷</h3><p>請幫 {role_name} 補充能量。</p></div>""", unsafe_allow_html=True)
        if st.button("模擬儲值 (測試)"):
            database.update_profile_stats(supabase, owner_id, energy_delta=100)
            st.rerun()
    else:
        st.markdown(f"<h2 style='text-align:center;'>📞 與 [{role_name}] 通話中...</h2>", unsafe_allow_html=True)
        persona = database.load_persona(supabase, role_name)
        
        if not persona:
            st.warning("對方尚未設定資料。")
        else:
            col_c1, col_c2 = st.columns([1, 2])
            with col_c1: st.image("https://cdn-icons-png.flaticon.com/512/607/607414.png", width=150)
            with col_c2: st.info(f"這是 {role_name} 留給您的聲音。\n每次對話消耗 1 點電量。")

            if "chat_history" not in st.session_state: st.session_state.chat_history = []

            audio_val = st.audio_input("請按此說話...", key="guest_rec")
            if audio_val:
                try:
                    database.update_profile_stats(supabase, owner_id, energy_delta=-1)
                    user_text = brain.transcribe_audio(audio_val)
                    if len(user_text.strip()) > 1:
                        with st.spinner("思考中..."):
                            memories = database.get_all_memories_text(supabase, role_name)
                            has_nick = audio.get_nickname_audio_bytes(supabase, role_name) is not None
                            ai_text = brain.think_and_reply(tier, persona, memories, user_text, has_nick)
                            raw_audio = audio.generate_speech(ai_text, tier)
                            
                            final_audio = raw_audio
                            if has_nick and raw_audio:
                                nick_bytes = audio.get_nickname_audio_bytes(supabase, role_name)
                                if nick_bytes: final_audio = audio.merge_audio_clips(nick_bytes, raw_audio)
                            
                            st.session_state.chat_history.append({"role": "user", "content": user_text})
                            st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                            
                            if final_audio: st.audio(final_audio, format="audio/mp3", autoplay=True)
                            st.markdown(f'<div class="ai-bubble">{ai_text}</div>', unsafe_allow_html=True)
                except Exception as e: st.error(f"Error: {e}")

    st.divider()
    if st.button("🚪 離開通話"):
        st.session_state.guest_data = None
        st.rerun()

# ------------------------------------------
# 情境 B: 首頁 (訪客驗證 / 會員登入)
# ------------------------------------------
elif not st.session_state.user:
    
    # 嘗試讀取 Cookie
    # 注意：第一次載入可能讀不到，這是正常的，stx 需要 re-render 才能拿到值
    cookies = cookie_manager.get_all()
    saved_email = cookies.get("member_email", "")
    saved_token = cookies.get("guest_token", "")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    # 左側：親友入口
    with col1:
        st.markdown("## 👋 我是親友")
        st.caption("輸入家人分享給您的邀請碼")
        
        token_input = st.text_input("通行碼", value=saved_token, placeholder="例如：A8K29")
        
        if st.button("🚀 開始對話", type="primary", use_container_width=True):
            data = database.validate_token(supabase, token_input.strip())
            if data:
                # 寫入 Cookie (有效期 30 天)
                cookie_manager.set("guest_token", token_input.strip(), expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.session_state.guest_data = {'owner_id': data['user_id'], 'role': data['role']}
                st.success("驗證成功！")
                time.sleep(0.5)
                st.rerun()
            else: st.error("無效的通行碼")

    # 右側：會員入口 (Form 支援瀏覽器記憶)
    with col2:
        st.markdown("## 👤 我是會員")
        tab_l, tab_s = st.tabs(["登入", "註冊"])
        
        with tab_l:
            with st.form("login_form"):
                l_e = st.text_input("Email", value=saved_email)
                l_p = st.text_input("密碼", type="password")
                submitted = st.form_submit_button("登入", use_container_width=True)
                
                if submitted:
                    res = auth.login_user(supabase, l_e, l_p)
                    if res and res.user: 
                        # 寫入 Cookie
                        cookie_manager.set("member_email", l_e, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                        st.session_state.user = res
                        st.success("登入成功")
                        time.sleep(0.5)
                        st.rerun()
                    else: st.error("登入失敗")
        
        with tab_s:
            s_e = st.text_input("Email", key="s_e")
            s_p = st.text_input("設定密碼", type="password", key="s_p")
            if st.button("註冊", use_container_width=True):
                res = auth.signup_user(supabase, s_e, s_p)
                if res and res.user:
                    database.get_user_profile(supabase, res.user.id)
                    st.session_state.user = res
                    st.success("註冊成功！")
                    st.rerun()
                else: st.error("註冊失敗")

# ------------------------------------------
# 情境 C: 會員後台
# ------------------------------------------
else:
    profile = database.get_user_profile(supabase)
    tier = profile.get('tier', 'basic')
    xp = profile.get('xp', 0)
    energy = profile.get('energy', 30)
    
    with st.sidebar:
        st.write(f"👤 {st.session_state.user.user.email}")
        if st.button("登出"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.title("🎙️ 靈魂刻錄室")
    
    engine_type = audio.get_tts_engine_type(profile)
    ui.render_status_bar(tier, energy, xp, engine_type)
    
    allowed = ["朋友"]
    if tier != 'basic' or xp >= 20: allowed = list(config.ROLE_MAPPING.keys())
    
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1: target_role = st.selectbox("選擇對象", allowed)
    
    if target_role == "朋友" and len(allowed) == 1:
        st.info("🔒 累積 **20 點 XP** 或 **付費升級**，即可解鎖「家人」角色。")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧬 聲紋訓練", "💎 分享解鎖完整版", "📝 人設補完", "🧠 回憶補完", "🎯 完美暱稱"])

    # TAB 1: 聲紋
    with tab1:
        cols = st.columns(5)
        steps = ["❶ 喚名", "❷ 安慰", "❸ 鼓勵", "❹ 詼諧", "❺ 完成"]
        for i, s in enumerate(steps):
            if i + 1 == st.session_state.step: cols[i].markdown(f"**<span style='color:#FF4B4B; font-size:18px;'>{s}</span>**", unsafe_allow_html=True)
            else: cols[i].markdown(f"<span style='color:#666'>{s}</span>", unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.step == 1:
            st.subheader("STEP 1: 輕輕喚你的名")
            lbl = "錄下您的招牌口頭禪" if target_role == "朋友" else "錄下您呼喚對方的暱稱"
            hint = "例如：搞什麼鬼～" if target_role == "朋友" else "例如：老婆～"
            nickname_text = st.text_input(lbl, placeholder=hint)
            rec = st.audio_input("錄音 (建議 2-3 秒)")
            if rec and nickname_text:
                if st.button("💾 上傳並試聽"):
                    with st.spinner("處理中..."):
                        audio_bytes = rec.read()
                        audio.upload_nickname_audio(supabase, target_role, audio_bytes)
                        rec.seek(0)
                        audio.train_voice_sample(rec.read())
                        database.update_profile_stats(supabase, st.session_state.user.user.id, xp_delta=1, log_reason="完成Step1")
                        ai_audio = audio.generate_speech("最近好嗎？", tier)
                        final = audio.merge_audio_clips(audio_bytes, ai_audio)
                        st.audio(final, format="audio/mp3")
                        st.success("聲紋已建立！")
            if st.button("下一步 →"): st.session_state.step = 2; st.rerun()

        elif st.session_state.step in [2, 3, 4]:
            scripts = {
                2: ("刻錄「安慰語氣」", "欸，我知道你現在心裡一定超悶的啦..."),
                3: ("刻錄「鼓勵語氣」", "哇塞！你真的決定要開始學那個東西了喔？..."),
                4: ("刻錄「輕鬆詼諧語氣」", "我跟你說，我昨天去圖書館 K 書，真的糗死了啦！...")
            }
            title, content = scripts[st.session_state.step]
            st.subheader(title)
            st.markdown(f'<div class="script-box">{content}</div>', unsafe_allow_html=True)
            rec = st.audio_input("請朗讀上方文字", key=f"s{st.session_state.step}")
            if rec:
                if st.button("💾 上傳訓練"):
                    with st.spinner("訓練 Voice ID 中..."):
                        audio.train_voice_sample(rec.read())
                        database.update_profile_stats(supabase, st.session_state.user.user.id, xp_delta=1, log_reason=f"Step{st.session_state.step}")
                        st.success("已上傳 (+1 XP)")
            c1, c2 = st.columns(2)
            with c1: 
                if st.button("← 上一步"): st.session_state.step -= 1; st.rerun()
            with c2: 
                if st.button("下一步 →" if st.session_state.step < 4 else "完成訓練 →"): st.session_state.step += 1; st.rerun()

        elif st.session_state.step == 5:
            st.balloons()
            st.markdown(f"""<div style='text-align:center; padding:30px; background-color:#262730; border:1px solid #4CAF50; border-radius:15px;'><h2 style='color:#4CAF50;'>🎉 恭喜！模型已完成。</h2><p>您可以分享給【{target_role}】了。</p></div>""", unsafe_allow_html=True)
            st.divider()
            if "share_token" not in st.session_state or st.session_state.get("share_role") != target_role:
                st.session_state.share_token = database.create_share_token(supabase, target_role)
                st.session_state.share_role = target_role
            token = st.session_state.share_token
            st.code(f"https://missyou.streamlit.app\n邀請碼：{token}\n\n一定要來幫我打個分數喔~", language="text")
            if st.button("← 返回重錄"): st.session_state.step = 1; st.rerun()

    # TAB 2: 商業
    with tab2:
        st.subheader("💎 會員權益")
        c1, c2, c3 = st.columns(3)
        with c1:
            ui.render_dashboard_card("免費解鎖", "20 XP")
            if st.button("檢查 XP"): 
                if xp>=20: st.success("符合資格")
                else: st.error(f"還差 {20-xp} XP")
        with c2:
            ui.render_dashboard_card("中級守護者", "$99")
            if st.button("💰 付費解鎖中級"):
                database.upgrade_tier(supabase, st.session_state.user.user.id, "intermediate", 99, 20)
                st.rerun()
        with c3:
            ui.render_dashboard_card("高級刻錄師", "$599")
            if st.button("💰 付費解鎖高級"):
                database.upgrade_tier(supabase, st.session_state.user.user.id, "advanced", 599, 20)
                st.rerun()
        st.divider()
        if st.button("生成邀請碼 (賺XP)"):
            token = database.create_share_token(supabase, target_role)
            st.code(token)

    # TAB 3: 人設
    with tab3:
        if tier == 'basic' and xp < 20: st.warning("🔒 需升級或累積 20 XP")
        else:
            c1, c2 = st.columns(2)
            with c1: mn = st.text_input("您的名字", value="爸爸")
            with c2: nk = st.text_input("專屬暱稱", placeholder="例如：寶貝")
            up = st.file_uploader("上傳紀錄", type="txt")
            if st.button("✨ 更新人設") and up:
                with st.spinner("分析中..."):
                    raw = up.read().decode("utf-8")
                    prompt = f"分析主角({mn})對{target_role}的說話風格。生成System Prompt。重點：模仿語氣，使用暱稱{nk}。資料：{raw[-20000:]}"
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    database.save_persona_summary(supabase, target_role, res.choices[0].message.content)
                    st.success("完成")

    # TAB 4: 回憶
    with tab4:
        if tier == 'basic' and xp < 20: st.warning("🔒 需升級或累積 20 XP")
        else:
            q_list = question_db.get(target_role, [])
            memories = database.get_memories_by_role(supabase, target_role)
            answered = set()
            for m in memories:
                if "【關於" in m['content']: answered.add(m['content'].split("【關於")[1].split("】：")[0])
            
            if "edit_target" not in st.session_state: st.session_state.edit_target = None
            curr_q = st.session_state.edit_target
            if not curr_q:
                for q in q_list:
                    if q not in answered: curr_q = q; break
            
            if len(q_list)>0: st.progress(len(answered)/len(q_list))
            
            cl, cr = st.columns([1.5, 1])
            with cl:
                if curr_q:
                    ui.render_question_card(curr_q, len(answered)+1, len(q_list))
                    ans = st.audio_input("回答", key=f"ans_{curr_q}")
                    if ans:
                        trans = client.audio.transcriptions.create(model="whisper-1", file=ans)
                        st.session_state.trans = trans.text
                        st.text_area("文字", value=st.session_state.trans)
                        if st.button("💾 存入"):
                            database.save_memory_fragment(supabase, target_role, curr_q, st.session_state.trans)
                            ans.seek(0)
                            audio.train_voice_sample(ans.read())
                            st.success("OK")
                            st.session_state.edit_target = None
                            st.rerun()
                    if st.button("跳過"): 
                        database.save_memory_fragment(supabase, target_role, curr_q, "(已略過)")
                        st.rerun()
                else: st.success("完成")
            with cr:
                for m in memories:
                    if "【關於" in m['content']:
                        q = m['content'].split("【關於")[1].split("】：")[0]
                        if st.button(f"🔄 {q}", key=f"re_{m['id']}"):
                            st.session_state.edit_target = q
                            st.rerun()

    # TAB 5: 完美暱稱
    with tab5:
        if tier == 'basic' and xp < 20: st.warning("🔒 需升級或累積 20 XP")
        else:
            nick_role = st.selectbox("錄製給誰？", list(config.ROLE_MAPPING.keys()), key="nr")
            rn = st.audio_input("錄音", key="rn")
            if rn and st.button("💾 上傳"):
                if audio.upload_nickname_audio(supabase, nick_role, rn.read()): st.success("成功")
