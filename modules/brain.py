import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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
    """生成雙人相聲劇本 (JSON格式)"""
    model = genai.GenerativeModel("gemini-1.5-flash") # 用 Flash 比較快
    
    prompt = f"""
    請生成一段「有趣的雙人對話腳本」。
    角色 A：{member_name} (性格：調皮、愛吐槽、自信)
    角色 B：訪客 (性格：聰明、反擊、無奈)
    
    情境：
    {member_name} 出了一道腦筋急轉彎：「{question}」
    訪客回答：「{user_answer}」
    
    請判斷訪客回答是否正確 (或是沾上邊)。
    生成一段 3-4 句的對話。
    如果答對：{member_name} 表示驚訝或懷疑偷看，訪客表示得意。
    如果答錯：{member_name} 嘲笑或提示，訪客找藉口。
    
    【重要】請直接回傳 JSON 格式列表，不要有其他文字：
    [
        {{"speaker": "member", "text": "{member_name} 說的話"}},
        {{"speaker": "guest", "text": "訪客說的話"}},
        {{"speaker": "member", "text": "{member_name} 的結語"}}
    ]
    """
    try:
        response = model.generate_content(prompt)
        # 清理 markdown 標記
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except:
        # Fallback script
        return [
            {"speaker": "member", "text": "哎唷，居然有反應？"},
            {"speaker": "guest", "text": "當然啊，這題太簡單了。"},
            {"speaker": "member", "text": "算你厲害，下一題看我不考倒你！"}
        ]
