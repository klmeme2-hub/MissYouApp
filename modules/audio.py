import streamlit as st
import requests
import io
from openai import OpenAI
from pydub import AudioSegment
from .auth import get_current_user_id
from .config import ROLE_MAPPING

def get_tts_engine_type(profile):
    if not profile: return "openai"
    tier = profile.get('tier', 'basic')
    return "elevenlabs" if tier in ['advanced', 'eternal', 'intermediate'] else "openai"

def generate_speech(text, tier):
    """根據等級生成語音"""
    engine = "elevenlabs" if tier in ['intermediate', 'advanced', 'eternal'] else "openai"
    
    if engine == "elevenlabs":
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
            headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
            data = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.7}}
            res = requests.post(url, json=data, headers=headers)
            if res.status_code == 200: return res.content
        except: pass
    
    try: # Fallback to OpenAI
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        res = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        return res.content
    except: return None

# --- 真實錄音處理 ---

def upload_audio_file(supabase, role, audio_bytes, file_type):
    """file_type: 'opening' (口頭禪) 或 'nickname' (暱稱)"""
    user_id = get_current_user_id()
    if not user_id: return False
    try:
        safe = ROLE_MAPPING.get(role, "others")
        path = f"{user_id}/{file_type}_{safe}.mp3"
        supabase.storage.from_("audio_clips").upload(path, audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"})
        return True
    except: return False

def get_audio_bytes(supabase, role, file_type):
    """讀取音檔 (若訪客模式則讀 owner_id)"""
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        safe = ROLE_MAPPING.get(role, "others")
        path = f"{user_id}/{file_type}_{safe}.mp3"
        return supabase.storage.from_("audio_clips").download(path)
    except: return None

def check_audio_exists(supabase, role, file_type):
    """檢查檔案是否存在 (用於按鈕鎖定)"""
    return get_audio_bytes(supabase, role, file_type) is not None

def train_voice_sample(audio_bytes):
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{st.secrets['VOICE_ID']}/edit"
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        requests.post(url, headers={"xi-api-key": st.secrets['ELEVENLABS_API_KEY']}, data={'name': 'Clone'}, files=files)
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
