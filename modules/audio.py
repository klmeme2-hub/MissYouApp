import streamlit as st
import requests
import io
from openai import OpenAI
from pydub import AudioSegment
from .auth import get_current_user_id
from .config import ROLE_MAPPING

def get_tts_engine_type(profile):
    """決定語音引擎"""
    if not profile: return "openai"
    tier = profile.get('tier', 'basic')
    if tier in ['advanced', 'eternal', 'intermediate']: return "elevenlabs"
    return "openai"

def generate_speech(text, tier):
    """生成語音 (雙引擎)"""
    engine = "elevenlabs" if tier in ['intermediate', 'advanced', 'eternal'] else "openai"

    if engine == "elevenlabs":
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
            headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
            data = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.7}}
            res = requests.post(url, json=data, headers=headers)
            if res.status_code == 200: return res.content
        except: pass
    
    # OpenAI Fallback
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        return response.content
    except: return None

# --- 通用音訊處理 (新版功能) ---

def upload_audio_file(supabase, role, audio_bytes, file_type="nickname"):
    """通用上傳函數"""
    user_id = get_current_user_id()
    if not user_id: return False
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/{file_type}_{safe_role}.mp3"
        supabase.storage.from_("audio_clips").upload(
            file_path, audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        return True
    except Exception as e:
        print(f"Upload Error: {e}")
        return False

def get_audio_bytes(supabase, role, file_type="nickname"):
    """通用下載函數"""
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/{file_type}_{safe_role}.mp3"
        return supabase.storage.from_("audio_clips").download(file_path)
    except: return None

# --- 舊版兼容函數 (為了讓 app.py 其他部分不報錯) ---

def upload_nickname_audio(supabase, role, audio_bytes):
    return upload_audio_file(supabase, role, audio_bytes, "nickname")

def get_nickname_audio_bytes(supabase, role):
    return get_audio_bytes(supabase, role, "nickname")

# --- 訓練與剪輯 ---

def train_voice_sample(audio_bytes):
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{st.secrets['VOICE_ID']}/edit"
        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY']}
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        data = {'name': 'My Digital Clone'} 
        requests.post(url, headers=headers, data=data, files=files)
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
