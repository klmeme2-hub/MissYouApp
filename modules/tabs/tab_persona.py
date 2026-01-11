import streamlit as st
import json
from modules import database, audio

def render(supabase, client, user_id, target_role, tier, xp):
    # 權限檢查
    if tier == 'basic' and xp < 20:
        st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        return

    st.info("上傳 LINE 對話紀錄 (.txt)，讓 AI 學習您的口頭禪與用詞習慣。")
    
    # 1. 讀取使用者設定的名字
    member_name = st.text_input("您的名字 (在LINE對話中的顯示名稱)", value="爸爸", key="per_mn", help="AI 需要知道哪一句話是您說的。")
    
    # 2. [邏輯保留，UI 隱藏] 讀取 Tab 1 設定的身分
    # 我們需要這個值來存檔，但不需要顯示給使用者看
    saved_persona = database.load_persona(supabase, target_role)
    current_identity = "我"
    if saved_persona and saved_persona.get('member_nickname'):
        current_identity = saved_persona['member_nickname']
    
    # 這裡移除了 st.caption 顯示身分的代碼

    # 3. 檔案上傳
    up_file = st.file_uploader("上傳紀錄檔", type="txt", key="per_up")
    
    # 4. 執行按鈕
    if st.button("✨ 啟動 GPT-4o 建立人設"):
        if up_file and member_name:
            with st.spinner("GPT-4o 正在閱讀回憶、尋找感動瞬間..."):
                try:
                    # 讀取檔案
                    raw = up_file.read().decode("utf-8")
                    
                    # 構建 Prompt (JSON 格式)
                    prompt = f"""
                    分析這份 LINE 對話紀錄。
                    
                    【角色定義】：
                    - 主角 (我)：{member_name}
                    - 對話對象：{target_role}
                    
                    【任務目標】：
                    1. **語氣分析**：深度模仿【主角】的說話風格（口頭禪、語氣助詞、斷句習慣）。
                    2. **稱呼規範**：在生成的對話中，請一律使用「我」自稱，並用「你」稱呼對方。
                    3. **回憶提取**：請從對話中找出一段具體、溫馨或有趣的「往事」（例如一起去過哪裡、吃過什麼、發生的小意外）。
                    
                    【輸出格式 (JSON)】：
                    請直接回傳以下 JSON 格式，不要有其他文字：
                    {{
                        "system_prompt": "你現在扮演... (請填入完整的人設指令)",
                        "flashback": "還記得那天..." (請填入提取出的往事，用口語表達，約 30-50 字)
                    }}
                    
                    資料片段：
                    {raw[-30000:]} 
                    """

                    # 呼叫 GPT-4o (強制 JSON 模式)
                    response = client.chat.completions.create(
                        model="gpt-4o", 
                        messages=[{"role": "user", "content": prompt}],
                        response_format={ "type": "json_object" }
                    )
                    
                    # 解析結果
                    result = json.loads(response.choices[0].message.content)
                    sys_prompt = result.get('system_prompt', '')
                    flashback_text = result.get('flashback', '')
                    
                    # 1. 存入資料庫
                    database.save_persona_summary(supabase, target_role, sys_prompt, member_nickname=current_identity)
                    
                    # 2. 準備驚喜 (語音生成 + 拼接)
                    nick_bytes = audio.get_audio_bytes(supabase, target_role, "nickname")
                    
                    # 生成往事語音
                    flashback_audio = audio.generate_speech(flashback_text, tier)
                    
                    # 拼接
                    final_audio = flashback_audio
                    if nick_bytes and flashback_audio:
                        final_audio = audio.merge_audio_clips(nick_bytes, flashback_audio)

                    # 3. 呈現結果 (文案更新)
                    st.success("✅ 已使用 GPT-4o 建立人設")
                    st.balloons()
                    
                    st.markdown("---")
                    st.markdown("### 😲 AI 好像想起了什麼...")
                    st.info(f"🗣️ **{current_identity}**：\n\n{flashback_text}")
                    
                    if final_audio:
                        st.audio(final_audio, format="audio/mp3", autoplay=True)
                    
                except Exception as e:
                    st.error(f"分析失敗，請檢查檔案格式。錯誤：{e}")
        else:
            st.warning("請填寫您的名字並上傳檔案")
