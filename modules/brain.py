import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import os

# 初始化 Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_tier_config(tier):
    """
    根據等級決定模型配置
    【修改】：中級 (intermediate) 升級為 Pro
    """
    # 只要是中級、高級、永恆，都用最強大腦
    if tier in ['intermediate', 'advanced', 'eternal']:
        return "gemini-1.5-pro", "高階思維 (Pro)"
    
    # 初級使用 Flash (省成本，速度快)
    return "gemini-1.5-flash", "標準思維 (Flash)"

def transcribe_audio(audio_file):
    try:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcript.text
    except: return ""

def think_and_reply(tier, persona, memories, user_text, has_nick):
    model_name, _ = get_tier_config(tier)
    
    nick_instr = "回應開頭不要包含對方的暱稱或打招呼，直接講內容。" if has_nick else "請在開頭自然呼喚對方的暱稱。"
    
    prompt = f"""
    【角色設定】：
    {persona}
    
    【過往回憶資料庫】：
    {memories}
    
    【當前對話規則】：
    1. {nick_instr}
    2. 語氣要像真人，包含語助詞、呼吸感。
    3. 如果回憶資料庫有相關內容，請具體引用細節。
    
    【使用者說】：{user_text}
    """
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"思考卡住了... ({e})"
