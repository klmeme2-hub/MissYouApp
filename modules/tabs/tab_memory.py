import streamlit as st
from modules import ui, database, audio
import time

def render(supabase, client, user_id, target_role, tier, xp, question_db):
    # 權限檢查
    if tier == 'basic' and xp < 20:
        st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        return

    # 1. 準備資料
    q_list = question_db.get(target_role, [])
    # 這裡抓回來的資料已經是按時間倒序排列 (最新的在最上面)
    memories = database.get_memories_by_role(supabase, target_role)
    
    # 找出已回答的題目集合 (用來過濾左邊的題目)
    answered_qs = set()
    for m in memories:
        content = m.get('content', '')
        # 寬鬆判斷：只要包含【關於...】格式就視為已回答
        if "【關於" in content and "】：" in content:
            try:
                q_part = content.split("【關於")[1].split("】：")[0]
                answered_qs.add(q_part)
            except:
                pass

    # 2. 狀態管理：編輯模式
    if "edit_target" not in st.session_state: 
        st.session_state.edit_target = None
    
    # 決定當前要顯示的題目
    current_q = None
    if st.session_state.edit_target:
        current_q = st.session_state.edit_target
        st.info(f"✏️ 正在重新錄製：**{current_q}**")
    else:
        # 自動找下一題沒回答的
        for q in q_list:
            if q not in answered_qs:
                current_q = q
                break
    
    # 進度條顯示
    if len(q_list) > 0:
        progress = len(answered_qs) / len(q_list)
        st.progress(progress, text=f"回憶補完進度：{len(answered_qs)} / {len(q_list)}")

    # --- 介面分欄 ---
    col_l, col_r = st.columns([1.5, 1], gap="medium")
    
    # ==========================
    # 左欄：進行中任務 (Active)
    # ==========================================
    with col_l:
        st.markdown("### 🎙️ 進行中任務")
        
        if current_q:
            # 顯示題目卡片
            ui.render_question_card(current_q, len(answered_qs)+1, len(q_list))
            
            # 錄音元件
            # 注意：key 必須包含 current_q 避免切換題目時狀態殘留
            audio_ans = st.audio_input("錄音回答", key=f"mem_ans_{current_q}")
            
            # 初始化暫存文字
            if "trans_text" not in st.session_state: 
                st.session_state.trans_text = ""
            
            if audio_ans:
                # 轉文字
                with st.spinner("語音轉文字中..."):
                    trans = client.audio.transcriptions.create(model="whisper-1", file=audio_ans)
                    st.session_state.trans_text = trans.text
                
                # 讓用戶編輯/確認文字
                final_text = st.text_area("文字確認 (可修改)", value=st.session_state.trans_text, key="mem_edit_area")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🔊 試聽 AI 語氣"):
                        with st.spinner("生成試聽中..."):
                            # 使用當前等級對應的引擎試聽
                            ai_voice = audio.generate_speech(final_text, tier)
                            if ai_voice:
                                st.audio(ai_voice, format="audio/mp3")
                
                with c2:
                    if st.button("💾 存入並訓練", type="primary", use_container_width=True):
                        with st.spinner("正在寫入記憶庫並訓練 Voice ID..."):
                            # 1. 存入資料庫
                            database.save_memory_fragment(supabase, target_role, current_q, final_text)
                            
                            # 2. 訓練聲音
                            audio_ans.seek(0)
                            audio.train_voice_sample(audio_ans.read())
                            
                            st.success("✅ 已儲存！")
                            st.balloons()
                            
                            # 重置狀態
                            st.session_state.edit_target = None
                            st.session_state.trans_text = ""
                            time.sleep(1) # 稍作停留讓用戶看到成功訊息
                            st.rerun()
            
            # 跳過按鈕
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("⏭️ 跳過此題 (以後再答)"):
                database.save_memory_fragment(supabase, target_role, current_q, "(已略過)")
                st.rerun()
        else:
            st.success("🎉 太棒了！此角色的所有題庫已全部完成。")
            if st.button("想要再多說一點？(自由錄製模式)"):
                # 未來可擴充自由錄製功能
                st.info("敬請期待自由錄製功能")

    # ==========================
    # 右欄：回憶存摺 (History) - 關鍵修復區
    # ==========================
    with col_r:
        st.markdown("### 📜 回憶存摺")
        
        # 方案 B: 空狀態提示
        if not memories:
            st.info("📭 目前還沒有回憶紀錄。\n\n請從左側開始回答第一個問題吧！")
        
        else:
            st.caption(f"已收錄 {len(memories)} 則回憶 (點擊可重錄)")
            
            with st.container(height=600): # 固定高度讓捲軸在內部
                for mem in memories:
                    content = mem.get('content', '')
                    item_id = mem.get('id')
                    
                    # 方案 A: 強壯解析邏輯
                    question_text = "未知題目"
                    answer_text = content # 預設顯示全部內容
                    
                    # 嘗試解析標準格式
                    if "【關於" in content and "】：" in content:
                        try:
                            # split(..., 1) 確保只切分第一個冒號，避免答案裡也有冒號被切斷
                            parts = content.split("】：", 1)
                            q_part = parts[0].replace("【關於", "").strip()
                            a_part = parts[1].strip()
                            
                            question_text = q_part
                            answer_text = a_part
                        except:
                            # 解析失敗就維持預設值，不報錯
                            pass
                    
                    # 渲染卡片
                    ui.render_history_card(question_text, answer_text)
                    
                    # 重錄按鈕
                    # 使用 columns 讓按鈕小一點並靠右
                    c_space, c_btn = st.columns([2, 1])
                    with c_btn:
                        if st.button("🔄 重錄", key=f"re_{item_id}", help="重新回答此題"):
                            st.session_state.edit_target = question_text
                            st.rerun()
