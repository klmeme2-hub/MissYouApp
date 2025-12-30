import streamlit as st
import requests
import io
from openai import OpenAI
from pydub import AudioSegment
from .auth import get_current_user_id
from .config import ROLE_MAPPING

def get_tts_engine_type(profile):
    """
    決定語音引擎
    【修改】：為了體驗感，全體會員(含初級)皆使用擬真版
    """
    return "elevenlabs"

def generate_speech(text, tier):
    """
    生成語音
    【修改】：優先使用 ElevenLabs，OpenAI 僅作備用
    """
    # 1. 優先嘗試 ElevenLabs (擬真)
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
        headers = {
            "xi-api-key": st.secrets['ELEVENLABS_API_KEY'], 
            "Content-Type": "application/json"
        }
        data = {
            "text": text, 
            "model_id": "eleven_multilingual_v2", 
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.75}
        }
        res = requests.post(url, json=data, headers=headers)
        
        if res.status_code == 200:
            return res.content
        else:
            print(f"ElevenLabs Error: {res.text}")
    except Exception as e:
        print(f"ElevenLabs Connection Error: {e}")
    
    # 2. 備用方案：OpenAI TTS (如果 ElevenLabs 掛了或沒錢了)
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response.content
    except Exception as e:
        print(f"OpenAI TTS Error: {e}")
        return None

# --- 真實音訊處理 (維持不變) ---

def upload_audio_file(supabase, role, audio_bytes, file_type="nickname"):
    user_id = get_current_user_id()
    if not user_id: return False
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/{file_type}_{safe_role}.mp3"
        supabase.storage.from_("audio_clips").upload(
            file_path, audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        return True
    except: return False

def get_audio_bytes(supabase, role, file_type="nickname"):
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/{file_type}_{safe_role}.mp3"
        return supabase.storage.from_("audio_clips").download(file_path)
    except: return None

def train_voice_sample(audio_bytes):
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{st.secrets['VOICE_ID']}/edit"
        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY']}
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        requests.post(url, headers=headers, data={'name': 'Clone'}, files=files)
        return True
    except: return False

def merge_audio_clips(intro_bytes, main_bytes):
    try:
        if not intro_bytes or len(intro_bytes) < 100: return main_bytes
        intro = AudioSegment.from_file(io.BytesIO(intro_bytes))
        main = AudioSegment.from_file(io.BytesIO(main_bytes))
        silence = AudioSegment.silent(duration=200)
        combined = intro + silence + main
        buffer = io.BytesIO()
        combined.export(buffer, format="mp3")
        return buffer.getvalue()
    except: return main_bytes
