import streamlit as st
from modules import database

def render(supabase, client, user_id, target_role, tier, xp):
    if tier == 'basic' and xp < 20:
        st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        return

    st.info("上傳 LINE 對話紀錄 (.txt)，讓 AI 學習您的口頭禪與用詞習慣。")
    
    c1, c2 = st.columns(2)
    with c1:
        member_name = st.text_input("您的名字 (在LINE對話中的顯示名稱)", value="爸爸", key="per_mn")
    with c2:
        nickname = st.text_input("專屬暱稱 (AI將用此稱呼對方)", placeholder="例如：寶貝", key="per_nk")
        
    up_file = st.file_uploader("上傳紀錄檔", type="txt", key="per_up")
    
    if st.button("✨ 分析並更新人設"):
        if up_file and member_name:
            with st.spinner("AI 正在閱讀並分析語氣特徵..."):
                raw = up_file.read().decode("utf-8")
                
                prompt = f"""
                分析對話紀錄。
                主角(我)：{member_name}
                對象：{target_role}
                專屬暱稱：{nickname}
                
                任務：
                1. 分析【主角】的說話風格（口頭禪、語氣助詞、長短句習慣）。
                2. 生成 System Prompt 指令。
                3. 強制要求：對象是{target_role}時，必須使用暱稱「{nickname}」稱呼對方。
                
                資料片段：{raw[-20000:]}
                """
                
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                
                # 存入資料庫
                # 這裡只存 content, member_nickname 是在 Tab 5 設定的，這裡不覆蓋它
                database.save_persona_summary(supabase, target_role, res.choices[0].message.content)
                st.success(f"成功！已建立對【{target_role}】的專屬人設。")
        else:
            st.warning("請填寫完整資訊並上傳檔案")
