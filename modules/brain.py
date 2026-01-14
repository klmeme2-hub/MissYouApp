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
    # 統一使用 gemini-pro 以求穩定
    return "gemini-pro", "Gemini Pro"

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
    except Exception as e:
        return f"思考暫時中斷 ({e})"

def generate_crosstalk_script(question, correct_answer, user_answer, member_name):
    """
    生成雙人相聲劇本 (JSON格式) - 解除安全限制 + 強力除錯版
    """
    model = genai.GenerativeModel("gemini-pro")
    
    # 【關鍵 1】解除安全限制：允許 AI 吐槽、開玩笑
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
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
        # 帶入 safety_settings
        response = model.generate_content(prompt, safety_settings=safety_settings)
        
        # 檢查是否被阻擋
        if not response.text:
            raise ValueError(f"AI 回傳空值，可能被安全過濾。Feedback: {response.prompt_feedback}")

        raw_text = response.text

        # 清洗 JSON
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        match = re.search(r'\[.*\]', clean_text, re.DOTALL)
        if match:
            clean_json = match.group()
            return json.loads(clean_json)
        else:
            raise ValueError("無法解析 JSON 格式")
            
    except Exception as e:
        # 【關鍵 2】將錯誤顯示在螢幕上，而不是默默吞掉
        print(f"Script Gen Error: {e}")
        st.toast(f"⚠️ AI 罷工了，錯誤原因: {e}", icon="🤖")
        
        return get_fallback_script(correct_answer, user_answer)

def get_fallback_script(correct_answer, user_answer):
    """備用劇本"""
    return [
        {"speaker": "member", "text": f"這題答案明明就是 {correct_answer}！"},
        {"speaker": "guest", "text": f"我剛剛也是想講這個啦！"},
        {"speaker": "member", "text": "少來，我明明聽到你說 {user_answer}！"}
    ]
