import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json
import re

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

def generate_crosstalk_script(question, correct_answer, user_answer, member_name):
    """
    生成雙人相聲劇本 (JSON格式) - 注入靈魂版
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    你現在是台灣最幽默的短劇編劇。請生成一段「3句話」的微型相聲腳本。
    
    【角色設定】
    A (會員-{member_name})：個性調皮、毒舌、喜歡吐槽，講話帶點台味。
    B (訪客)：個性反應快、或者喜歡找藉口、偶爾會裝傻。
    
    【當前狀況】
    題目：{question}
    標準答案：{correct_answer}
    訪客的回答：{user_answer}
    
    【判斷邏輯】
    1. 先判斷訪客回答是否正確 (或是意思相近)。
    2. 如果訪客回答包含「天靈靈」、「谷哥大神」、「不知道」：
       -> A 嘲笑 B 求神問卜也沒用，B 反駁說是在召喚靈感，最後 A 公佈答案並虧 B 笨。
    3. 如果訪客 **答對**：
       -> A 很驚訝，懷疑 B 偷看答案或由狗屎運，B 則表現得很得意。
    4. 如果訪客 **答錯**：
       -> A 瘋狂吐槽或給出超明顯提示，B 硬拗說自己是在測試 A 知不知道。
    
    【絕對禁止】
    1. **禁止** A 重複念一次題目。
    2. **禁止** 過於客套的對話。
    
    【JSON 輸出格式範例 (請嚴格遵守)】
    [
        {{"speaker": "member", "text": "哇靠！你是不是偷看劇本？這題連我都想了三秒欸！"}},
        {{"speaker": "guest", "text": "拜託，這種小兒科題目，我用膝蓋想都知道是{correct_answer}好嗎？"}},
        {{"speaker": "member", "text": "少來，下次出個難一點的看你還能不能囂張！"}}
    ]
    
    請直接回傳 JSON，不要有 Markdown 標記。
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # 清洗 JSON
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        match = re.search(r'\[.*\]', clean_text, re.DOTALL)
        if match: clean_text = match.group()
            
        return json.loads(clean_text)
        
    except Exception as e:
        print(f"Script Gen Error: {e}")
        # 備用劇本 (萬一 AI 掛了)
        return [
            {"speaker": "member", "text": "哎唷，這麼有自信？"},
            {"speaker": "guest", "text": f"那是當然，答案不就是 {correct_answer} 嗎？"},
            {"speaker": "member", "text": "算你厲害，這局算你贏！"}
        ]
