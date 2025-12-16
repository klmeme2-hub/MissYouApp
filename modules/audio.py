import streamlit as st
import requests
import io
from openai import OpenAI
from pydub import AudioSegment
from .auth import get_current_user_id
from .config import ROLE_MAPPING

def generate_speech(text, tier):
    """
    雙引擎嘴巴：
    Basic -> OpenAI TTS (便宜)
    Advanced -> ElevenLabs (擬真)
    """
    # 1. 判斷等級
    if tier in ['advanced', 'eternal']:
        # --- 高級版：ElevenLabs ---
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
            headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
            data = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.7}}
            res = requests.post(url, json=data, headers=headers)
            if res.status_code == 200: return res.content
        except: pass
    
    # 2. 基礎版/備用：OpenAI TTS
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        return response.content
    except: return None

# --- 真實暱稱相關 (維持不變) ---
def upload_nickname_audio(supabase, role, audio_bytes):
    user_id = get_current_user_id()
    if not user_id: return False
    try:
        safe = ROLE_MAPPING.get(role, "others")
        path = f"{user_id}/nickname_{safe}.mp3"
        supabase.storage.from_("audio_clips").upload(path, audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"})
        return True
    except: return False

def get_nickname_audio_bytes(supabase, role):
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        safe = ROLE_MAPPING.get(role, "others")
        path = f"{user_id}/nickname_{safe}.mp3"
        return supabase.storage.from_("audio_clips").download(path)
    except: return None

def train_voice_sample(audio_bytes):
    # 只有高級會員才真正上傳訓練，避免浪費額度 (這裡先全開，實際運營可加判斷)
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{st.secrets['VOICE_ID']}/edit"
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        requests.post(url, headers={"xi-api-key": st.secrets['ELEVENLABS_API_KEY']}, data={'name':'Clone'}, files=files)
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
