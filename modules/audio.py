import streamlit as st
import requests
import io
from openai import OpenAI
from pydub import AudioSegment
from .auth import get_current_user_id
from .config import ROLE_MAPPING

def get_tts_engine_type(profile):
    return "elevenlabs"

def generate_speech(text, tier, specific_voice_id=None):
    """
    生成語音
    specific_voice_id: 若有指定(例如訪客的暫時ID)，則使用該ID，否則用系統預設
    """
    voice_id = specific_voice_id if specific_voice_id else st.secrets['VOICE_ID']
    
    # 1. ElevenLabs
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY'], "Content-Type": "application/json"}
        data = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}
        res = requests.post(url, json=data, headers=headers)
        if res.status_code == 200: return res.content
        else: print(f"EL Error: {res.text}")
    except: pass
    
    # 2. OpenAI Fallback
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        res = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        return res.content
    except: return None

# --- 進階功能：複製訪客聲音 ---
def clone_guest_voice(audio_bytes):
    """上傳訪客錄音，建立暫時 Voice ID"""
    try:
        url = "https://api.elevenlabs.io/v1/voices/add"
        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY']}
        files = {'files': ('guest_sample.mp3', io.BytesIO(audio_bytes), 'audio/mpeg')}
        data = {'name': 'Guest_Temp_Voice', 'description': 'Temporary guest voice'}
        response = requests.post(url, headers=headers, data=data, files=files)
        if response.status_code == 200:
            return response.json()['voice_id']
        return None
    except: return None

def delete_voice(voice_id):
    """刪除暫時的 Voice ID 以節省空間"""
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{voice_id}"
        headers = {"xi-api-key": st.secrets['ELEVENLABS_API_KEY']}
        requests.delete(url, headers=headers)
    except: pass

# --- 音訊處理 ---
def upload_audio_file(supabase, role, audio_bytes, file_type="nickname"):
    user_id = get_current_user_id()
    if not user_id: return False
    try:
        safe = ROLE_MAPPING.get(role, "others")
        path = f"{user_id}/{file_type}_{safe}.mp3"
        supabase.storage.from_("audio_clips").upload(path, audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"})
        return True
    except: return False

def get_audio_bytes(supabase, role, file_type="nickname"):
    user_id = get_current_user_id()
    if not user_id: return None
    try:
        safe = ROLE_MAPPING.get(role, "others")
        path = f"{user_id}/{file_type}_{safe}.mp3"
        return supabase.storage.from_("audio_clips").download(path)
    except: return None

def train_voice_sample(audio_bytes):
    try:
        url = f"https://api.elevenlabs.io/v1/voices/{st.secrets['VOICE_ID']}/edit"
        files = {'files': ('training_sample.mp3', audio_bytes, 'audio/mpeg')}
        requests.post(url, headers={"xi-api-key": st.secrets['ELEVENLABS_API_KEY']}, data={'name': 'Clone'}, files=files)
        return True
    except: return False

def merge_audio_clips(intro_bytes, main_bytes):
    try:
        if not intro_bytes: return main_bytes
        intro = AudioSegment.from_file(io.BytesIO(intro_bytes))
        main = AudioSegment.from_file(io.BytesIO(main_bytes))
        silence = AudioSegment.silent(duration=300)
        combined = intro + silence + main
        buffer = io.BytesIO()
        combined.export(buffer, format="mp3")
        return buffer.getvalue()
    except: return main_bytes

def merge_dialogue(dialogue_list):
    """合併多段對話音訊 (List of bytes)"""
    try:
        combined = AudioSegment.empty()
        silence = AudioSegment.silent(duration=400) # 對話間隔
        for audio_data in dialogue_list:
            if audio_data:
                seg = AudioSegment.from_file(io.BytesIO(audio_data))
                combined += seg + silence
        buffer = io.BytesIO()
        combined.export(buffer, format="mp3")
        return buffer.getvalue()
    except: return None
