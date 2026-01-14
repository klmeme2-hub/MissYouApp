import streamlit as st
import random
import time
import datetime
from modules import ui, database, audio, brain
import extra_streamlit_components as stx

def render(supabase, client, teaser_db):
    # 為了存 Cookie，需要在這裡初始化 manager (或從 app.py 傳入，這裡簡化直接 new)
    cookie_manager = stx.CookieManager(key="guest_cookie_mgr")
    
    owner_data = st.session_state.guest_data
    role_key = owner_data['role'] 
    owner_id = owner_data['owner_id']
    url_name = owner_data.get('display_name', '朋友')
    
    profile = database.get_user_profile(supabase, user_id=owner_id)
    tier = profile.get('tier', 'basic')
    energy = profile.get('energy', 0)
    persona_data = database.load_persona(supabase, role_key)
    display_name = persona_data.get('member_nickname', url_name) if persona_data else url_name

    # Header
    st.markdown("""<div class="brand-header"><div style="font-size: 30px;">♾️</div><div><div class="header-title" style="font-size: 24px !important;">EchoSoul · 聲紋ID刻錄室</div></div></div>""", unsafe_allow_html=True)

    # 狀態管理
    if "has_rated" not in st.session_state: st.session_state.has_rated = False
    if "teaser_idx" not in st.session_state: st.session_state.teaser_idx = 0
    if "guest_voice_id" not in st.session_state: st.session_state.guest_voice_id = None
    if "crosstalk_audio" not in st.session_state: st.session_state.crosstalk_audio = None
    if "teaser_stage" not in st.session_state: st.session_state.teaser_stage = "answer"
    
    teasers = teaser_db.get("brain_teasers", [])

    # 1. 開場白 & 評分
    if not st.session_state.has_rated and role_key == "friend":
        # ... (維持原有的評分邏輯，省略以節省篇幅，請保留上一版內容) ...
        # 這裡為了演示，直接放簡化版
        if "opening_played" not in st.session_state:
            op_bytes = audio.get_audio_bytes(supabase, role_key, "opening")
            ai_ask = audio.generate_speech("你覺得這個AI分身像不像？幫我打個分數。", tier)
            final = audio.merge_audio_clips(op_bytes, ai_ask) if op_bytes else ai_ask
            if final: st.audio(final, format="audio/mp3", autoplay=True)
            st.session_state.opening_played = True
            
        ui.render_status_bar(tier, energy, 0, "elevenlabs", is_guest=True, member_name=display_name)
        st.markdown("---")
        st.markdown("### ⭐ 聽完請評分 (解鎖功能)")
        if st.button("😱 像到發毛 (5分)", type="primary", use_container_width=True):
            database.submit_feedback(supabase, owner_id, 5, "朋友評分")
            st.session_state.has_rated = True
            st.rerun()

    # 2. 主要功能
    else:
        ui.render_status_bar(tier, energy, 0, "elevenlabs", is_guest=True, member_name=display_name)
        
        if role_key != "friend":
            # 家人模式 (維持原樣)
            st.info("家人模式對話區")
        else:
            tab_teaser, tab_parrot = st.tabs(["🧠 腦力激盪", "🦜 九官鳥"])
            
            with tab_teaser:
                # ... (維持原有的腦筋急轉彎邏輯) ...
                current_q = teasers[st.session_state.teaser_idx % len(teasers)]
                ui.render_question_card(current_q['q'], st.session_state.teaser_idx + 1, len(teasers), hint=current_q['hint'])
                
                # (這裡省略中間的錄音/生成邏輯，請保留上一版代碼)
                
                # 【修改重點】註冊按鈕邏輯
                if st.session_state.get("crosstalk_audio"):
                    st.audio(st.session_state.crosstalk_audio, format="audio/mp3")
                    st.warning("⚠️ 聲紋 ID 暫時生成中")
                    
                    if st.button(f"🔥 註冊綁定 (幫{display_name} +10 XP)", type="primary", use_container_width=True):
                        # 1. 暫存 Voice ID 到 Cookie
                        if st.session_state.guest_voice_id:
                            cookie_manager.set("pending_voice_id", st.session_state.guest_voice_id, expires_at=datetime.datetime.now() + datetime.timedelta(days=1))
                        
                        # 2. 清除訪客狀態
                        st.session_state.guest_data = None
                        
                        # 3. 【關鍵】清除網址參數，強制跳回首頁
                        st.query_params.clear()
                        st.rerun()

            with tab_parrot:
                # ... (九官鳥邏輯維持原樣) ...
                st.caption("九官鳥模式")

    st.divider()
