import streamlit as st
from modules import database

def render(supabase, client, user_id, target_role, tier, xp):
    # 權限檢查
    if tier == 'basic' and xp < 20:
        st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        return

    st.info("上傳 LINE 對話紀錄 (.txt)，讓 AI 學習您的口頭禪與用詞習慣。")
    
    # 連結教學 (可選)
    # st.caption("[教學連結] 如何匯出 LINE 對話紀錄?")

    # 1. 讀取使用者設定的名字 (LINE顯示名稱)
    # 因為移除了暱稱欄位，這裡我們讓版面變寬，只留一個輸入框
    member_name = st.text_input("您的名字 (在LINE對話中的顯示名稱)", value="爸爸", key="per_mn", help="AI 需要知道哪一句話是您說的，請輸入您在聊天紀錄中的名字。")
    
    # 2. 自動讀取 Tab 1 設定的「專屬暱稱」
    # 用途：告訴 GPT-4o 必須用這個暱稱稱呼對方
    saved_persona = database.load_persona(supabase, target_role)
    target_nickname = "寶貝" # 預設值
    if saved_persona and saved_persona.get('member_nickname'):
        target_nickname = saved_persona['member_nickname']
        
    # 顯示目前系統認知的暱稱 (唯讀，讓會員知道 AI 會怎麼叫他)
    st.caption(f"ℹ️ 系統已綁定稱呼：AI 將會稱呼您為 **「{target_nickname}」** (若需修改請至「聲紋訓練」Step 1)")

    # 3. 檔案上傳
    up_file = st.file_uploader("上傳紀錄檔", type="txt", key="per_up")
    
    # 4. 按鈕與執行邏輯
    # 修改按鈕文字為強調 GPT-4o
    if st.button("✨ 啟動 GPT-4o 建立人設"):
        if up_file and member_name:
            with st.spinner("GPT-4o 正在閱讀並分析語氣特徵..."):
                try:
                    # 讀取檔案
                    raw = up_file.read().decode("utf-8")
                    
                    # 構建 Prompt
                    prompt = f"""
                    分析對話紀錄。
                    主角(我)：{member_name}
                    對象：{target_role}
                    
                    【任務目標】：
                    1. 分析【主角】的說話風格（口頭禪、語氣助詞、長短句習慣、常用表情符號）。
                    2. 針對主角的個性生成一段 System Prompt。
                    3. 【重要】：強制要求 AI 在對話中，必須使用暱稱「{target_nickname}」來稱呼對方。
                    
                    資料片段：
                    {raw[-25000:]} 
                    """
                    # 取最後 25000 字元 (GPT-4o Context 很大，可以多吃一點)

                    # 呼叫 GPT-4o
                    res = client.chat.completions.create(
                        model="gpt-4o", 
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    # 存入資料庫 (只更新 content, 不動 member_nickname)
                    # 這裡使用 load_persona 讀取到的 nickname 再次傳入以防萬一，或直接只更新 content
                    # 為了安全，我們呼叫 save_persona_summary 時保留原有的 nickname
                    database.save_persona_summary(supabase, target_role, res.choices[0].message.content, member_nickname=target_nickname)
                    
                    # 成功訊息
                    st.success("✅ 已使用 GPT-4o 建立人設")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"分析失敗，請檢查檔案格式。錯誤：{e}")
        else:
            st.warning("請填寫您的名字並上傳檔案")
