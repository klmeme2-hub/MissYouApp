import streamlit as st
from modules import ui, database, audio

def render(supabase, client, user_id, target_role, tier, xp, question_db):
    if tier == 'basic' and xp < 20:
        st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        return

    q_list = question_db.get(target_role, [])
    memories = database.get_memories_by_role(supabase, target_role)
    answered_qs = set()
    for m in memories:
        if "【關於" in m['content'] and "】：" in m['content']:
            answered_qs.add(m['content'].split("【關於")[1].split("】：")[0])

    if "edit_target" not in st.session_state: st.session_state.edit_target = None
    
    current_q = None
    if st.session_state.edit_target:
        current_q = st.session_state.edit_target
        st.info(f"✏️ 正在重新錄製：{current_q}")
    else:
        for q in q_list:
            if q not in answered_qs:
                current_q = q
                break
    
    if len(q_list) > 0:
        st.progress(len(answered_qs) / len(q_list), text=f"進度：{len(answered_qs)} / {len(q_list)}")

    col_l, col_r = st.columns([1.5, 1], gap="medium")
    
    with col_l:
        st.markdown("### 🎙️ 進行中任務")
        if current_q:
            ui.render_question_card(current_q, len(answered_qs)+1, len(q_list))
            
            audio_ans = st.audio_input("錄音回答", key=f"mem_ans_{current_q}")
            if "trans_text" not in st.session_state: st.session_state.trans_text = ""
            
            if audio_ans:
                trans = client.audio.transcriptions.create(model="whisper-1", file=audio_ans)
                st.session_state.trans_text = trans.text
                
                st.text_area("文字確認", value=st.session_state.trans_text, key="mem_edit")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🔊 試聽 AI 唸"):
                        ai_voice = audio.generate_speech(st.session_state.trans_text, tier)
                        st.audio(ai_voice, format="audio/mp3")
                with c2:
                    if st.button("💾 存入並訓練", type="primary"):
                        database.save_memory_fragment(supabase, target_role, current_q, st.session_state.trans_text)
                        audio_ans.seek(0)
                        audio.train_voice_sample(audio_ans.read())
                        st.success("已儲存")
                        st.session_state.edit_target = None
                        st.session_state.trans_text = ""
                        st.rerun()
            
            if st.button("⏭️ 跳過"):
                database.save_memory_fragment(supabase, target_role, current_q, "(已略過)")
                st.rerun()
        else:
            st.success("🎉 所有題目已完成！")

    with col_r:
        st.markdown("### 📜 回憶存摺")
        with st.container(height=500):
            for mem in memories:
                if "【關於" in mem['content']:
                    try:
                        q = mem['content'].split("【關於")[1].split("】：")[0]
                        a = mem['content'].split("】：")[1]
                        ui.render_history_card(q, a)
                        if st.button("🔄 重錄", key=f"mem_re_{mem['id']}"):
                            st.session_state.edit_target = q
                            st.rerun()
                    except: pass
