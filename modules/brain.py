import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json
import re

# 初始化
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except: pass

def get_tier_config(tier):
    # 預設回傳配置
    return "gemini-1.5-flash", "標準思維"

def transcribe_audio(audio_file):
    """語音轉文字 (Whisper)"""
    try:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcript.text
    except: return ""

def think_and_reply(tier, persona, memories, user_text, has_nick):
    """一般對話 (優先用 Gemini，失敗轉 OpenAI)"""
    try:
        # 1. 嘗試 Google Gemini
        model = genai.GenerativeModel("gemini-1.5-flash")
        nick_instr = "回應開頭不要包含暱稱。" if has_nick else "請在開頭自然呼喚對方的暱稱。"
        prompt = f"【角色】{persona}\n【回憶】{memories}\n【規則】1.{nick_instr} 2.語氣自然。\n【用戶】{user_text}"
        return model.generate_content(prompt).text
    except:
        # 2. 失敗則用 OpenAI 救援
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"{persona}\n{user_text}"}]
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"思考暫時中斷: {e}"

def generate_crosstalk_script(question, correct_answer, user_answer, member_name):
    """
    生成雙人相聲劇本 (正式版 - 使用 OpenAI GPT-4o-mini)
    """
    
    prompt = f"""
    你現在是台灣最幽默的短劇編劇。請生成一段「3句話」的微型相聲腳本。
    
    【角色設定】
    A ({member_name})：個性調皮、毒舌、喜歡吐槽，講話帶點台味。
    B (訪客)：個性反應快、或者喜歡找藉口、偶爾會裝傻。
    
    【當前狀況】
    1. {member_name} 出了一題腦筋急轉彎：「{question}」
    2. 標準答案是：「{correct_answer}」
    3. 訪客剛剛的回答(或反應)是：「{user_answer}」
    
    【編劇邏輯】
    1. 如果訪客回答包含「天靈靈」、「麥克風測試」、「聽不清楚」：
       -> 這是因為系統剛剛引導他唸咒語。請 A 吐槽 B 居然真的乖乖唸咒語，B 說這是召喚靈感，最後 A 公佈答案並虧 B 笨。
    2. 如果訪客回答了答案：
       -> 請判斷對錯。
       -> 答對：A 很驚訝，懷疑 B 偷看答案，B 則表現得很得意。
       -> 答錯：A 瘋狂吐槽或給出超明顯提示，B 硬拗說自己是在測試 A 知不知道。
    
    【JSON 輸出格式要求】
    請回傳一個 JSON 物件，包含一個鍵值 "dialogue"，內容是列表。範例：
    {{
        "dialogue": [
            {{"speaker": "member", "text": "哇靠！你是不是偷看劇本？"}},
            {{"speaker": "guest", "text": "拜託，這種小兒科題目，我用膝蓋想都知道。"}},
            {{"speaker": "member", "text": "少來，下次出個難一點的！"}}
        ]
    }}
    """
    
    try:
        # 使用 OpenAI 生成 (穩定性最高)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)

        # 智慧解析 JSON
        if isinstance(data, list): return data
        if isinstance(data, dict):
            for key in ['dialogue', 'script', 'conversation', 'lines']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            for value in data.values():
                if isinstance(value, list):
                    return value

        raise ValueError("JSON 格式不符")
        
    except Exception as e:
        print(f"Script Error: {e}")
        return get_fallback_script(correct_answer, user_answer)

def get_fallback_script(correct_answer, user_answer):
    """備用劇本"""
    return [
        {"speaker": "member", "text": f"這題答案明明就是 {correct_answer}！"},
        {"speaker": "guest", "text": f"我剛剛也是想講這個啦！"},
        {"speaker": "member", "text": "少來，別以為我不知道你在想什麼！"}
    ]
