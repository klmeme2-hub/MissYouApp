import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import json
import re

# 初始化
try:
    # 這裡保留 Google 設定，但下面的生成我們改用 OpenAI
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except: pass

def get_tier_config(tier):
    return "gemini-1.5-flash", "標準思維"

def transcribe_audio(audio_file):
    try:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcript.text
    except: return ""

def think_and_reply(tier, persona, memories, user_text, has_nick):
    # 一般對話維持原樣 (若 Google 失敗可考慮也切換)
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model.generate_content(f"{persona}\n{user_text}").text
    except:
        # Fallback to OpenAI
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"{persona}\n{user_text}"}]
        )
        return res.choices[0].message.content

def generate_crosstalk_script(question, correct_answer, user_answer, member_name):
    """
    生成雙人相聲劇本 - 李白測試版 (使用 OpenAI GPT-4o-mini)
    """
    
    # 這裡我們強制改用 OpenAI，因為它最穩定，不會有 404 問題
    prompt = f"""
    請生成一段「2人接力背誦李白詩句」的對話腳本。
    
    角色 A：{member_name}
    角色 B：訪客
    
    情境：
    不管 {member_name} 出什麼題，也不管訪客回答什麼 ({user_answer})。
    請讓這兩人突然開始莫名其妙地接力背誦李白的《靜夜思》。
    
    要求：
    1. A 先唸第一句。
    2. B 接第二句。
    3. A 唸最後兩句並稱讚 B。
    
    【JSON 輸出格式範例】
    [
        {{"speaker": "member", "text": "哎呀別說了，床前明月光！"}},
        {{"speaker": "guest", "text": "疑...疑是地上霜？"}},
        {{"speaker": "member", "text": "舉頭望明月，低頭思故鄉。背得好啊！"}}
    ]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        content = response.choices[0].message.content
        return json.loads(content).get('scripts', json.loads(content)) # 兼容某些回傳格式
        
    except Exception as e:
        print(f"OpenAI Script Error: {e}")
        # 如果連 OpenAI 都失敗，回傳寫死的李白
        return [
            {"speaker": "member", "text": "測試模式：床前明月光。"},
            {"speaker": "guest", "text": "疑是地上霜。"},
            {"speaker": "member", "text": "舉頭望明月，低頭思故鄉。測試成功！"}
        ]
