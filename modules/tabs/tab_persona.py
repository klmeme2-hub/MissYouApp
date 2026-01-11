import streamlit as st
import json
from modules import database, audio

def render(supabase, client, user_id, target_role, tier, xp):
    if tier == 'basic' and xp < 20:
        st.warning("🔒 需升級或累積 20 XP 解鎖此功能")
        return

    st.info("上傳 LINE 對話紀錄 (.txt)，讓 AI 學習您的口頭禪與用詞習慣。")
    
    # 1. 讀取使用者設定的名字
    member_name = st.text_input("您的名字 (在LINE對話中的顯示名稱)", value="爸爸", key="per_mn", help="AI 需要知道哪一句話是您說的。")
    
    # 2. 顯示身分與檢查錄音 (新增區塊)
    saved_persona = database.load_persona(supabase, target_role)
    current_identity = "我"
    if saved_persona and saved_persona.get('member_nickname'):
        current_identity = saved_persona['member_nickname']
    
    st.markdown(f"ℹ️ **當前身分設定：** AI 將顯示為 **「{current_identity}」**")

    # 【新增】檢查目前已存的真實暱稱
    nick_bytes = audio.get_audio_bytes(supabase, target_role, "nickname")
    if nick_bytes:
        st.caption("🎵 目前已儲存的開頭暱稱 (若不對請至聲紋訓練重錄)：")
        st.audio(nick_bytes, format="audio/mp3")
    else:
        st.caption("⚠️ 尚未錄製此角色的完美暱稱 (AI 將無法拼接真實聲音)")

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
                    2. **稱呼規範**：在生成的對話中，請一律使用「我」自稱，並用「你」稱呼對方。**絕對不要**在句子中加入對方的名字或暱稱（因為系統會在語音開頭自動拼接真實呼喚）。
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

                    # 呼叫 GPT-4o
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
                    
                    # 2. 生成往事語音
                    flashback_audio = audio.generate_speech(flashback_text, tier)
                    
                    # 3. 拼接：[真實暱稱] + [AI往事]
                    final_audio = flashback_audio
                    if nick_bytes and flashback_audio:
                        final_audio = audio.merge_audio_clips(nick_bytes, flashback_audio)

                    # 4. 呈現結果
                    st.success("✅ 已使用 GPT-4o 建立人設")
                    st.balloons()
                    
                    st.markdown("---")
                    st.markdown("### 😲 AI 好像想起了什麼...")
                    st.info(f"🗣️ **{current_identity}**：\n\n{flashback_text}")
                    
                    if final_audio:
                        st.audio(final_audio, format="audio/mp3", autoplay=True)
                        st.caption("🔊 (聽聽看，這是不是你說話的感覺？)")
                    
                except Exception as e:
                    st.error(f"分析失敗：{e}")
        else:
            st.warning("請填寫您的名字並上傳檔案")
