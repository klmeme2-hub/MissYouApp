# modules/audio.py
import streamlit as st
import requests
import io
from pydub import AudioSegment
from modules.auth import get_current_user_id
from modules.config import ROLE_MAPPING

def get_elevenlabs_usage():
    try:
        key = st.secrets["ELEVENLABS_API_KEY"]
        url = "https://api.elevenlabs.io/v1/user/subscription"
        response = requests.get(url, headers={"xi-api-key": key})
        if response.status_code == 200:
            data = response.json()
            return data['character_count'], data['character_limit']
        return 0, 0
    except: return 0, 0

def upload_nickname_audio(supabase, role, audio_bytes):
    user_id = get_current_user_id()
    if not user_id: return False
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/nickname_{safe_role}.mp3"
        supabase.storage.from_("audio_clips").upload(
            file_path, audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        return True
    except Exception as e:
        print(f"Upload error: {e}")
        return False

def get_nickname_audio_bytes(supabase, role):
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        safe_role = ROLE_MAPPING.get(role, "others")
        file_path = f"{user_id}/nickname_{safe_role}.mp3"
        response = supabase.storage.from_("audio_clips").download(file_path)
        return response
    except: return None

def train_voice_sample(audio_bytes):
    try:
        key = st.secrets["ELEVENLABS_API_KEY"]
        voice_id = st.secrets["VOICE_ID"]
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}/edit"
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        data = {'name': 'My Digital Clone'} 
        requests.post(url, headers={"xi-api-key": key}, data=data, files=files)
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
