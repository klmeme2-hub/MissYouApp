import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json
import re # 用於正則表達式清洗

# 初始化
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except: pass

def get_tier_config(tier):
    if tier in ['intermediate', 'advanced', 'eternal']:
        return "gemini-1.5-pro", "高階思維"
    return "gemini-1.5-flash", "標準思維"

def transcribe_audio(audio_file):
    try:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcript.text
    except: return ""

def think_and_reply(tier, persona, memories, user_text, has_nick):
    model_name, _ = get_tier_config(tier)
    nick_instr = "回應開頭不要包含暱稱。" if has_nick else "請在開頭自然呼喚對方的暱稱。"
    prompt = f"【角色】{persona}\n【回憶】{memories}\n【規則】1.{nick_instr} 2.語氣自然。\n【用戶】{user_text}"
    try:
        model = genai.GenerativeModel(model_name)
        return model.generate_content(prompt).text
    except Exception as e: return f"思考中斷: {e}"

def generate_crosstalk_script(question, user_answer, member_name):
    """生成雙人相聲劇本 (JSON格式) - 強壯解析版"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    請生成一段「有趣的雙人對話腳本」。
    角色 A：{member_name} (性格：調皮、愛吐槽、自信)
    角色 B：訪客 (性格：反應快、或者在找藉口)
    
    情境：
    {member_name} 出了一道腦筋急轉彎：「{question}」
    訪客的回答是：「{user_answer}」
    
    邏輯判斷：
    1. 如果訪客說「谷哥大神」或「天靈靈地靈靈」：代表他不知道，{member_name} 就要嘲笑他求神問卜也沒用，並公佈答案。
    2. 如果訪客回答了答案（例如西瓜）：判斷對錯。對了就稱讚(或懷疑偷看)，錯了就吐槽。
    3. 如果訪客亂說話：就針對亂說的話互虧。
    
    【重要】請直接回傳 JSON 格式列表，不要有 markdown 標記，格式如下：
    [
        {{"speaker": "member", "text": "{member_name} 的回應"}},
        {{"speaker": "guest", "text": "訪客的回應"}},
        {{"speaker": "member", "text": "{member_name} 的結語"}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # --- 關鍵修復：清洗 JSON 字串 ---
        # 1. 移除 ```json 和 ``` 標記
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        # 2. 有時候 AI 會在前後加雜訊，嘗試用正則抓取 [ ... ] 的部分
        match = re.search(r'\[.*\]', clean_text, re.DOTALL)
        if match:
            clean_text = match.group()
            
        return json.loads(clean_text)
        
    except Exception as e:
        print(f"AI Script Error: {e}") # 在後台印出錯誤以便除錯
        # 只有真的失敗時才回傳備用劇本
        return [
            {"speaker": "member", "text": f"這題是 {question} 欸！"},
            {"speaker": "guest", "text": f"我剛剛說 {user_answer} 你沒聽到嗎？"},
            {"speaker": "member", "text": "訊號不好啦，我們再來一題！"}
        ]
