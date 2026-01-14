import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json
import re # 引入正則表達式

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

def generate_crosstalk_script(question, correct_answer, user_answer, member_name):
    """
    生成雙人相聲劇本 (JSON格式) - 強力清洗版
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    你現在是台灣最幽默的短劇編劇。請生成一段「3句話」的微型相聲腳本。
    
    【角色設定】
    A ({member_name})：個性調皮、毒舌、喜歡吐槽，講話帶點台味。
    B (訪客)：個性反應快、或者喜歡找藉口、偶爾會裝傻。
    
    【當前狀況】
    題目：{question}
    標準答案：{correct_answer}
    訪客的回答：{user_answer}
    
    【判斷邏輯】
    1. 如果訪客回答包含「天靈靈」、「麥克風測試」、「不知道」：
       -> A 嘲笑 B 根本在亂念，B 說是在召喚靈感，最後 A 公佈答案並虧 B 笨。
    2. 如果訪客 **答對** (意思接近{correct_answer})：
       -> A 很驚訝，懷疑 B 偷看答案，B 則表現得很得意。
    3. 如果訪客 **答錯**：
       -> A 瘋狂吐槽或給出超明顯提示，B 硬拗說自己是在測試 A 知不知道。
    
    【輸出格式】
    請只回傳 JSON 列表 (List of Objects)，不要有任何 Markdown (如 ```json)。範例：
    [
        {{"speaker": "member", "text": "哇靠！你是不是偷看劇本？"}},
        {{"speaker": "guest", "text": "拜託，這種小兒科題目，我用膝蓋想都知道。"}},
        {{"speaker": "member", "text": "少來，下次出個難一點的！"}}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        print(f"Gemini Raw: {raw_text}") # Debug用

        # --- 暴力清洗 JSON ---
        # 使用正則表達式，只抓取 [ 和 ] 中間的內容 (含括號)
        match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if match:
            clean_json = match.group()
            return json.loads(clean_json)
        else:
            raise ValueError("No JSON found")
        
    except Exception as e:
        print(f"Script Gen Error: {e}")
        # 備用劇本 (只有在真的掛掉時才用)
        return [
            {"speaker": "member", "text": f"這題答案是 {correct_answer} 啦！"},
            {"speaker": "guest", "text": f"我剛剛也是想講這個！"},
            {"speaker": "member", "text": "聽你在吹牛！"}
        ]
