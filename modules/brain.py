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
    # 這裡可以根據需求切換，目前李白測試用不到
    return "gemini-1.5-flash", "標準思維"

def transcribe_audio(audio_file):
    try:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcript.text
    except: return ""

def think_and_reply(tier, persona, memories, user_text, has_nick):
    try:
        # 簡單對話用 Gemini
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model.generate_content(f"{persona}\n{user_text}").text
    except:
        # Fallback
        return "我正在思考..."

def generate_crosstalk_script(question, correct_answer, user_answer, member_name):
    """
    生成雙人相聲劇本 (OpenAI 李白測試版 - 強力格式修正)
    """
    
    prompt = f"""
    請生成一段「2人接力背誦李白詩句」的對話腳本。
    
    角色 A：{member_name}
    角色 B：訪客
    
    情境：
    不管 {member_name} 出什麼題，也不管訪客回答什麼 ({user_answer})。
    請讓這兩人突然開始莫名其妙地接力背誦李白的《靜夜思》。
    
    【JSON 輸出格式要求】
    請回傳一個 JSON 物件，包含一個鍵值 "dialogue"，內容是列表。範例：
    {{
        "dialogue": [
            {{"speaker": "member", "text": "哎呀別說了，床前明月光！"}},
            {{"speaker": "guest", "text": "疑...疑是地上霜？"}},
            {{"speaker": "member", "text": "舉頭望明月，低頭思故鄉。背得好啊！"}}
        ]
    }}
    """
    
    try:
        # 使用 OpenAI 生成
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)

        # --- 關鍵修正：智慧解析 ---
        # 情況 1: 直接回傳了列表 (List)
        if isinstance(data, list):
            return data
            
        # 情況 2: 回傳了字典 (Dict)，嘗試尋找內部的列表
        if isinstance(data, dict):
            # 常見的 key
            for key in ['dialogue', 'script', 'conversation', 'lines']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            
            # 如果找不到常見 key，就找第一個是 list 的 value
            for value in data.values():
                if isinstance(value, list):
                    return value

        # 如果都沒找到，拋出異常，使用備用劇本
        raise ValueError("JSON 格式不符")
        
    except Exception as e:
        print(f"Script Error: {e}")
        return get_fallback_script()

def get_fallback_script():
    """絕對安全的備用劇本"""
    return [
        {"speaker": "member", "text": "測試模式啟動：床前明月光。"},
        {"speaker": "guest", "text": "疑是地上霜。"},
        {"speaker": "member", "text": "舉頭望明月，低頭思故鄉。測試成功！"}
    ]
