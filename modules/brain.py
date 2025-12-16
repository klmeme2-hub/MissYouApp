import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import os

# 初始化 Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 這裡也初始化 OpenAI 供 Whisper 用 (或之後轉用 Gemini Audio)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_tier_config(tier):
    """根據等級決定模型配置"""
    if tier in ['advanced', 'eternal']:
        return "gemini-1.5-pro", "高階思維"
    return "gemini-1.5-flash", "標準思維"

def transcribe_audio(audio_file):
    """目前為了穩定，先維持使用 OpenAI Whisper 轉文字"""
    # 雖然 Gemini 可以直接聽，但在 Streamlit 介面顯示文字對話框比較直觀
    try:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcript.text
    except: return ""

def think_and_reply(tier, persona, memories, user_text, has_nick):
    """
    雙引擎大腦：
    Basic -> Gemini Flash (省錢)
    Advanced -> Gemini Pro (聰明)
    """
    model_name, _ = get_tier_config(tier)
    
    # 建構 Prompt (Google 風格)
    nick_instr = "回應開頭不要包含對方的暱稱或打招呼，直接講內容。" if has_nick else "請在開頭自然呼喚對方的暱稱。"
    
    # 組合 Context (全量記憶：Gemini 很大，可以直接塞進去)
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
